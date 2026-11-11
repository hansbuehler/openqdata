# oqdata.massive.testing

Massive market-data client, quote/trade processing, option contracts and ticker histories.

```python
from oqdata.massive import MassiveClient
client = MassiveClient()
```

MASSIVE_TOKEN. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Scope for locally stored testing data. Public entry points: package exports.
- `generate.py`: Generate massive test data. Public entry points: `generate_day`, `main`.
- `scope.py`: WIDB Testing scope for locally stored sample testing data. Public entry points: package exports.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

Fixture generation is an explicit live operation. It is never invoked by the offline test suite. Use an external data root and copy reviewed fixtures intentionally.
