# Fitted rows and saved model fields

This page describes the [WIDB benchmark data](pipeline.md): the daily rows, which hold the cleaned quotes and the interpolated prices, and the saved `ArbFreePricer`, which is the interpolating surface itself. A daily observation row pairs a call and a put at the same strike, expiry, settlement and exercise style; it does not represent two independent calibration targets. The six labels distinguish the Everything (`all`) and selected (`flt`) calibration populations at smoothness 0, 0.1 and 0.25. The source configuration and saved model, rather than the filename alone, determine the fitting settings.

The raw, enriched and fitted schemas are cumulative. The declarations in [day.py](../../src/openqdata/widb/day.py) (`SCHEMA_RAW_DAY`, `SCHEMA_ENRICHED_DAY`) and [arbfree.py](../../src/openqdata/widb/arbfree.py) (`SCHEMA_ARB_FREE_DAY_EXPIRY`, `SCHEMA_ARB_FREE_DAY_SURFACE`) define the column names and dtypes. Unless noted otherwise, numerical row fields are `float32`; identifiers are `int32`, flags are Boolean, dates are stored as `datetime64[ms]`, and ticker/symbol fields are strings represented by pandas object columns.

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

These original quotes remain licensed observations. Keeping them alongside the fit does not mean they are all active in the fitting objective. In particular, the selected dataset omits unselected rows, and the internal fitter can mask strikes. The default input cleaning is documented separately in the [market-data pipeline](pipeline.md#1-default-cleaning-before-the-linear-fit).

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

The reference-call midpoint lies halfway between the higher call-equivalent bid and lower call-equivalent ask; its spread is the smaller original call/put spread. It need not be the actual intersection of the two quote intervals. See [reference quotes versus original markets](fit-quality.md#reference-quotes-versus-original-markets) for the separate original-market evaluation and treatment of inverted pairs.

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

The native-coordinate fitted call price is `df*fwd*pure_fitX_price`; the fitted put price follows parity as `df*fwd*(pure_fitX_price - 1 + pure_strike)`. These daily schemas do not add native-coordinate `fit_*` Greek columns.

Generic `filter_options_day` output can additionally apply `OptionsFilter(normalize=True)`. That removes `spot`, adds the original close as `spot_ref` and the return `spot_ret = spot/spot_prev - 1`, and divides `spot_prev`, `strike`, `fwd`, `call_bid`, `call_ask` and all four `mkt_*` quote columns by the current spot. `fwd_ref` remains in its original units. All `pure_*` fields remain unchanged. `fit_sanos_day` selects with `normalize=False`, retaining native price units; do not confuse spot-normalized time-series output with these fitted caches. See [the output-normalization setting](pipeline.md#3-separate-eligible-option-filter-and-1000-row-cap).

Packed time series add `is_valid` to distinguish real rows from padded slots. It is a packing mask, separate from `mask_arb_free`. Per-day fit statistics such as coverage, excess and runtime live in reports rather than being replicated as option-row columns.

### Saved model parameters

A saved model is `ArbFreePricer.to_dict()`, typically written as HDF5. Reload it with `ArbFreePricer.from_dict` (see [the toolkit](../arbfree.md#saving-and-reloading)); optional fields are encoded for HDF5 and should not be interpreted by reading sentinel strings directly. The model uses normalized strikes and prices; join its maturities to the daily rows to recover the corresponding expiry dates, forwards and discount factors.

| Model field | Meaning |
| --- | --- |
| `smoothness`, `expiry_linear` | Surface smoothing parameter and whether the preliminary expiry fits use the linear representation. |
| `min_half_spread` | Normalized half-spread floor for fit weighting and excess statistics; `1e-4` by default. |
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

DLV values are derived from the saved representation rather than stored in a separate daily DLV column. Fitted ATM implied volatilities come from `model.price(model.expiries[:, None], strikes=1.0, mode="surface", and_vols=True)`; the second return value holds them. `sqrt(model.variances / model.expiries)` gives the reference ATM volatilities instead.
