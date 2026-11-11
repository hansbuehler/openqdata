"""Shared namespace for separately installed openqdata benchmark packages."""
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
