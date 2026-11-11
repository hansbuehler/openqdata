from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest

from openqdata.massive import MassiveClient


@pytest.mark.parametrize("mapping_records", [False, True])
@pytest.mark.parametrize("days,expected", [(["2024-03-05", "2024-03-05", "2023-01-01"], [date(2024, 3, 5)]), (["2023-01-01"], []), ([], [])])
def test_ticker_changes_use_sdk_event_type(monkeypatch, days, expected, mapping_records):
    from massive.rest.models.tickers import TickerChange, TickerChangeEvent
    events = [TickerChangeEvent(date=day, type="ticker_change", ticker_change=TickerChange(ticker="NEW")) for day in days]
    if mapping_records:
        events = [{"date": day, "type": "ticker_change", "ticker_change": {"ticker": "NEW"}} for day in days]
    sdk = SimpleNamespace(get_ticker_events=lambda ticker: SimpleNamespace(events=events))
    monkeypatch.setattr(MassiveClient, "get_rest_client", staticmethod(lambda: sdk))
    frame = MassiveClient.has_ticker_changes.__wrapped__(MassiveClient(), "OLD", date(2024, 3, 1), date(2024, 3, 8))
    assert frame.schema == MassiveClient.SCHEMA_HAS_TICKER_CHANGES
    assert frame["date"].to_list() == expected
    assert frame["has_ticker_change"].to_list() == [True] * len(expected)
