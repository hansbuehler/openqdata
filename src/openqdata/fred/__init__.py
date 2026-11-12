"""
openqdata.fred

FRED (Federal Reserve Economic Data) rates.
"""

from openqdata.fred.client import FREDClient
from openqdata.fred.rates import load_fred_rates

__all__ = ["FREDClient", "load_fred_rates"]
