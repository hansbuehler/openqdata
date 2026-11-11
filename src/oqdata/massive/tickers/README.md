# oqdata.massive.tickers

Massive market-data client, quote/trade processing, option contracts and ticker histories.

```python
from oqdata.massive import MassiveClient
client = MassiveClient()
```

MASSIVE_TOKEN. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: oqdata.massive.tickers. Public entry points: package exports.
- `basics.py`: oqdata.massive.tickers.basics. Public entry points: `get_listing_date`.
- `data.py`: oqdata.massive.tickers.data. Public entry points: `build_unadjusted_trades`, `build_unadjusted_spot_wmid`, `build_1s_trade_bars`.
- `filtered_history.py`: oqdata.massive.tickers.filtered_history. Public entry points: `ticker_filtered_history`.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
