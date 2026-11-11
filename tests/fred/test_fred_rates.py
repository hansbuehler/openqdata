"""Exercise FRED response conversion without network access."""
from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest

import oqdata.fred.rates as rates


@pytest.mark.parametrize("observations", [[], [
    {"date": "2025-01-02", "value": "."}, {"date": "2025-01-03", "value": "4.35"},
]])
def test_fetch_fred_series_converts_dates_values_and_missing(monkeypatch, observations):
    monkeypatch.setattr(rates.env, "require_live", lambda provider: None)
    def get(url, *, params, timeout):
        assert params["series_id"] == "SOFR"
        assert params["observation_start"] == "2025-01-02" and params["observation_end"] == "2025-01-03"
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"observations": observations})
    monkeypatch.setattr(rates.requests, "get", get)
    result = rates._fetch_fred_series("test-key", "SOFR", date(2025, 1, 2), date(2025, 1, 3))
    assert result.schema == {"date": pl.Date, "SOFR": pl.Float64}
    assert result["date"].to_list() == ([date(2025, 1, 2), date(2025, 1, 3)] if observations else [])
    assert result["SOFR"].to_list() == ([None, 4.35] if observations else [])


@pytest.mark.parametrize("error", [
    rates.requests.exceptions.HTTPError("500 Server Error for url: https://api.stlouisfed.org/fred/series/observations?api_key=secret-key&series_id=SOFR"),
    rates.requests.exceptions.ConnectionError("Max retries exceeded with url: /fred/series/observations?api_key=secret-key"),
    rates.requests.exceptions.ReadTimeout("HTTPSConnectionPool: Read timed out. (api_key=secret-key)"),
])
def test_fetch_fred_series_redacts_api_key_from_errors(monkeypatch, error):
    monkeypatch.setattr(rates.env, "require_live", lambda provider: None)
    def get(url, *, params, timeout):
        raise error
    monkeypatch.setattr(rates.requests, "get", get)
    with pytest.raises(type(error)) as err:
        rates._fetch_fred_series("secret-key", "SOFR", date(2025, 1, 2), date(2025, 1, 3))
    assert "secret-key" not in str(err.value) and "***" in str(err.value)
    assert err.value.__cause__ is None and err.value.__suppress_context__
    assert getattr(err.value, "response", None) is None
