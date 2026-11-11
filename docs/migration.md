# Migrating to openqdata

The distribution and Python namespace are now `openqdata` (version 0.2.0). The core repository is `hansbuehler/openqdata`; the restricted WIDB extension is `hansbuehler/openqdata_benchmark_widb`, installed as `openqdata-benchmark-widb`.

Update imports and command lines:

```python
import openqdata
import openqdata.models
import openqdata.benchmark.widb  # requires the separately installed WIDB extension
from openqdata.arbfree.arbfree import ArbFreePricer, MkArbFree
```

Model extensions supply `src/openqdata/models/<name>/`; benchmark extensions supply `src/openqdata/benchmark/<source>/`. Each depends on `openqdata` and leaves the parent namespace modules to the core distribution. There is no compatibility package under `quantdata`, which belongs to an unrelated PyPI project. Update downstream projects' dependencies and imports before switching their environment.

## Existing licensed data and calibrated models

Keep `OQ_DATA_ROOT`, `OQ_DATA_RAW`, `OQ_DATA_PROCESSED` and `OQ_DATA_CONFIG` pointed at the same locations. Their names have not changed. Existing `qdata.toml`, `~/.config/qdata/config.toml` and `~/.qdata.toml` files remain discoverable; the equivalent `openqdata` names are also supported. The default root remains `~/.local/share/qdata`. No data directory is renamed automatically, including the host's `/home/hans/quantdata_data` archive.

The package rename preserves configuration hashes, cache IDs and numerical pipeline versions. Existing licensed caches, Parquet rows and serialized `ArbFreePricer.to_dict()` states remain valid and require no download or recalibration. Load saved model dictionaries with `openqdata.arbfree.arbfree.ArbFreePricer.from_dict` as shown in [SANOS.md](../SANOS.md). Historical archive paths in that document remain literal paths to the existing data.

The six WIDB benchmark datasets and their configuration/provenance files remain byte-for-byte unchanged in the restricted extension repository. Their embedded `quantdata` names describe their original generation. New benchmark exports use `openqdata.benchmark.*` Parquet metadata keys and advance only `write_benchmark` to version 0.4; source-cache lookup, extraction values and configuration IDs are unchanged.

Package renaming does not publish a PyPI release. Install from the repositories until the first release is published. The pre-commit interpreter override is now `OPENQDATA_TEST_PYTHON`.
