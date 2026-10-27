"""FRED transformation over an intentionally retained synthetic local input."""
from datetime import date
from pathlib import Path

import polars as pl
import pytest

import quantdata.fred.rates as rates


def test_fred_fallback_scaling_and_forward_fill(monkeypatch):
    source = pl.read_csv(Path(__file__).parents[1] / "stored_data/processed/fred/rates.csv", try_parse_dates=True)
    def fetch(*, api_key, series_id, start, end):
        assert start == date(2025, 1, 2) and end == date(2025, 1, 4)
        return source.select("date", series_id)
    monkeypatch.setattr(rates, "_fetch_fred_series", fetch)
    monkeypatch.setenv("FRED_API_KEY", "local-test-placeholder")
    result = rates.load_fred_rates.__wrapped__("2025-01-02", "2025-01-04")
    assert result.height == 2
    assert result["on"].to_list() == pytest.approx([0.0433, 0.0435])
    assert result["effr"].to_list() == pytest.approx([0.0433, 0.0433])
    assert result["sofr"].null_count() == 1
    assert all(dtype == pl.Float32 for name, dtype in result.schema.items() if name != "date")
