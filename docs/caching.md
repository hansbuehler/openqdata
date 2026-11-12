# Caching, test mode and commands

## Caching

Cached functions in openqdata use `cdxcore`'s `SubDir.cache`. Each cache entry is identified by two kinds of arguments:

- **Scope** arguments say *what* is computed, for example the ticker and the date. They appear directly in the file path.
- **Configuration** arguments say *how* it is computed. They are frozen dataclasses such as `RawDayFilter`, `ExpiryFilter`, `MkArbFree` or `OptionsFilter`, and they enter the path as a short label plus a hash.

Operational arguments, such as worker pools, verbosity and timeouts, do not affect the key.

Every cached function and configuration also carries a `@version`. Changing that version, or the version of anything it declares as a dependency, makes the existing entries stale. They are then recomputed instead of being loaded silently.

Pass `override_cache_mode=...` to a cached function, or set `cache_mode`/`OQ_DATA_CACHE_MODE` globally:

| Mode | Behaviour |
|---|---|
| `on` | Read a compatible entry, or compute and write it (the default). |
| `off` | Compute without reading or writing. |
| `update` | Compute and overwrite. |
| `readonly` | Read if present; compute without writing otherwise. |
| `cacheonly` | Read only. Raise on a missing or incompatible entry; never download or compute. |
| `gen`, `clear` | Advanced `cdxcore` modes; see its documentation. |

A cached function identifies its inputs by scope and configuration, not by the content of a frame you pass in. If you pass an edited frame, use `override_cache_mode="off"` so that an existing entry cannot override your edits.

## Test mode

Set `OQ_DATA_TEST_MODE=1` to read only from existing fixture caches:

- Every cached call runs in `cacheonly` mode.
- Every provider entry point (`require_live`) refuses to run.
- `OQ_DATA_TEST_ROOT` must point to a directory that contains `raw/` and `processed/`.

The offline test suite uses this mode. Generating fixtures is always a separate, explicit live operation with an external data root.

## Commands

Processing modules and client modules can be run from the command line:

```sh
python -m openqdata.fred.rates --help
python -m openqdata.widb.day --help
python -m openqdata.massive.client --help
```

Public functions take keyword arguments as JSON through `--params`. Client methods are invoked as `Client.method`, with optional constructor arguments in `--init-params`. Credential helpers are never exposed. Dates are ISO strings.

```sh
python -m openqdata.fred.rates load_fred_rates \
    --params '{"start":"2022-01-01","end":"2022-02-01"}' \
    --output /data/openqdata/runs/example/rates.parquet
```

Outside test mode, this can download data. `--output` must be outside the Git working tree. Some modules, such as `openqdata.widb.day` and `openqdata.widb.arbfree`, have their own batch commands. Configuration dataclasses and numerical classes are Python APIs only.
