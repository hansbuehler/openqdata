"""Versioned daily SANOS fits to the linearly cleaned, filtered option population."""
from __future__ import annotations

import datetime as dt
from dataclasses import replace

import pandas as pd
from cdxcore.subdir import CacheMode, SubDir
from cdxcore.uniquehash import named_unique_filename48_8
from cdxcore.util import verify_inp
from cdxcore.verbose import Context

from oqdata import env
from oqdata.arbfree.arbfree import MkArbFree
from oqdata.widb.arbfree import mk_arb_free_day
from oqdata.widb.day import SCHEMA_ENRICHED_DAY, ExpiryFilter, RawDayFilter
from oqdata.widb.options_filter import OptionsFilter, filter_options_day

_processing = env.locations("arbfree").processed


@_processing(fmt=SubDir.PANDAS_PARQUET).cache(
    "0.2", dependencies=[mk_arb_free_day, filter_options_day, MkArbFree],
    uid=lambda ticker, d, raw_day_filter, expiry_filter, sanos, options_filter:
        f"fit_sanos_day/{named_unique_filename48_8(f'{raw_day_filter},{expiry_filter},{options_filter}', raw_day_filter, expiry_filter, options_filter)}/"
        f"{named_unique_filename48_8(str(sanos), sanos)}/{ticker}/{d}",
    exclude_args=["verbose", "raise_if_bad_day"],
)
def fit_sanos_day(ticker: str, d: dt.date, sanos: MkArbFree, *,
                  raw_day_filter: RawDayFilter = RawDayFilter(),
                  expiry_filter: ExpiryFilter = ExpiryFilter(),
                  options_filter: OptionsFilter = OptionsFilter(normalize=False),
                  raise_if_bad_day: bool = True,
                  override_cache_mode: CacheMode | None = None,
                  verbose: Context = Context.all) -> pd.DataFrame:
    """Fit after full-book linear cleaning and eligibility selection.

    The output has the standard daily fitted-row schema. Its cache includes the
    selection configuration, separately from full-book mk_arb_free_day entries.
    With cacheonly a missing entry raises before any processing or fitting.
    """
    verify_inp(not options_filter.normalize, lambda: "Filtered SANOS fits require native coordinates")
    linear_config = replace(sanos, smoothness=0.)
    selected = filter_options_day(ticker, d, raw_day_filter=raw_day_filter,
                                  expiry_filter=expiry_filter, mk_arb_free=linear_config,
                                  options_filter=options_filter, raise_if_bad_day=raise_if_bad_day,
                                  override_cache_mode=override_cache_mode, verbose=verbose)
    if selected is None or selected.empty:
        return selected
    # The outer cache keys this fit by its selection; never overwrite a full-book fit.
    return mk_arb_free_day(ticker, d, enriched_data=selected.loc[:, list(SCHEMA_ENRICHED_DAY)], raw_day_filter=raw_day_filter,
                           expiry_filter=expiry_filter, mk_arb_free=sanos,
                           override_cache_mode="off", raise_if_bad_day=raise_if_bad_day, verbose=verbose)


if __name__ == "__main__":
    from oqdata.cli import run_module
    run_module(globals())
