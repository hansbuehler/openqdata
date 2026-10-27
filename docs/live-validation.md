# Live download and pipeline validation

Validated on 2026-10-26. The primary run used isolated Python 3.13 and a unique external data root; WRDS used one process throughout (limit four). No source or fixture directory was used as an output cache.

Run directory: `/home/hans/quantdata_data/quant_data/qdata/runs/live-20261026T222158Z-4daa84d5`.

| Stage | Result |
|---|---|
| fred_download | passed |
| cboe_download | passed |
| yahoo_download | passed |
| massive_bars_download | passed |
| massive_tick_download | passed |
| massive_processing | passed |
| widb_download | passed |
| widb_enrichment | passed |
| widb_arbfree | passed |
| widb_filter | passed |
| widb_timeseries | passed |
| ticker_calendar | passed |
| widb_surface | passed |
| massive_contracts | passed |

Real downloads succeeded for FRED, official Cboe VIX, Yahoo prices, Massive daily bars and trades/quotes, and WRDS IvyDB. Massive trade/quote filtering and both alignment directions completed. The WRDS SPX 2024-03-05 pipeline produced 10,154 cleaned raw option rows, 9,124 enriched/arb-free rows, and a 1,000-option time-series sample. The full linear arbitrage-free surface, narrow Massive contract filtering and AAPL ticker calendar completed.

A fresh process with socket access blocked replayed 15 table outputs and reproduced each live export exactly, rebuilt the WIDB time-series sample with finite positive prices/strikes/expiries, and exercised the FRED CLI output path. Dates for direct rate/price tests were 2024-03-04 to 2024-03-08; the ticker event/calendar test used 2024-03-01 to 2024-03-28 so it included actual standard-expiry events rather than a legitimately empty event window.

Live Python 3.14 WIDB raw collection, enrichment, per-expiry fitting and option filtering matched the Python 3.13 results. Authentication used the configured PostgreSQL password file; credential values were not written into the reports.

## Fixes found by live execution

- Massive SDK ticker events can contain dictionaries or model objects with a `type` field. The client now normalizes those explicitly rather than constructing an inconsistent `event_type` frame and querying a nonexistent column. Its cache version was bumped; six offline regression cases cover both representations, duplicates, empty responses and date filtering.
- The ticker calendar returns Polars data, so its cache now uses POLARS_PARQUET instead of PANDAS_PARQUET. Its cache version was bumped and an offline real-cache-roundtrip regression was added.
- Pandas 3 infers StringDtype both during construction and when reading Parquet. WIDB restores only strings explicitly declared as object columns at processing input/output boundaries. Numeric schema validation remains strict. A regression verifies this without altering the caller's input.
- An unreachable raw-schema validation after an early return was restored to the active enrichment path.

The full offline suite now has 109 passing tests and 12 skipped for missing legacy fixtures. Detailed live results are in report.json, cache-replay.json, wrds314-report.json and the persistent run logs. Initial failed attempts were retained separately; the report records the successful final run. No commit or push has been made.

The subsequent all-date/model/dependency comparison is documented in reference-validation.md.
