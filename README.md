# openqdata

Data connectors and processing pipelines with simple, versioned caching, for academic research in quantitative finance. openqdata is not a trading system and provides no investment advice.

The package has four parts:

1. **Caching and configuration.** Every result is cached under two storage locations, `raw` and `processed`, keyed by its scope and configuration.
2. **Data connectors.** WRDS OptionMetrics IvyDB (WIDB), Massive, Yahoo Finance, FRED and Cboe VIX. Each source has a `Client` class that holds its authentication and basic access methods.
3. **The WIDB benchmark data.** Cleaned daily option data from WRDS OptionMetrics IvyDB, together with an arbitrage-free interpolation of each day's quotes. The interpolation is a SANOS surface that prices any strike and maturity.
4. **The `arbfree` toolkit.** It fits arbitrage-free option surfaces to bid/ask quotes from any source.

Targets Python 3.13 and supports Python 3.12–3.14.

```sh
python -m pip install openqdata          # or: pip install -e '.[test]' from a clone
export OQ_DATA_ROOT="$HOME/.local/share/openqdata"
```

```python
from openqdata.widb import WIDBClient
from openqdata.massive import MassiveClient
from openqdata.yahoo import YFClient
from openqdata.fred import FREDClient
from openqdata.vixdata import CboeClient
from openqdata.arbfree.arbfree import MkArbFree
```

## Documentation

- [Getting started](https://github.com/hansbuehler/openqdata/blob/main/docs/getting-started.md): installation, storage and credentials
- [Caching, test mode and commands](https://github.com/hansbuehler/openqdata/blob/main/docs/caching.md)
- [Data connectors](https://github.com/hansbuehler/openqdata/blob/main/docs/connectors/index.md)
- [WIDB benchmark data](https://github.com/hansbuehler/openqdata/blob/main/docs/widb-benchmark/pipeline.md), [interpolation quality](https://github.com/hansbuehler/openqdata/blob/main/docs/widb-benchmark/fit-quality.md) and [field reference](https://github.com/hansbuehler/openqdata/blob/main/docs/widb-benchmark/fields.md)
- [The arbfree toolkit](https://github.com/hansbuehler/openqdata/blob/main/docs/arbfree.md)
- [Extension packages](https://github.com/hansbuehler/openqdata/blob/main/docs/extensions.md)
- [Development and testing](https://github.com/hansbuehler/openqdata/blob/main/docs/development.md), [releasing](https://github.com/hansbuehler/openqdata/blob/main/docs/releasing.md) and the [changelog](https://github.com/hansbuehler/openqdata/blob/main/CHANGELOG.md)

## Licensing and data

The code is licensed under [PolyForm Noncommercial 1.0.0](https://github.com/hansbuehler/openqdata/blob/main/LICENSE), with the attribution in [NOTICE](https://github.com/hansbuehler/openqdata/blob/main/NOTICE). Dependency and provider-data licenses are separate. This software license grants no rights to redistribute licensed observations or derived datasets.

This repository contains no licensed observations or datasets. Offline tests use synthetic inputs. To run the examples you need your own access to each provider.
