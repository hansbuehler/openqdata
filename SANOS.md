# SANOS — “Everything” fit

Updated 2026-10-30T00:12:10.502937+00:00. **Complete: 5,151 SPX dates × three smoothness values = 15,453 feasible fits.**

The comparison covers **2005-01-03 to 2025-08-29**. Every model passed independent checks of the original linear constraints and variable bounds, including density mass/mean and calendar prices across adjacent strike grids, at absolute tolerance **1e-5**. Publication also reloaded each recovered model and reproduced its saved quote errors.

## Population and method

**Everything means all reasonable options.** Every quote passing the existing raw-data and expiry-validity checks enters the calibration input and fit evaluation. The original redundant-strike masks determine which quotes enter the active objective. There is no additional volume/open-interest screen, NMS window, maturity cap, option-count cap, strike subsampling or liquidity weighting. Active quotes have user weight 1; the original half-spread normalization remains in the objective.

**Market-data defaults before any linear fit:** `RawDayFilter()` removes known bad inputs, missing/locked/crossed quotes, same-day/irregular expiries and nonstandard settlement flags, and requires each call/put bid to be strictly greater than 0.011 before pairing. `ExpiryFilter()` requires ten strike rows per expiry with either side traded and four with both traded, a minimum pure spread of 1e-6 and usable implied-volatility inversion within [0.01, 5.0]. These traded-strike counts validate the expiry forward; they impose no per-row open-interest threshold or 1,000-row cap.

**Later eligible-option selection is separate:** the paper-style population additionally applies `OptionsFilter()` (maturity, ATM NMS5, volume/open interest and minimum eligible rows per expiry), followed by the 1,000-row cap. Everything bypasses this selection. The [complete market-data pipeline, exact defaults and Python examples](docs/market-data.md) describe both stages and the intervening linear fit.

MkArbFree retains its linear per-expiry preprocessing, then fits the joint surface at smoothness 0, 0.1 or 0.25. Its internal redundant-strike masks and density repair are unchanged. Input and active objective counts are recorded separately; fit statistics evaluate **all reasonable input quotes**, including internally masked quotes.

The 5,131 previously successful 0.25 models are retained at their original paths. Option counts and outside counts match exactly; error statistics match to numerical precision.

Two historical day exclusions, **2006-11-17** and **2015-08-21**, were explicitly reconstructed from stored WRDS downloads. Only those day exclusions were bypassed; all per-option rules remain. Their six fits are labeled `historical_day_exclusion_override=true`. The frozen baseline has 5,149 dates; this comparison uses the expanded 5,151-date universe consistently for every smoothness.

## Results on the same dates and quotes

| Smoothness | Outside bid/ask, pooled | Outside bid/ask, daily mean | Conditional mean excess | Median daily conditional median | Median recorded fit seconds |
|---|---:|---:|---:|---:|---:|
| 0 | 1.8446% | 2.0730% | 0.4031 | 0.1232 | 12.36 |
| 0.1 | 1.9809% | 2.3206% | 0.3930 | 0.1168 | 19.04 |
| 0.25 | 8.4219% | 5.9465% | 1.5263 | 0.2088 | 15.45 |

Errors are measured in half-spreads: distance outside the original bid/ask interval divided by `max((ask-bid)/2, 1e-4)`. Conditional statistics include only quotes outside bid/ask; a day with no excess has conditional mean/median zero. Pooled percentages weight options equally; daily means weight dates equally. The median column is the median of daily conditional medians, not the pooled option-level median.

Recorded fit times are stored per-expiry plus surface durations, excluding enrichment, evaluation and unsuccessful attempts. Reused geometry can carry an earlier preprocessing duration, so these are not necessarily fresh wall-clock timings. Historical native-iterate reuse has no fresh calibration runtime and is excluded. There is no timing graph.

![Everything fit across all 5,151 dates](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/sanos-fit.png)

## Numerical failures and remedies

The explicit recovery register contains **47 observed failed fits recovered; 18 paired validation fits; 10 missing scheduled fits completed; zero unresolved fits.** Five preseeded recovery reports contained only smoothness 0.25 and were incorrectly treated as complete by the controller. Their ten missing 0/0.1 fits were subsequently calibrated and independently validated; these are recorded separately from LP failures.

Clarabel numerical stops could occur before the time limit while retaining a usable primal vector. CVXPY raised before unpacking that vector and before the original density repair. Recovery checks the native vector against original constraints and bounds at the strict 1e-7 gate first, then the permitted 1e-5 tolerance, preserves nonconverged status, applies the original repair, and validates the saved model again. When a new solve is needed, the isolated adapter tries alternative numerical regularization settings without changing the objective, option population or constraints.

Some preliminary per-expiry hard bid/ask helper LPs were infeasible, while the final soft fit remained feasible. A solver-reported optimal helper result that violated its constraints could prevent the existing soft fallback. Independent native checks, including HiGHS classification where needed, restored that fallback without changing the final objective.

Independent checks distinguish the original interior calendar rows from the full range, including adjacent-grid endpoints. Density repair can change calendar residuals, so a pre-repair feasibility check alone is insufficient. Nonconverged acceptance establishes numerical feasibility, not optimality. Historical HiGHS `kNotset` events were interface/numerical failures, not established infeasibility; absent old native logs prevent a more precise retrospective cause.

The model/solver package source was not changed for these recoveries. Work used frozen source and the temporary updated Python environment documented in the manifest. Source hashes, solver settings, available failed reports and native vectors, input hashes and model certificates are retained. Earlier attempt artifacts removed by approved cleanup limit retrospective diagnosis of their internal solver breakdown; every final model was independently audited.

## Records and evidence

- [Every fit, model path and input provenance](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/consolidated-fit-records.jsonl)
- [Daily statistics](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/consolidated-daily-stats.csv)
- [Aggregate statistics and index checksum](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/consolidated-summary.json)
- [Independent full-LP feasibility snapshot](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/diagnostics/latest-feasibility-snapshot.json)
- [Final coverage, stored-statistics and file-integrity validation](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/diagnostics/latest-completion-validation.json)
- [Recovery adapter and numerical-audit tests: 44 passed](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/diagnostics/highs-operation-review-20261029T121100Z/validation.json)
- [Failure and completion case register](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/diagnostics/failure-cases.md)
- [Detailed diagnoses and remedies](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/diagnostics/failure-review.md)
- [Population definition](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/fit-scope.json)
- [Frozen source, environment and run settings](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/manifest.json)
- [Three-panel figure as PDF](/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e/sanos-fit.pdf)

Generated data, models, logs and certificates remain outside Git under `/home/hans/quantdata_data/quant_data/qdata/runs/spx-full-sanos-20261028T224615Z-49d7676e`.

<!-- SANOS PAPER FILTERED COMPARISON -->
## Paper-style filtered comparison

Updated 2026-10-30T19:46:07.337630+00:00. **Complete: 15,453 verified fits; 5,151 dates with all three smoothness values.** Requested: all 5,151 dates from the Everything run, newest first.

The default paper-style filter is applied before the joint fit: ATM-based NMS5 in [-5, 2], maturity at most 756 business days, combined call/put `log10(1+volume) >= 1` and `log10(1+open_interest) >= 1`, at least ten quotes per expiry, and the original **1,000-option cap**. The cap retains at least ten near-ATM strikes per expiry and fills remaining slots by absolute NMS5. AM-settled options remain eligible. The declared `min_vegaSqrtVar=0.001` is unused by the original filter implementation; no new vega screen is added.

Same-date original linear preprocessing determines the initial retained expiries and is reused from the saved Everything model. The raw bids/asks and enrichment are unchanged. After filtering, MkArbFree performs its original linear per-expiry preprocessing and fits smoothness 0, 0.1 and 0.25, with equal user weights, existing redundant-strike masks and original density repair. The shared linear geometry is reused between the three fits. Native vectors are checked at 1e-7 first, then the permitted absolute 1e-5; each saved model also passes the independent full-range original-LP audit.

These are new computations with the paper-style filter. The exact source/settings/cache behind the historical attached paper figure remain unverified; numerical identity to that figure is not claimed. The Everything results above remain a separate population. The two explicitly reconstructed historical input dates retain their override labels.

| Smoothness | Dates | Outside bid/ask, pooled | Outside bid/ask, daily mean | Conditional mean excess | Median daily conditional median | Full fit outside on identical filtered quotes |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 5,151 | 0.2969% | 0.5230% | 0.3517 | 0.0000 | 0.4699% |
| 0.1 | 5,151 | 0.5512% | 0.9072% | 0.5915 | 0.1198 | 0.5377% |
| 0.25 | 5,151 | 6.7159% | 4.9603% | 1.5116 | 0.3598 | 8.9749% |

Fit statistics evaluate every quote in the filtered input, including internally masked quotes. Conditional errors use only quotes outside bid/ask, measured in half-spreads with a 1e-4 floor. A day with no excess has conditional mean/median zero. The median column is the median of daily conditional medians. The last column revalues each saved Everything model on the exact same filtered quotes; it is not the full-book percentage.

Dates with no quotes after filtering: 0. Pending or failed requested fits: 0. Such cases are recorded explicitly and excluded from fit statistics; this is not a claim of an infeasible LP.

![Filtered fits](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/filtered-fit.png)

[Every fit and certificate](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/fit-records.jsonl) · [Daily statistics, including paired full-model errors](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/daily-stats.csv) · [Summary and coverage](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/summary.json) · [Filter, inputs and provenance](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/manifest.json) · [Alerts](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/alerts.jsonl)

[Final coverage and integrity validation](/home/hans/quantdata_data/quant_data/qdata/runs/spx-paper-filtered-20261030T185303Z-1f451fc1/diagnostics/final-validation.json)

<!-- END SANOS PAPER FILTERED COMPARISON -->
