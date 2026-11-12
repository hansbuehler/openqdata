from datetime import date

import pytest

from openqdata import env
from openqdata.fred import FREDClient
from openqdata.fred.rates import _fetch_fred_series, load_fred_rates
from openqdata.massive import MassiveClient
from openqdata.vixdata import CboeClient, load_cboe_vix, refresh_cboe_vix
from openqdata.widb import WIDBClient
from openqdata.yahoo import YFClient


@pytest.mark.parametrize("operation", [
    lambda: _fetch_fred_series("unused", "SOFR", date(2025, 1, 1), date(2025, 1, 2)),
    refresh_cboe_vix,
    lambda: load_cboe_vix(refresh=True),
    FREDClient.api_key,
    lambda: FREDClient().fetch_series("SOFR", date(2025, 1, 1), date(2025, 1, 2)),
    lambda: CboeClient().refresh_vix(),
    lambda: CboeClient().load_vix(refresh=True),
    MassiveClient.get_token,
    WIDBClient.connect,
    lambda: YFClient().validate_status(),
])
def test_live_entry_points_refuse_fixture_mode(operation):
    with pytest.raises(RuntimeError, match="test mode|disabled"):
        operation()


def test_missing_fred_cache_does_not_fall_back_to_network(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(Exception) as error:
        load_fred_rates("1901-01-01", "1901-01-02")
    assert not isinstance(error.value, AssertionError), "A missing fixture attempted network access"


def test_missing_cboe_cache_does_not_fall_back_to_network(monkeypatch):
    import openqdata.vixdata.cboe as cboe
    monkeypatch.setattr(cboe._raw_cache, "read", lambda *a, **kw: None)
    with pytest.raises(RuntimeError, match="disabled"):
        load_cboe_vix()
