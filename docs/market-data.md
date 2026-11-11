# WIDB market-data pipeline and default filters

WRDS/OptionMetrics observations and the resulting fitted caches are **licensed source datasets**. Licensed observations, caches and models remain outside Git.

The pipeline has three distinct kinds of selection: **market-data cleaning before any linear fit**, **the linear fit's own expiry/strike handling**, and **the optional eligible-option selection, capped at 1,000 rows**. The first two also apply to the SANOS “Everything” surface. Only the last produces the paper-style selected population.

One option row represents a **paired call and put at one strike and expiry/settlement**, not two separately counted contracts. Thus the 1,000-option cap means at most 1,000 such rows per day. A retained row requires usable quotes for both sides of the pair.

## Pipeline and controlling configurations

| Stage | Function | Configuration | Output |
|---|---|---|---|
| 1. Collect and clean observations | `collect_raw_day` | `RawDayFilter`, `BAD`, `IRREGULAR_EXPIRES` | Paired market quotes, spot, discount factors and reference forwards |
| 2. Enrich and validate expiries | `enrich_day` | `ExpiryFilter` | Implied forwards, pure call bid/ask, implied vols, Greeks and NMS5 |
| 3. Fit the initial linear surface | `mk_arb_free_day` / `MkArbFree` | `MkArbFree(no_arb_mode="surface", smoothness=None)` | Per-expiry linear fits, global DLV fit, retained expiries and strike masks |
| 4a. Everything population | Use the enriched input directly | No `OptionsFilter` | Every reasonable input row; the fitter still performs stage 3's per-expiry handling internally |
| 4b. Paper-style population | `filter_options_day` on stage 3's rows | `OptionsFilter` | Eligible rows after maturity, NMS5 and liquidity selection, then the 1,000-row cap |
| 5. Fit and assess the chosen population | `MkArbFree`, `ArbFreePricer.compute_market_fit` | Explicit `smoothness=0`, `0.1` or `0.25` | Linear or smooth surface and errors on the chosen input quotes |
| 6. Store models or pack daily observations | `to_dict` / `from_dict`; `build_time_series` | Data locations; `TimeSeriesDefinition`, `DateRange`, `PoolConfig` | Reloadable model, or padded daily arrays with an `is_valid` mask |

The normal paper ordering is **clean → enrich → initial linear fit → eligible-option selection → fit the selected surface**. Setting a smooth `MkArbFree` inside `TimeSeriesDefinition` instead fits the smooth surface **before** eligible-option selection; it does not create the paper ordering automatically.

## 1. Default cleaning before the linear fit

### Raw quotes: `RawDayFilter()` and `collect_raw_day`

| Rule | Default / exact action |
|---|---|
| Known bad inputs | Exclude dates in `BAD.DAYS_ALL` / `BAD.DAYS_TICKER`, and symbols in `BAD.OPTIONS` / `BAD.OPTIONS_BY_DATE`. A bad day raises by default; `raise_if_bad_day=False` returns an empty frame. |
| Same-day expiry | Remove quotes whose expiry date equals the observation date. |
| Irregular expiry | `drop_irregular_expiries=True`; remove expiry dates in `IRREGULAR_EXPIRES`, currently including 2025-01-09. |
| Missing quotes | Remove rows with missing bid or ask. |
| Locked/crossed quotes | Remove `bid >= ask`, including locked markets. |
| Bid floor | `min_bid=0.011`: retain **bid > 0.011**, strictly, in the original cash-price units. This is applied separately to calls and puts, before pairing. |
| Settlement flag | Retain only provider `ss_flag == "0"`. This is separate from AM/PM settlement; AM options are not excluded by this rule. |
| Pairing | Inner-join surviving calls and puts on expiry, AM/PM settlement, exercise style and strike. A quote without its matching call/put is not a usable paired row. |

Observation-date exclusions and expiry-date exclusions are separate. **2025-01-08** is explicitly listed in [`BAD.DAYS_ALL`](../src/quantdata/widb/bad.py), so it raises by default or returns an empty frame before provider access with `raise_if_bad_day=False`, even if vendor quotes exist. Its historical SANOS calibration was never attempted. The blacklist comment only says `expiries with zero business days?`; no fitting failure is documented as justification. **2025-01-09** was a market closure and is separately listed as an irregular expiry. The current expiry filter therefore does not itself justify excluding the entire January 8 observation day. See the [coverage and provenance note](retained-model-day-gaps.md) before reassessing that inherited exclusion.

Spot and previous-business-day spot, a zero curve and provider forwards are required. Reference-forward checks reject suspicious values or duplicate expiry/settlement keys; one recognized `spot / 1_000_000` data error is repaired to spot. These are data-integrity checks, not liquidity selection.

Business-day maturity uses the NYSE calendar, with 0.8 business days subtracted for AM settlement and a floor of zero; `tte_y = bdte / 252`. The source quotes remain available as `mkt_call_*` and `mkt_put_*`.

### Expiry validity and enrichment: `ExpiryFilter()` and `enrich_day`

| Parameter / rule | Default / meaning |
|---|---|
| `num_min_either_traded` | **10 distinct strike rows per expiry** with positive call **or** put volume. |
| `num_min_both_traded` | **4 distinct strike rows per expiry** with positive call **and** put volume. |
| Implied forward | Estimate from put-call parity using inverse-spread weights on strikes where both sides traded. Drop an expiry if its discounted implied forward is below `1e-6`. |
| Synthetic prices | Combine market calls with put-call-parity synthetic calls; remove nonpositive synthetic bid/ask or unusably small spreads. |
| `min_pure_spread` | **1e-6**, in pure-price units. The equivalent synthetic-call spread check is scaled by the discounted forward. |
| `min_implied_vol`, `max_implied_vol` | **0.01, 5.0**: bounded implied-volatility inversion, corresponding to 1%–500% annualized volatility. Remove boundary solutions that cannot reprice the quote within tolerance. |

The 10/4 traded-strike checks are made before and again after synthetic-price cleaning, before the final implied-volatility checks. Positive volume means **greater than zero**, not the later `log10(1+volume) >= 1` threshold. These are **expiry-level requirements for estimating the forward**: an otherwise valid, untraded strike can remain in an eligible expiry. There is no per-row minimum volume or open interest at this stage, and no 1,000-row cap, maturity cap or NMS5 window.

`ExpiryFilter` has no normalization switch. The former unused `normalize` field was removed in configuration version **0.6**. Its legacy default (`normalize=False`) label and hash encoding are retained internally, preserving the existing enriched-data and downstream fit/time-series **cache IDs**. The bumped dependency **version** makes old processed entries stale at those same IDs; normal caching recomputes them, while cache-only access rejects the version mismatch. Raw/provider caches are unaffected.

Write `F` for the implied forward and `DF` for the discount factor. There are two different normalizations to distinguish here:

- **Forward normalization always happens during enrichment**: `pure_strike = strike / F` and `pure_*_price = call_price / (DF * F)`. These dimensionless fields are the inputs to the no-arbitrage fit. The ordinary strike, forward and quote fields retain their cash units.
- **Spot normalization is a later output transformation**, controlled by the active `OptionsFilter.normalize` setting (default `True`). It divides the selected cash-price fields and strike/forward by spot, retains the original spot as `spot_ref`, and adds `spot_ret`. It leaves the `pure_*` fitting inputs unchanged. See the separate eligibility table below.

For example, with strike 105, forward 102 and spot 100, enrichment produces `pure_strike = 105 / 102` while retaining `strike = 105`. Later spot normalization changes `strike` to `105 / 100 = 1.05`; `pure_strike` remains `105 / 102`.

The implied-volatility price tolerance is `min(0.1 * pure_spread, 1e-6)`; the boundary-repricing check allows 1.1 times that tolerance. Enrichment also computes `nms`, `nms_atm`, Greeks and combined liquidity fields; computing these fields does not select an ATM subset.

Source: [day.py](../src/quantdata/widb/day.py), [bad.py](../src/quantdata/widb/bad.py), [calendar and NMS5](../src/quantdata/biz_calendar.py).

## 2. Linear fitting and its own masks

`MkArbFree(no_arb_mode="surface", smoothness=None)` first fits each expiry linearly, then fits a globally arbitrage-free linear DLV surface. Its separate numerical controls include `min_strikes_per_expiry=5`, `min_density=1e-4`, `min_dC_eps=1e-3` and `min_atm_vol=0.05`.

The fitter extends strike boundaries, can trim unsuitable boundary strikes, mask strikes that cannot be fitted within bid/ask, reduce redundant linear-interpolation grid points, and omit unusable expiries. These are part of constructing the no-arbitrage model; they are not the market-data cleaning rules or the paper's liquidity/ATM selection. A solver error or timeout alone does not establish mathematical infeasibility.

`mk_arb_free_day` retains **all original strike rows for retained expiries**, with `mask_arb_free` identifying active strikes. `pure_fit1_*` describes the per-expiry fit and `pure_fitX_*` the global fit. Original `pure_bid_price` / `pure_ask_price` remain the calibration observations; later smoothing does not silently replace them with fitted linear mids.

Source: [WIDB arbfree adapter](../src/quantdata/widb/arbfree.py), [MkArbFree and ArbFreePricer](../src/quantdata/arbfree/arbfree.py).

## 3. Separate eligible-option filter and 1,000-row cap

`OptionsFilter()` acts on the cleaned/enriched rows, usually after the initial linear fit. Its order is: maturity and optional cash normalization → NMS5 → volume/open interest → optional AM exclusion → minimum rows per expiry → count cap.

| Parameter | Default / effect |
|---|---|
| `max_business_days_to_expiry` | **756** business days (3 × 252), inclusive. |
| `max_nms`, `nms_use_atm` | **(-5, 2)**, inclusive, applied to **`nms_atm`** because `nms_use_atm=True`. |
| `min_log_volume` | **1.0**: `log10(1 + call_volume + put_volume) >= 1`, i.e. combined volume at least **9**. |
| `min_log_open_interest` | **1.0**: `log10(1 + call_OI + put_OI) >= 1`, i.e. combined open interest at least **9**. |
| `remove_am` | **False**: retain AM and PM options. |
| `min_opt_per_expiry` | **10** eligible rows per expiry, checked after the preceding filters and before the cap. |
| `max_num_options` | **1,000 total rows per day**, across all retained expiries. |
| `normalize` | **True**: normalize selected cash-price fields by spot and add `spot_ref` / `spot_ret`. This does not change the pure fitting inputs or selected identities. Use `False` when passing a frame back into WIDB fitting adapters. |

`NMS5` uses five-business-day regularization (`EPS = 5 / 252`) and the default log-strike scale `log(1.1)`. The fixed-scale `nms` uses that scale throughout; `nms_atm` uses the expiry's ATM volatility in the maturity-dependent term while retaining the default scale in the regularization term.

**The cap is a second operation after eligibility.** If more than 1,000 rows remain, reserve ten per expiry, including the nearest positive and negative `nms` where available, and fill those reservations with the smallest absolute `nms`. Fill the remaining daily slots globally by smallest absolute **`nms`**, with stable ordering. The cap ranks the fixed-scale NMS5 field `nms`; the eligibility window uses ATM-volatility NMS5 `nms_atm`. It does not span the entire strike range uniformly. If eligibility leaves fewer than 1,000 rows, all of them remain.

To study eligibility without a cap, retain the other settings and set `max_num_options` above the input row count. That is a different population from the original capped paper-style sample. “Everything” bypasses `OptionsFilter` entirely.

Source: [options_filter.py](../src/quantdata/widb/options_filter.py).

## 4. Final surface and fit statistics

Choose smoothness explicitly: **0** for the linear surface, **0.1** or **0.25** for the smooth SANOS surface. The class default is `smoothness=None`, also linear; the data pipeline does not add a 0.25 fit automatically. With `surface_expiry_linear=True` (default), the initial per-expiry step stays linear when fitting a smooth surface.

Other defaults are `mid_fit_weight=0.1`, `min_half_spread=1e-4`, and no DLV floor/cap (`min_dlv=None`, `max_dlv=None`). Active quotes receive equal user weights, with the existing half-spread normalization. The package solver defaults to HiGHS simplex with Clarabel fallback; `timeout_seconds=300` is the class default. The historical comparison runs explicitly used 600-second attempts, 3,000-second retries and an isolated audited solver adapter; those operational settings are not implicit library defaults.

Evaluate with `compute_market_fit(..., and_vols=False)` on the **entire chosen input population**, omitting `masks` to include internally masked rows. `pcnt_fit` is the **fraction outside** bid/ask, despite its name. `mean_err` and `median_err` are conditional on being outside, in half-spread units with the `min_half_spread` floor; zero-excess days have zero conditional statistics. A feasible model can still fit quotes poorly. Stored model fields `input_index` and `masks` explain the active objective population.

The completed historical comparisons are linked from {download}`SANOS.md <../SANOS.md>`; they include daily within-bid/ask, conditional excess and recorded fit-time plots. The completed comparisons evaluate both the Everything model and filtered model on identical selected quotes, and separately retain the full-book statistics. Their independent post-repair certificates check density bounds, mass, first moment, full-range calendar and original quote/slack constraints. The permitted absolute tolerance is 1e-5, trying 1e-7 first; this extra audit/recovery layer belongs to the recorded runs, not to `OptionsFilter`.

## 5. Python example: clean, fit linearly, select, then smooth

Configure the external data root before importing quantdata; see [configuration](configuration.md). This example uses cached provider data where available and may download missing observations in normal mode. Tests use stored inputs and block provider access.

`enrich_day` and `mk_arb_free_day` identify cached inputs by ticker, date and configuration, not by the contents of an explicitly supplied frame. If you modify `raw` or `enriched`, pass `override_cache_mode="off"` to those consuming calls so an existing cache cannot override your edits. `filter_options_day(source_data=linear, ...)` itself is uncached and consumes the supplied frame directly.

```python
from datetime import date

import numpy as np
import pandas as pd
from cdxcore.verbose import Context

from quantdata.arbfree.arbfree import MkArbFree
from quantdata.widb.arbfree import mk_arb_free_day
from quantdata.widb.day import ExpiryFilter, RawDayFilter, collect_raw_day, enrich_day
from quantdata.widb.options_filter import OptionsFilter, filter_options_day

ticker, day = "SPX", date(2025, 1, 3)
raw_filter = RawDayFilter()               # bid > 0.011; raw quality rules
expiry_filter = ExpiryFilter()           # expiry-level 10/4 traded-strike rules
linear_config = MkArbFree(smoothness=None, timeout_seconds=600)
eligible_filter = OptionsFilter(normalize=False)  # separate eligibility + 1,000 cap

raw = collect_raw_day(ticker, day, raw_filter, verbose=Context.quiet)
enriched = enrich_day(
    ticker, day, raw_data=raw, raw_day_filter=raw_filter,
    expiry_filter=expiry_filter, verbose=Context.quiet,
)
linear = mk_arb_free_day(
    ticker, day, enriched_data=enriched, raw_day_filter=raw_filter,
    expiry_filter=expiry_filter, mk_arb_free=linear_config, verbose=Context.quiet,
)
eligible = filter_options_day(
    ticker, day, source_data=linear, raw_day_filter=raw_filter,
    expiry_filter=expiry_filter, mk_arb_free=linear_config,
    options_filter=eligible_filter, verbose=Context.quiet,
)
print({"raw": len(raw), "enriched": len(enriched),
       "linear_retained": len(linear), "eligible": len(eligible)})


def fit_surface(frame: pd.DataFrame, smoothness: float):
    if frame.empty:
        raise ValueError("No quotes left after cleaning/selection")
    groups = [g.sort_values("pure_strike", kind="stable")
              for _, g in frame.groupby("expiry_id", sort=True)]
    market = dict(
        expiries=np.array([float(g.tte_y.iloc[0]) for g in groups]),
        strikes=[g.pure_strike.to_numpy(float) for g in groups],
        bids=[g.pure_bid_price.to_numpy(float) for g in groups],
        asks=[g.pure_ask_price.to_numpy(float) for g in groups],
    )
    model = MkArbFree(
        smoothness=smoothness, surface_expiry_linear=True, timeout_seconds=600,
    )(**market, verbose=Context.quiet)
    fit = model.compute_market_fit(**market, and_vols=False)
    return model, fit


models = {}
for eta in (0.0, 0.1, 0.25):
    models[eta], fit = fit_surface(eligible, eta)
    print(eta, {"outside_percent": 100 * fit.pcnt_fit,
                "conditional_mean": fit.mean_err,
                "conditional_median": fit.median_err})

# For Everything instead: fit_surface(enriched, eta).
# For eligibility without the cap, rerun filter_options_day with
# OptionsFilter(normalize=False, max_num_options=len(linear) + 1000).
```

The public fitting call performs its own linear per-expiry preprocessing on the selected quotes. The historical runner reused identical per-expiry geometry between smoothness values for speed; it checked that this matched a fresh fit. Neither path substitutes linear mids for the observed bid/ask inputs.

To store a model in a uniquely named external processed directory:

```python
from uuid import uuid4

from cdxcore.subdir import SubDir

from quantdata import env
from quantdata.arbfree.arbfree import ArbFreePricer

run = env.locations.processed(
    f"examples/options-{uuid4().hex}", fmt=SubDir.PYTREE_HDF5,
)
run.write("sanos", models[0.25].to_dict())
restored = ArbFreePricer.from_dict(run.read("sanos"))
```

## 6. Time-series packing

`TimeSeriesDefinition` carries all four configurations into daily processing. `DateRange` controls the calendar; its default excludes early-close days, so choose `exclude_half_days` explicitly when matching a historical run. `PoolConfig.off()` keeps this example serial. Limit concurrent **WRDS downloads** to four if enabling a pool.

```python
from quantdata.biz_calendar import DateRange
from quantdata.pool import PoolConfig
from quantdata.widb.timeseries import TimeSeriesDefinition, build_time_series

definition = TimeSeriesDefinition(
    raw_day_filter=raw_filter, expiry_filter=expiry_filter,
    mk_arb_free=linear_config, options_filter=eligible_filter,
)
series = build_time_series(
    ticker, DateRange(day, day, exclude_half_days=False),
    include_fields=None, exclude_fields=None,
    time_series_def=definition, pool_config=PoolConfig.off(),
    verbose=Context.quiet,
)
```

This packs the **linearly fitted and selected observations**. With `override_cache_mode="off"`, daily frames are recomputed and packed in memory; no processed-cache files are required. It does not pack the additional smooth `models` created above. Array width is the largest selected day in the requested range, up to the configured cap. Use `series["is_valid"]` to exclude zero-padded slots; it is a padding mask, distinct from the fitter's `mask_arb_free`. For smooth post-filter models over a date range, repeat the explicit selected-surface fit above per date and retain each model and its population statistics separately.

Source: [timeseries.py](../src/quantdata/widb/timeseries.py), [storage configuration](configuration.md), [offline pipeline tests](testing.md).
