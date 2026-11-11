"""Offline market-processing contracts over independent synthetic observations."""
from datetime import date

import numpy as np
import polars as pl
import pytest

from openqdata.massive.processing import (
    SCHEMA_ALIGN_QUOTES_TO_TRADES,
    SCHEMA_ALIGN_TRADES_TO_QUOTES,
    align_quotes_to_trades,
    align_trades_to_quotes,
    filter_valid_quotes,
    filter_valid_trades,
)
from openqdata.massive.testing.scope import DATES, TICKERS

pytestmark = pytest.mark.usefixtures("synthetic_massive")


@pytest.mark.parametrize("within_session", [False, True])
def test_valid_observations(within_session):
    trades = filter_valid_trades(TICKERS[0], DATES[0], within_session)
    quotes = filter_valid_quotes(TICKERS[0], DATES[0], within_session)
    assert trades.height > 0 and quotes.height > 0
    assert trades["ts_ns"].is_sorted() and quotes["ts_ns"].is_sorted()
    assert trades["ts_ns"].n_unique() == trades.height
    for frame, columns in [(trades, ["price", "size"]), (quotes, ["bid_price", "ask_price", "bid_size", "ask_size"])]:
        for column in columns:
            assert frame[column].is_finite().all()
            assert (frame[column] > 0).all()
    assert (quotes["ask_price"] > quotes["bid_price"]).all()

@pytest.mark.parametrize("within_session", [False, True])
@pytest.mark.parametrize("direction", ["quotes_to_trades", "trades_to_quotes"])
def test_alignment_keeps_observations_and_enforces_match_rules(direction, within_session):
    function, schema, matched_ts = (
        (align_quotes_to_trades, SCHEMA_ALIGN_QUOTES_TO_TRADES, "quote_ts_ns")
        if direction == "quotes_to_trades" else
        (align_trades_to_quotes, SCHEMA_ALIGN_TRADES_TO_QUOTES, "trade_ts_ns")
    )
    complete = function(TICKERS[0], DATES[0], within_session=within_session, drop_unmatched=False)
    matched = function(TICKERS[0], DATES[0], within_session=within_session, drop_unmatched=True)
    assert complete.height >= matched.height > 0
    assert set(complete.columns) == set(schema)
    assert set(matched.columns) == set(schema)
    assert matched[matched_ts].null_count() == 0
    assert matched["ts_ns"].is_sorted()
    expected = complete.filter(pl.col(matched_ts).is_not_null())
    from polars.testing import assert_frame_equal
    assert_frame_equal(matched, expected)
    price = matched["price"].to_numpy()
    assert np.all(price >= matched["bid_price"].to_numpy())
    assert np.all(price <= matched["ask_price"].to_numpy())
