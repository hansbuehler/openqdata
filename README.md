# quantdata

A standardized data access and processing pipeline for academic research, extracted from `openquantai/quant_data`. Targets Python 3.13 and supports Python 3.12–3.14. The distribution and import namespace are both `quantdata`. Install in an environment separate from the original quantdata checkout.

```sh
git clone https://github.com/hansbuehler/quantdata.git
cd quantdata
python -m pip install -e '.[test]'
export OQ_DATA_ROOT="$HOME/.local/share/quantdata"
```

The code is licensed under [PolyForm Noncommercial 1.0.0](LICENSE), with the attribution in [NOTICE](NOTICE). Dependency and provider-data licenses remain separate; this software license grants no rights to redistribute licensed observations or derived datasets. Previously distributed Apache-2.0 copies retain their original license.

For an existing installation under the former distribution name, uninstall `qdata` before installing `quantdata`.

```python
from quantdata import env
from quantdata.fred import load_fred_rates
from quantdata.yahoo import YFClient
from quantdata.widb import WIDBClient
from quantdata.massive import MassiveClient
from quantdata.arbfree.arbfree import MkArbFree
```

Sources: `fred`, `yahoo`, `widb`, `vixdata`, `massive`, `tickers`; numerical surface tools: `arbfree` (formerly `sanos`).

See [configuration](docs/configuration.md), [commands](docs/commands.md), [testing](docs/testing.md), [Massive API coverage and trade defaults](docs/massive.md) and [consolidation review](docs/review.md). Initial consolidation used offline tests. Subsequent [live validation](docs/live-validation.md) and [reference-model comparisons](docs/reference-validation.md) document the authorized download and solver checks.

The [WIDB market-data pipeline](docs/market-data.md) documents the default cleaning before linear fitting separately from eligible-option selection and the 1,000-row cap, with configuration references and executable Python examples.

See [SANOS fitting results](SANOS.md) for historical SPX bid/ask coverage, conditional fit errors, option counts and runtime comparisons.

The core package provides the shared `quantdata.benchmark` namespace for optional benchmark extensions. The [WIDB benchmark package](https://github.com/hansbuehler/quantdata_benchmark_widb) supplies `import quantdata.benchmark.widb`, extraction code and restricted datasets. Its redistribution status is unconfirmed, so it remains in a separate private repository.

This repository contains no licensed observations or benchmark datasets. Offline tests use independent synthetic inputs; examples require users to supply their own provider access. Existing licensed caches remain external and retain their configuration IDs and fitting versions.

See [repository migration](docs/migration.md) for the split and cache-compatibility checks.
