# quantdata

A standardized data access and processing pipeline for academic research. Targets Python 3.13 and supports Python 3.12–3.14. The distribution and import namespace are both `quantdata`.

```sh
git clone https://github.com/hansbuehler/quantdata.git
cd quantdata
python -m pip install -e '.[test]'
export OQ_DATA_ROOT="$HOME/.local/share/quantdata"
```

Install from this repository. An unrelated package of the same name exists on PyPI; `pip install quantdata` without a source installs that package instead, and both cannot share one environment.

The code is licensed under [PolyForm Noncommercial 1.0.0](LICENSE), with the attribution in [NOTICE](NOTICE). Dependency and provider-data licenses remain separate; this software license grants no rights to redistribute licensed observations or derived datasets. Previously distributed Apache-2.0 copies retain their original license.

```python
from quantdata import env
from quantdata.fred import load_fred_rates
from quantdata.yahoo import YFClient
from quantdata.widb import WIDBClient
from quantdata.massive import MassiveClient
from quantdata.arbfree.arbfree import MkArbFree
```

Sources: `fred`, `yahoo`, `widb`, `vixdata`, `massive`, `tickers`; numerical surface tools: `arbfree`.

See [configuration](docs/configuration.md), [commands](docs/commands.md), [testing](docs/testing.md) and [Massive API coverage and trade defaults](docs/massive.md). [Live validation](docs/live-validation.md) documents the authorized download checks.

The [WIDB market-data pipeline](docs/market-data.md) documents the default cleaning before linear fitting separately from eligible-option selection and the 1,000-row cap, with configuration references and executable Python examples.

See [SANOS fitting results](SANOS.md) for historical SPX bid/ask coverage, conditional fit errors, option counts and runtime comparisons.

The package provides the shared `quantdata.benchmark` namespace for separately installed benchmark extensions; see [its README](src/quantdata/benchmark/README.md).

Independently installed model packages use the shared `quantdata.models` namespace, for example `quantdata.models.example`, and depend on the core package. See the [model-package layout and installation example](src/quantdata/models/README.md).

This repository contains no licensed observations or benchmark datasets. Offline tests use independent synthetic inputs; examples require users to supply their own provider access. Licensed caches are kept outside Git.
