"""Official Cboe VIX end-of-day data management."""

from oqdata.vixdata.cboe import load_cboe_vix, refresh_cboe_vix

__all__ = ["load_cboe_vix", "refresh_cboe_vix"]
