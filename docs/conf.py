"""Minimal Sphinx/MyST documentation scaffold."""
import tomllib
from pathlib import Path

metadata = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())["project"]
project = metadata["name"]
release = metadata["version"]
extensions = ["myst_parser", "sphinx.ext.autodoc"]
source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "alabaster"
