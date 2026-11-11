# Configuration

Only `raw` and `processed` storage locations are required. Configure before importing `openqdata`.

Environment variables take precedence over TOML. `OQ_DATA_CONFIG` selects a required config file; otherwise the first existing file wins: `./openqdata.toml`, `./qdata.toml`, `$XDG_CONFIG_HOME/openqdata/config.toml`, `$XDG_CONFIG_HOME/qdata/config.toml`, `~/.openqdata.toml`, then `~/.qdata.toml`. `XDG_CONFIG_HOME` defaults to `~/.config`. The legacy paths remain supported. See `openqdata.example.toml`; relative TOML paths resolve against the configuration file directory. The default data root remains `~/.local/share/qdata` so existing caches stay accessible; use `OQ_DATA_ROOT` or TOML to select another root.

```toml
[data]
root = "/data/openqdata"
# Optional individual overrides:
# raw = "/data/openqdata/raw"
# processed = "/data/openqdata/processed"
cache_mode = "on"
```

Equivalent variables: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, `OQ_DATA_PROCESSED`, `OQ_DATA_CACHE_MODE`. Legacy `QUANTDATA_*` settings are not read. Existing data-access APIs use `env.locations.processed` in place of `processing`; there are no training, experiments or temp locations. Massive's optional session cache is a subtree of processed data.

Provider credentials retain provider names: `FRED_API_KEY`, `MASSIVE_TOKEN`, and WRDS client authentication. Never commit credentials.

`OQ_DATA_TEST_MODE=1` selects read-only cache lookup and refuses network entry paths. `OQ_DATA_TEST_ROOT` points to existing `raw/` and `processed/` fixture directories. Fixture generation is a separate explicit live operation using an external data root; `generate_tests` is no longer an implicit environment mode.

## Python 3.14 and WRDS

The vendor WRDS SDK pins a Pandas release that is incompatible with Python 3.14. On 3.14 the same WIDBClient uses a small SQLAlchemy/PostgreSQL transport, retaining raw_sql, list_libraries and list_tables. Authentication uses the standard libpq `.pgpass` file or `PGPASSFILE`; create that file outside this repository. `WRDS_USERNAME` is still the username setting. The transport uses TLS and the standard WRDS endpoint; `PGHOST`, `PGPORT`, `PGDATABASE` can override it. It does not provide the SDK's interactive password-setup wizard. Live authentication has not been exercised during consolidation.


Existing storage is reused without moving or regenerating it. When no new configuration exists, the corresponding `oqdata` configuration paths are also recognized. If the new default data directory does not exist, an existing `~/.local/share/oqdata` or `~/.local/share/qdata` is reused, in that order. `OQ_DATA_*` variables, cache IDs and numerical pipeline versions are unchanged by the package rename. Historical manifests retain their recorded paths and provenance.
