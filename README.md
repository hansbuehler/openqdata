# quantdata

Standalone data access extracted from `openquantai/quant_data`. Targets Python 3.13 and supports Python 3.12–3.14. The distribution and import namespace are both `quantdata`. Install in an environment separate from the original quantdata checkout.

```sh
git clone git@github.com:openquantai/quantdata.git
cd quantdata
python -m pip install -e '.[test]'
export OQ_DATA_ROOT="$HOME/.local/share/quantdata"
```

For an existing installation under the former distribution name, uninstall `qdata` before installing `quantdata`.

```python
from quantdata import env
from quantdata.fred import load_fred_rates
from quantdata.yahoo import YFClient
from quantdata.widb import WIDBClient
from quantdata.massive import MassiveClient
from quantdata.arbfree.arbfree import MkArbFree
```

Sources: `fred`, `yahoo`, `widb`, `vixdata`, `massive`, `tickers`; numerical surface tools: `arbfree` (formerly `sanos`). No DYSANOS/GROMM experiments are included.

See [configuration](docs/configuration.md), [commands](docs/commands.md), [testing](docs/testing.md), [Massive API coverage and trade defaults](docs/massive.md) and [consolidation review](docs/review.md). Initial consolidation used offline tests. Subsequent [live validation](docs/live-validation.md) and [reference-model comparisons](docs/reference-validation.md) document the authorized download and solver checks.
