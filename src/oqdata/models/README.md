# oqdata.models

Shared namespace for independently installed model packages that depend on oqdata. The core package owns this namespace; each model distribution supplies its own `oqdata.models.<name>` package.

For example, a separate model repository can use this source layout:

```text
pyproject.toml
src/oqdata/models/example/__init__.py
```

Leave `oqdata/__init__.py` and `oqdata/models/__init__.py` to the core package. Package only the model's own subtree:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "oqdata-model-example"
version = "0.1.0"
requires-python = ">=3.12,<3.15"
dependencies = ["oqdata @ git+https://github.com/hansbuehler/oqdata.git@main"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["oqdata.models.example*"]
```

Pin the oqdata dependency to a compatible commit for reproducible installations. Use the repository dependency until oqdata is published on PyPI.

After installing both distributions into the same environment:

```python
import oqdata
import oqdata.models
import oqdata.models.example
```

Multiple model distributions can coexist under this namespace. Each model owns its dependencies and public API and is imported explicitly by the caller.
