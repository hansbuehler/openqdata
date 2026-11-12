# Style guide

## Scope and priorities

- This repository is a Python 3.12+ quantitative-data and numerical-research codebase for academic research. It is not a trading system.
- Preserve existing user work and notebook workflows. Do not rewrite unrelated code while making a focused change.
- Treat correctness of measures, densities, sample normalization, array shapes and timing conventions as higher priority than cosmetic cleanup.

## System and Environment

- Support Linux and Windows development environments.
- Install this checkout with ``pip install -e '.[test]'``; package source is in ``src/openqdata``.
- ``cdxcore`` is a dependency declared in ``pyproject.toml``.


## Python style

- Use Python 3.12 syntax and built-in generics: `list[int]`, `dict[str, np.ndarray]`, `X | None`.
- Add type annotations to public functions, configuration fields, and non-obvious return values.
- Use `from __future__ import annotations` in new standalone modules when forward references are useful.
- Use Ruff leniently on changed files. At minimum, check import sorting with `ruff check --select I`; do not introduce broad lint cleanup into a focused change. Do not impose a 100-character target line length.
- Align equal signs across lines where reasonable.
- Add comments before non-obvious blocks where they explain intent, statistical meaning, financial timing, or a numerical safeguard. Do not comment code whose purpose is already clear.
- Follow the modern style in `openqdata/` and `tests/`: four-space indentation, compact but readable expressions, and descriptive snake_case names.
- Do not mechanically reformat existing modules as part of an unrelated change. Match the local style where a narrow edit is safer.
- Do not import from random packages. E.g. if ``numpy/np`` is missing import from ``numpy`` not elsewhere. Flag if an import is unknown.
- Prefer explicit keyword-only arguments for configuration-heavy APIs. Use positional parameters only sparingly (e.g. where the parameter is natural from the context).
  Validate data types of parameters using ``verify_inp``.

### Filenames and Unique Labels

- For any string which needs to be a filename validate using ``is_filename`` from ``cdxcore.util``.
- For any string which is unique, but may contain characters which do not allow for a filename, and needs to be converted to a unique filename, use ``label_unique_filename48_8``
  from ``cdxcore.uniquehash``.
- To generate a filename from some ``config`` and a ``label``, use ``named_unique_filename48_8(label, config)`` from ``cdxcore.uniquehash``. However, make sure ``config`` does not
  contain large objects such as dataframes or numpy arrays. For those use the generating config as input.

## Validation and invariants

- Internal consistency - issues which are not caused by user inputs:
  - Use ``assert`` for debug-only internal invariants. Assertions may be disabled with `python -O`; use ``verify`` or an explicit exception for correctness-critical runtime validation. 
  - Assert internal array shapes near the operation that establishes them. Include expected and actual shapes in the message.
  - Assert generously as long as it does not affect code performance. For example, do not re-sort if an array or datadframe is already expected to be sorted by test
    whether it is sorted (much faster). 
- Validate user/configuration inputs in `__post_init__` with `verify_inp(...)` defined in ``cdxcore.err`` and clear messages that include the invalid value. Wrap the error message
  into a zero parameter ``lambda`` (``verify_inp`` throws ``ValueError``).
- Use `verify(...)` defined in ``cdxcore.err`` or explicit exceptions for runtime/data validation (``verify`` throws ``RuntimeError``),
- Check finiteness and sign constraints for probabilities, densities, prices and other numerically sensitive outputs, in particular before passing them to a solver and
  when retrieving results.
- Normalize probability/density objects explicitly and verify their normalization.
- Guard divisions, logarithms, variances, and square roots with an appropriate floor or clamp if a violation is possible due to the context. If such violation
  should not be possible (e.g. $u'>0$) then assert/verify instead. Preserve the configured dtype.
- Do not silently change statistical conventions. State whether a standard deviation is population or sample based and whether an error uses paths, time steps, or both.

## Configuration

- Parameters of a function/method call often split into two
  * *Scope* parameters which define *what* the function operates on e.g. "ticker", "date", "date range" etc. Usually these are very few. Those are the parameters
    which will usually explicitly show up in data file names or directories, while configs will be shown as the beginning of their ``str(config)`` followed
    by a hash computed using ``named_unique_filename48_8`` from ``cdxcore.uniquehash``.
  * *Config* parameters which define *how* the functions operates e.g. "num_bins", "num_steps" etc.
  * *Processing* parameters are used by the function but which do not affects its numerical outcome e.g. "num_workers", "debug", etc

- Use dataclasses for Configs, usually `@dataclass(frozen=True, kw_only=True)`.
  - Configurations should be universal e.g. exclude *Scope* arguments.
  - With *Scope* and *Config* the returned value of a function should be uniquely defined up to numerical precision.
  - Provide tight ``__str__`` implementations because the standard caching file name is computed using
    ``named_unique_filename48_8(str(config),config)`` using
     ``named_unique_filename48_8`` from ``cdxcore.uniquehash``.

    This function
    - Does not hash members starting with ``_``. Therefore use such protected members for minute numerical parameters (eps) and debugging flags.
    - Hashing large dataframes or NumPy arrays is not sensible. Avoid putting large data objects into configuration dataclasses. Instead, key data with their generating config.
  - Add a ``@version`` decorator with ``from cdxcore.version import version``. Use the ``dependencies=`` keyword to sepcify any
    functions or other configs this config depends on. Examples are all over the code.

## Caching

- Use  ``cdxcore.SubDir.cache`` to transparently cache function results in the data pipeline. Examples are all over the code base.
- Use the ``fmt`` parameter to define the output type to avoid using pickle where not appropriate. Use ``SubDir.POLARS_PARQUET``, ``SubDir.PANDAS_PARQUET``
  or ``SubDir.PYTREE_HDF5`` where suitable. The latter is restricted to pretty native python and numpy.
- Use the ``uid=`` parameter to define a function which computes a unique filename from the function parameters. Do not include parameters which do not
  alter the logical function outcome such as ``num_workers`` or ``Context`` or ``debug``.
  ```python
  from cdxcore.subdir import SubDir
  from cdxcore.uniquehash import named_unique_filename48_8

  _cache = SubDir("~/.cache/", fmt=SubDir.PYTREE_HDF5)

  @_cache.cache(
      "0.1",
      dependencies=[Config],
      uid=lambda ticker, config, num_workers: (
          f"{ticker}/{named_unique_filename48_8(str(config), config)}"
      ),
  )
  def function(ticker: str, config: Config, num_workers: int) -> dict[str, np.ndarray]:
      ...
  ```

## Numerical conventions

- Treat sample axes explicitly. Use names such as `S`, `TAU`, `T`, and `N` consistently with their established meanings, and document reductions over them.
  Validate shapes using ``assert``.
- Preserve reproducibility: use explicit random generators (avoid the global ``numpy.random`` state) and seed them deliberately.
- When changing objective semantics, density construction or cached-output interpretation, bump the relevant `@version(...)` dependency so incompatible caches are recomputed rather than loaded silently.

## Data and financial conventions

- Avoid look-ahead bias. Make the timing and adjustment basis of prices, strikes, reference spots, quotes, trades, and filters explicit.
- Preserve schema and dtype declarations for Polars/dataframe outputs.
- Prefer vectorized NumPy, Polars or JAX operations over Python loops for large data.
- Keep units visible in names or documentation, for example `_k`, `_m`, business days, annualized values, or normalized prices.
- Cache expensive external-data and preprocessing operations through the existing `SubDir`/`cdxcore` mechanisms. Include all result-affecting inputs and versioned dependencies in cache identities; exclude only operational arguments such as verbosity and pools.

## Testing and verification

- Use `pytest`; tests live under `tests/` and should be named `test_*.py` with `test_*` functions.
- Add focused regression tests for bug fixes and mathematical tests for changed formulas. Use small deterministic arrays and `pytest.approx`, `numpy.testing`, or exact shape checks as appropriate.
- Test edge cases relevant to numerical code: zero variance, one observation, empty inputs, non-finite inputs, dtype behavior, and cache compatibility.
- Run the narrowest relevant test first, then the containing test module, followed by broader tests when risk warrants it.
- Minimum verification for a modified Python module is a syntax compilation check. Typical commands are:

  ```bash
  python -m py_compile path/to/module.py
  pytest -q tests/test_relevant_module.py
  ruff check --select I path/to/module.py tests/test_relevant_module.py
  ```

- Do not claim notebook-level behavior is verified unless the relevant notebook or an equivalent scripted path was actually executed.

## Documentation and comments

- Public data-access APIs and reusable modules should have useful docstrings; NumPy-style parameter/return sections are preferred for substantial APIs.
- Comments should explain financial timing, statistical meaning, numerical safeguards, or non-obvious design decisions—not restate syntax.
- Keep formulas close to their implementation and name the measure and reduction axes.
- Correct stale comments whenever behavior changes.

## Change discipline

- Keep changes narrow and review the complete diff before handing off.
- Preserve public names and cache/data compatibility unless the task requires a breaking change.
- Do not edit generated notebook output, numbered backups, cached artifacts, or archived implementations as a substitute for changing the canonical source.
- Report which checks ran, and identify any verification that could not be performed.
