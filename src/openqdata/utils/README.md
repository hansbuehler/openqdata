# openqdata.utils

Shared array backbones, Pandas/Polars schemas, numerical helpers and test comparisons.

```python
from openqdata.utils import Eps
eps = Eps()
```

No provider credentials. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Basic shared Utilities. Public entry points: `Eps`.
- `backbone.py`: Abstract Numerical Backbone. Public entry points: `Backbone`, `sigmoid`, `relu`, `are_broadcastable`, `BackboneNumpy`.
- `cvxpy.py`: CVXPY Utilities. Public entry points: `patch_cvxpy_sum_shape_from_args`.
- `pd.py`: Panda Utilities. Public entry points: `create_empty_df`, `verify_schema`.
- `pl.py`: Polars Utilities. Public entry points: `create_empty_df`, `verify_schema`.
- `testing.py`: Utility functions for testing Data Frames. Public entry points: `assert_pl_frame_equal`, `assert_pd_frame_equal`, `hash_pandas_df`, `hash_polars_df`.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
