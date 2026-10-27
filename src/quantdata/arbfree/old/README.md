# quantdata.arbfree.old

SANOS arbitrage-free option surfaces, density projection and fitting utilities.

```python
from quantdata.arbfree.arbfree import MkArbFree
config = MkArbFree()
```

Numerical fitting uses CPU by default; optional JAX fitter requires the jax extra. Data paths come from `quantdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `fitter.py`: Grid Sanos Fitter. Public entry points: `Fitter`.
- `grid.py`: Grid Sanos. Public entry points: `GridGeometry`, `GridGeometryGenerator`, `GridSanos`.
- `open.py`: Open Sanos. Public entry points: `OpenGeometry`, `OpenGeometryGenerator`, `OpenSanos`.
- `utils.py`: Basic utilities for SANOS. Public entry points: `GeometryBase`, `Eps`, `vec_fill`, `vec_max_dx`, `extract_atm_fwd_vols`.

Processing modules provide `python -m quantdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

Legacy implementations are retained for reference; prefer the parent package APIs.
