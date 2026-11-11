# oqdata.jax

Optional JAX numerical backbone for the SANOS fitter.

```python
from oqdata.jax.bbjax import BackboneJax
backbone = BackboneJax("cpu")
```

Install the jax extra; no GPU allocation is performed by this package. Data paths come from `oqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Optional JAX numerical backend.. Public entry points: package exports.
- `bbjax.py`: Jax Backbone. Public entry points: `BackboneJax`.

Processing modules provide `python -m oqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.
