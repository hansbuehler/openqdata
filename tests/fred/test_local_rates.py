"""FRED transformation over an intentionally retained synthetic local input."""
from datetime import date
from pathlib import Path

import polars as pl
import pytest

import quantdata.fred.rates as rates


def test_fred_fallback_scaling_and_forward_fill(monkeypatch):
    source = pl.read_csv(Path(__file__).parents[1] / "stored_data/processed/fred/rates.csv", try_parse_dates=True)
    source = source.vstack(pl.DataFrame({"date": [date(2025, 1, 5)], "SOFR": [None], "EFFR": [None],
                                         "DGS1MO": [4.6], "DGS3MO": [None], "DGS6MO": [None]}, schema=source.schema)).reverse()
    def fetch(*, api_key, series_id, start, end):
        assert start == date(2025, 1, 2) and end == date(2025, 1, 5)
        return source.select("date", series_id)
    monkeypatch.setattr(rates, "_fetch_fred_series", fetch)
    monkeypatch.setenv("FRED_API_KEY", "local-test-placeholder")
    result = rates.load_fred_rates.__wrapped__("2025-01-02", "2025-01-05")
    assert result["date"].to_list() == [date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 5)]
    assert result["on"].to_list() == pytest.approx([0.0433, 0.0435, 0.046])
    assert result["effr"].to_list() == pytest.approx([0.0433, 0.0433, 0.0433])
    assert result["sofr"].null_count() == 1
    assert result["sofr"].drop_nulls().to_list() == pytest.approx([.0435, .0435])
    assert result["dgs1mo"].to_list() == pytest.approx([.045, .0455, .046])
    assert result["dgs3mo"].to_list() == pytest.approx([.044, .044, .044])
    assert result["dgs6mo"].to_list() == pytest.approx([.043, .0435, .0435])
    assert all(dtype == pl.Float32 for name, dtype in result.schema.items() if name != "date")
