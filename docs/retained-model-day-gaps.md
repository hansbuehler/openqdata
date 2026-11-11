# The 19 gaps in the retained 2022–2025 model panel

All six quantdata SPX benchmark extracts contain **910 dates from 2022-01-03 through 2025-08-29**. Their dates match the completed daily `ArbFreePricer` archive exactly. The older derived hedging panel contains **891** of those dates: it inherited a historical market-loading failure list before the retained affine-200 DLV model was trained.

## Why the dates disappeared

The original shared-strike native completion report records 19 failures while loading its smoothness-0.25 market surfaces:

- **15** reported `Cannot find no-arbitrage surface mids: reached timeout 300.0 and/or iteration limit.` This message does not distinguish a wall-time limit from an iteration limit and does not establish infeasibility.
- **4** reported `SolverError` because `CLARABEL` failed. The report does not record a more specific native solver status for these errors.

The market loader recorded the errors and continued with the successfully loaded dates. The later fixed-grid report retained the same 891-date `market_dates` list. Preparation of the daily 25-expiry, 200-strike calibration tensor explicitly read that list; the affine-200 model and its derived hedging extract therefore inherited the gaps. Later reports showing no failed dates had already requested only those 891 dates.

The original failure records are preserved here on the calibration host:

```text
/home/hans/quantdata_data/training/flex-shared-strikes/capacity/spx-2022-2025-shared-strikes-v1/reports/spx-2022-2025-shared-strikes-v1-native-complete.json
```

Its `failed_market_dates` field contains the per-date errors; `market_dates` contains the retained dates. That original run requested 918 sessions: the 19 surface failures, seven other failures reporting missing WRDS credentials on early-close dates, and one missing day (`2025-01-08`) left 891. The present benchmark's declared calendar already excludes those seven early closes and the missing day, leaving the 910-date comparison population.

Here "missing" on **2025-01-08** means a policy exclusion, not an absence of quotes or a failed SANOS solve. `BAD.DAYS_ALL` explicitly contains that observation date with the tentative comment `expiries with zero business days?`. `collect_raw_day(..., raise_if_bad_day=False)` returns an empty frame before provider access for a blacklisted date; the raw, enriched and fitted daily caches for SPX on that date are all empty. The historical run therefore did not attempt its calibration. Separately, the raw-quote filter excludes the irregular **2025-01-09 expiry** by default. The whole-day blacklist has not been justified by a recorded fitting failure and should be reassessed against the January 8 quotes with the current expiry cleaning before its scope is changed.

## Per-date reasons

| Date | Recorded historical failure |
|---|---|
| 2022-03-22 | 300-second timeout and/or iteration limit |
| 2022-08-11 | 300-second timeout and/or iteration limit |
| 2022-10-28 | 300-second timeout and/or iteration limit |
| 2023-05-17 | 300-second timeout and/or iteration limit |
| 2023-06-02 | 300-second timeout and/or iteration limit |
| 2023-07-06 | 300-second timeout and/or iteration limit |
| 2023-10-02 | Clarabel solver error |
| 2023-10-06 | 300-second timeout and/or iteration limit |
| 2023-11-02 | 300-second timeout and/or iteration limit |
| 2024-01-10 | Clarabel solver error |
| 2024-01-26 | 300-second timeout and/or iteration limit |
| 2024-02-13 | 300-second timeout and/or iteration limit |
| 2024-02-28 | Clarabel solver error |
| 2024-03-04 | 300-second timeout and/or iteration limit |
| 2024-07-11 | 300-second timeout and/or iteration limit |
| 2024-07-18 | 300-second timeout and/or iteration limit |
| 2024-07-24 | 300-second timeout and/or iteration limit |
| 2024-08-01 | 300-second timeout and/or iteration limit |
| 2025-05-16 | Clarabel solver error |

All 19 dates have completed, audited models for **both populations and all three smoothness levels** in the current quantdata archive. All 114 corresponding model files exist and their daily reports record `passed`. These historical errors explain the older panel's date selection; they are not current quantdata calibration failures or an additional option-quality filter.

## Verification and reproduction

The 2026-11-10 date audit read the date column of every retained benchmark Parquet partition and matched each of the six 5,151-date extracts to the licensed run manifest. Restricting each extract to 2022 onward gives exactly 910 dates. The original completion report, later fixed-grid date report, daily calibration tensor and derived hedging dataset all retain the same 891-date subset. Their difference is exactly the 19 dates above.

To inspect the original reasons without downloading data or running a solver:

```python
import json
from pathlib import Path

root = Path("/home/hans/quantdata_data")
run = root / "quant_data/qdata/runs/spx-private-public-20261101T135819Z-819d9b59"
source = root / "training/flex-shared-strikes/capacity/spx-2022-2025-shared-strikes-v1/reports/spx-2022-2025-shared-strikes-v1-native-complete.json"
expected = {d for d in json.loads((run / "manifest.json").read_text())["dates"] if d >= "2022-01-01"}
report = json.loads(source.read_text())
missing = expected - set(report["market_dates"])
errors = {item["date"]: item["error"] for item in report["failed_market_dates"]}
assert len(expected) == 910 and len(missing) == 19
for day in sorted(missing):
    print(day, errors[day])
```

The detailed audit, original error text and source-report fingerprints are retained outside Git under the completed run's `analysis/public-day-coverage/retained-891-gaps.json`. The fitted models, derived datasets and their immutable manifests remain unchanged.

## Recovery for subsequent derived-model runs

The derived-model production runner now retries recognized surface-solver errors and limit failures once with a 3,000-second budget, preserving the date, book, filters, geometry and smoothness. The established HiGHS-to-Clarabel solver fallback remains in use. Successful retries record the primary error and retry budget under `recovered_market_dates`. If any requested day remains failed or empty, the run writes `status="market_loading_failed"` and raises before training. A reduced date population requires an explicit requested scope; it cannot result silently from loading errors.
