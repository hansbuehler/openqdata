# oqdata.yahoo

Yahoo Finance prices, dividends and earnings.

```python
from oqdata.yahoo import YFClient
client = YFClient()
```

Yahoo Finance access is managed by yfinance. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Yahoo finance. Public entry points: package exports.
- `client.py`: Yahoo finance. Public entry points: `YFConnectionConfig`, `DataError`, `YFClient`.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

## Original module documentation

# [Yahoo Finance](https://ranaroussi.github.io/yfinance/)

This directory provides access to Yahoo Finance via https://ranaroussi.github.io/yfinance/.
So far coverage is minimal.

## Data Access

This data is freely available and does not require configuration
beyon what is required by **oqdata**:

  1. Make sure you configure the python environment for **oqdata** following [the introduction](../../../README.md) which means to set at
  least the ``OQ_DATA_ROOT`` environment variable. 
  [See the configuration guide for data locations](../../../docs/configuration.md).

  2. Run [``notebooks/viz_history.ipynb``](notebooks/viz_history.ipynb) to validate everything works.
