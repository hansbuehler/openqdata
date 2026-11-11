# openqdata

A standardized data access and processing pipeline for academic research. Targets Python 3.13 and supports Python 3.12–3.14. The distribution and import namespace are both `openqdata`.

```sh
git clone https://github.com/hansbuehler/openqdata.git
cd openqdata
python -m pip install -e '.[test]'
export OQ_DATA_ROOT="$HOME/.local/share/openqdata"
```

Install from this repository until the first `openqdata` release is published on PyPI. The project was renamed from `quantdata` to avoid that existing PyPI package; update imports to `openqdata`. See the [migration notes](docs/migration.md) for existing caches and separate extensions.

Maintainers: see [releasing to PyPI](docs/releasing.md) for version tags, package checks and publishing approval.

The code is licensed under [PolyForm Noncommercial 1.0.0](LICENSE), with the attribution in [NOTICE](NOTICE). Dependency and provider-data licenses remain separate; this software license grants no rights to redistribute licensed observations or derived datasets. Previously distributed Apache-2.0 copies retain their original license.

```python
from openqdata import env
from openqdata.fred import load_fred_rates
from openqdata.yahoo import YFClient
from openqdata.widb import WIDBClient
from openqdata.massive import MassiveClient
from openqdata.arbfree.arbfree import MkArbFree
```

Sources: `fred`, `yahoo`, `widb`, `vixdata`, `massive`, `tickers`; numerical surface tools: `arbfree`.

See [configuration](docs/configuration.md), [commands](docs/commands.md), [testing](docs/testing.md) and [Massive API coverage and trade defaults](docs/massive.md). [Live validation](docs/live-validation.md) documents the authorized download checks.

The [WIDB market-data pipeline](docs/market-data.md) documents the default cleaning before linear fitting separately from eligible-option selection and the 1,000-row cap, with configuration references and executable Python examples.

See [SANOS fitting results](SANOS.md) for historical SPX bid/ask coverage, conditional fit errors, option counts and runtime comparisons.

The package provides the shared `openqdata.benchmark` namespace for separately installed benchmark extensions; see [its README](src/openqdata/benchmark/README.md).

Independently installed model packages use the shared `openqdata.models` namespace, for example `openqdata.models.example`, and depend on the core package. See the [model-package layout and installation example](src/openqdata/models/README.md).

This repository contains no licensed observations or benchmark datasets. Offline tests use independent synthetic inputs; examples require users to supply their own provider access. Licensed caches are kept outside Git.
