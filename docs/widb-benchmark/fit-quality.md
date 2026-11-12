# Interpolation quality on SPX, 2005–2025

The [WIDB benchmark data](pipeline.md) pair cleaned SPX quotes with an arbitrage-free SANOS interpolation. This page reports how closely that interpolation stays within the cleaned bid/ask quotes. It covers 5,151 dates from 2005-01-03 to 2025-08-29, with NYSE early-close days excluded, for two input populations at smoothness 0, 0.1 and 0.25:

- **`all` (Everything)** fits every reasonable paired observation after raw and expiry validation.
- **`flt` (filtered)** fits the selected book: eligibility criteria and the 1,000-row cap applied after a full-book linear fit.

Fit quality is measured in two ways:

1. **Against the constructed reference call quotes** that the fitter calibrates to. This is the main table and the graphs.
2. **Against both original call and put markets.** See [Reference quotes versus original markets](#reference-quotes-versus-original-markets).

Everything fits all reasonable paired observations after raw and expiry validation. The filtered dataset first performs full-book linear cleaning, applies the paper eligibility criteria and 1,000-row cap, then fits a separate SANOS surface. All saved models passed an independent post-repair audit of density bounds, mass, forward mean, calendar and calibration-LP constraints at 1e-5. Recovery checks 1e-7 first.

Two ticker-level historical day exclusions, 2006-11-17 and 2015-08-21, use separately reconstructed observations. These overrides are part of the run's recorded configuration.

**The table and graphs below measure the fit to the constructed ("fixed") reference call quotes.** They do not measure whether the fitted call and its parity-derived put both lie inside their original markets. The [quote construction](../../src/openqdata/widb/day.py) converts put quotes to calls using the implied forward and discount factor, takes the midpoint between the higher bid and lower ask, then assigns the smaller of the original call and put spreads. This interval can differ from the actual overlap of the two markets, including when they do not overlap at all. The [original-market comparison](#reference-quotes-versus-original-markets) below excludes those inverted pairs from evaluation only; all saved calibrations remain unchanged.

| Population | Smoothness | Dates | Mean daily within bid/ask | Mean daily conditional excess | Median daily conditional median | Median runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| all | 0 | 5,151 | 97.9293% | 0.371128 | 0.123896 | 6.458 |
| all | 0.1 | 5,151 | 97.6819% | 0.284828 | 0.117361 | 9.769 |
| all | 0.25 | 5,151 | 94.0571% | 0.615790 | 0.209612 | 9.787 |
| flt | 0 | 5,151 | 99.4770% | 0.178039 | 0.000000 | 0.663 |
| flt | 0.1 | 5,151 | 99.0928% | 0.352947 | 0.119839 | 1.150 |
| flt | 0.25 | 5,151 | 95.0397% | 0.774698 | 0.359810 | 1.215 |

The isolated runtime recovery adapter starts with Clarabel at 600 seconds and retries unsuccessful solves at 3,000 seconds. Feasible native iterates are checked at 1e-7 before permitting 1e-5, then the original density repair and an independent post-repair audit are applied. Acceptance proves numerical feasibility, not optimality. An infeasible preliminary hard bid/ask helper LP does not imply that the final soft-fitting problem is infeasible. Each input population is evaluated without dropping internally masked strikes.

Conditional excess is measured in reference half-spreads for observations outside the constructed reference bid/ask, with the fitter's minimum half-spread of 1e-4 in normalized price units; a day with no excess records zero. Runtime is the sum of the recorded per-expiry and surface fitting times. It excludes enrichment, fitted-row packing, model serialization and the independent feasibility audit; audited wall time is recorded separately. All requested dates were processed before refreshing these figures.

Each column shows one smoothness level. Dates and each metric’s vertical scale are shared across columns. The first two rows report the same saved model’s reference-quote coverage on the full eligible book and on the filtered book, respectively. These historical plots include inverted pairs in their reference-quote evaluation. The filtered model evaluates other maturities using its usual interpolation and extrapolation; 0.50% of full-book observations across the three smoothness levels fall outside the fitted maturity range. Conditional errors and option counts refer to each model’s input population. Each counted paired strike/expiry observation corresponds to one call and one put.

### Fitting to all options

The full eligible book consists of paired observations that pass the [default raw-quote and expiry-validation pipeline](pipeline.md#1-default-cleaning-before-the-linear-fit); it has no subsequent 1,000-option selection.

![Everything](../figures/sanos-all-population-comparison.png)

### Fitting to 1000 filtered options

After the default cleaning and a full-book linear fit, the [eligible-option filter](pipeline.md#3-separate-eligible-option-filter-and-1000-row-cap) retains options with at most 756 business days to expiry, ATM-based NMS5 between -5 and 2, combined volume and open interest each at least 9, and at least 10 eligible strikes per expiry. It retains AM and PM options and caps the selection at 1,000 paired observations, prioritizing strikes near ATM while reserving strikes per expiry. The smooth surface is then fitted to that selection.

Filtering mainly improves speed: at smoothness 0.25, median fit time falls from 9.79 seconds for the full book to 1.22 seconds for the filtered book. On the same filtered options, mean daily bid/ask coverage rises modestly from 93.64% for the full-book model to 95.04% for the filtered model. Individual days can differ much more: on 11 April 2025, the corresponding 0.25 fits cover 39.1% and 90.9%, respectively.

![Filtered](../figures/sanos-flt-population-comparison.png)

## Excluded dates

**2025-01-08 is excluded from both populations by `BAD.DAYS_ALL`.** No SANOS fit was attempted for it. The only recorded reason is the tentative comment `expiries with zero business days?`; there is no recorded solver failure. **2025-01-09 was a market closure**, and quotes for that irregular expiry are filtered out by default. The whole-day exclusion of January 8 should be checked against its quotes, using the current expiry cleaning, before the date scope changes.

Fitted rows and saved models are described in the [field reference](fields.md). Licensed observations, caches, models and diagnostics are kept outside Git.

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

As a check, the evaluation reproduced all 61,812 daily reference-coverage counts across both evaluation populations exactly, before the inverted-pair exclusion. Removing inverted pairs changes the denominators and the excess distribution, not the successful-pair counts.

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
