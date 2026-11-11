"""Official Cboe VIX end-of-day data management."""

from openqdata.vixdata.cboe import load_cboe_vix, refresh_cboe_vix

__all__ = ["load_cboe_vix", "refresh_cboe_vix"]
