"""Systematic market-data access and processing for academic research."""
from pkgutil import extend_path

from cdxcore.pretty import PrettyObject
from cdxcore.subdir import CacheController, CacheMode, SubDir, version
from cdxcore.verbose import Context

from oqdata.env import Environment, Locations, env

__version__ = "0.2.0"

# Discover optional oqdata extension packages in separate installations.
__path__ = extend_path(__path__, __name__)
