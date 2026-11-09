# Consolidation review

## Scope and provenance

Repository: `git@github.com:hansbuehler/quantdata.git` (formerly `openquantai/qdata`). The existing local checkout remains `~/python/qdata`; new clones use `quantdata`.

Copied the working `quant_data/quantdata` source for `fred`, `yahoo`, `widb`, `vixdata`, `tickers`, and `sanos` (renamed `arbfree`). The source checkout was based on `992ad9d01b42a83ef45f55df190c953bcad8e55c`. Local edits in `widb/arbfree.py` were included. The original source working tree was not edited.

Restored `massive` from `7571da77dfa799368ac41f1b9e4dbaf43f61e87e`, the parent of deletion commit `77a0017`. A temporary historical checkout at `~/python/qd_massive` was created, copied, and removed.

Retained the required `biz_calendar`, `pool`, `utils`, and minimal optional JAX numerical backbone. DYSANOS, GROMM, Torch training infrastructure and experiment locations are excluded. The untracked unfinished `widb/market.py` was excluded: it contains invalid syntax and depends directly on DYSANOS geometry. Its original file remains untouched.

The standard source layout is `src/quantdata/`. The distribution and import namespace are both named `quantdata`. Do not install both this package and the original quantdata distribution in one environment. The package path change is limited to the requested `quantdata.sanos` → `quantdata.arbfree` rename and its internal references.

Inherited notebook examples and legacy `arbfree/old` code are retained as reference material. Notebook execution is not verified. Runtime wheel assets exclude notebooks. The current source uses PolyForm Noncommercial 1.0.0 and the attribution in NOTICE; earlier Apache-2.0 distributions retain their original terms.

## Review findings addressed

- Removed dependencies on omitted research packages and training environments.
- Reduced locations to `raw` and `processed`; updated affected clients and caches. Massive's optional session cache is below processed data.
- Replaced `QUANTDATA_*` configuration with `OQ_DATA_*`, added TOML discovery and validation, and avoided creating storage on environment construction.
- Forced offline test mode, cache-only lookups and network blocking. Missing local fixtures do not trigger provider access. Fixture generation no longer changes the environment implicitly at import.
- Added explicit FRED, Cboe and cached-credential Massive/WIDB access guards; Yahoo prices now validates mode before downloading.
- Corrected Yahoo's missing-column check and DataError context handling, with local processing regressions.
- Replaced version-specific Polars row-hash baselines with schema, validity and alignment checks over retained historical observations. Shared hash helpers use a Pandas encoding rather than removed Polars hash arguments.
- Preserved the CVXPY shape-inference fix at the numerical solver boundary.
- Corrected stale legacy tridiagonal imports and adapted their backbone arguments.
- Removed accidental Torch operations from the optional JAX backend; fixed JAX stop-gradient dispatch. The fitter remains optional.
- Added module CLI adapters and client-method commands, preserving existing specialized CLIs. Complex filter/config dataclasses remain Python APIs.
- Added module READMEs, configuration and command documentation, a Sphinx/MyST scaffold and a 3.12/3.13/3.14 CI matrix.

## Python 3.14 compatibility

The vendor WRDS SDK pins Pandas below 2.3. Building that old Pandas release on Python 3.14 succeeded but crashed on datetime construction during validation. Package metadata therefore retains the vendor SDK on 3.12/3.13 and uses supported Pandas plus the narrow SQLAlchemy/PostgreSQL transport on 3.14. The public WIDBClient data interface is unchanged; direct `connect()` returns the narrow transport on 3.14 rather than the full vendor SDK. See configuration notes for `.pgpass` authentication. The transport was verified with local SQL queries and mocked discovery/routing, not live WRDS authentication.

## Validation and limits

Full offline tests pass on Python 3.12, 3.13 and 3.14: 101 passed on each interpreter. Twelve legacy tests skip because their specific stored provider fixtures are absent. Added synthetic FRED/Yahoo data exercises transformations without a provider connection. Existing numerical surface fixtures and Massive raw observations exercise real processing. Import checks, command help checks, in-memory syntax compilation, import sorting and wheel builds are recorded during the consolidation run.

Initial consolidation used no live provider downloads; subsequent authorized live tests are documented in live-validation.md and reference-validation.md. No model estimates were rerun. Optional JAX CPU array conversion, dtype handling and stopped gradients passed a focused smoke check. Full JAX fitting and inherited notebooks are not claimed as verified. Third-party calendar dependencies emit Pandas/NumPy deprecation warnings. Generated validation environments, build staging, logs and caches are outside the Git checkout under `/tmp/quant_data/qdata_consolidation/`.

The working changes are left local for review; no commit or push has been made. The authorized download and reference tests are documented separately.
