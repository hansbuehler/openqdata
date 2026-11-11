# openqdata.massive.tickers

Massive market-data client, quote/trade processing, option contracts and ticker histories.

```python
from openqdata.massive import MassiveClient
client = MassiveClient()
```

MASSIVE_TOKEN. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: openqdata.massive.tickers. Public entry points: package exports.
- `basics.py`: openqdata.massive.tickers.basics. Public entry points: `get_listing_date`.
- `data.py`: openqdata.massive.tickers.data. Public entry points: `build_unadjusted_trades`, `build_unadjusted_spot_wmid`, `build_1s_trade_bars`.
- `filtered_history.py`: openqdata.massive.tickers.filtered_history. Public entry points: `ticker_filtered_history`.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
