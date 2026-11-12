"""Cboe client for official end-of-day VIX history.

The Cboe history file is public; no credentials are required.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from openqdata import version
from openqdata.vixdata import cboe


@version("0.1")
class CboeClient:
    """Cboe connectivity: cached official daily VIX observations.

    Standard usage::

        from openqdata.vixdata import CboeClient
        vix = CboeClient().load_vix("2024-01-02", "2024-03-28")
    """

    locations = cboe._locations
    """ :class:`openqdata.Locations` for Cboe VIX data. """

    URL = cboe.CBOE_VIX_HISTORY_URL  #: Source of the official VIX history.

    def refresh_vix(self, *, timeout_seconds: float = 30.0) -> pl.DataFrame:
        """Download the full history and replace the raw cache; refused in test mode."""
        return cboe.refresh_cboe_vix(timeout_seconds=timeout_seconds)

    def load_vix(self, start: date | str | None = None, end: date | str | None = None, *,
                 refresh: bool = False) -> pl.DataFrame:
        """Cached daily VIX OHLC in volatility points; see :func:`openqdata.vixdata.cboe.load_cboe_vix`."""
        return cboe.load_cboe_vix(start, end, refresh=refresh)


if __name__ == "__main__":
    from openqdata.cli import run_module

    run_module(globals())
