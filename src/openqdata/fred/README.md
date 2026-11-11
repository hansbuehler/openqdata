# openqdata.fred

FRED interest-rate series.

```python
from openqdata.fred import load_fred_rates
rates = load_fred_rates("2022-01-01", "2022-02-01")
```

FRED_API_KEY. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: openqdata.fred. Public entry points: package exports.
- `rates.py`: openqdata.fred.rates. Public entry points: `load_fred_rates`.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
