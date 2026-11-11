"""Minimal Sphinx/MyST documentation scaffold."""
project = "oqdata"
release = "0.1.0"
extensions = ["myst_parser", "sphinx.ext.autodoc"]
source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "alabaster"
