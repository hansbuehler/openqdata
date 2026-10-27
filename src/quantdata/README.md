# quantdata

Shared environment, calendar, pool and command-line infrastructure.

```python
from quantdata import env
print(env.locations.raw.path)
print(env.locations.processed.path)
```

See docs/configuration.md. Data paths come from `quantdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Standalone quantitative data access; the quantdata namespace is retained.. Public entry points: package exports.
- `biz_calendar.py`: Business day calendar utilities.. Public entry points: `NormalizedStrikes`, `to_date`, `get_business_days`, `count_business_days_between`, `add_business_days`, `prev_business_day`, `next_business_day`, `get_half_days`, `DateRange`, `session_open_close`, `full_second_grid_ns`.
- `cli.py`: Shared command line adapter for public data-processing functions.. Public entry points: `run_module`.
- `env.py`: Data locations configured by OQ_DATA_* variables or a TOML file.. Public entry points: `Locations`, `Environment`.
- `pool.py`: Implementation helpers. Public entry points: package exports.

Processing modules provide `python -m quantdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
