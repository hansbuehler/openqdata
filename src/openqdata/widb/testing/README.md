# openqdata.widb.testing

WRDS IvyDB options, zero curves, forwards, filters and processed daily surfaces.

```python
from openqdata.widb import WIDBClient
client = WIDBClient()
```

WRDS credentials are supplied to WIDBClient. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Implementation helpers. Public entry points: package exports.
- `generate.py`: Generate WIDB test data. Public entry points: `generate_day`, `main`.
- `scope.py`: WIDB Testing scope for locally stored sample testing data. Public entry points: package exports.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

Fixture generation is an explicit live operation. It is never invoked by the offline test suite. Use an external data root and copy reviewed fixtures intentionally.
