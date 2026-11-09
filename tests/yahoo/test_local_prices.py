"""Yahoo transformations use local synthetic data; downloads are replaced."""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import quantdata.yahoo.client as yahoo


@pytest.fixture
def local_prices(monkeypatch):
    source = pd.read_csv(Path(__file__).parents[1] / "stored_data/processed/yahoo/prices.csv", parse_dates=["date"]).set_index("date")
    downloaded = source.copy()
    downloaded.columns = pd.MultiIndex.from_product([source.columns, ["TEST"]])
    monkeypatch.setattr(yahoo.yf, "download", lambda *a, **kw: downloaded.copy())
    client = yahoo.YFClient()
    monkeypatch.setattr(client, "validate_status", lambda: None)
    return client, source, downloaded


def test_local_yahoo_price_schema(local_prices):
    client, expected, _ = local_prices
    result = yahoo.YFClient.prices.__wrapped__(client, "TEST", date(2025, 1, 2), date(2025, 1, 4))
    np.testing.assert_array_equal(result["Close"], expected["Close"])
    assert set(result.columns) == client.PRICE_FIELDS
    assert all(dtype == np.dtype("float64") for dtype in result.dtypes)


def test_invalid_yahoo_price_raises_data_error_with_context(local_prices, monkeypatch):
    client, _, downloaded = local_prices
    downloaded.loc[:, ("Close", "TEST")] = 0
    monkeypatch.setattr(yahoo.yf, "download", lambda *a, **kw: downloaded)
    with pytest.raises(yahoo.DataError, match="Closing prices") as error:
        yahoo.YFClient.prices.__wrapped__(client, "TEST", date(2025, 1, 2), date(2025, 1, 4))
    assert error.value.context["ticker"] == "TEST"


def test_missing_yahoo_field_with_extra_column_is_rejected(local_prices, monkeypatch):
    client, _, downloaded = local_prices
    downloaded = downloaded.drop(columns="Close", level=0)
    downloaded[("Extra", "TEST")] = 1
    monkeypatch.setattr(yahoo.yf, "download", lambda *a, **kw: downloaded)
    with pytest.raises(AttributeError, match="missing column headers"):
        yahoo.YFClient.prices.__wrapped__(client, "TEST", date(2025, 1, 2), date(2025, 1, 4))


def test_yahoo_end_date_is_inclusive(local_prices, monkeypatch):
    client, _, downloaded = local_prices
    calls = []
    def download(ticker, *, start, end, **kwargs):
        calls.append((start, end))
        return downloaded.copy()
    monkeypatch.setattr(yahoo.yf, "download", download)
    yahoo.YFClient.prices.__wrapped__(client, "TEST", date(2025, 1, 2), date(2025, 1, 3))
    assert calls == [(date(2025, 1, 2), date(2025, 1, 4))]  # yfinance's 'end' is exclusive
