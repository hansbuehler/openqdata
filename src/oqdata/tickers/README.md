# oqdata.tickers

Ticker reference data, corporate actions and exchange calendar integration.

```python
from oqdata.tickers.ticker_calendar import build_ticker_calendar
```

Provider dependencies: Massive and Yahoo. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Ticker Data Module. Public entry points: package exports.
- `ticker_calendar.py`: oqdata.tickers.ticker_calendar. Public entry points: `EXPIRY`, `get_standard_expiries`, `has_dividends`, `has_splits`, `build_ticker_calendar`.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
