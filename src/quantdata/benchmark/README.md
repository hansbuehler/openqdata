# quantdata.benchmark

Shared namespace for separately installed benchmark packages. The core package owns this namespace and discovers extensions on the Python package path.

The WIDB extension is installed from [quantdata_benchmark_widb](https://github.com/hansbuehler/quantdata_benchmark_widb):

```python
import quantdata.benchmark.widb
from quantdata.benchmark.widb.pipeline import BenchmarkConfig, write_benchmark
```

Additional benchmark distributions should package `quantdata/benchmark/<source>/` and leave the parent namespace's `__init__.py` to the core package. WIDB dataset redistribution permission remains unconfirmed; that extension repository stays private.
