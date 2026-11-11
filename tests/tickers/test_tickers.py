"""
Tests for ticker-level data loading utilities added in oqdata.massive.tickers
and the session-calendar helpers in oqdata.biz_calendar.

Mirrors the checks done manually in:
  poly/tickers/test_adj.ipynb
  poly/tickers/test_calendar.ipynb
  poly/tickers/test_filters.ipynb
  poly/expiries/test_expiries.ipynb
  poly/poly/test_fetch.ipynb
"""

from __future__ import annotations

import runpy
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.usefixtures("synthetic_massive")
synthetic = runpy.run_path(str(Path(__file__).resolve().parents[1] / "stored_data/synthetic_massive.py"))

# ---------------------------------------------------------------------------
# Session calendar helpers (no API key needed)
# ---------------------------------------------------------------------------


def test_session_open_close_normal_day() -> None:
    from oqdata.biz_calendar import session_open_close

    open_dt, close_dt, is_half_day = session_open_close(date(2024, 6, 17))

    assert open_dt.hour == 9 and open_dt.minute == 30
    assert close_dt.hour == 16 and close_dt.minute == 0
    assert not is_half_day


def test_session_open_close_half_day() -> None:
    from oqdata.biz_calendar import session_open_close

    # Black Friday 2024 (confirmed half day in test_biz_calendar.py)
    open_dt, close_dt, is_half_day = session_open_close(date(2024, 11, 29))

    assert open_dt.hour == 9 and open_dt.minute == 30
    assert close_dt.hour == 13 and close_dt.minute == 0
    assert is_half_day


def test_full_second_grid_ns_normal_day() -> None:
    from oqdata.biz_calendar import full_second_grid_ns, session_open_close

    open_dt, close_dt, _ = session_open_close(date(2024, 6, 17))
    grid = full_second_grid_ns(open_dt, close_dt)

    assert isinstance(grid, pl.Series)

    # last bin key is close_dt - 1s
    last = grid[-1].replace(tzinfo=None)
    expected = (close_dt - timedelta(seconds=1)).replace(tzinfo=None)
    assert last == expected


# ---------------------------------------------------------------------------
# classify_expiry (no API key needed)
# ---------------------------------------------------------------------------


def test_classify_expiry_normal_day() -> None:
    from oqdata.massive.expiries import classify_expiry

    # June 24 is after the third Friday of June 2024 (Jun 21), so it can never be
    # selected as the monthly expiry date and is always classified NONE.
    df = classify_expiry(pl.DataFrame({"date": [date(2024, 6, 24)]}))
    assert df["has_expiry"][0] == 0  # EXPIRY.NONE


def test_classify_expiry_monthly() -> None:
    from oqdata.massive.expiries import classify_expiry

    # Third Friday of January 2024 = Jan 19
    df = classify_expiry(pl.DataFrame({"date": [date(2024, 1, 19)]}))
    assert df["has_expiry"][0] == 3  # EXPIRY.MONTHLY


def test_classify_expiry_quad_witching() -> None:
    from oqdata.massive.expiries import classify_expiry

    # Third Friday of March 2024 = Mar 15 (quad witching)
    df = classify_expiry(pl.DataFrame({"date": [date(2024, 3, 15)]}))
    assert df["has_expiry"][0] == 2  # EXPIRY.QUAD_WITCHING


def test_classify_expiry_is_independent_of_other_rows() -> None:
    from oqdata.massive.expiries import classify_expiry

    # Each date is classified on its own: weeklies are not monthly expiries, and the
    # month's standard expiry is recognised without the rest of the month present.
    single = {d: classify_expiry(pl.DataFrame({"date": [d]}))["has_expiry"][0]
              for d in (date(2024, 6, 7), date(2024, 6, 21), date(2024, 6, 28), date(2022, 4, 14), date(2024, 1, 19))}
    assert single == {date(2024, 6, 7): 0, date(2024, 6, 21): 2, date(2024, 6, 28): 0,
                      date(2022, 4, 14): 3, date(2024, 1, 19): 3}
    df = classify_expiry(pl.DataFrame({"date": list(single), "x": range(len(single))}))
    assert dict(zip(df["date"].to_list(), df["has_expiry"].to_list())) == single
    assert df.columns == ["date", "x", "has_expiry"]


@pytest.mark.parametrize("day,expiring,expected", [
    (date(2024, 6, 7), True, 1),    # weekly -> STANDARD
    (date(2024, 6, 21), True, 2),   # June standard expiry -> QUAD_WITCHING
    (date(2024, 1, 19), True, 3),   # MONTHLY
    (date(2022, 4, 14), True, 3),   # shifted monthly before Good Friday
    (date(2024, 6, 21), False, None),
])
def test_ticker_expiries_day_codes(monkeypatch, day, expiring, expected) -> None:
    from oqdata.massive import expiries

    rows = [{"expiration_date": day.isoformat(), "ticker": "O:SPY"}] if expiring else []
    monkeypatch.setattr(expiries.MassiveClient, "paginate", lambda self, url, params: rows)
    assert expiries.ticker_expiries_day("SPY", day) == (day, expected)


def test_classify_expiry_shifted_when_friday_is_holiday() -> None:
    from oqdata.massive.expiries import classify_expiry

    # Good Friday 2022 (Apr 15) is a market holiday — the third Friday of April falls on it.
    # When only trading days are passed (Apr 15 absent), expiry shifts to Thu Apr 14.
    df = classify_expiry(
        pl.DataFrame({"date": [date(2022, 4, 13), date(2022, 4, 14), date(2022, 4, 19)]})
    )
    codes = dict(zip(df["date"].to_list(), df["has_expiry"].to_list()))
    assert codes[date(2022, 4, 14)] == 3  # shifted monthly expiry (EXPIRY.MONTHLY)
    assert codes[date(2022, 4, 13)] == 0  # normal day (EXPIRY.NONE)


# ---------------------------------------------------------------------------
# Reference data and adjustment factors
# ---------------------------------------------------------------------------


def test_get_listing_date() -> None:
    from oqdata.massive.tickers.basics import get_listing_date

    d = get_listing_date("SPY")

    assert isinstance(d, date)
    assert d < date(2000, 1, 1)  # SPY listed Jan 1993


def test_adjustment_factors_aapl(monkeypatch) -> None:
    from oqdata.massive import MassiveClient

    client = MassiveClient()
    df = client.adjustment_factors("AAPL", date(2020, 1, 1), date(2021, 1, 1))

    assert isinstance(df, pl.DataFrame)
    assert df.height > 0
    assert set(df.columns) == {"date", "adjfactor"}
    before = df.filter(pl.col("date").is_in([date(2020, 8, 27), date(2020, 8, 28)]))
    after = df.filter(pl.col("date").is_in([date(2020, 8, 31), date(2020, 9, 1)]))
    assert before["date"].to_list() == [date(2020, 8, 27), date(2020, 8, 28)]
    assert after["date"].to_list() == [date(2020, 8, 31), date(2020, 9, 1)]
    assert before["adjfactor"].to_list() == pytest.approx([0.25, 0.25])
    assert after["adjfactor"].to_list() == pytest.approx([1., 1.])


# ---------------------------------------------------------------------------
# Filtered daily history (mirrors test_filters.ipynb)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker,start,end,expected_symbols", [
    ("SPY", date(2023, 1, 1), date(2024, 1, 1), {"SPY"}),
    ("META", date(2021, 1, 1), date(2023, 1, 1), {"FB", "META"}),
    ("VXX", date(2023, 1, 1), date(2024, 1, 1), {"VXX"}),
    ("ARKK", date(2023, 1, 1), date(2024, 1, 1), {"ARKK"}),
])
def test_ticker_filtered_history(ticker, start, end, expected_symbols) -> None:
    from oqdata.massive.tickers.filtered_history import ticker_filtered_history

    # Execute history processing over invented bars, including cache bypass.
    df = ticker_filtered_history(ticker, start, end, num_workers=0, override_cache_mode="off")
    assert df.height > 0
    assert set(df.columns) == {
        "date", "ticker", "cash_vol", "n_trades", "return_open_prev_close", "return_close_open",
    }
    assert set(df["ticker"].to_list()) & expected_symbols
    assert df["date"].is_sorted()
    assert df["date"].n_unique() == df.height
    assert df["cash_vol"].is_finite().all()
    assert df["cash_vol"].min() > 0
    assert df["n_trades"].min() > 0
    assert df["return_open_prev_close"].is_finite().all()
    assert df["return_close_open"].is_finite().all()


# ---------------------------------------------------------------------------
# Ticker calendar (mirrors test_calendar.ipynb)
# ---------------------------------------------------------------------------


def test_build_ticker_calendar_spy() -> None:
    from oqdata.biz_calendar import DateRange
    from oqdata.tickers.ticker_calendar import build_ticker_calendar

    dr = DateRange(date(2024, 1, 2), date(2024, 3, 31))
    df = build_ticker_calendar.__wrapped__("SPY", dr)

    assert isinstance(df, pl.DataFrame)
    assert df.height > 0
    assert "date" in df.columns
    assert "expiry_code" in df.columns


# ---------------------------------------------------------------------------
# Option expiry flags (mirrors test_expiries.ipynb — short window to stay fast)
# ---------------------------------------------------------------------------


def test_ticker_expiries_short_window() -> None:
    from oqdata.biz_calendar import get_business_days
    from oqdata.massive.expiries import ticker_expiries

    days = get_business_days(date(2024, 1, 2), date(2024, 1, 19))  # ~13 trading days
    df = ticker_expiries("SPY", days, num_workers=4, threading=True)

    assert isinstance(df, pl.DataFrame)
    assert "date" in df.columns
    assert "has_expiry" in df.columns


# ---------------------------------------------------------------------------
# Tick-level trade data (mirrors test_fetch.ipynb)
# ---------------------------------------------------------------------------


def test_build_unadjusted_trades(monkeypatch) -> None:
    from oqdata.massive import MassiveClient
    from oqdata.massive.tickers.data import build_unadjusted_trades

    sample = synthetic["trades"](date(2024, 1, 2))
    monkeypatch.setattr(MassiveClient, "fetch_trades", lambda self, ticker, d: sample)
    df = build_unadjusted_trades.__wrapped__("SPY", date(2024, 1, 2))
    assert df.height == 1000
    assert df["price"].is_finite().all()
    assert df["price"].min() > 0

    assert isinstance(df, pl.DataFrame)
    assert df.height > 0
    assert set(df.columns) >= {"ts_ns", "price", "size"}


def test_build_1s_trade_bars() -> None:
    from oqdata.massive.tickers.data import build_1s_trade_bars

    sample = synthetic["trades"](date(2024, 1, 2))
    df = build_1s_trade_bars("SPY", date(2024, 1, 2), trades=sample)
    assert df["num_trades"].sum() == sample.height
    assert df.height == 23400
    traded = df.filter(pl.col("num_trades") > 0)
    assert traded.filter(pl.col("low") > pl.col("high")).is_empty()

    assert isinstance(df, pl.DataFrame)
    assert df.height > 0
    assert "dt_ns" in df.columns
    assert "num_trades" in df.columns
    assert "log_cash_volume" in df.columns


def test_supplied_trades_bypass_the_cache(monkeypatch) -> None:
    from oqdata.massive.tickers import data

    def cached(*args, **kwargs):
        raise AssertionError("caller-supplied trades must not read or write the default cache")
    monkeypatch.setattr(data, "_build_1s_trade_bars_cached", cached)
    sample = synthetic["trades"](date(2024, 1, 2))
    full = data.build_1s_trade_bars("SPY", date(2024, 1, 2), trades=sample)
    half = data.build_1s_trade_bars("SPY", date(2024, 1, 2), trades=sample.head(sample.height // 2))
    assert full["num_trades"].sum() == sample.height
    assert half["num_trades"].sum() == sample.height // 2
    with pytest.raises(AssertionError, match="default cache"):
        data.build_1s_trade_bars("SPY", date(2024, 1, 2))
