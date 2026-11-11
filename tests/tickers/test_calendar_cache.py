"""Exercise calendar computation and its real cache writer without providers."""
import os
import subprocess
import sys
from pathlib import Path


def test_calendar_polars_cache_roundtrip(tmp_path):
    code = r"""
import socket
from datetime import date
import polars as pl
from polars.testing import assert_frame_equal
from cdxcore.verbose import Context
from oqdata.massive import MassiveClient
from oqdata.yahoo import YFClient
from oqdata.biz_calendar import DateRange
from oqdata.tickers.ticker_calendar import build_ticker_calendar, SCHEMA_TICKER_CALENDAR

def blocked(*args, **kwargs):
    raise AssertionError("Provider access is forbidden")
socket.socket.connect = blocked
MassiveClient.get_dividends = lambda *a, **k: pl.DataFrame(schema={"ex_dividend_date": pl.Date})
MassiveClient.get_splits = lambda *a, **k: pl.DataFrame(schema={"execution_date": pl.Date})
MassiveClient.has_ticker_changes = lambda *a, **k: pl.DataFrame(schema=MassiveClient.SCHEMA_HAS_TICKER_CHANGES)
YFClient.has_earnings = lambda *a, **k: pl.DataFrame(schema=YFClient.SCHEMA_HAS_EARNINGS)
period = DateRange(date(2024,3,1),date(2024,3,28))
first = build_ticker_calendar("FIXTURE", period, verbose=Context.quiet)
assert first.height == 2
assert first.schema == SCHEMA_TICKER_CALENDAR
MassiveClient.get_dividends = blocked
second = build_ticker_calendar("FIXTURE", period, verbose=Context.quiet)
assert_frame_equal(first, second)
"""
    settings = os.environ.copy()
    settings.update(OQ_DATA_TEST_MODE="0", OQ_DATA_ROOT=str(tmp_path / "data"),
                    OQ_DATA_CACHE_MODE="on", PYTHONDONTWRITEBYTECODE="1",
                    PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"))
    for name in ("OQ_DATA_CONFIG", "OQ_DATA_RAW", "OQ_DATA_PROCESSED"):
        settings.pop(name, None)
    result = subprocess.run([sys.executable, "-c", code], env=settings, cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
