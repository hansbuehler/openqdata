# SANOS historical fits

Completed 5,151 SPX dates from 2005-01-03 to 2025-08-29; both populations at smoothness 0, 0.1 and 0.25.

Everything fits all reasonable paired observations after raw and expiry validation. The filtered dataset first performs full-book linear cleaning, applies the paper eligibility criteria and 1,000-row cap, then fits a separate SANOS surface. All saved models passed an independent post-repair audit of density bounds, mass, forward mean, calendar and calibration-LP constraints at 1e-5. Recovery checks 1e-7 first.

Two ticker-level historical day exclusions, 2006-11-17 and 2015-08-21, use separately reconstructed observations. These date-scope overrides are recorded in the public provenance; licensed input paths remain outside Git.

**The table and graphs below measure the fit to the constructed ("fixed") reference call quotes.** They do not measure whether the fitted call and its parity-derived put both lie inside their original markets. The [quote construction](src/openqdata/widb/day.py) converts put quotes to calls using the implied forward and discount factor, takes the midpoint between the higher bid and lower ask, then assigns the smaller of the original call and put spreads. This interval can differ from the actual overlap of the two markets, including when they do not overlap at all. The [original-market comparison](#reference-quotes-versus-original-markets) below excludes those inverted pairs from evaluation only; all saved calibrations remain unchanged.

| Population | Smoothness | Dates | Mean daily within bid/ask | Mean daily conditional excess | Median daily conditional median | Median runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| all | 0 | 5,151 | 97.9293% | 0.371128 | 0.123896 | 6.458 |
| all | 0.1 | 5,151 | 97.6819% | 0.284828 | 0.117361 | 9.769 |
| all | 0.25 | 5,151 | 94.0571% | 0.615790 | 0.209612 | 9.787 |
| flt | 0 | 5,151 | 99.4770% | 0.178039 | 0.000000 | 0.663 |
| flt | 0.1 | 5,151 | 99.0928% | 0.352947 | 0.119839 | 1.150 |
| flt | 0.25 | 5,151 | 95.0397% | 0.774698 | 0.359810 | 1.215 |

The isolated runtime recovery adapter starts with Clarabel at 600 seconds and retries unsuccessful solves at 3,000 seconds. Feasible native iterates are checked at 1e-7 before permitting 1e-5, then the original density repair and an independent post-repair audit are applied. Acceptance proves numerical feasibility, not optimality. An infeasible preliminary hard bid/ask helper LP does not imply that the final soft-fitting problem is infeasible. Each input population is evaluated without dropping internally masked strikes.

Conditional excess is measured in reference half-spreads for observations outside the constructed reference bid/ask, with the fitter's minimum half-spread of 1e-4 in normalized price units; a day with no excess records zero. Runtime is the sum of the recorded per-expiry and surface fitting times. It excludes enrichment, fitted-row packing, model serialization and the independent feasibility audit; audited wall time is retained separately in the licensed source statistics. All requested dates were processed before refreshing these figures.

Each column shows one smoothness level. Dates and each metric’s vertical scale are shared across columns. The first two rows report the same saved model’s reference-quote coverage on the full eligible book and on the filtered book, respectively. These historical plots include inverted pairs in their reference-quote evaluation. The filtered model evaluates other maturities using its usual interpolation and extrapolation; 0.50% of full-book observations across the three smoothness levels fall outside the fitted maturity range. Conditional errors and option counts refer to each model’s input population. Each counted paired strike/expiry observation corresponds to a call and put in the public extract.

### Fitting to all options*

The full eligible book consists of paired observations that pass the [default raw-quote and expiry-validation pipeline](docs/market-data.md#1-default-cleaning-before-the-linear-fit); it has no subsequent 1,000-option selection.

![Everything](docs/figures/sanos-all-population-comparison.png)

### Fitting to 1000 filtered options*

After the default cleaning and a full-book linear fit, the [eligible-option filter](docs/market-data.md#3-separate-eligible-option-filter-and-1000-row-cap) retains options with at most 756 business days to expiry, ATM-based NMS5 between -5 and 2, combined volume and open interest each at least 9, and at least 10 eligible strikes per expiry. It retains AM and PM options and caps the selection at 1,000 paired observations, prioritizing strikes near ATM while reserving strikes per expiry. The smooth surface is then fitted to that selection.

Filtering mainly improves speed: at smoothness 0.25, median fit time falls from 9.79 seconds for the full book to 1.22 seconds for the filtered book. On the same filtered options, mean daily bid/ask coverage rises modestly from 93.64% for the full-book model to 95.04% for the filtered model. Individual days can differ much more: on 11 April 2025, the corresponding 0.25 fits cover 39.1% and 90.9%, respectively.

![Filtered](docs/figures/sanos-flt-population-comparison.png)

Licensed observations, caches, models and diagnostics remain outside Git.

## Saved daily ArbFreePricer parameters

The completed historical run stores the full `ArbFreePricer.to_dict()` state for every day and each of the six fits in licensed storage outside Git. Below, `<run-root>` denotes that run directory:

```text
<run-root>/days/<YYYY-MM-DD>/models/<label>/model.h5
```

`label` is one of `all-0`, `all-0.1`, `all-0.25`, `flt-0`, `flt-0.1`, or `flt-0.25`. Each day's `report.json`, alongside its `models` directory, also records the exact path under `fits[label]["model_path"]`. The separate `cache_path` points to fitted observation rows, not the serialized pricer.

The [licensed-data field appendix](#appendix-licensed-fitted-data-fields) describes those observation rows and the saved model parameters, including their units and quote conventions.

Reload a saved pricer without recalibrating:

```python
from pathlib import Path

from cdxcore.subdir import SubDir
from openqdata.arbfree.arbfree import ArbFreePricer

root = Path("<run-root>")
path = root / "days/2025-08-29/models/all-0.25/model.h5"
saved = SubDir(str(path.parent), fmt=SubDir.PYTREE_HDF5).read(path.stem)
model = ArbFreePricer.from_dict(saved)
```

`model.mstrikes` and `model.mdensities` retain the surface grids and calibrated probability masses; `model.xstrikes` and `model.xdensities` retain the preliminary per-expiry fits. Maturities, smoothing settings, quote arrays and fitted prices are also retained. DLV arrays are not stored separately; they can be derived from the saved surface grids, masses and maturities. `model.variances` stores the reference ATM total variances, giving reference ATM volatilities as `sqrt(model.variances / model.expiries)`. Actual fitted ATM implied volatilities come from `model.price(model.expiries[:, None], strikes=1.0, mode="surface", and_vols=True)`, whose second return value contains those volatilities. The [market-data manual](docs/market-data.md) describes the general storage workflow.

## Date coverage

From 2022-01-03 through 2025-08-29, the six benchmark extracts and their saved daily pricers contain **910 dates**.

**2025-01-08 is excluded from both date populations by `BAD.DAYS_ALL`.** The loader returns an empty frame before provider access when `raise_if_bad_day=False`, so its SANOS fit was never attempted. The only recorded justification is the tentative comment `expiries with zero business days?`; this is not a demonstrated solver failure. **2025-01-09 was a market closure**, a separate calendar exclusion, and quotes for that irregular expiry are also filtered out by default. The whole-day January 8 exclusion needs reassessment against its quotes under the current expiry cleaning before changing the published date scope.

### Half-day completion in the licensed archive

The historical figures and benchmark exports use 5,151 dates with early closes excluded. An in-place completion job adds the **44 omitted NYSE early-close dates** from 2005-01-03 through 2025-08-29 to both licensed populations at smoothness 0, 0.1 and 0.25: **264 fits**, with the same configuration IDs, cache paths and daily model locations. Existing fitted dates are retained. The target is 5,195 dates per licensed population, including 917 dates from 2022 onward; these are completion targets, not claims that pending fits have finished. The existing benchmark exports and historical plots are unchanged by this job. January 8 remains a separate whole-day exclusion.

The authoritative progress file is:

```text
<run-root>/extensions/half-days-20261111T112306Z/status.json
```

Its `completed_fits`, `completed_dates`, `failed` and `status` fields distinguish completed fits from pending work. The adjacent README describes the explicit detached environment and resumption. Downloads use at most four WRDS processes; fitting uses up to eight CPU workers and the established audited solver adapter, with 600-second attempts and 3,000-second recovery. The half-spread denominator floor remains `1e-4` in normalized price units. Saved parameters and fitted rows are written into the existing parent archive; this is an extension of those datasets, not another dataset identity.

Read the licensed Everything fit through its standard cache function, setting the processed root before the first openqdata import:

```python
import os
from datetime import date

root = "<run-root>"
os.environ["OQ_DATA_PROCESSED"] = f"{root}/data/processed"
os.environ["OQ_DATA_TEST_MODE"] = "0"

from openqdata.arbfree.arbfree import MkArbFree
from openqdata.widb.arbfree import mk_arb_free_day

rows = mk_arb_free_day(
    "SPX", date(2025, 8, 29),
    mk_arb_free=MkArbFree(smoothness=0.1),
    override_cache_mode="cacheonly",
)
```

`cacheonly` reads compatible stored rows and raises on a missing or incompatible entry; it never starts a download or recalibration. Restart the interpreter before changing the data root if openqdata is already imported.

## Reference quotes versus original markets

For the actual market fit, the fitted call price `Cfit` and its parity-derived put `Pfit = Cfit - DF*(F-K)` must **both** lie inside their respective original bid/ask intervals. Equivalently, require `L <= Cfit <= U`, where `L = max(call_bid, put_bid + DF*(F-K))` and `U = min(call_ask, put_ask + DF*(F-K))`. A passing observation therefore means both options fit, rather than averaging separate call and put successes.

For this comparison, pairs with `L > U` are excluded from every coverage and excess calculation, for both quote definitions. This removes 125,126 of 15,112,757 whole-market pairs (0.8280%), leaving 14,987,631. In the selected book, 2,373 of 3,037,229 pairs are excluded, leaving 3,034,856. All 5,151 dates remain. These are evaluations of the saved surfaces: the calibration inputs, implied forwards and models have not changed. The historical graphs and first table retain their original reference-quote population, including inverted pairs.

**Whole-market coverage, pooling all retained pairs across dates:**

| Fitted population | Smoothness | Fixed reference within bid/ask | Both original markets within bid/ask |
|---|---:|---:|---:|
| all | 0 | 98.2745% | 98.2583% |
| all | 0.1 | 98.1580% | 98.0715% |
| all | 0.25 | 91.7598% | 91.4264% |
| flt | 0 | 40.8787% | 40.7203% |
| flt | 0.1 | 45.5006% | 45.3448% |
| flt | 0.25 | 42.4889% | 42.2630% |

The filtered models' whole-market results include options outside their calibration selection. They should not be confused with their fit to the selected options below. Pooling gives larger daily books more weight; the graphs instead give each date equal weight.

**Mean daily coverage on the two evaluation populations, with inverted pairs excluded:**

| Fitted population | Smoothness | Whole market: reference | Whole market: original | Selected: reference | Selected: original |
|---|---:|---:|---:|---:|---:|
| all | 0 | 97.9861% | 97.9798% | 99.2751% | 99.2620% |
| all | 0.1 | 97.7490% | 97.6941% | 98.9950% | 98.9229% |
| all | 0.25 | 94.1336% | 93.9522% | 93.6613% | 93.4186% |
| flt | 0 | 65.6452% | 65.5482% | 99.4823% | 99.4743% |
| flt | 0.1 | 67.8620% | 67.7591% | 99.1047% | 99.0338% |
| flt | 0.25 | 65.9845% | 65.8348% | 95.0630% | 94.8785% |

**Conditional excess on each model's input population**, after the same exclusions (`all`: whole market; `flt`: selected book):

| Fitted population | Smoothness | Reference mean daily conditional mean | Original mean daily conditional mean | Reference median daily conditional median | Original median daily conditional median |
|---|---:|---:|---:|---:|---:|
| all | 0 | 0.281068 | 0.285121 | 0.119296 | 0.119850 |
| all | 0.1 | 0.191854 | 0.200679 | 0.113145 | 0.115076 |
| all | 0.25 | 0.561499 | 0.584621 | 0.205869 | 0.211323 |
| flt | 0 | 0.174260 | 0.177074 | 0.000000 | 0.006605 |
| flt | 0.1 | 0.330594 | 0.375833 | 0.117408 | 0.129960 |
| flt | 0.25 | 0.761171 | 0.813545 | 0.356036 | 0.364951 |

Reference excess uses the constructed interval's half-spread. Original-market excess is the distance of `Cfit` outside `[L,U]`, divided by `max((U-L)/2, 1e-4*DF*F)`. The true overlap can be narrower than the reference interval, so the two excess measures use different half-spreads. Days with no misses contribute zero to both daily conditional statistics. Reference prices use the stored normalized strikes, reproducing the historical metric; native-market prices use `K/F` from the stored strike and forward. Re-evaluating reference coverage at these native coordinates changes pooled coverage by less than 0.0003 percentage points for every model and evaluation population.

Validation reproduced all 61,812 historical daily reference-coverage counts across both evaluation populations exactly before applying the new exclusion. The original-market success counts also match the earlier evaluation exactly; removing inverted pairs changes their denominator and excess distribution, not their successful-pair counts.

## Solver attempt statuses

<table>
  <thead>
    <tr><th rowspan="2">Population, smoothness</th><th rowspan="2">Failures</th><th rowspan="2">Dates below 90% within bid/ask</th><th colspan="4">Reported intermediate issues (solver attempts)</th></tr>
    <tr><th>Time limit</th><th>Clarabel numerical error</th><th>Insufficient progress</th><th>Iteration limit</th></tr>
  </thead>
  <tbody>
  <tr><td>all, 0</td><td>0</td><td>1</td><td>0</td><td>6</td><td>2</td><td>0</td></tr>
  <tr><td>all, 0.1</td><td>0</td><td>6</td><td>31</td><td>334</td><td>30</td><td>0</td></tr>
  <tr><td>all, 0.25</td><td>0</td><td>731</td><td>60</td><td>618</td><td>22</td><td>0</td></tr>
  <tr><td>flt, 0</td><td>0</td><td>2</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
  <tr><td>flt, 0.1</td><td>0</td><td>5</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
  <tr><td>flt, 0.25</td><td>0</td><td>613</td><td>0</td><td>1</td><td>0</td><td>0</td></tr>
  </tbody>
</table>

Failures counts dates without a completed, audited final fit. Reported intermediate issues count native LP attempts, including retries and preprocessing; they are not counts of failed daily models. Dates below 90% refers to the historical reference-quote metric on each model's input population, before excluding inverted pairs. A numerical-error attempt is one for which Clarabel stopped because of numerical difficulty. Of the 959 such attempts, 604 returned an iterate that passed the linear-constraint and bound checks and was accepted; the other 355 attempts were not accepted, and their daily fits subsequently passed through another recovery path. An accepted feasible iterate does not imply optimality. Preliminary hard bid/ask helper infeasibility is a normal branch into the soft fit and is excluded from this table. All six final datasets have complete, independently certified daily fits; no unresolved daily fits remain.


## Appendix: licensed fitted-data fields

This appendix describes the licensed daily fitted rows and `model.h5` states above. It is not the schema of the separately distributed benchmark extracts. A daily observation row pairs a call and a put at the same strike, expiry, settlement and exercise style; it does not represent two independent calibration targets. The six labels distinguish the Everything (`all`) and selected (`flt`) calibration populations at smoothness 0, 0.1 and 0.25. The source configuration and saved model, rather than the filename alone, determine the fitting settings.

The raw, enriched and fitted schemas are cumulative. The declarations in [day.py](src/openqdata/widb/day.py) (`SCHEMA_RAW_DAY`, `SCHEMA_ENRICHED_DAY`) and [arbfree.py](src/openqdata/widb/arbfree.py) (`SCHEMA_ARB_FREE_DAY_EXPIRY`, `SCHEMA_ARB_FREE_DAY_SURFACE`) define the column names and dtypes. Unless noted otherwise, numerical row fields are `float32`; identifiers are `int32`, flags are Boolean, dates are stored as `datetime64[ms]`, and ticker/symbol fields are strings represented by pandas object columns.

### Identity, dates and market references

| Field | Meaning and units |
| --- | --- |
| `ticker`, `date` | Underlying ticker and observation date. |
| `call_symbol`, `put_symbol` | Original call and put contract symbols. |
| `call_opt_id`, `put_opt_id` | Provider contract identifiers. |
| `expiry`, `expiry_id` | Expiration date and an integer key distinguishing its AM/PM settlement. The key is `year*100000 + month*1000 + day*10 + (0 if is_am else 1)`. |
| `is_am`, `is_american` | AM settlement and American exercise flags, respectively. |
| `spot`, `spot_prev` | Current and previous underlying reference close, in underlying price units. These are the values used by the day loader. |
| `strike` | Contract strike, in underlying price units. |
| `bdte` | NYSE business days to expiry, reduced by 0.8 for AM settlement and floored at zero; fractional values are intentional. |
| `tte_y` | Business-year maturity, `bdte / 252`; not calendar days divided by 365. There is no separate stored calendar-DTE column in these daily schemas. |
| `fwd_ref` | Provider reference forward, in underlying price units; distinct from the estimated forward actually used to fit. |
| `fwd` | Implied forward estimated across eligible put/call pairs in the expiry, in underlying price units. |
| `df` | Discount factor to expiry, interpolated from the provider zero curve; dimensionless. |
| `nms` | Fixed-scale normalized log-moneyness, `NMS5.to_nms(strike/fwd, tte_y)`, using scale `log(1.1)` and five-business-day regularization. |
| `nms_atm` | The same NMS5 transformation using the expiry's interpolated ATM quote volatility in its maturity-dependent term. This is the eligibility-window field; the count cap ranks by `abs(nms)`. |

### Original quotes and liquidity

| Field | Meaning and units |
| --- | --- |
| `mkt_call_bid`, `mkt_call_ask` | Original retained call bid and ask, in option price units. |
| `mkt_put_bid`, `mkt_put_ask` | Original retained put bid and ask, in option price units. |
| `mkt_call_log_volume`, `mkt_put_log_volume` | `log10(1 + volume)` for the respective option; not natural logarithms. |
| `mkt_call_log_open_interest`, `mkt_put_log_open_interest` | `log10(1 + open_interest)` for the respective option. |
| `log_volume` | `log10(1 + call_volume + put_volume)`, combining the paired options. |
| `log_open_interest` | `log10(1 + call_open_interest + put_open_interest)`, combining the paired options. |

These original quotes remain licensed observations. Keeping them alongside the fit does not mean they are all active in the fitting objective. In particular, the selected dataset omits unselected rows, and the internal fitter can mask strikes. The default input cleaning is documented separately in the [market-data pipeline](docs/market-data.md#1-default-cleaning-before-the-linear-fit).

### Constructed reference calls and normalized fitting coordinates

Let `F = fwd`, `D = df`, and `k = strike/F`. A normalized call price is `c = C/(D*F)`. The `pure_*` fields always use these forward-normalized, undiscounted coordinates.

| Field | Meaning and units |
| --- | --- |
| `pure_strike` | `k = strike/fwd`; dimensionless. |
| `pure_bid_price`, `pure_ask_price` | Constructed reference call bid and ask, divided by `df*fwd`, after implied-volatility repricing. These are the calibration quotes, not the two original call/put markets. |
| `call_bid`, `call_ask` | The same repriced reference call prices in option price units: `df*fwd*pure_*_price`. They are not original call quotes. |
| `bid_vol`, `ask_vol` | Black–Scholes implied volatilities of the reference call quotes, annualized on `tte_y` and expressed as decimals, e.g. `0.2` for 20%. |
| `pure_bid_delta`, `pure_ask_delta` | Black–Scholes call deltas in the normalized forward coordinates, at the corresponding quote implied volatility. |
| `pure_bid_gamma`, `pure_ask_gamma` | Corresponding normalized Black–Scholes gammas. |
| `pure_bid_vega`, `pure_ask_vega` | Corresponding normalized Black–Scholes vegas, per unit volatility, not per percentage point. |
| `pure_bid_theta`, `pure_ask_theta` | Corresponding normalized Black–Scholes derivative with respect to remaining year fraction, holding volatility fixed. The library uses positive time-to-maturity theta, not negative calendar-time decay. |
| `pure_bid_dk`, `pure_ask_dk` | Corresponding Black–Scholes derivatives with respect to normalized strike `k`. |

The reference-call midpoint lies halfway between the higher call-equivalent bid and lower call-equivalent ask; its spread is the smaller original call/put spread. It need not be the actual intersection of the two quote intervals. See [reference quotes versus original markets](#reference-quotes-versus-original-markets) for the separate original-market evaluation and treatment of inverted pairs.

### Fitted row fields

| Field | Meaning and units |
| --- | --- |
| `mask_arb_free` | Whether this retained row's strike survived the per-expiry fitting mask. A false value is not an absent or padded row, nor a guarantee about final bid/ask coverage. |
| `fit1_vol` | Implied volatility of the preliminary per-expiry fitted call. |
| `pure_fit1_price` | Preliminary per-expiry fitted normalized call price, aligned to the retained input rows. |
| `pure_fit1_delta`, `pure_fit1_gamma`, `pure_fit1_vega`, `pure_fit1_theta`, `pure_fit1_dk` | Black–Scholes Greeks evaluated at `fit1_vol`, with the same conventions as the quote Greeks above. |
| `fitX_vol` | Implied volatility of the final surface fitted call; present for surface-mode output. |
| `pure_fitX_price` | Final SANOS surface fitted normalized call price; present for surface-mode output. |
| `pure_fitX_delta`, `pure_fitX_gamma`, `pure_fitX_vega`, `pure_fitX_theta`, `pure_fitX_dk` | Black–Scholes Greeks evaluated at `fitX_vol`, with the same conventions as above. These are not derivatives of the entire calibrated SANOS surface. |

The native-coordinate fitted call price is `df*fwd*pure_fitX_price`; the fitted put price follows parity as `df*fwd*(pure_fitX_price - 1 + pure_strike)`. These daily schemas do not themselves add native-coordinate `fit_*` Greek columns. The benchmark exporter has its own schema and conversion rules.

Generic `filter_options_day` output can additionally apply `OptionsFilter(normalize=True)`. That removes `spot`, adds the original close as `spot_ref` and the return `spot_ret = spot/spot_prev - 1`, and divides `spot_prev`, `strike`, `fwd`, `call_bid`, `call_ask` and all four `mkt_*` quote columns by the current spot. `fwd_ref` remains in its original units. All `pure_*` fields remain unchanged. The historical licensed fit adapters select with `normalize=False`, retaining native price units; do not confuse spot-normalized time-series output with these fitted caches. See [the output-normalization setting](docs/market-data.md#3-separate-eligible-option-filter-and-1000-row-cap).

Packed time series add `is_valid` to distinguish real rows from padded slots. It is a packing mask, separate from `mask_arb_free`. Per-day fit statistics such as coverage, excess and runtime live in reports rather than being replicated as option-row columns.

### Saved model parameters

`model.h5` contains `ArbFreePricer.to_dict()`. Reload it through `ArbFreePricer.from_dict` as shown above; optional fields are encoded for HDF5 and should not be interpreted by reading sentinel strings directly. The model uses normalized strikes and prices; join its maturities to the daily rows to recover the corresponding expiry dates, forwards and discount factors.

| Model field | Meaning |
| --- | --- |
| `smoothness`, `expiry_linear` | Surface smoothing parameter and whether the preliminary expiry fits use the linear representation. |
| `min_half_spread` | Normalized half-spread floor for fit weighting and excess statistics; `1e-4` for these runs. |
| `expiries` | Increasing array of fitted maturities in business-year fractions. |
| `variances` | Reference ATM total variances used by the representation. `sqrt(variances/expiries)` gives reference ATM volatilities; they need not equal the final fitted ATM implied volatilities. |
| `input_index` | Indices mapping retained model maturities back to the input expiry groups. |
| `strikes`, `bids`, `asks` | Per-expiry input normalized strike and reference-quote arrays. |
| `masks` | Per-expiry active-strike masks relative to those input arrays. |
| `fits1`, `fitsX` | Preliminary per-expiry and final surface normalized fitted prices on the input strikes. `fitsX` is optional outside surface mode. |
| `xstrikes`, `xdensities` | Preliminary per-expiry support grids and calibrated probability weights. |
| `mstrikes`, `mdensities` | Final surface support grids and calibrated probability weights, interpreted together with `smoothness` and `variances`. These weights are not pointwise density ordinates. |
| `xix_to_mix` | Maps each preliminary support grid into its final surface grid; an expiry can use `None` when the grids coincide. |
| `run_time_expiry`, `run_time_surface` | Recorded fitting times in seconds; exclude data preparation and independent auditing. |

DLV values are derived from the saved representation rather than stored in a separate daily DLV column. Fitted ATM implied volatilities can be obtained from the saved pricer at normalized strike `1.0`; see [saved daily parameters](#saved-daily-arbfreepricer-parameters).
