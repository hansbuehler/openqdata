"""Standalone quantitative data access; the quantdata namespace is retained."""
from pkgutil import extend_path

from cdxcore.pretty import PrettyObject
from cdxcore.subdir import CacheController, CacheMode, SubDir, version
from cdxcore.verbose import Context

from quantdata.env import Environment, Locations, env

__version__ = "0.1.0"

# Discover optional quantdata extension packages in separate installations.
__path__ = extend_path(__path__, __name__)
