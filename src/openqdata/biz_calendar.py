"""
Business day calendar utilities.

Uses pandas_market_calendars to get NYSE trading days and identify
early-close (half) days.
"""

from __future__ import annotations

import datetime as dt
import math as math
import warnings
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas_market_calendars as mcal
import polars as pl
from cdxcore.err import verify_inp
from cdxcore.version import version

import openqdata as openqdata  # NOQA

TZ_NY = ZoneInfo("America/New_York")
""" New York time zone. """

DAYS_PER_YEAR = 252
""" Standardized business days per year. """

ONE_MINUTE = 1.0 / (60.0 * 6.5 * DAYS_PER_YEAR)
""" One minute in year fraction, assuming 6.5 trading hours per day and ``DAYS_PER_YEAR`` trading days per year. """

AM_EXIRY_SUBTRACT = 0.8
""" How much to subtract from an expiry (in days) to account for AM settlement. """

NYSE_CALENDAR = mcal.get_calendar("NYSE")
""" NYSE calendar provided by `pandas market calendars <https://pandas-market-calendars.readthedocs.io/en/latest/usage.html>`_. """

_BUSINESS_DAYS_CACHE = {}
_EARLY_DAYS_CACHE = {}

@dataclass(frozen=True)
class NormalizedStrikes:
    r"""
    NMS generates relative strikes by:
    $$
        \mathrm{NMS}(z,t) := \exp\left(  z \cdot \sqrt{\frac{\sigma_\epsilon^2\epsilon+\sigma^2 t}{\epsilon+1}} \right)
    $$
    where:
    
    * $\epsilon$ is :attr:`EPS`, and $t$ is time to expiry in years. 
    * $\sigma$ is the volatility scale, which defaults to :attr:`SCALE`.
    * $\sigma_\epsilon$ is the volatility scale for epsilon.
    """

    EPS   : float = 1.0 / DAYS_PER_YEAR / 8.0  #: Small epsilon for NMS computation ~ 1 hour
    SCALE : float = math.log(1.1)            #: 10% vol

    def __post_init__(self):
        verify_inp( self.EPS > 0., "EPS must be positive" )
        verify_inp( self.SCALE > 0., "SCALE must be positive" )

    def from_nms(self, z: float|np.ndarray, t: float|np.ndarray, *, vol : float|np.ndarray|None = None, eps_vol : float|np.ndarray|None = None, backbone=np) -> float|np.ndarray:
        """
        Converts an NMS strike to a relative strike

        Parameters
        ----------
        z : float | :class:`numpy.ndarray`
            NMS strike level.
        t : float | :class:`numpy.ndarray`
            Time to expiry in years.
        vol : float | :class:`numpy.ndarray` | None, default ``None``
            Volatility in year fraction. If None, :attr:`SCALE` is used.
        eps_vol : float | :class:`numpy.ndarray`| None, default ``None``
            Volatility scale for epsilon. If None, :attr:`SCALE` is used.
        backbone : :class:`Backbone`, default :class:`BackboneNumpy`
            Alternative array namespace, e.g. ``jax.numpy``.

        Returns
        -------
        Strikes: float or :class:`numpy.ndarray`
            Relative strikes corresponding to the given NMS strikes, time to expiry and volatility.
        """
        assert np.min(t) >= 0., "Time must be non-negative"
        if not vol is None:
            assert np.min(vol) > 0., "Volatility must be positive"
        else:
            vol = self.SCALE
        if eps_vol is None:
            eps_vol = self.SCALE
        else:
            assert np.min(eps_vol) > 0., "Eps_vol must be positive"
        return backbone.exp(z * backbone.sqrt((eps_vol * eps_vol * self.EPS + vol * vol * t) / (self.EPS + 1.0)))

    def to_nms(self, k: float|np.ndarray, t: float|np.ndarray, *, vol: float|np.ndarray|None = None, eps_vol : float|np.ndarray|None = None, backbone=np) -> float|np.ndarray:
        """
        Converts a relative strike to an NMS strike.

        Parameters
        ----------
        k : float | :class:`numpy.ndarray`
            Relative strike level.
        t : float | :class:`numpy.ndarray`
            Time to expiry in years.
        vol : float | :class:`numpy.ndarray` | None, default ``None``
            Volatility in year fraction. If None, :attr:`SCALE` is used.
        eps_vol : float | :class:`numpy.ndarray`| None, default ``None``
            Volatility scale for epsilon. If None, :attr:`SCALE` is used.
        backbone : :class:`Backbone`, default :class:`BackboneNumpy`
            Alternative array namespace, e.g. ``jax.numpy``.

        Returns
        -------
        NMS Strikes: float or :class:`numpy.ndarray`
            Relative strikes corresponding to the given NMS strikes, time to expiry and volatility.
        """
        vol = self.SCALE if vol is None else vol
        assert np.min(k) > 0., "Strike must be positive"
        assert np.min(t) >= 0., "Time must be non-negative"
        if not vol is None:
            assert np.min(vol) > 0., "Volatility must be positive"
        else:
            vol = self.SCALE
        if eps_vol is None:
            eps_vol = self.SCALE
        else:
            assert np.min(eps_vol) > 0., "Eps_vol must be positive"
        return (backbone.log(k) ) * backbone.sqrt((self.EPS + 1.0) / (eps_vol * eps_vol * self.EPS + vol * vol * t))

NMS = NormalizedStrikes(EPS = 1.0 / DAYS_PER_YEAR / 8.0, SCALE = math.log(1.1))
NMS5 = NormalizedStrikes(EPS = 5.0 / DAYS_PER_YEAR, SCALE=math.log(1.1))

def to_date(d: str | dt.datetime | dt.date | np.datetime64 | None) -> dt.date | None:
    """
    Convert ``d`` to a :class:`datetime.date`, or ``None`` if ``d`` is ``None``.
    This function converts:

    * ``np.datetime64``
    * :class:`datetime.datetime`
    * :class:`datetime.date`
    * ``str`` assuming it is in iso format e.g. "2024-01-31"    
    """
    if d is None:
        return d
    if isinstance(d, np.datetime64):
        d = d.astype("datetime64[D]").astype(dt.date)
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    if isinstance(d, str):
        return dt.date.fromisoformat(d)
    raise ValueError(f"Unsupported type for date conversion: {type(d)}")


@version("0.1")
def get_business_days(
    start: str | dt.date, end: str | dt.date, exclude_half_days: bool = False
) -> list[dt.date]:
    """
    Return NYSE trading days within start and end.

    This function returns business days inclusive of ``start`` and ``end``. That means that if ``start`` equals ``end``, and if that is a trading day,
    then this function returns that day.

    Parameters
    ----------
    start : str | :class:`datetime.date`
        Start date (inclusive).
    end : str | :class:`datetime.date`
        End date (inclusive).
    exclude_half_days : bool, default ``False``
        If True, remove early-close trading sessions from the calendar.

    Returns
    -------
    list[:class:`datetime.date`]
        Sorted trading dates (timezone-naive, date-only precision).
    """
    global _BUSINESS_DAYS_CACHE
    start = to_date(start)
    end = to_date(end)
    exclude_half_days = bool(exclude_half_days)

    if start > end:
        raise ValueError(f"start ({start}) must be <= end ({end})")

    key = (start, end, exclude_half_days)
    schedule = _BUSINESS_DAYS_CACHE.get(key, None)
    if schedule is not None:
        return schedule

    schedule = NYSE_CALENDAR.schedule(start_date=str(start), end_date=str(end))

    if exclude_half_days and len(schedule) > 0:
        early = NYSE_CALENDAR.early_closes(schedule)
        schedule = schedule.drop(early.index, errors="ignore")

    schedule = schedule.index.normalize().tz_localize(
        None
    )  # index is a DatetimeIndex of trading days in the range
    schedule = [dt.date(d.year, d.month, d.day) for d in schedule]
    assert len(schedule) == 0 or schedule[0] <= schedule[-1], f"Internal error: schedule is not sorted: {schedule}"

    _BUSINESS_DAYS_CACHE[key] = schedule
    return schedule


@version("0.1", dependencies=[get_business_days])
def count_business_days_between(
    start: dt.date | np.ndarray,
    end: dt.date | np.ndarray,
    exclude_half_days: bool = False,
) -> int | np.ndarray:
    """
    Count the number of trading days in ``(start, end]``, i.e. from ``start`` (exclusive) to ``end`` (inclusive).
    If ``end < start``, then count the number of trading days in ``[end, start)`` and return the negative of that count.

    The count *includes* ``end`` if it is a trading day, but *excludes* ``start``, assuming, essentially, an end-of-day convention.
    Half days are counted as full trading days unless ``exclude_half_days`` is ``True``.

    If ``start == end``, and if that day is a business day, then this function returns 0.
    If ``start`` and ``end`` are non-business days bracketing no business days, this function raises a :class:`ValueError`.

    Parameters
    ----------
    start : ``datetime.date`` | :class:`numpy.ndarray` of dates
        Start date(s) (exclusive).
    end : ``datetime.date`` | :class:`numpy.ndarray` of dates
        End date(s) (inclusive).
    exclude_half_days : bool, default ``False``
        If True, remove early-close trading sessions from the calendar before counting.

    Returns
    -------
    Count: ``int`` or :class:`numpy.ndarray`
        Number of trading days.
    """
    start = to_date(start) if not isinstance(start, np.ndarray) else start
    end = to_date(end) if not isinstance(end, np.ndarray) else end
    is_vec = isinstance(start, np.ndarray) or isinstance(end, np.ndarray)
    start = np.asarray(start, dtype="datetime64[D]")
    end = np.asarray(end, dtype="datetime64[D]")

    mstart = min(np.min(start), np.min(end))
    mend = max(np.max(start), np.max(end))
    trading_days = get_business_days(mstart, mend, exclude_half_days=exclude_half_days)

    if len(trading_days) == 0:
        raise ValueError(f"No trading days between {mstart} and {mend} with half days {'excluded' if exclude_half_days else 'included'}")

    if not is_vec:
        # Scalar case: count how many trading days are in (start, end]
        if start <= end:
            count = np.sum((trading_days > start) & (trading_days <= end))
        else:
            count = -np.sum((trading_days >= end) & (trading_days < start))

        return int(count)

    # Vectorised case, matching the scalar convention:
    # count trading days in (start, end] if start <= end, and minus those in [end, start) otherwise.
    td_array = np.asarray(trading_days, dtype="datetime64[D]")
    forward = np.searchsorted(td_array, end, side="right") - np.searchsorted(td_array, start, side="right")
    backward = np.searchsorted(td_array, end, side="left") - np.searchsorted(td_array, start, side="left")
    return np.where(start <= end, forward, backward).astype(np.int32)


@version("0.2", dependencies=[get_business_days])
def add_business_days(
    start: dt.date, num_days: int, exclude_half_days: bool = False, *, count_start: bool = False
) -> dt.date:
    """
    Add a number of business days to a date.

    Counting starts from the first business day after (or, if ``num_days < 0``, before) ``start``.
    If ``start`` is a business day and ``count_start`` is ``True``, then ``start`` itself is counted
    as the first day in either direction, i.e. ``num_days=1`` and ``num_days=-1`` both return ``start``.

    If ``start`` is not a business day, the first business day after (before) ``start`` is
    counted as the first day; ``count_start`` has no effect. For example, if ``start`` is a Saturday
    then ``num_days=1`` returns the following Monday and ``num_days=-1`` the preceding Friday,
    assuming both are business days.

    ``num_days=0`` returns ``start`` if it is a business day, and otherwise the next business day.

    Parameters
    ----------
    start : ``datetime.date`` | :class:`numpy.ndarray` of dates
        Start date(s). Does not need to be a business day.
    num_days : int | :class:`numpy.ndarray` of ints
        Number of business days to add. Can be negative to subtract business days.
    exclude_half_days : bool, default ``False``
        If ``True``, remove early-close trading sessions from the calendar before counting.
    count_start : bool, default ``False``
        Whether to count ``start`` as the first day if it is a business day.
        This flag has no effect if ``start`` is not a business day.

    Returns
    -------
    ``datetime.date`` | :class:`numpy.ndarray` of dates
        Resulting date(s) after adding the specified number of business days.
        Array inputs return ``datetime64[D]`` arrays with element-wise identical results to the scalar version.
    """
    kwargs = dict(exclude_half_days=exclude_half_days, count_start=count_start)
    if isinstance(start, np.ndarray) or isinstance(num_days, np.ndarray):
        starts, nums = np.broadcast_arrays(np.asarray(start, dtype="datetime64[D]"), np.asarray(num_days))
        verify_inp(np.issubdtype(nums.dtype, np.integer),
                   lambda: f"num_days must be integer, found dtype {nums.dtype}")
        out = [add_business_days(s.astype(dt.date), int(n), **kwargs) for s, n in zip(starts.ravel(), nums.ravel(), strict=True)]
        return np.asarray(out, dtype="datetime64[D]").reshape(starts.shape)

    # scalar version
    start = to_date(start)
    num_days = int(num_days)
    forward = num_days >= 0
    steps = abs(num_days)

    # Calendar window large enough for ``steps`` business days; widened on long market closures.
    window = steps * 7 // 5 + 10
    while True:
        if forward:
            schedule = get_business_days(start, start + dt.timedelta(days=window), exclude_half_days=exclude_half_days)
        else:
            schedule = list(reversed(get_business_days(start - dt.timedelta(days=window), start, exclude_half_days=exclude_half_days)))
        # schedule[0] is ``start`` if it is a business day, otherwise the first business day beyond it.
        start_is_business_day = len(schedule) > 0 and schedule[0] == start
        if start_is_business_day and not count_start:
            index = steps
        else:
            index = max(steps - 1, 0)
        if index < len(schedule):
            return schedule[index]
        window *= 2


@version("0.2", dependencies=[add_business_days])
def prev_business_day(
    date: dt.date, exclude_half_days: bool = False, *, count_start: bool = False
) -> dt.date:
    """
    Get the previous business day before the given date.

    Parameters
    ----------
    date : ``datetime.date``
        Reference date. This date does not have to be a business day.
    exclude_half_days : bool, default ``False``
        If True, remove early-close trading sessions from the calendar before counting.
    count_start : bool, default ``False``
        Whether to count ``date`` if it is a business day. If ``False``, then the counts starts from the first business day before date.
        That means even if ``date`` is a business day, the function will return the previous business day before it.
        If ``True``, then if ``date`` is a business day, the function will return that date.

        This flag has no effect if ``date`` is not a business day.

    Returns
    -------
    ``datetime.date``
        Previous business day before the given date.
    """
    return add_business_days(date, -1, exclude_half_days=exclude_half_days, count_start=count_start)


@version("0.2", dependencies=[add_business_days])
def next_business_day(
    date: dt.date, exclude_half_days: bool = False, *, count_start: bool = False
) -> dt.date:
    """
    Get the next business day after the given date.

    Parameters
    ----------
    date : ``datetime.date``
        Reference date. This date does not have to be a business day.
    exclude_half_days : bool, default ``False``
        If True, remove early-close trading sessions from the calendar before counting.
    count_start : bool, default ``False``
        Whether to count ``date`` if it is a business day. If ``False``, then the counts starts from the first business day after date.
        That means even if ``date`` is a business day, the function will return the next business day after it.
        If ``True``, then if ``date`` is a business day, the function will return that date.
        This flag has no effect if ``date`` is not a business day.

    Returns
    -------
    ``datetime.date``
        Next business day after the given date.
    """
    return add_business_days(date, 1, exclude_half_days=exclude_half_days, count_start=count_start)


@version("0.1")
def get_half_days(start: dt.date, end: dt.date) -> list[dt.date]:
    """
    Return a list of half days (early closes) between start and end, inclusive.
    """
    global _EARLY_DAYS_CACHE

    start = to_date(start)
    end = to_date(end)
    if start > end:
        raise ValueError(f"start ({start}) must be <= end ({end})")

    key = (start, end)
    schedule = _EARLY_DAYS_CACHE.get(key, None)
    if schedule is not None:
        return schedule

    schedule = NYSE_CALENDAR.schedule(start_date=str(start), end_date=str(end))
    schedule = NYSE_CALENDAR.early_closes(schedule=schedule)
    schedule = schedule.index.normalize().tz_localize(
        None
    )  # index is a DatetimeIndex of trading days in the range
    schedule = [dt.date(d.year, d.month, d.day) for d in schedule]
    _EARLY_DAYS_CACHE[key] = schedule
    return schedule


@version("0.1", dependencies=[get_business_days, get_half_days])
@dataclass
class DateRange:
    """A simple date range class."""

    start: dt.date | str  #: Start date (inclusive).
    end: dt.date | str  #: End date (inclusive).
    exclude_half_days: bool = True  #: Whether to exclude half days (early closes) from the business day count. Default is True.

    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = dt.date.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = dt.date.fromisoformat(self.end)
        verify_inp(
            isinstance(self.start, dt.date),
            f"'start' must be a datetime.date, but found {type(self.start)}",
        )
        verify_inp(
            isinstance(self.end, dt.date),
            f"'end' must be a datetime.date, but found {type(self.end)}",
        )

        if self.start > self.end:
            raise ValueError(f"'start' ({self.start}) must be at or before 'end' ({self.end})")

        bdays = self.get_business_days()
        if len(bdays) == 0:
            raise ValueError(
                f"No business days in the range {self.start} to {self.end} with half days {'excluded' if self.exclude_half_days else 'included'}"
            )

    def __str__(self):
        return f"{self.start}_{self.end}{'x' if self.exclude_half_days else 'i'}"

    def __hash__(self):
        return hash((self.start, self.end, self.exclude_half_days))

    def get_business_days(self) -> list[dt.date]:
        """Get business days in this date range."""
        return get_business_days(self.start, self.end, exclude_half_days=self.exclude_half_days)

    def get_half_days(self) -> list[dt.date]:
        """Get half days (early closes) in this date range."""
        return get_half_days(self.start, self.end) if not self.exclude_half_days else []

@version("0.1")
def session_open_close( date: dt.date ) -> tuple[dt.datetime, dt.datetime, bool]:
    """
    Returns the session open and close for a given ``date`` as :class:`datetime.datetime` objects in New York time zone,
    and a boolean indicating whether it is a half day (early close) or not.

    This function will return ``(None, None, False)`` if the given date is not a trading day.    
    """

    date          = to_date(date)
    schedule      = NYSE_CALENDAR.schedule(start_date=date, end_date=date)

    if len(schedule) == 0:
        return None, None, False

    early         = NYSE_CALENDAR.early_closes(schedule)

    with warnings.catch_warnings(action="ignore"):
        schedule['market_open']  = schedule['market_open'].apply(lambda ts: ts.to_pydatetime())
        schedule['market_close'] = schedule['market_close'].apply(lambda ts: ts.to_pydatetime())
    schedule['market_open']  = schedule['market_open'].dt.tz_convert('America/New_York')
    schedule['market_close'] = schedule['market_close'].dt.tz_convert('America/New_York')

    assert len(schedule['market_open']) <= 1, "Internal error"
    assert len(schedule['market_close']) <= 1, "Internal error"

    return schedule['market_open'].iloc[0], schedule['market_close'].iloc[0], len(early)>0

@version("0.1")
def full_second_grid_ns(open_dt: dt.datetime, close_dt: dt.datetime) -> pl.Series:
    """
    Per-second Polars Series for RTH bins: ``[open_dt, open_dt+1s, ..., close_dt-1s]``.

    The grid is end-exclusive so the last bin key is ``close_dt - 1s`` and represents
    ``[close_dt-1s, close_dt]`` (inclusive close handled by timestamp mapping in the caller).
    """
    s = pl.datetime_range(
        open_dt,
        close_dt,
        interval="1s",
        time_zone=TZ_NY.key,
        eager=True,
        closed="left",
    )
    return s.dt.cast_time_unit("ns").rename("dt_ns")
