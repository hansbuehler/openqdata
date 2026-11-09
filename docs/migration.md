# Repository split

`hansbuehler/quantdata` contains provider access, filtering, DLV/SANOS calibration and licensed-cache generation. It contains synthetic test inputs and output-cleared notebook sources, and owns the shared `quantdata.benchmark` namespace. WIDB benchmark data and extraction are in the separate private `hansbuehler/quantdata_benchmark_widb` repository, which depends on quantdata and supplies `quantdata.benchmark.widb`. Other benchmark distributions can share the parent namespace.

The existing local core checkout remains `~/python/qdata`. Imports, OQ_DATA configuration, source-cache keys and fitting dependency versions are preserved. Existing licensed observations, calibrated DLVs, SANOS densities and other production caches remain external. No licensed data were downloaded, calibrated or re-extracted during migration. All 126 existing benchmark Parquet files were checked against their recorded SHA-256 hashes; all six benchmark configuration IDs remain unchanged.

Source history was retained after removing benchmark datasets, original provider fixtures and notebook output history. Commit hashes therefore changed. Existing clones must switch deliberately to the rewritten history or use a fresh clone; merging the old history back would restore the removed data. The previous Git metadata and original fixtures are archived outside the public working tree.

The core repository remains private during preparation. The owner will make it public after review. The benchmark repository stays private until redistribution permission is established. Its Python wheel contains code and documentation only; dataset files require an explicit Git LFS checkout. Earlier extract metadata may say “public”; those labels do not establish distribution rights.

The code now uses PolyForm Noncommercial 1.0.0 and the attribution in NOTICE. Dependency and provider-data licenses remain separate. Previously distributed Apache-2.0 versions retain their earlier terms.
