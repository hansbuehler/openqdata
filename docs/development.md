# Development

openqdata is research software for academic use. Contributions follow [STYLE_GUIDE.md](https://github.com/hansbuehler/openqdata/blob/main/STYLE_GUIDE.md): correct measures, units and timing conventions come first, and every cache-affecting change bumps its `@version`.

## Offline tests

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

The suite forces `OQ_DATA_TEST_MODE=1`, selects `tests/stored_data`, and blocks socket connections. WIDB and arbfree tests construct deterministic synthetic markets from `tests/stored_data/synthetic_widb.py`; no WRDS observations, historical surface samples or processed WIDB snapshots are needed. The recipe reads no data files and never connects to a provider. Tests write caches and model round trips only beneath their temporary output directory.

Massive endpoint, quote/trade, contract and ticker-history tests also use independently invented payloads from `tests/stored_data/synthetic_massive.py`. Conversion and processing execute normally; only provider retrieval and cache-only vendor lookup are replaced. The remaining FRED/Yahoo CSV tables are synthetic transformation inputs. No downloaded provider fixtures are included.

Python compatibility is checked in CI on 3.12, 3.13 (primary) and 3.14. Optional JAX is tested separately from the default data package. Generated test/build output belongs in an external run directory.

Synthetic endpoint payloads cover client conversion, split-adjustment dates, option-bar cache keys, pagination and closing-condition filtering. Live endpoint coverage is described below.


### WIDB benchmark pipeline

`tests/widb/test_pipeline.py` recomputes cleaning, enrichment, the linear DLV fit, eligible-option selection, smooth SANOS fits at 0/0.1/0.25, HDF5 reload/repricing, time-series padding and downstream day extraction from independently constructed synthetic observations. Only provider retrieval is replaced; the filters, fitters and packing functions execute normally. The shared network guard remains active. Calls and puts are built from an independent Black–Scholes formula with invented strikes, forwards, rates, identifiers and activity. Deliberate above-IV-ceiling prices exercise enrichment rejection; a butterfly-arbitrage expiry exercises fitter expiry removal. These inputs are not masked or rescaled licensed observations.

The checks target behavior: strict bid-floor and quote rejection before call/put pairing; distinct pre-linear 10/4 traded-strike requirements; eligibility boundaries and the AM default; expiry removal after selection; 1,000-row cap reservations on a larger synthetic book; normalization preserving pure inputs; original quotes preserved by linear fitting; density mass/mean/calendar feasibility; quote-error definitions and model round trips; and padding masks distinct from active-fit masks. They do not compare arbitrary optimizer-dependent fitted mids or merely count tests.

Cache regressions exercise uncached/read-only packing, the configured fitting backend, writable daily caches, cache-only replay and known-bad-day skip/raise behavior. The writable-cache check uses an isolated subprocess with an empty configuration and temporary raw/processed roots. It constructs the same synthetic observations, blocks network access and then refuses every provider lookup to prove cache reuse.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/widb tests/arbfree
```

The existing CI command runs these alongside all other offline source/processing tests on Python 3.12–3.14. See [the pipeline and configurations](widb-benchmark/pipeline.md).

### Commit hook

The tracked `.githooks/pre-commit` runs the full offline suite against the working tree, using the active environment's `python`. It creates and removes its own scratch directory beneath `${TMPDIR:-/tmp}/openqdata/`; it never downloads fixtures or installs dependencies.

```sh
git config core.hooksPath .githooks
git hook run pre-commit
```

Activate the environment containing `.[test]` first, or select its interpreter explicitly:

```sh
OPENQDATA_TEST_PYTHON=/path/to/environment/bin/python git hook run pre-commit
```

The hook is configured locally for this checkout; other clones can opt in with the command above. It does not replace the Python-version CI matrix. To disable this checkout's hook configuration, use `git config --unset core.hooksPath`.

## Live validation

Live checks are run manually against real provider accounts, with an isolated environment and a fresh external data root. They are never part of the offline suite.

- **Downloads:** FRED, Cboe VIX, Yahoo prices, Massive (every supported endpoint and aggregate timespan, with pagination) and WRDS IvyDB.
- **Processing:**
  - Massive trade/quote filtering and alignment, and contract filtering.
  - The WIDB stages: raw collection, enrichment, arbitrage-free fitting, option filtering, time-series packing and surface fitting.
  - Ticker calendars.
- **Cache replay:** a second process with network access blocked replays every output from the cache and checks it against the live run.
- **Python 3.14:** the WIDB results on Python 3.14 are checked against Python 3.13. On 3.14, authentication uses `.pgpass`.

Reports and logs stay with the external run outputs. Credentials are never written into reports.

## Releases

See [releasing](releasing.md). Changes are listed in [CHANGELOG.md](https://github.com/hansbuehler/openqdata/blob/main/CHANGELOG.md).
