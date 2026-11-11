# openqdata.models

Shared namespace for independently installed model packages that depend on openqdata. The core package owns this namespace; each model distribution supplies its own `openqdata.models.<name>` package.

For example, a separate model repository can use this source layout:

```text
pyproject.toml
src/openqdata/models/example/__init__.py
```

Leave `openqdata/__init__.py` and `openqdata/models/__init__.py` to the core package. Package only the model's own subtree:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "openqdata-model-example"
version = "0.1.0"
requires-python = ">=3.12,<3.15"
dependencies = ["openqdata @ git+https://github.com/hansbuehler/openqdata.git@main"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["openqdata.models.example*"]
```

Pin the openqdata dependency to a compatible commit for reproducible installations. Use the repository dependency until openqdata is published on PyPI.

After installing both distributions into the same environment:

```python
import openqdata
import openqdata.models
import openqdata.models.example
```

Multiple model distributions can coexist under this namespace. Each model owns its dependencies and public API and is imported explicitly by the caller.
