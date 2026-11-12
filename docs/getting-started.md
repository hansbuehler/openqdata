# Getting started

## Installation

```sh
python -m pip install openqdata            # release
python -m pip install 'openqdata[jax]'     # optional JAX backend for the SANOS fitter
```

To develop from a clone:

```sh
git clone https://github.com/hansbuehler/openqdata.git
cd openqdata
python -m pip install -e '.[test]'
```

## Storage locations

openqdata stores data in two locations, and you must configure them before importing `openqdata`:

- **`raw`** holds provider observations exactly as downloaded.
- **`processed`** holds derived, reusable data products.

There are no separate locations for training, experiments or temporary files. Massive's optional session cache lives inside `processed`.

Environment variables take precedence over a TOML file. `OQ_DATA_CONFIG` names a config file that must exist. Without it, the first file found is used: `./openqdata.toml`, `$XDG_CONFIG_HOME/openqdata/config.toml` (where `XDG_CONFIG_HOME` defaults to `~/.config`), then `~/.openqdata.toml`. Relative paths in a TOML file resolve against that file's directory. See `openqdata.example.toml`.

```toml
[data]
root = "/data/openqdata"
# Optional individual overrides:
# raw = "/data/openqdata/raw"
# processed = "/data/openqdata/processed"
cache_mode = "on"
```

| Variable | Meaning |
|---|---|
| `OQ_DATA_ROOT` | Root of both locations. Defaults to `~/.local/share/openqdata`. |
| `OQ_DATA_RAW`, `OQ_DATA_PROCESSED` | Override the individual locations. |
| `OQ_DATA_CACHE_MODE` | Default cache mode; see [caching](caching.md). |
| `OQ_DATA_TEST_MODE`, `OQ_DATA_TEST_ROOT` | Offline fixture mode; see [caching](caching.md#test-mode). |

```python
from openqdata import env
print(env.locations.raw.path, env.locations.processed.path)
```

Settings are read once, when `openqdata` is first imported. Restart the interpreter after changing them.

## Provider credentials

Credentials keep their providers' own names. Never commit them.

| Source | Client | Credentials | Provider setup |
|---|---|---|---|
| WIDB (WRDS OptionMetrics IvyDB) | `WIDBClient` | `WRDS_USERNAME` and a libpq `.pgpass` file (or `PGPASSFILE`) | [WIDB](connectors/widb.md#access) |
| Massive | `MassiveClient` | `MASSIVE_TOKEN` | [Massive](connectors/massive.md#access) |
| Yahoo Finance | `YFClient` | none | |
| FRED | `FREDClient` | `FRED_API_KEY` | [FRED API keys](https://fred.stlouisfed.org/docs/api/api_key.html) |
| Cboe VIX | `CboeClient` | none | |
