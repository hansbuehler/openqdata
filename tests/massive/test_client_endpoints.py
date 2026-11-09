"""Replay invented Massive responses; sockets stay blocked by conftest."""
import runpy
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import polars as pl
import pytest
import requests

from quantdata.massive import MassiveClient
from quantdata.massive.processing import filter_valid_trades
from quantdata.massive.trade_conds import NORMAL_TRADE_EXCLUDE_FLAGS


@pytest.fixture
def responses():
    return runpy.run_path(str(Path(__file__).parents[1] / 'stored_data/synthetic_massive.py'))['responses']()


@pytest.fixture
def client(monkeypatch, responses):
    client = MassiveClient()
    for name in dir(MassiveClient):
        method = getattr(client, name)
        if callable(method) and hasattr(method, '__wrapped__'):
            monkeypatch.setattr(client, name, method.__wrapped__.__get__(client, MassiveClient))

    def get(url, params=None):
        path = urlsplit(url).path
        return runpy.run_path(str(Path(__file__).parents[1] / 'stored_data/synthetic_massive.py'))['request'](path, params)

    monkeypatch.setattr(client, 'get', get)
    return client


@pytest.mark.parametrize('name,args,kwargs', [
    ('ticker_reference_data', ('KWR',), {}),
    ('has_any_quotes_or_trades', ('KWR', date(2024, 1, 2)), {}),
    ('has_any_quotes', ('KWR', date(2024, 1, 2)), {}),
    ('has_any_trades', ('KWR', date(2024, 1, 2)), {}),
    ('fetch_trades', ('KWR', date(2024, 1, 2)), {}),
    ('fetch_quotes', ('KWR', date(2024, 1, 2)), {}),
    ('fetch_trades', ('O:SPY240102C00475000', date(2024, 1, 2)), {}),
    ('fetch_quotes', ('O:SPY240102C00475000', date(2024, 1, 2)), {}),
    ('fetch_bars', ('KWR', date(2024, 1, 2), date(2024, 1, 2)), {'adjusted': False, 'timespan': 'day'}),
    ('fetch_day_summary', ('KWR', date(2024, 1, 2)), {'adjusted': False}),
    ('fetch_day_summary', ('O:SPY240102C00475000', date(2024, 1, 2)), {'adjusted': False}),
    ('list_all_contracts_expiring_after_day', ('SPY', date(2024, 1, 2)), {'max_dte': 1}),
    ('list_all_contracts_for_expiry', ('SPY', date(2024, 1, 2), date(2024, 1, 2)), {}),
    ('option_contract_overview', ('O:SPY240102C00475000',), {'as_of': date(2024, 1, 2)}),
    ('get_dividends', ('SPY', date(2023, 12, 1), date(2024, 1, 3)), {}),
    ('get_splits', ('AAPL', date(2020, 8, 28), date(2020, 9, 2)), {}),
    ('adjustment_factors', ('AAPL', date(2020, 8, 28), date(2020, 9, 2)), {}),
    ('consistent_prev_close', ('KWR', date(2024, 1, 2)), {}),
])
def test_endpoint_response_conversion(client, name, args, kwargs):
    result = getattr(client, name)(*args, **kwargs)
    if isinstance(result, pl.DataFrame):
        assert result.height > 0
        schemas = {'fetch_trades': MassiveClient.SCHEMA_TRADES, 'fetch_quotes': MassiveClient.SCHEMA_QUOTES,
                   'fetch_bars': MassiveClient.SCHEMA_BARS, 'get_dividends': MassiveClient.SCHEMA_DIVIDENDS,
                   'get_splits': MassiveClient.SCHEMA_SPLITS}
        if name in schemas:
            assert result.schema == schemas[name]
        for column, dtype in result.schema.items():
            if dtype in (pl.Float32, pl.Float64):
                assert result[column].drop_nulls().is_finite().all()
        if name == 'get_splits':
            assert result.schema == MassiveClient.SCHEMA_SPLITS
            assert result['execution_date'].to_list() == [date(2020, 8, 31)]
    else:
        assert result


def test_option_bars_accept_provider_ticker_in_cache_key(client):
    # Use the cache wrapper: the old UID failed before reaching the endpoint.
    result = MassiveClient.fetch_bars(client, 'O:SPY240102C00475000', date(2024, 1, 2),
                                      date(2024, 1, 2), adjusted=False, timespan='day', override_cache_mode='off')
    assert result.height > 0
    assert result.schema == MassiveClient.SCHEMA_BARS


def test_missing_day_summary(client):
    assert client.fetch_day_summary('KWR', date(2024, 1, 6), adjusted=False, can_be_none=True) is None


def test_pagination_replays_synthetic_pages(client, monkeypatch, responses):
    pages = iter(responses['pagination_pages'])
    monkeypatch.setattr(client, 'get', lambda *args, **kwargs: next(pages))
    result = client.paginate(client.BASE_URL + '/v3/reference/options/contracts', {})
    assert len(result) == 2
    assert len({p['ticker'] for p in result}) == 2


@pytest.mark.parametrize('within_session', [True, False])
def test_closing_conditions_are_excluded_independently_of_session(client, monkeypatch, responses, within_session):
    rows = responses['closing_trade_sample']
    assert any(set(p.get('conditions', [])) & {8, 15, 19, 38} for p in rows)
    monkeypatch.setattr(client, 'get', lambda *args, **kwargs: {'results': rows})
    raw = client.fetch_trades('KWR', date(2024, 1, 2))
    assert raw.filter((pl.col('trade_code') & int(NORMAL_TRADE_EXCLUDE_FLAGS)) != 0).height > 0
    monkeypatch.setattr(MassiveClient, 'fetch_trades', lambda *args, **kwargs: raw)
    result = filter_valid_trades('KWR', date(2024, 1, 2), within_session=within_session)
    assert result.height > 0
    assert result.filter((pl.col('trade_code') & int(NORMAL_TRADE_EXCLUDE_FLAGS)) != 0).is_empty()


@pytest.mark.parametrize("ticker,trade_price,trade_size,trade_ns,bid,ask,quote_ns", [
    ("KWR", 101., 2., 1704205800000000000, 100., 102., 1704205800000000000),
    ("O:SPY240102C00475000", .5, 2., 1704205800000000000, .49, .51, 1704205800000000000),
])
def test_trade_and_quote_values(client, ticker, trade_price, trade_size, trade_ns, bid, ask, quote_ns):
    trades = client.fetch_trades(ticker, date(2024, 1, 2))
    quotes = client.fetch_quotes(ticker, date(2024, 1, 2))
    assert trades["price"][0] == pytest.approx(trade_price)
    assert trades["size"][0] == trade_size
    assert trades["ts_ns"].cast(pl.Int64)[0] == trade_ns
    assert quotes["bid_price"][0] == pytest.approx(bid)
    assert quotes["ask_price"][0] == pytest.approx(ask)
    assert quotes["ts_ns"].cast(pl.Int64)[0] == quote_ns


def test_daily_bar_values(client):
    bars = client.fetch_bars("KWR", date(2024, 1, 2), date(2024, 1, 2), adjusted=False, timespan="day")
    assert bars["ts_ms"].dt.date().to_list() == [date(2024, 1, 2)]
    assert bars.select("open", "high", "low", "close", "volume", "vwap", "num_trades").row(0) == pytest.approx(
        (101., 104., 100., 103., 123456., 102., 2345))


@pytest.mark.parametrize("name,schema", [
    ("fetch_trades", MassiveClient.SCHEMA_TRADES), ("fetch_quotes", MassiveClient.SCHEMA_QUOTES),
    ("fetch_bars", MassiveClient.SCHEMA_BARS),
])
def test_empty_market_responses_keep_schema(client, monkeypatch, name, schema):
    monkeypatch.setattr(client, "get", lambda *a, **k: {"results": []})
    args = ("KWR", date(2024, 1, 2)) + ((date(2024, 1, 2),) if name == "fetch_bars" else ())
    kwargs = {"adjusted": False, "timespan": "day"} if name == "fetch_bars" else {}
    result = getattr(client, name)(*args, **kwargs)
    assert result.is_empty() and result.schema == schema


def test_missing_reference_and_absent_observations(client, monkeypatch):
    monkeypatch.setattr(client, "get", lambda *a, **k: {"results": []})
    assert client.has_any_quotes("KWR", date(2024, 1, 2)) is False
    assert client.has_any_trades("KWR", date(2024, 1, 2)) is False
    with pytest.raises(FileNotFoundError):
        client.ticker_reference_data("KWR")


def test_invalid_bar_requests_fail_before_transport(client, monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("Invalid bar request reached transport")
    monkeypatch.setattr(client, "get", blocked)
    with pytest.raises(ValueError, match="timespan"):
        client.fetch_bars("KWR", date(2024, 1, 2), date(2024, 1, 2), adjusted=False, timespan="invalid")
    with pytest.raises(ValueError, match="start date"):
        client.fetch_bars("KWR", date(2024, 1, 3), date(2024, 1, 2), adjusted=False, timespan="day")
