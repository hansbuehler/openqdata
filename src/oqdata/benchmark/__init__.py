"""Shared namespace for separately installed oqdata benchmark packages."""
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
