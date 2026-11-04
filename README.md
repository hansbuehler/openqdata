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

The [WIDB market-data pipeline](docs/market-data.md) documents the default cleaning before linear fitting separately from eligible-option selection and the 1,000-row cap, with configuration references and executable Python examples.

See [SANOS fitting results](SANOS.md) for historical SPX bid/ask coverage, conditional fit errors, option counts and runtime comparisons.

The [WIDB benchmark pipeline](src/quantdata/benchmark_data/widb/PUB_PIPELINE.md) documents extraction of versioned benchmark data from completed licensed source fits.

Public benchmark Parquet files use Git LFS. With Git LFS installed, fetch them using:

```sh
git lfs install --local
git lfs pull
```

For a source-only checkout, prefix the clone command with `GIT_LFS_SKIP_SMUDGE=1`; benchmark files can be fetched later.
