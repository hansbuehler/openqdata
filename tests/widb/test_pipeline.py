"""Exercise real cleaning, selection, fitting and packing from stored observations.

Only provider retrieval is replaced. No processing function or optimizer is mocked.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
import pytest
from cdxcore.subdir import SubDir
from cdxcore.verbose import Context

from quantdata.arbfree.arbfree import ArbFreePricer, MkArbFree
from quantdata.biz_calendar import DateRange
from quantdata.pool import PoolConfig
from quantdata.widb import WIDBClient, timeseries
from quantdata.widb.arbfree import mk_arb_free_day
from quantdata.widb.day import ExpiryFilter, RawDayFilter, collect_raw_day, enrich_day
from quantdata.widb.options_filter import OptionsFilter, filter_options_day
from quantdata.widb.timeseries import TimeSeriesDefinition, build_time_series

FIXTURES = Path(__file__).resolve().parents[1] / "stored_data"
DAY = date(2005, 11, 21)


@pytest.fixture
def provider_inputs(monkeypatch, request: pytest.FixtureRequest) -> dict:
    """Read required local vendor files, bypassing only versioned vendor-cache lookup."""
    root = FIXTURES / "raw/widb"
    day = getattr(request, "param", DAY)
    quotes = pd.read_parquet(root / "options/108105" / f"{day}.pdq")
    forwards = pd.read_parquet(root / "forwards/108105" / f"{day}.pdq")
    curve = pd.read_parquet(root / "zero_curve" / f"{day}.pdq")

    def spot(self, secid, day, **kwargs):
        directory = SubDir(str(root / "spot_price/108105"), fmt=SubDir.PICKLE, create_directory=False)
        return directory.read(str(day), version="*", delete_wrong_version=False, raise_on_error=True)

    monkeypatch.setattr(WIDBClient, "lookup_secid", lambda self, ticker: 108105)
    monkeypatch.setattr(WIDBClient, "options", lambda self, secid, d, **kw: quotes.copy(deep=True) if d == day else pd.read_parquet(root / "options/108105" / f"{d}.pdq"))
    monkeypatch.setattr(WIDBClient, "forwards", lambda self, secid, d, **kw: forwards.copy(deep=True) if d == day else pd.read_parquet(root / "forwards/108105" / f"{d}.pdq"))
    monkeypatch.setattr(WIDBClient, "zero_curve", lambda self, d, **kw: curve.copy(deep=True) if d == day else pd.read_parquet(root / "zero_curve" / f"{d}.pdq"))
    monkeypatch.setattr(WIDBClient, "spot_price", spot)
    return {"quotes": quotes, "forwards": forwards, "curve": curve}


@pytest.fixture
def market_day(provider_inputs) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = collect_raw_day("SPX", DAY, RawDayFilter(), override_cache_mode="off", verbose=Context.quiet)
    enriched = enrich_day("SPX", DAY, raw_data=raw, override_cache_mode="off", verbose=Context.quiet)
    assert not raw.empty and not enriched.empty
    return raw, enriched


def test_raw_cleaning_rejects_bad_quotes_before_pairing(provider_inputs, monkeypatch) -> None:
    quotes = provider_inputs["quotes"]
    # Inject one valid pair, invalid call sides and one unmatched call. The put
    # sides remain valid, proving that rejected calls cannot survive pairing.
    template = quotes.loc[quotes.cp_flag.astype(str).str.upper() == "C"].iloc[0]
    extra = []
    reasons = ["valid", "floor", "missing_bid", "missing_ask", "locked", "crossed", "same_day", "irregular", "settlement", "bad_symbol", "unpaired"]
    strike_by_reason = {}
    for i, reason in enumerate(reasons):
        strike = float(quotes.strike_price.max()) + 100 + i
        strike_by_reason[reason] = strike
        for side in (["C"] if reason == "unpaired" else ["C", "P"]):
            row = template.copy()
            row["cp_flag"], row["strike_price"] = side, strike
            row["optionid"] = int(quotes.optionid.max()) + 2 * i + (side == "P") + 1
            row["symbol"] = f"offline-{reason}-{side}"
            row["best_bid"], row["best_offer"] = .02, .04
            row["volume"], row["open_interest"], row["ss_flag"] = 0, 0, "0"
            if side == "C":
                if reason == "floor": row["best_bid"] = .011
                if reason == "missing_bid": row["best_bid"] = np.nan
                if reason == "missing_ask": row["best_offer"] = np.nan
                if reason == "locked": row["best_bid"] = .04
                if reason == "crossed": row["best_bid"] = .05
                if reason == "same_day": row["exdate"] = pd.Timestamp(DAY)
                if reason == "irregular": row["exdate"] = pd.Timestamp("2025-01-09")
                if reason == "settlement": row["ss_flag"] = "1"
                if reason == "bad_symbol": row["symbol"] = "SPZ.OT"
            extra.append(row)
    contaminated = pd.concat([quotes, pd.DataFrame(extra)], ignore_index=True)
    monkeypatch.setattr(WIDBClient, "options", lambda *args, **kwargs: contaminated.copy(deep=True))
    result = collect_raw_day("SPX", DAY, RawDayFilter(), override_cache_mode="off", verbose=Context.quiet)
    strikes = set(result.strike)
    assert strike_by_reason["valid"] in strikes
    assert not strikes.intersection(strike_by_reason[r] for r in reasons if r != "valid")
    valid = result.loc[result.strike == strike_by_reason["valid"]].iloc[0]
    assert valid.mkt_call_log_volume == valid.mkt_put_log_volume == 0
    assert valid.mkt_call_log_open_interest == valid.mkt_put_log_open_interest == 0
    assert np.all(result.mkt_call_bid > .011) and np.all(result.mkt_put_bid > .011)
    assert np.all(result.mkt_call_bid < result.mkt_call_ask)
    assert np.all(result.mkt_put_bid < result.mkt_put_ask)


@pytest.mark.parametrize(("either", "both", "keep"), [(10, 4, True), (9, 4, False), (10, 3, False)])
def test_enrichment_trade_requirements_are_per_expiry(market_day, either: int, both: int, keep: bool) -> None:
    raw, baseline = market_day
    expiry = baseline.expiry_id.value_counts().index[0]
    surviving = baseline.loc[baseline.expiry_id == expiry, "strike"].iloc[:10]
    assert len(surviving) == 10
    modified = raw.copy(deep=True)
    mask = modified.expiry_id == expiry
    modified.loc[mask, ["mkt_call_log_volume", "mkt_put_log_volume"]] = 0.
    modified.loc[:, ["mkt_call_log_open_interest", "mkt_put_log_open_interest"]] = 0.
    for i, strike in enumerate(surviving):
        row = mask & (modified.strike == strike)
        if i < either: modified.loc[row, "mkt_call_log_volume"] = np.float32(np.log10(2.))
        if i < both: modified.loc[row, "mkt_put_log_volume"] = np.float32(np.log10(2.))
    enriched = enrich_day("SPX", DAY, raw_data=modified, override_cache_mode="off", verbose=Context.quiet)
    assert (expiry in set(enriched.expiry_id)) == keep
    assert set(baseline.expiry_id) - {expiry} <= set(enriched.expiry_id)
    if keep:
        same_expiry = enriched.loc[enriched.expiry_id == expiry]
        assert (same_expiry.log_volume == 0).any()  # untraded rows remain
        assert np.all(same_expiry.log_open_interest == 0)
        np.testing.assert_allclose(same_expiry.pure_strike, same_expiry.strike / same_expiry.fwd, rtol=1e-6)
        assert np.all(same_expiry.pure_ask_price > same_expiry.pure_bid_price)


def test_eligible_filter_boundaries_and_am_default(market_day) -> None:
    _, enriched = market_day
    frame = pd.concat([enriched.iloc[:1]] * 26, ignore_index=True)
    frame.index = [f"control-{i}" for i in range(16)] + ["nms-low", "nms-high", "outside-low", "outside-high", "maturity-edge", "too-long", "thin-volume", "thin-oi", "am", "rank-only"]
    for field, value in {"bdte": 20., "nms": 0., "nms_atm": 0., "log_volume": 1., "log_open_interest": 1., "is_am": False}.items():
        frame[field] = np.full(len(frame), value, dtype=enriched[field].dtype)
    frame.loc["nms-low", "nms_atm"] = -5.
    frame.loc["nms-high", "nms_atm"] = 2.
    frame.loc["outside-low", "nms_atm"] = -5.01
    frame.loc["outside-high", "nms_atm"] = 2.01
    frame.loc["maturity-edge", "bdte"] = 756.
    frame.loc["too-long", "bdte"] = 757.
    frame.loc["thin-volume", "log_volume"] = .999
    frame.loc["thin-oi", "log_open_interest"] = .999
    frame.loc["am", "is_am"] = True
    frame.loc["rank-only", "nms"] = 100.  # window uses ATM NMS, not cap ranking NMS
    config = OptionsFilter(normalize=False)
    result = filter_options_day("SPX", DAY, source_data=frame, mk_arb_free=None, options_filter=config, verbose=Context.quiet)
    rejected = {"outside-low", "outside-high", "too-long", "thin-volume", "thin-oi"}
    assert set(result.index) == set(frame.index) - rejected
    without_am = filter_options_day("SPX", DAY, source_data=frame, mk_arb_free=None, options_filter=replace(config, remove_am=True), verbose=Context.quiet)
    assert set(without_am.index) == set(result.index) - {"am"}


def test_expiry_minimum_is_checked_after_eligibility(market_day) -> None:
    _, enriched = market_day
    frame = pd.concat([enriched.iloc[:1]] * 20, ignore_index=True)
    frame["expiry_id"] = np.array([1] * 10 + [2] * 10, dtype=enriched.expiry_id.dtype)
    for field, value in {"bdte": 20., "nms": 0., "nms_atm": 0., "log_volume": 1., "log_open_interest": 1.}.items():
        frame[field] = np.full(len(frame), value, dtype=enriched[field].dtype)
    frame.loc[19, "log_volume"] = 0.
    result = filter_options_day("SPX", DAY, source_data=frame, mk_arb_free=None, options_filter=OptionsFilter(normalize=False), verbose=Context.quiet)
    assert result.index.tolist() == list(range(10))  # nine remaining rows drop the whole second expiry


def test_count_cap_reserves_farther_expiry_instead_of_only_global_atm(market_day) -> None:
    _, enriched = market_day
    frame = pd.concat([enriched.iloc[:1]] * 40, ignore_index=True)
    frame["expiry_id"] = np.array([1] * 20 + [2] * 20, dtype=enriched.expiry_id.dtype)
    for field, value in {"bdte": 20., "nms_atm": 0., "log_volume": 1., "log_open_interest": 1.}.items():
        frame[field] = np.full(len(frame), value, dtype=enriched[field].dtype)
    frame["nms"] = np.r_[np.linspace(-.2, .2, 20), np.linspace(2., 3., 20)].astype(enriched.nms.dtype)
    selected = filter_options_day("SPX", DAY, source_data=frame, mk_arb_free=None,
                                  options_filter=OptionsFilter(normalize=False, max_num_options=20), verbose=Context.quiet)
    # A simple global nearest-ATM sort would take all 20 from expiry 1.
    assert selected.groupby("expiry_id").size().to_dict() == {1: 10, 2: 10}


def test_empty_eligible_population_retains_the_public_schema(market_day) -> None:
    _, enriched = market_day
    frame = enriched.copy(deep=True)
    frame["log_volume"] = np.zeros(len(frame), dtype=frame.log_volume.dtype)
    selected = filter_options_day("SPX", DAY, source_data=frame, mk_arb_free=None,
                                  options_filter=OptionsFilter(normalize=False), verbose=Context.quiet)
    assert selected.empty
    assert selected.columns.tolist() == frame.columns.tolist()
    assert selected.dtypes.to_dict() == frame.dtypes.to_dict()


@pytest.mark.parametrize("provider_inputs", [date(2025, 1, 3)], indirect=True)
def test_real_1000_cap_preserves_expiries_anchors_and_original_quotes(provider_inputs) -> None:
    raw = collect_raw_day("SPX", date(2025, 1, 3), RawDayFilter(), override_cache_mode="off", verbose=Context.quiet)
    frame = enrich_day("SPX", date(2025, 1, 3), raw_data=raw, override_cache_mode="off", verbose=Context.quiet)
    config = OptionsFilter(normalize=False)
    uncapped = filter_options_day("SPX", date(2025, 1, 3), source_data=frame, mk_arb_free=None,
                                  options_filter=replace(config, max_num_options=len(frame) + 1000), verbose=Context.quiet)
    capped = filter_options_day("SPX", date(2025, 1, 3), source_data=frame, mk_arb_free=None, options_filter=config, verbose=Context.quiet)
    assert len(uncapped) > 1000 and len(capped) == 1000
    assert capped.index.is_unique and set(capped.expiry_id) == set(uncapped.expiry_id)
    assert capped.groupby("expiry_id").size().min() >= 10
    pd.testing.assert_frame_equal(capped.sort_index(), frame.loc[capped.index].sort_index())
    for _, group in uncapped.groupby("expiry_id"):
        positive, negative = group[group.nms > 0], group[group.nms < 0]
        if not positive.empty: assert positive.nms.idxmin() in capped.index
        if not negative.empty: assert negative.nms.idxmax() in capped.index
    reserved = filter_options_day("SPX", date(2025, 1, 3), source_data=frame, mk_arb_free=None,
                                  options_filter=replace(config, max_num_options=10 * uncapped.expiry_id.nunique()), verbose=Context.quiet)
    assert set(reserved.index) <= set(capped.index)
    extras = capped.loc[~capped.index.isin(reserved.index)]
    excluded = uncapped.loc[~uncapped.index.isin(capped.index)]
    assert not extras.empty and not excluded.empty
    assert extras.nms.abs().max() <= excluded.nms.abs().min()
    normalized = filter_options_day("SPX", date(2025, 1, 3), source_data=frame, mk_arb_free=None,
                                    options_filter=replace(config, normalize=True), verbose=Context.quiet)
    assert normalized.index.tolist() == capped.index.tolist()
    np.testing.assert_array_equal(normalized.pure_strike, capped.pure_strike)
    np.testing.assert_array_equal(normalized.pure_bid_price, capped.pure_bid_price)
    np.testing.assert_allclose(normalized.strike, capped.strike / capped.spot, rtol=1e-6)


@pytest.fixture
def linear_day(market_day) -> tuple[pd.DataFrame, pd.DataFrame]:
    _, enriched = market_day
    config = MkArbFree(smoothness=None)
    linear = mk_arb_free_day("SPX", DAY, enriched_data=enriched, mk_arb_free=config,
                             override_cache_mode="off", verbose=Context.quiet)
    keys = ["expiry_id", "pure_strike", "pure_bid_price", "pure_ask_price"]
    expected = enriched.loc[enriched.expiry_id.isin(linear.expiry_id), keys].sort_values(keys[:2]).reset_index(drop=True)
    pd.testing.assert_frame_equal(linear[keys].reset_index(drop=True), expected)
    assert linear.mask_arb_free.dtype == np.dtype(bool)
    assert np.all(np.isfinite(linear.pure_fit1_price)) and np.all(np.isfinite(linear.pure_fitX_price))
    return enriched, linear


@pytest.mark.parametrize("eta", [0., .1, .25])
def test_selected_surface_is_feasible_and_roundtrips(linear_day, tmp_path, eta: float) -> None:
    _, linear = linear_day
    selected = filter_options_day("SPX", DAY, source_data=linear, options_filter=OptionsFilter(normalize=False), verbose=Context.quiet)
    groups = [g.sort_values("pure_strike", kind="stable") for _, g in selected.groupby("expiry_id", sort=True)]
    market = dict(expiries=np.array([float(g.tte_y.iloc[0]) for g in groups]),
                  strikes=[g.pure_strike.to_numpy(float) for g in groups],
                  bids=[g.pure_bid_price.to_numpy(float) for g in groups],
                  asks=[g.pure_ask_price.to_numpy(float) for g in groups])
    model = MkArbFree(smoothness=eta, surface_expiry_linear=True)(**market, verbose=Context.quiet)
    assert model.smoothness == eta and model.expiry_linear
    assert np.all(np.diff(model.variances) >= 0.)
    for i, (strikes, probabilities) in enumerate(zip(model.mstrikes, model.mdensities, strict=True)):
        assert np.isfinite(probabilities).all() and probabilities.min() >= -1e-5 and probabilities.max() <= 1 + 1e-5
        assert abs(probabilities.sum() - 1) <= 1e-5
        assert abs(strikes @ probabilities - 1) <= 1e-5
        query = np.union1d(strikes, [0.] if i == 0 else np.r_[0., model.mstrikes[i - 1]])
        earlier = np.maximum(1 - query, 0.) if i == 0 else np.maximum(model.mstrikes[i - 1][None, :] - query[:, None], 0.) @ model.mdensities[i - 1]
        later = np.maximum(strikes[None, :] - query[:, None], 0.) @ probabilities
        assert np.max(earlier - later) <= 1e-5
    fit = model.compute_market_fit(**market, and_vols=False)
    errors = np.concatenate(fit.fit_errs)
    assert len(errors) == len(selected)  # evaluate all selected rows, without active-strike masks
    for prices, bids, asks, error in zip(fit.fits, market["bids"], market["asks"], fit.fit_errs, strict=True):
        expected = (np.maximum(prices - asks, 0.) + np.maximum(bids - prices, 0.)) / np.maximum((asks - bids) / 2, 1e-4)
        np.testing.assert_allclose(error, expected, rtol=0., atol=1e-12)
    assert fit.pcnt_fit == pytest.approx(np.count_nonzero(errors > 0.) / len(errors))
    directory = SubDir(str(tmp_path), fmt=SubDir.PYTREE_HDF5)
    directory.write("model", model.to_dict())
    restored = ArbFreePricer.from_dict(directory.read("model"))
    replay = restored.compute_market_fit(**market, and_vols=False)
    np.testing.assert_array_equal(np.concatenate(replay.fit_errs), errors)
    np.testing.assert_array_equal(np.concatenate(replay.fits), np.concatenate(fit.fits))


@pytest.mark.parametrize("cache_mode", ["off", "readonly"])
def test_time_series_packs_selected_rows_and_padding(linear_day, monkeypatch, cache_mode: str) -> None:
    _, linear = linear_day
    definition = TimeSeriesDefinition(mk_arb_free=MkArbFree(smoothness=None), options_filter=OptionsFilter(normalize=False))
    selected = filter_options_day("SPX", DAY, source_data=linear, options_filter=definition.options_filter, verbose=Context.quiet)
    other_day = date(2010, 7, 7)
    other_linear = mk_arb_free_day("SPX", other_day, mk_arb_free=definition.mk_arb_free, override_cache_mode="off", verbose=Context.quiet)
    other_selected = filter_options_day("SPX", other_day, source_data=other_linear, options_filter=definition.options_filter, verbose=Context.quiet)
    dates = DateRange(DAY, other_day, exclude_half_days=False)
    # Restrict the calendar to two real stored observations; all market
    # processing, solvers, selection and packing still execute normally.
    monkeypatch.setattr(dates, "get_business_days", lambda: [DAY, other_day])
    backends = []
    real_pool = timeseries.JCPool

    def pool(**kwargs):
        backends.append(kwargs["threading"])
        return real_pool(**kwargs)

    monkeypatch.setattr(timeseries, "JCPool", pool)
    series = build_time_series("SPX", dates, include_fields=None, exclude_fields=None,
                               time_series_def=definition, pool_config=PoolConfig(num_workers=0, threading=False), override_cache_mode=cache_mode, verbose=Context.quiet)
    assert backends == [False]  # uncached fitting honors the configured process backend
    valid = series["is_valid"]
    counts = [len(selected), len(other_selected)]
    assert valid.shape == (2, max(counts)) and valid.dtype == np.dtype(bool)
    assert counts[0] != counts[1] and max(counts) <= 1000
    assert series["dates"] == [DAY, other_day]
    for i, expected in enumerate([selected, other_selected]):
        assert valid[i].sum() == len(expected)
        assert valid[i, :len(expected)].all() and not valid[i, len(expected):].any()
        for field in ["pure_strike", "pure_bid_price", "pure_ask_price", "expiry_id", "mask_arb_free"]:
            np.testing.assert_array_equal(series[field][i, valid[i]], expected[field].to_numpy())
        block = timeseries.extract_day_block(series, i, "spot", "time_y", "tte_y", pure_strike="strikes", pure_bid_price="bids")
        assert float(block.spot) == pytest.approx(float(expected.spot.iloc[0]))
        assert block.time_y == series["time_y"][i, 0]
        assert set(block.tte_y) == set(expected.tte_y)
        for expiry, strikes, bids in zip(block.tte_y, block.strikes, block.bids, strict=True):
            group = expected.loc[expected.tte_y == expiry]
            np.testing.assert_array_equal(strikes, group.pure_strike)
            np.testing.assert_array_equal(bids, group.pure_bid_price)
    assert np.all(series["pure_strike"][~valid] == 0)
    assert "pure_strike" in str(timeseries.table_of_time_series(series))


def test_time_series_default_writes_and_reuses_daily_cache_without_provider(tmp_path) -> None:
    # Import in an isolated process so writable caches cannot touch the retained
    # fixture tree or alter the other tests' read-only environment.
    script = dedent(f"""
        import runpy, socket
        from types import SimpleNamespace
        import numpy as np
        import pytest

        def blocked(*args, **kwargs):
            raise AssertionError("Provider/network access after initial stored-data collection")

        socket.socket.connect = blocked
        socket.create_connection = blocked
        checks = runpy.run_path({str(Path(__file__).resolve())!r})
        with pytest.MonkeyPatch.context() as patch:
            checks['provider_inputs'].__wrapped__(patch, SimpleNamespace())
            client = checks['WIDBClient']
            patch.setattr(client, 'connect', blocked)
            ts = checks['timeseries']
            backends = []
            real_pool = ts.JCPool
            def pool(**kwargs):
                backends.append(kwargs['threading'])
                return real_pool(**kwargs)
            patch.setattr(ts, 'JCPool', pool)
            definition = ts.TimeSeriesDefinition(options_filter=checks['OptionsFilter'](normalize=False))
            kwargs = dict(ticker='SPX', date_range=checks['DateRange'](checks['DAY'], checks['DAY']),
                          time_series_def=definition, exclude_fields=None,
                          pool_config=checks['PoolConfig'](num_workers=0, threading=False),
                          verbose=checks['Context'].quiet)
            first = ts.build_time_series(include_fields=None, **kwargs)
            assert backends == [False, True]  # configured computation, threaded cache reads
            for name in ['lookup_secid', 'options', 'forwards', 'zero_curve', 'spot_price']:
                patch.setattr(client, name, blocked)
            # A new aggregate key forces assembly from the existing daily cache.
            fields = {{'is_valid', 'pure_strike'}}
            cached = ts.build_time_series(include_fields=fields, **kwargs)
            replay = ts.build_time_series(include_fields=fields, override_cache_mode='cacheonly', **kwargs)
            readonly = ts.build_time_series(include_fields=fields | {{'expiry_id'}}, override_cache_mode='readonly', **kwargs)
            for result in [cached, replay, readonly]:
                np.testing.assert_array_equal(result['is_valid'], first['is_valid'])
                np.testing.assert_array_equal(result['pure_strike'], first['pure_strike'])
            assert backends == [False, True, True, False], backends
        """)
    environment = os.environ.copy()
    config = tmp_path / "config.toml"
    config.write_text("", encoding="utf-8")
    environment.update(OQ_DATA_ROOT=str(tmp_path), QUANTDATA_ROOT=str(tmp_path),
                       OQ_DATA_CONFIG=str(config), OQ_DATA_RAW=str(tmp_path / "raw"),
                       OQ_DATA_PROCESSED=str(tmp_path / "processed"),
                       OQ_DATA_TEST_MODE="0", OQ_DATA_CACHE_MODE="on", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"))
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=environment,
                            text=True, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    assert any((tmp_path / "processed").rglob("*.h5"))


def test_time_series_bad_day_raises_or_skips_explicitly(provider_inputs, monkeypatch) -> None:
    bad_day = date(2015, 8, 21)
    dates = DateRange(DAY, bad_day, exclude_half_days=False)
    monkeypatch.setattr(dates, "get_business_days", lambda: [DAY, bad_day])
    kwargs = dict(ticker="SPX", date_range=dates, include_fields=None, exclude_fields=None,
                  time_series_def=TimeSeriesDefinition(), pool_config=PoolConfig.off(),
                  override_cache_mode="off", verbose=Context.quiet)
    with pytest.raises(IndexError, match="BAD.DAYS_TICKER"):
        build_time_series(**kwargs)
    with pytest.warns(UserWarning, match="no data after filtering"):
        series = build_time_series(skip_bad_days=True, **kwargs)
    assert series["dates"] == [DAY] and series["is_valid"].any()
