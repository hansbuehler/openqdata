"""Tests always use local fixtures and refuse network access."""
import os
import runpy
import socket
from pathlib import Path

import pytest

os.environ["OQ_DATA_TEST_MODE"] = "1"
os.environ["OQ_DATA_TEST_ROOT"] = str(Path(__file__).parent / "stored_data")

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network access is forbidden in qdata tests")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture
def synthetic_massive(monkeypatch):
    """Use real client conversions over invented endpoint payloads."""
    import polars as pl

    import quantdata.massive.expiries
    import quantdata.massive.tickers.data
    import quantdata.massive.tickers.filtered_history
    from quantdata.massive import MassiveClient
    from quantdata.yahoo import YFClient
    inputs = runpy.run_path(str(Path(__file__).parent / "stored_data/synthetic_massive.py"))
    for name in dir(MassiveClient):
        method = getattr(MassiveClient, name)
        if callable(method) and hasattr(method, '__wrapped__'):
            monkeypatch.setattr(MassiveClient, name, method.__wrapped__)
    monkeypatch.setattr(MassiveClient, '_get', lambda self, url, params=None: inputs['request'](url, params))
    monkeypatch.setattr(MassiveClient, '__call__', lambda self, url, params=None: inputs['request'](url, params))
    monkeypatch.setattr(MassiveClient, 'fetch_trades', lambda self, ticker, day: inputs['trades'](day))
    monkeypatch.setattr(MassiveClient, 'fetch_quotes', lambda self, ticker, day: inputs['quotes'](day))
    monkeypatch.setattr(MassiveClient, 'has_ticker_changes', lambda *a, **kw: pl.DataFrame(schema=MassiveClient.SCHEMA_HAS_TICKER_CHANGES))
    monkeypatch.setattr(YFClient, 'has_earnings', lambda *a, **kw: pl.DataFrame(schema=YFClient.SCHEMA_HAS_EARNINGS))
    return inputs
