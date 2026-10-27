# quantdata.massive.options

Massive market-data client, quote/trade processing, option contracts and ticker histories.

```python
from quantdata.massive import MassiveClient
client = MassiveClient()
```

MASSIVE_TOKEN. Data paths come from `quantdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Massive.com Options Data Module. Public entry points: package exports.
- `contracts.py`: quantdata.massive.options.contracts. Public entry points: `REJECTED`, `ContractsFilter`, `filter_contracts`, `filter_contracts_between`, `main`.

Processing modules provide `python -m quantdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
