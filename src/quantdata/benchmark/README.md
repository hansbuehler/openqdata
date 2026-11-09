# quantdata.benchmark

Shared namespace for separately installed benchmark packages. The core package owns this namespace and discovers extensions on the Python package path.

A benchmark distribution packages `quantdata/benchmark/<source>/` and leaves the parent namespace's `__init__.py` to the core package. Once installed, it is imported as `quantdata.benchmark.<source>`. No benchmark extension or dataset is included in this repository.
