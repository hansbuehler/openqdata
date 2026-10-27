# Offline testing

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

The suite forces `OQ_DATA_TEST_MODE=1`, selects `tests/stored_data`, and blocks socket connections. Retained fixtures originate from quant_data tests/stored_data; training sample input is now deliberately retained under processed. No fixture generation or downloads run during tests. The formerly missing FRED, Massive contract and ticker fixtures have been explicitly downloaded and curated; see `tests/stored_data/downloaded-fixtures.json` for provenance. Required fixtures are mandatory: missing files fail tests instead of triggering skips. Small real contract/trade samples exercise processing offline, with contract results checked against the full downloaded reference.

Python compatibility is checked in CI on 3.12, 3.13 (primary) and 3.14. Optional JAX is tested separately from the default data package. Generated test/build output belongs in an external run directory.

Small real endpoint responses in `tests/stored_data/raw/massive/endpoint-responses.json` also cover client conversion, split dates, option-bar cache keys, pagination, and closing-condition filtering. Their provenance identifies the separate live run. Live endpoint coverage is documented in [Massive](massive.md).
