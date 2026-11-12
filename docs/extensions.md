# Extension packages

openqdata owns two namespaces that separately installed packages can extend:

| Namespace | Purpose | Layout |
|---|---|---|
| `openqdata.models` | Model packages built on openqdata data, for example `openqdata.models.example` | `src/openqdata/models/<name>/` |
| `openqdata.benchmark` | Benchmark dataset packages, for example `openqdata.benchmark.<source>` | `src/openqdata/benchmark/<source>/` |

An extension contains only its own subtree. It must not ship `openqdata/__init__.py`, `openqdata/models/__init__.py` or `openqdata/benchmark/__init__.py`; those belong to the core package. No extension and no dataset is included in this repository.

A minimal `pyproject.toml` for a model package:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "openqdata-model-example"
version = "0.1.0"
requires-python = ">=3.12,<3.15"
dependencies = ["openqdata>=0.2"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["openqdata.models.example*"]
```

After you install both distributions into one environment, import the extension explicitly:

```python
import openqdata.models.example
```

Several extensions can be installed side by side. Each one owns its own dependencies and public API.
