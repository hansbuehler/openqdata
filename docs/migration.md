# Migrating to oqdata

The distribution and Python namespace are now `oqdata` (version 0.2.0). The core repository is `hansbuehler/oqdata`; the restricted WIDB extension is `hansbuehler/oqdata_benchmark_widb`, installed as `oqdata-benchmark-widb`.

Update imports and command lines:

```python
import oqdata
import oqdata.models
import oqdata.benchmark.widb  # requires the separately installed WIDB extension
from oqdata.arbfree.arbfree import ArbFreePricer, MkArbFree
```

Model extensions supply `src/oqdata/models/<name>/`; benchmark extensions supply `src/oqdata/benchmark/<source>/`. Each depends on `oqdata` and leaves the parent namespace modules to the core distribution. There is no compatibility package under `quantdata`, which belongs to an unrelated PyPI project. Update downstream projects' dependencies and imports before switching their environment.

## Existing licensed data and calibrated models

Keep `OQ_DATA_ROOT`, `OQ_DATA_RAW`, `OQ_DATA_PROCESSED` and `OQ_DATA_CONFIG` pointed at the same locations. Their names have not changed. Existing `qdata.toml`, `~/.config/qdata/config.toml` and `~/.qdata.toml` files remain discoverable; the equivalent `oqdata` names are also supported. The default root remains `~/.local/share/qdata`. No data directory is renamed automatically, including the host's `/home/hans/quantdata_data` archive.

The package rename preserves configuration hashes, cache IDs and numerical pipeline versions. Existing licensed caches, Parquet rows and serialized `ArbFreePricer.to_dict()` states remain valid and require no download or recalibration. Load saved model dictionaries with `oqdata.arbfree.arbfree.ArbFreePricer.from_dict` as shown in [SANOS.md](../SANOS.md). Historical archive paths in that document remain literal paths to the existing data.

The six WIDB benchmark datasets and their configuration/provenance files remain byte-for-byte unchanged in the restricted extension repository. Their embedded `quantdata` names describe their original generation. New benchmark exports use `oqdata.benchmark.*` Parquet metadata keys and advance only `write_benchmark` to version 0.4; source-cache lookup, extraction values and configuration IDs are unchanged.

Package renaming does not publish a PyPI release. Install from the repositories until the first release is published. The pre-commit interpreter override is now `OQDATA_TEST_PYTHON`.
