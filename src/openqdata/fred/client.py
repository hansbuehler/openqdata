"""FRED (Federal Reserve Economic Data) client.

Live access requires the ``FRED_API_KEY`` environment variable;
see https://fred.stlouisfed.org/docs/api/api_key.html.
"""

from __future__ import annotations

import os
from datetime import date

import polars as pl
from cdxcore.err import verify

from openqdata import env, version


@version("0.1")
class FREDClient:
    """FRED connectivity: credentials and cached rate series.

    Standard usage::

        from openqdata.fred import FREDClient
        rates = FREDClient().load_rates("2024-01-02", "2024-03-28")
    """

    locations = env.locations("fred")
    """ :class:`openqdata.Locations` for FRED data. """

    @staticmethod
    def api_key() -> str:
        """Return the FRED API key from ``FRED_API_KEY``; refuse in test mode."""
        env.require_live("FRED")
        key = os.environ.get("FRED_API_KEY")
        verify(
            key is not None,
            "Please set FRED_API_KEY in your environment. See https://fred.stlouisfed.org/docs/api/api_key.html",
            exception=RuntimeError,
        )
        return key

    def fetch_series(self, series_id: str, start: date, end: date) -> pl.DataFrame:
        """Download one FRED series without caching; ``"."`` observations become nulls."""
        from openqdata.fred.rates import _fetch_fred_series
        return _fetch_fred_series(self.api_key(), series_id, start, end)

    def load_rates(self, start: str | date, end: str | date) -> pl.DataFrame:
        """Cached SOFR, EFFR and short Treasury rates; see :func:`openqdata.fred.rates.load_fred_rates`."""
        from openqdata.fred.rates import load_fred_rates
        return load_fred_rates(start, end)


if __name__ == "__main__":
    from openqdata.cli import run_module

    run_module(globals())
