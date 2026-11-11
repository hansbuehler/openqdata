# oqdata.arbfree

SANOS arbitrage-free option surfaces, density projection and fitting utilities.

**Performance:** See [historical SPX fit quality and runtime](../../../SANOS.md) for bid/ask coverage on the full and filtered populations, conditional errors, option counts, and runtimes at each smoothness level.

```python
from oqdata.arbfree.arbfree import MkArbFree
config = MkArbFree()
```

Numerical fitting uses CPU by default; optional JAX fitter requires the jax extra. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: SANOS Smooth Arbitrage-free Non-parametruc Option Surfaces. Public entry points: package exports.
- `arbfree.py`: Make arbfree markets. Public entry points: `ArbFreePricer`, `MkArbFree`.
- `sanos.py`: SANOS. Public entry points: `SanosFitter`.
- `sanos_jax.py`: SANOS (Jax). Public entry points: `fit_dlvsqs`.
- `sanos_tools.py`: SANOS. Public entry points: `SanosPricer`, `SanosLPSolver`, `repair_density_nonnegative`, `warn_and_fix_density`, `make_variances`.
- `tridiag.py`: Grid Sanos tridiagonal solver for SANOS-type transition operators, c.f. http://arxiv.org/abs/2211.13227. Public entry points: `solve_sanos_tridiagonal`.
- `widb_sanos_day.py`: Arbitrage-Free Market Data Filter. Public entry points: `fit_sanos_day`.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

`widb_sanos_day.fit_sanos_day` caches the paper-style licensed fit: full-book linear cleaning, native-coordinate option selection, then a separate SANOS surface fit. Its output is the standard fitted daily DataFrame and its cache identity includes the source, eligibility and SANOS configurations.
