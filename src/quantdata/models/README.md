# quantdata.models

Shared namespace for independently installed model packages that depend on quantdata. The core package owns this namespace; each model distribution supplies its own `quantdata.models.<name>` package.

For example, a separate model repository can use this source layout:

```text
pyproject.toml
src/quantdata/models/example/__init__.py
```

Leave `quantdata/__init__.py` and `quantdata/models/__init__.py` to the core package. Package only the model's own subtree:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "quantdata-model-example"
version = "0.1.0"
requires-python = ">=3.12,<3.15"
dependencies = ["quantdata @ git+https://github.com/hansbuehler/quantdata.git@main"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["quantdata.models.example*"]
```

Pin the quantdata dependency to a compatible commit for reproducible installations. This direct repository dependency selects this quantdata package; the package of the same name on PyPI is unrelated.

After installing both distributions into the same environment:

```python
import quantdata
import quantdata.models
import quantdata.models.example
```

Multiple model distributions can coexist under this namespace. Each model owns its dependencies and public API and is imported explicitly by the caller.
