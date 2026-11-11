# oqdata

A standardized data access and processing pipeline for academic research. Targets Python 3.13 and supports Python 3.12–3.14. The distribution and import namespace are both `oqdata`.

```sh
git clone https://github.com/hansbuehler/oqdata.git
cd oqdata
python -m pip install -e '.[test]'
export OQ_DATA_ROOT="$HOME/.local/share/oqdata"
```

Install from this repository until the first `oqdata` release is published on PyPI. The project was renamed from `quantdata` to avoid that existing PyPI package; update imports to `oqdata`. See the [migration notes](docs/migration.md) for existing caches and separate extensions.

The code is licensed under [PolyForm Noncommercial 1.0.0](LICENSE), with the attribution in [NOTICE](NOTICE). Dependency and provider-data licenses remain separate; this software license grants no rights to redistribute licensed observations or derived datasets. Previously distributed Apache-2.0 copies retain their original license.

```python
from oqdata import env
from oqdata.fred import load_fred_rates
from oqdata.yahoo import YFClient
from oqdata.widb import WIDBClient
from oqdata.massive import MassiveClient
from oqdata.arbfree.arbfree import MkArbFree
```

Sources: `fred`, `yahoo`, `widb`, `vixdata`, `massive`, `tickers`; numerical surface tools: `arbfree`.

See [configuration](docs/configuration.md), [commands](docs/commands.md), [testing](docs/testing.md) and [Massive API coverage and trade defaults](docs/massive.md). [Live validation](docs/live-validation.md) documents the authorized download checks.

The [WIDB market-data pipeline](docs/market-data.md) documents the default cleaning before linear fitting separately from eligible-option selection and the 1,000-row cap, with configuration references and executable Python examples.

See [SANOS fitting results](SANOS.md) for historical SPX bid/ask coverage, conditional fit errors, option counts and runtime comparisons.

The package provides the shared `oqdata.benchmark` namespace for separately installed benchmark extensions; see [its README](src/oqdata/benchmark/README.md).

Independently installed model packages use the shared `oqdata.models` namespace, for example `oqdata.models.example`, and depend on the core package. See the [model-package layout and installation example](src/oqdata/models/README.md).

This repository contains no licensed observations or benchmark datasets. Offline tests use independent synthetic inputs; examples require users to supply their own provider access. Licensed caches are kept outside Git.
