from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal

from quantdata.massive import MassiveClient
from quantdata.massive.options.contracts import (
    REJECTED,
    ContractsFilter,
    filter_contracts,
)


def test_filter_contracts_value_ranges(monkeypatch) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "stored_data/processed/massive"
    contracts = json.loads((fixtures / "contracts-sample.json").read_text())
    monkeypatch.setattr(MassiveClient, "list_all_contracts_expiring_after_day", lambda *args, **kwargs: contracts)
    day_summary = MassiveClient.fetch_day_summary

    def split_day_summary(self, ticker, day, *, adjusted, can_be_none=False):
        if ticker == "SPY" and day == date(2023, 12, 29) and not adjusted:
            return {"close": 999.0}
        return day_summary(self, ticker, day, adjusted=adjusted, can_be_none=can_be_none)

    monkeypatch.setattr(MassiveClient, "fetch_day_summary", split_day_summary)
    contracts_filter = ContractsFilter(max_dte=25, max_mns=3.0, min_opt_vol_k=1)
    from quantdata.pool import PoolConfig

    df = filter_contracts.__wrapped__("SPY", date(2024, 1, 2), contracts_filter, exclude_half_days=True,
                                    pool_config=PoolConfig(num_workers=4, threading=True))
    expected = pl.read_parquet(next((fixtures / "contracts").glob("*/SPY/contracts/2024-01-02.prq")))
    expected = expected.filter(pl.col("ticker").is_in([c["ticker"] for c in contracts]))
    expected = expected.with_columns(pl.lit(999.0, dtype=pl.Float32).alias("spot_prev_close"))
    assert_frame_equal(df, expected, check_row_order=False)
    assert df["spot_adj_prev_close"][0] != df["spot_prev_close"][0]
    active = df.filter(pl.col("reject_code") == REJECTED.USED)

    known_codes = {
        REJECTED.USED,
        REJECTED.EXPIRY,
        REJECTED.MONEYNESS,
        REJECTED.VOLUME,
        REJECTED.PREV_VOLUME_MISSING,
        REJECTED.PREV_NO_QUOTES_OR_TRADES,
        REJECTED.NO_TODAY_QUOTES,
    }
    assert set(df["reject_code"].unique().to_list()).issubset(known_codes)

    assert df.filter(pl.col("days_to_exp") < 0).height == 0
    assert df.filter(pl.col("strike_price") <= 0).height == 0
    assert df.filter(pl.col("exp_date") < pl.lit(date(2024, 1, 2))).height == 0

    assert active.height > 0
    assert active.filter(pl.col("days_to_exp") > contracts_filter.max_dte).height == 0
    assert active.filter(pl.col("nms") > contracts_filter.max_mns).height == 0
    assert (
        active.filter(pl.col("approx_cash_vol_prev_k") < contracts_filter.min_opt_vol_k).height == 0
    )
