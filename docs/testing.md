# Offline testing

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

The suite forces `OQ_DATA_TEST_MODE=1`, selects `tests/stored_data`, and blocks socket connections. Retained fixtures originate from quant_data tests/stored_data; training sample input is now deliberately retained under processed. No fixture generation or downloads run during tests. The formerly missing FRED, Massive contract and ticker fixtures have been explicitly downloaded and curated; see `tests/stored_data/downloaded-fixtures.json` for provenance. Required fixtures are mandatory: missing files fail tests instead of triggering skips. Small real contract/trade samples exercise processing offline, with contract results checked against the full downloaded reference.

Python compatibility is checked in CI on 3.12, 3.13 (primary) and 3.14. Optional JAX is tested separately from the default data package. Generated test/build output belongs in an external run directory.

Small real endpoint responses in `tests/stored_data/raw/massive/endpoint-responses.json` also cover client conversion, split dates, option-bar cache keys, pagination, and closing-condition filtering. Their provenance identifies the separate live run. Live endpoint coverage is documented in [Massive](massive.md).


## Core market-data pipeline

`tests/widb/test_pipeline.py` recomputes cleaning, enrichment, the linear DLV fit, eligible-option selection, smooth SANOS fits at 0/0.1/0.25, HDF5 reload/repricing, time-series padding and downstream day extraction from retained IvyDB observations. Only provider retrieval is replaced with local files; the filters, fitters and packing functions execute normally. Required fixtures are mandatory and the shared network guard remains active.

The checks target behavior: strict bid-floor and quote rejection before call/put pairing; distinct pre-linear 10/4 traded-strike requirements; eligibility boundaries and the AM default; expiry removal after selection; real 1,000-row cap reservations; normalization preserving pure inputs; original quotes preserved by linear fitting; density mass/mean/calendar feasibility; quote-error definitions and model round trips; and padding masks distinct from active-fit masks. They do not compare arbitrary optimizer-dependent fitted mids or merely count tests.

Cache regressions exercise uncached/read-only packing, the configured fitting backend, writable daily caches, cache-only replay and known-bad-day skip/raise behavior. The writable-cache check uses an isolated subprocess with an empty configuration and temporary raw/processed roots. It reads the same stored observations, blocks network access and then refuses every provider lookup to prove cache reuse.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/widb tests/arbfree
```

The existing CI command runs these alongside all other offline source/processing tests on Python 3.12–3.14. See [the pipeline and configurations](market-data.md).

## Commit hook

The tracked `.githooks/pre-commit` runs the full offline suite against the working tree, using the active environment's `python`. It creates and removes its own scratch directory beneath `${TMPDIR:-/tmp}/quant_data/`; it never downloads fixtures or installs dependencies.

```sh
git config core.hooksPath .githooks
git hook run pre-commit
```

Activate the environment containing `.[test]` first, or select its interpreter explicitly:

```sh
QUANTDATA_TEST_PYTHON=/path/to/environment/bin/python git hook run pre-commit
```

The hook is configured locally for this checkout; other clones can opt in with the command above. It does not replace the Python-version CI matrix. To disable this checkout's hook configuration, use `git config --unset core.hooksPath`.

The tracked `post-checkout`, `post-commit`, `post-merge` and `pre-push` hooks run Git LFS for the public benchmark files. After selecting `.githooks`, run `git lfs install --local` to configure the checkout. If you later unset `core.hooksPath`, run that command again to install the LFS hooks in the default location. Automated regeneration sets `QUANTDATA_TEST_PYTHON` to its explicit project interpreter when committing.
