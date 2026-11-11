"""Contract rejection and split-coordinate checks with invented provider inputs."""
from __future__ import annotations

from datetime import date

import polars as pl
import pytest
from click.testing import CliRunner

from oqdata.massive import MassiveClient
from oqdata.massive.options import contracts
from oqdata.massive.options.contracts import (
    REJECTED,
    ContractsFilter,
    filter_contracts,
)
from oqdata.pool import PoolConfig


def test_filter_contracts_value_ranges(monkeypatch, synthetic_massive) -> None:
    cases = dict(used=REJECTED.USED, expiry=REJECTED.EXPIRY, moneyness=REJECTED.MONEYNESS,
                 volume=REJECTED.VOLUME, no_previous=REJECTED.PREV_NO_QUOTES_OR_TRADES,
                 no_today=REJECTED.NO_TODAY_QUOTES)
    contracts = [synthetic_massive['contract'](
        name, expiry='2024-06-21' if name == 'expiry' else '2024-01-19',
        strike=200. if name == 'moneyness' else 100.,
    ) for name in cases]
    monkeypatch.setattr(MassiveClient, 'list_all_contracts_expiring_after_day', lambda *a, **kw: contracts)

    def summary(self, ticker, day, *, adjusted, can_be_none=False):
        if ticker == 'SPY':
            close = 50. if adjusted else 999. if day == date(2023, 12, 29) else 100.
            return dict(open=close, close=close, volume=10000.)
        return dict(open=.5, close=.5, volume=500. if ticker == 'volume' else 2000.)

    def activity(self, ticker, day):
        if ticker == 'no_previous' and day == date(2023, 12, 29):
            return False, False
        return ticker != 'no_today' or day != date(2024, 1, 2), True

    monkeypatch.setattr(MassiveClient, 'fetch_day_summary', summary)
    monkeypatch.setattr(MassiveClient, 'has_any_quotes_or_trades', activity)
    config = ContractsFilter(max_dte=25, max_mns=3., min_opt_vol_k=1.)
    frame = filter_contracts.__wrapped__('SPY', date(2024, 1, 2), config, exclude_half_days=True,
                                        pool_config=PoolConfig(num_workers=4, threading=True))
    actual = dict(zip(frame['ticker'], frame['reject_code'], strict=True))
    assert actual == cases
    assert frame['spot_prev_close'].unique().to_list() == [999.]
    assert frame['spot_adj_prev_close'].unique().to_list() == [50.]
    assert frame['spot_ref_prev_close'].unique().to_list() == [100.]
    active = frame.filter(pl.col('reject_code') == REJECTED.USED)
    assert active['ticker'].to_list() == ['used']
    assert active['approx_cash_vol_prev_k'].to_list() == [1.]
    assert active['nms'].to_list() == [0.]


@pytest.mark.parametrize("flag,exclude_half_days", [([], True), (["--halfdays"], False)])
def test_contracts_cli_honours_halfdays_and_passes_dates(monkeypatch, flag, exclude_half_days):
    seen = []
    monkeypatch.setattr(contracts, "filter_contracts_between", lambda ticker, date_range, **kw: seen.append((ticker, date_range)))
    result = CliRunner().invoke(contracts.main, ["SPY", "QQQ", "--period", "2024-12-20", "2024-12-31", "--workers", "0", *flag])
    assert result.exit_code == 0, result.output
    assert [t for t, _ in seen] == ["SPY", "QQQ"]
    for _, date_range in seen:
        assert date_range.exclude_half_days is exclude_half_days
        assert (date_range.start, date_range.end) == (date(2024, 12, 20), date(2024, 12, 31))
        assert type(date_range.start) is date and "00:00" not in str(date_range)
