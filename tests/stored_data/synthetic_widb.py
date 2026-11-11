"""Deterministic test markets constructed without reading provider observations.

Dates and ticker labels exercise calendar and cache conventions. Prices, strikes,
identifiers, forwards, rates and activity are invented, not transformed market data.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from scipy.special import ndtr

from oqdata.biz_calendar import count_business_days_between


def call_price(strikes: np.ndarray, tte: float, vol: float = .25) -> np.ndarray:
    """Unit-forward Black–Scholes calls, independently of cdxcore.bs."""
    std = vol * np.sqrt(tte)
    d1 = -np.log(strikes) / std + std / 2
    return ndtr(d1) - strikes * ndtr(d1 - std)


def provider_day(day: date) -> dict:
    """Invent paired quotes and reference inputs in the WIDB provider schema."""
    large = day == date(2025, 1, 3)
    offsets = [21, 42, 63, 84, 126, 189, 252, 378] if large else [42, 126, 252]
    count = 201 if large else 41 if day == date(2005, 11, 21) else 31
    expiries = np.busday_offset(day, offsets, roll="forward").astype('datetime64[D]')
    quotes, forwards = [], []
    for i, expiry in enumerate(expiries):
        is_am = i % 2 == 0
        tte = (count_business_days_between(day, expiry) - .8 * is_am) / 252
        forward = 200. * np.exp(.01 * tte)
        discount = np.exp(-.02 * (expiry - np.datetime64(day)).astype(int) / 365)
        k = np.exp(np.linspace(-2.5, 1.5, count) * .25 * np.sqrt(tte))
        k = np.round(k * forward * 8) / (8 * forward)
        call = discount * forward * call_price(k, tte)
        # A price above the IV ceiling survives raw pairing but fails enrichment.
        call[0] = .999 * discount * forward
        put = call - discount * forward * (1 - k)
        forwards.append(dict(exdate=expiry, am_settlement=int(is_am), forward_price=forward * 1.001))
        for j, strike in enumerate(k * forward):
            for side, prices in (("C", call), ("P", put)):
                quotes.append(dict(
                    symbol=f"SYNTHETIC-{i}-{j}-{side}", optionid=2 * (i * count + j) + (side == "P"),
                    cp_flag=side, exercise_style="E", am_settlement=int(is_am),
                    strike_price=strike, exdate=expiry, best_bid=prices[j] - .03,
                    best_offer=prices[j] + .03, volume=0 if j % 7 == 0 else 30,
                    open_interest=1 if j % 11 == 0 else 80, ss_flag="0",
                ))
    return dict(quotes=pd.DataFrame(quotes), forwards=pd.DataFrame(forwards),
                curve=pd.DataFrame(dict(days=[1, 30, 90, 365, 1095], rate=[2.] * 5)),
                spot=200.)


def surface_sample(drop_expiry: bool) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    """Analytic surface with optional butterfly arbitrage at the middle expiry."""
    expiries = np.array([.1, .5, 1.])
    strikes = [np.linspace(.7, 1.3, 25) for _ in expiries]
    mids = [call_price(k, t) for k, t in zip(strikes, expiries, strict=True)]
    if drop_expiry:
        # Strict concavity violates nonnegative density despite positive quotes.
        mids[1] = .8 - .5 * strikes[1] - .2 * (strikes[1] - 1.) ** 2
    return expiries, strikes, [p - .001 for p in mids], [p + .001 for p in mids]
