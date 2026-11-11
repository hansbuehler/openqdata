from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from oqdata.biz_calendar import (
    DateRange,
    add_business_days,
    count_business_days_between,
    get_business_days,
    get_half_days,
    next_business_day,
    prev_business_day,
    session_open_close,
    to_date,
)

TZ_NY = ZoneInfo("America/New_York")


def test_get_business_days_includes_christmas_eve_and_new_year_boundary() -> None:
    business_days = get_business_days(date(2024, 12, 20), date(2025, 1, 3))

    assert business_days == [
        date(2024, 12, 20),
        date(2024, 12, 23),
        date(2024, 12, 24),
        date(2024, 12, 26),
        date(2024, 12, 27),
        date(2024, 12, 30),
        date(2024, 12, 31),
        date(2025, 1, 2),
        date(2025, 1, 3),
    ]


def test_get_business_days_can_exclude_half_days() -> None:
    business_days = get_business_days(date(2024, 12, 20), date(2025, 1, 3), exclude_half_days=True)

    assert business_days == [
        date(2024, 12, 20),
        date(2024, 12, 23),
        date(2024, 12, 26),
        date(2024, 12, 27),
        date(2024, 12, 30),
        date(2024, 12, 31),
        date(2025, 1, 2),
        date(2025, 1, 3),
    ]


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (date(2024, 11, 25), date(2024, 11, 30), [date(2024, 11, 29)]),
        (date(2024, 7, 1), date(2024, 7, 5), [date(2024, 7, 3)]),
        (date(2024, 12, 20), date(2025, 1, 3), [date(2024, 12, 24)]),
    ],
)
def test_get_half_days_reports_known_early_closes(start: date, end: date, expected: list[date]) -> None:
    assert get_half_days(start, end) == expected


def test_date_range_respects_half_day_toggle() -> None:
    include_half_days = DateRange(date(2024, 12, 24), date(2024, 12, 27), exclude_half_days=False)
    exclude_half_days = DateRange(date(2024, 12, 24), date(2024, 12, 27), exclude_half_days=True)

    assert include_half_days.get_business_days() == [
        date(2024, 12, 24),
        date(2024, 12, 26),
        date(2024, 12, 27),
    ]
    assert include_half_days.get_half_days() == [date(2024, 12, 24)]

    assert exclude_half_days.get_business_days() == [
        date(2024, 12, 26),
        date(2024, 12, 27),
    ]
    assert exclude_half_days.get_half_days() == []


def test_business_day_navigation_and_counting_across_holiday_edges() -> None:
    assert add_business_days(date(2024, 12, 24), 1) == date(2024, 12, 26)
    # Christmas is closed; the half day before it is the previous business day unless half days are excluded.
    assert prev_business_day(date(2024, 12, 25)) == date(2024, 12, 24)
    assert prev_business_day(date(2024, 12, 25), exclude_half_days=True) == date(2024, 12, 23)
    assert next_business_day(date(2024, 12, 24)) == date(2024, 12, 26)

    assert count_business_days_between(date(2024, 12, 23), date(2024, 12, 24)) == 1
    assert count_business_days_between(date(2024, 12, 23), date(2024, 12, 24), exclude_half_days=True) == 0
    assert count_business_days_between(date(2024, 12, 24), date(2024, 12, 27)) == 2


def test_date_range_requires_at_least_one_business_day() -> None:
    with pytest.raises(ValueError):
        DateRange(date(2024, 12, 25), date(2024, 12, 25))

    assert get_business_days(date(2024, 12, 25), date(2024, 12, 25)) == []


def test_session_open_close_covers_regular_half_and_closed_days() -> None:
    regular_open, regular_close, regular_half_day = session_open_close(date(2024, 12, 23))
    half_open, half_close, half_day = session_open_close(date(2024, 12, 24))
    closed_open, closed_close, closed_half_day = session_open_close(date(2024, 12, 25))

    assert (regular_open, regular_close, regular_half_day) == (
        datetime(2024, 12, 23, 9, 30, tzinfo=TZ_NY),
        datetime(2024, 12, 23, 16, 0, tzinfo=TZ_NY),
        False,
    )
    assert (half_open, half_close, half_day) == (
        datetime(2024, 12, 24, 9, 30, tzinfo=TZ_NY),
        datetime(2024, 12, 24, 13, 0, tzinfo=TZ_NY),
        True,
    )
    assert (closed_open, closed_close, closed_half_day) == (None, None, False)


def test_to_date_handles_common_inputs() -> None:
    assert to_date("2024-12-24") == date(2024, 12, 24)
    assert to_date(date(2024, 12, 24)) == date(2024, 12, 24)
    assert to_date(np.datetime64("2024-12-24")) == date(2024, 12, 24)
    assert to_date(None) is None

    with pytest.raises(ValueError, match="Unsupported type for date conversion"):
        to_date(123)


# Sat 2024-06-08 / Sun 2024-06-09 lie between Fri 06-07 and Mon 06-10; Mon 2010-07-05 was a holiday.
@pytest.mark.parametrize("start,num_days,count_start,expected", [
    (date(2024, 6, 8), 1, False, date(2024, 6, 10)),   # non-business start: first business day after is day one
    (date(2024, 6, 8), 1, True, date(2024, 6, 10)),
    (date(2024, 6, 8), 2, False, date(2024, 6, 11)),
    (date(2024, 6, 9), -1, False, date(2024, 6, 7)),
    (date(2024, 6, 9), -2, True, date(2024, 6, 6)),
    (date(2024, 6, 8), 0, False, date(2024, 6, 10)),
    (date(2010, 7, 5), 1, False, date(2010, 7, 6)),
    (date(2024, 6, 10), 1, False, date(2024, 6, 11)),  # business start: excluded unless count_start
    (date(2024, 6, 10), 1, True, date(2024, 6, 10)),
    (date(2024, 6, 10), -1, True, date(2024, 6, 10)),
    (date(2024, 6, 10), -1, False, date(2024, 6, 7)),
    (date(2024, 6, 10), 0, False, date(2024, 6, 10)),
    (date(2024, 6, 10), 2, True, date(2024, 6, 11)),
])
def test_add_business_days_counting_convention(start, num_days, count_start, expected):
    assert add_business_days(start, num_days, count_start=count_start) == expected


def test_next_and_prev_business_day_from_non_business_days():
    assert next_business_day(date(2024, 6, 8)) == date(2024, 6, 10)
    assert next_business_day(date(2024, 6, 8), count_start=True) == date(2024, 6, 10)
    assert prev_business_day(date(2024, 6, 9)) == date(2024, 6, 7)
    assert prev_business_day(date(2024, 6, 9), count_start=True) == date(2024, 6, 7)
    assert next_business_day(date(2024, 6, 10), count_start=True) == date(2024, 6, 10)


def test_add_business_days_spans_long_market_closures():
    # NYSE was closed 2001-09-11 to 2001-09-14 and 2012-10-29/30 (Hurricane Sandy).
    assert add_business_days(date(2001, 9, 10), 1) == date(2001, 9, 17)
    assert add_business_days(date(2001, 9, 10), 4) == date(2001, 9, 20)
    assert add_business_days(date(2001, 9, 17), -1) == date(2001, 9, 10)
    assert add_business_days(date(2012, 10, 26), 1) == date(2012, 10, 31)
    assert add_business_days(date(2024, 1, 2), 500) == get_business_days(date(2024, 1, 2), date(2026, 12, 31))[500]


@pytest.mark.parametrize("count_start", [False, True])
@pytest.mark.parametrize("num_days", [-3, -1, 0, 1, 3])
def test_add_business_days_array_matches_scalar(num_days, count_start):
    starts = [date(2024, 6, d) for d in range(6, 12)] + [date(2010, 7, 5), date(2024, 12, 24)]
    arr = np.asarray(starts, dtype="datetime64[D]")
    expected = np.asarray([add_business_days(s, num_days, count_start=count_start) for s in starts], dtype="datetime64[D]")
    np.testing.assert_array_equal(add_business_days(arr, num_days, count_start=count_start), expected)
    nums = np.full(len(starts), num_days)
    np.testing.assert_array_equal(add_business_days(arr, nums, count_start=count_start), expected)
    np.testing.assert_array_equal(add_business_days(starts[0], nums, count_start=count_start),
                                  [add_business_days(starts[0], num_days, count_start=count_start)] * len(starts))


def test_count_business_days_between_array_matches_scalar():
    days = [date(2024, 6, d) for d in range(5, 13)]
    # Pairs of weekend days enclosing no business day raise by design and are excluded.
    pairs = [(a, b) for a in days for b in days if get_business_days(min(a, b), max(a, b))]
    starts = np.asarray([a for a, _ in pairs], dtype="datetime64[D]")
    ends = np.asarray([b for _, b in pairs], dtype="datetime64[D]")
    expected = [count_business_days_between(a, b) for a, b in pairs]
    np.testing.assert_array_equal(count_business_days_between(starts, ends), expected)
    assert count_business_days_between(date(2024, 6, 8), date(2024, 6, 7)) == -1
    assert count_business_days_between(date(2024, 6, 10), date(2024, 6, 7)) == -1
    assert count_business_days_between(date(2024, 6, 7), date(2024, 6, 10)) == 1
