# openqdata.vixdata

Cboe daily VIX history and option-based VIX formulas.

```python
from openqdata.vixdata import load_cboe_vix
vix = load_cboe_vix("2025-01-01", "2025-02-01")
```

Cboe requires no API key. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Official Cboe VIX end-of-day data management.. Public entry points: package exports.
- `cboe.py`: Download, validate, and cache official Cboe end-of-day VIX observations.. Public entry points: `parse_cboe_vix_csv`, `refresh_cboe_vix`, `load_cboe_vix`.
- `formula.py`: Cboe's discrete-strike VIX formula, independent of a pricing model.. Public entry points: `VixStrip`, `select_vix_strip`, `discrete_total_variance`, `constant_maturity_vix`.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

## Original module documentation

# `openqdata.vixdata`

## Dataset contract

**Dataset:** official Cboe daily VIX OHLC history.  It is used as an
independent market-level benchmark for 30-calendar-day S&P 500 implied
variance in academic research.  It is not an option-quote
dataset and must not be used as a substitute for the WRDS option surface.

**Canonical location:** resolve the location through
`openqdata.env.locations("vixdata", fmt_raw=SubDir.POLARS_PARQUET).raw`; do
not hard-code a data-root path. Under the configured raw-data root, the cache
contains `vixdata/cboe/vix_eod.prq` and its provenance manifest
`vixdata/cboe/vix_eod_metadata.json`.

The manifest records the source URL, UTC retrieval time, observation count,
date range, and units.  The data and manifest are deliberately external to
Git; this README is the repository-tracked contract other agents should use.

**Schema:** `date` (`Date`), `open`, `high`, `low`, and `close` (`Float64`).
Levels are annualized implied-volatility percentage points.  `close` is the
official end-of-day series used in research diagnostics.

**Source and refresh:** Cboe's public
[`VIX_History.csv`](https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv).
Use `openqdata.vixdata.refresh_cboe_vix()` to refresh and
`load_cboe_vix(start, end)` to read the inclusive date interval.  The loader
validates the source schema, positive levels, and unique dates.  Some early
Cboe rows have anomalous intraday high/low fields; valid closing levels are
retained.
