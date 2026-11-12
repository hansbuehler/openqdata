# The arbfree toolkit

`openqdata.arbfree` fits arbitrage-free option surfaces to bid/ask quotes. The toolkit works on its own: it takes plain arrays and has no dependency on any data source. The [WIDB benchmark data](widb-benchmark/pipeline.md) use it to interpolate cleaned option quotes without arbitrage.

## Method

The fitter represents each expiry by discrete probability masses on a strike grid. The no-arbitrage conditions are:

- non-negative masses with total mass one;
- mean equal to the forward;
- a calendar ordering across expiries.

All three are linear constraints, so finding a surface inside the bid/ask spread is a linear program. In surface mode, a fit inside bid/ask exists, up to numerical precision, if and only if the quotes are free of arbitrage.

- **Linear (DLV) surface:** `smoothness=None` or `0`. See [SSRN 2642630](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2642630) and [arXiv:2211.13227](https://arxiv.org/abs/2211.13227).
- **SANOS surface:** `smoothness > 0`. A smooth, arbitrage-free, non-parametric option surface, following [SANOS](https://arxiv.org/abs/2601.11209). The strike range is extended per remark 2.7 of that paper.

All inputs use forward-normalized, undiscounted coordinates: the strike is `k = K/F` and the call price is `c = C/(DF·F)`. Maturities are year fractions.

## Classes

| Object | Role |
|---|---|
| `arbfree.MkArbFree` | Frozen configuration and fitter. Calling it with `expiries, strikes, bids, asks` returns an `ArbFreePricer`. |
| `arbfree.ArbFreePricer` | The fitted surface: `price(...)`, `compute_market_fit(...)`, `interpolate_atm_vols(...)`, `to_dict()` / `from_dict()`. |
| `sanos.SanosFitter`, `sanos_tools.SanosPricer` | Lower-level SANOS fitter and pricer, used by `MkArbFree` for smooth surfaces. |
| `sanos_tools.SanosLPSolver` | LP backend: HiGHS simplex with a Clarabel fallback, time limits and density repair. |
| `sanos_jax.fit_dlvsqs` | Optional JAX fitter (install `openqdata[jax]`; see `openqdata.jax`). |
| `tridiag.solve_sanos_tridiagonal` | Banded solver for SANOS transition operators. |

`MkArbFree` works in two modes:

- **`no_arb_mode="expiry"`** fits each expiry inside its bid/ask spread and drops any expiry where that is impossible, since that means actionable arbitrage.
- **`no_arb_mode="surface"`** (the default) then fits a globally arbitrage-free surface.

Along the way it extends the strike boundaries and can mask strikes that cannot be fitted. It drops expiries that have fewer than `min_strikes_per_expiry` strikes or boundary slopes that are too steep.

| Parameter | Default | Meaning |
|---|---|---|
| `smoothness` | `None` | `None`/`0` for linear; for example `0.1` or `0.25` for SANOS. |
| `surface_expiry_linear` | `True` | Keep the per-expiry step linear when fitting a smooth surface. |
| `mid_fit_weight` | `0.1` | 1 fits mids only; 0 only penalizes distance outside bid/ask. |
| `min_half_spread` | `1e-4` | Spread floor for weighting and error statistics, in normalized units. |
| `min_dlv`, `max_dlv` | `None` | Optional bounds on discrete local volatility. |
| `timeout_seconds` | `300` | Solver time limit. It is excluded from the cache key. |

## Example

```python
import numpy as np
from scipy.stats import norm
from cdxcore.verbose import Context
from openqdata.arbfree.arbfree import ArbFreePricer, MkArbFree

def bs_call(k, vol, t):                     # undiscounted call on a unit forward
    sd = vol * np.sqrt(t)
    d1 = -np.log(k) / sd + 0.5 * sd
    return norm.cdf(d1) - k * norm.cdf(d1 - sd)

expiries = np.array([0.1, 0.25, 0.5, 1.0])
strikes, bids, asks = [], [], []
for t in expiries:
    k = np.linspace(0.8, 1.2, 21)
    mid = bs_call(k, 0.2 - 0.1 * np.log(k), t)   # a simple skew
    half = np.maximum(0.02 * mid, 2e-4)
    strikes.append(k); bids.append(mid - half); asks.append(mid + half)

model = MkArbFree(smoothness=0.1)(expiries=expiries, strikes=strikes, bids=bids, asks=asks,
                                  verbose=Context.quiet)
fit = model.compute_market_fit(expiries=expiries, strikes=strikes, bids=bids, asks=asks, and_vols=False)
prices, vols = model.price(np.array([[0.3]]), strikes=np.array([[0.9, 1.0, 1.1]]),
                           mode="surface", and_vols=True)
```

`compute_market_fit` reports `pcnt_fit`, which despite its name is the **fraction of quotes outside** bid/ask. It also reports `mean_err` and `median_err`, the excess outside bid/ask in half-spread units, conditional on being outside. In this example `pcnt_fit` is `0.0`.

## Saving and reloading

`to_dict()` returns plain NumPy data that can be written as HDF5. `from_dict()` restores the pricer without recalibrating:

```python
from cdxcore.subdir import SubDir
from openqdata import env

store = env.locations.processed("examples/arbfree", fmt=SubDir.PYTREE_HDF5)
store.write("model", model.to_dict())
restored = ArbFreePricer.from_dict(store.read("model"))
```

The [field reference](widb-benchmark/fields.md#saved-model-parameters) describes every saved field.
