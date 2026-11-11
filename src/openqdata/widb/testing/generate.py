"""
Generate WIDB test data
"""

import os

from cdxcore.verbose import Context

from openqdata import env  # triggers construction of caches.
from openqdata.widb.testing.scope import DATES, TICKERS


def generate_day(ticker, d):
    from openqdata.widb.arbfree import MkArbFree, mk_arb_free_day
    from openqdata.widb.day import (
        ExpiryFilter,
        RawDayFilter,
        collect_raw_day,
        enrich_day,
    )

    raw_day_filter = RawDayFilter()
    expiry_filter = ExpiryFilter()
    mk_arb_free = MkArbFree()
    verbose = Context.all

    raw_day = collect_raw_day(ticker, d, raw_day_filter=raw_day_filter, verbose=verbose, raise_if_bad_day=False)
    print(raw_day)

    enr_day = enrich_day(ticker, d, raw_day_filter=raw_day_filter, expiry_filter=expiry_filter, verbose=verbose, raise_if_bad_day=False)
    print(enr_day)

    af_day = mk_arb_free_day(ticker, d, mk_arb_free=mk_arb_free, raw_day_filter=raw_day_filter, expiry_filter=expiry_filter, verbose=verbose, raise_if_bad_day=False)
    print(af_day)

def main():
    env.require_live("fixture generation")

    for ticker in TICKERS:
        for d in DATES:
            print(f"Generating data for {ticker} {d}")
            generate_day(ticker, d)


if __name__ == "__main__":
    main()