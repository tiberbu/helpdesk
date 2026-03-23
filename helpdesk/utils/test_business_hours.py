# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for helpdesk.utils.business_hours.

Pure-Python tests — no Frappe dependency required.
Run standalone:
    python -m pytest helpdesk/utils/test_business_hours.py -v

Or via bench:
    bench --site helpdesk.localhost run-tests \
        --module helpdesk.utils.test_business_hours
"""

import unittest
from datetime import date, datetime, time, timedelta

from helpdesk.utils.business_hours import (
    calculate_business_minutes,
    get_next_business_start,
    subtract_pause_minutes,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Standard Mon-Fri 09:00-18:00 working schedule
_WEEKDAYS_9_18 = [
    {"weekday": 0, "start_time": time(9, 0), "end_time": time(18, 0)},   # Monday
    {"weekday": 1, "start_time": time(9, 0), "end_time": time(18, 0)},   # Tuesday
    {"weekday": 2, "start_time": time(9, 0), "end_time": time(18, 0)},   # Wednesday
    {"weekday": 3, "start_time": time(9, 0), "end_time": time(18, 0)},   # Thursday
    {"weekday": 4, "start_time": time(9, 0), "end_time": time(18, 0)},   # Friday
]

_NO_HOLIDAYS: set[date] = set()

# 2026-01-05 is a Monday
_MONDAY = date(2026, 1, 5)
_TUESDAY = date(2026, 1, 6)
_WEDNESDAY = date(2026, 1, 7)
_THURSDAY = date(2026, 1, 8)
_FRIDAY = date(2026, 1, 9)
_SATURDAY = date(2026, 1, 10)
_SUNDAY = date(2026, 1, 11)
_NEXT_MONDAY = date(2026, 1, 12)


def _dt(d: date, h: int, m: int = 0) -> datetime:
    """Build a naive datetime in UTC at date d, hour h, minute m."""
    return datetime(d.year, d.month, d.day, h, m)


# ---------------------------------------------------------------------------
# Tests: calculate_business_minutes
# ---------------------------------------------------------------------------


class TestCalculateBusinessMinutes(unittest.TestCase):

    def test_same_day_within_hours(self):
        """Mon 10:00→12:00 → 120 business minutes."""
        start = _dt(_MONDAY, 10)
        end = _dt(_MONDAY, 12)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_same_day_outside_hours(self):
        """Mon 19:00→21:00 — after close → 0 business minutes."""
        start = _dt(_MONDAY, 19)
        end = _dt(_MONDAY, 21)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 0)

    def test_start_before_business_hours(self):
        """Mon 07:00→11:00 — only 09:00-11:00 counts → 120 min."""
        start = _dt(_MONDAY, 7)
        end = _dt(_MONDAY, 11)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_end_after_business_hours(self):
        """Mon 16:00→20:00 — only 16:00-18:00 counts → 120 min."""
        start = _dt(_MONDAY, 16)
        end = _dt(_MONDAY, 20)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_overnight_to_next_business_day(self):
        """Mon 17:00→Tue 10:00 → 60 (Mon 17-18) + 60 (Tue 09-10) = 120 min."""
        start = _dt(_MONDAY, 17)
        end = _dt(_TUESDAY, 10)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_full_weekend_span(self):
        """Fri 17:00→Mon 10:00 → 60 (Fri 17-18) + 0 (Sat/Sun) + 60 (Mon 09-10) = 120 min."""
        start = _dt(_FRIDAY, 17)
        end = _dt(_NEXT_MONDAY, 10)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_holiday_exclusion(self):
        """Mon-Wed 09:00-18:00, Tue is holiday → 540 (Mon) + 0 (Tue) + 540 (Wed) = 1080 min."""
        holidays = {_TUESDAY}
        start = _dt(_MONDAY, 9)
        end = _dt(_WEDNESDAY, 18)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, holidays)
        self.assertEqual(result, 1080)

    def test_different_timezone(self):
        """US/Eastern SLA: business hours 09:00-18:00 ET = 14:00-23:00 UTC.

        Start: 2026-01-05 14:00 UTC (= Mon 09:00 ET), End: 2026-01-05 16:00 UTC (= Mon 11:00 ET)
        → 120 business minutes.
        """
        service_days = [
            {"weekday": 0, "start_time": time(9, 0), "end_time": time(18, 0)},
        ]
        # 14:00 UTC = 09:00 US/Eastern (UTC-5 in January)
        start = datetime(2026, 1, 5, 14, 0)
        end = datetime(2026, 1, 5, 16, 0)
        result = calculate_business_minutes(
            start, end, service_days, _NO_HOLIDAYS, timezone="US/Eastern"
        )
        self.assertEqual(result, 120)

    def test_zero_duration(self):
        """start == end → 0 business minutes."""
        dt = _dt(_MONDAY, 10)
        result = calculate_business_minutes(dt, dt, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 0)

    def test_start_after_end(self):
        """start > end → 0 (non-negative guarantee)."""
        start = _dt(_MONDAY, 12)
        end = _dt(_MONDAY, 10)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 0)

    def test_no_service_days_falls_back_to_calendar_minutes(self):
        """Empty service_days → raw calendar minutes (fallback for unconfigured SLAs)."""
        start = _dt(_MONDAY, 10)
        end = _dt(_MONDAY, 12)
        result = calculate_business_minutes(start, end, [], _NO_HOLIDAYS)
        self.assertEqual(result, 120)

    def test_full_workday(self):
        """Mon 09:00→18:00 → exactly 540 min."""
        start = _dt(_MONDAY, 9)
        end = _dt(_MONDAY, 18)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 540)

    def test_partial_minute_floors(self):
        """30-second overlap only → floors to 0 minutes."""
        start = datetime(2026, 1, 5, 9, 0, 0)
        end = datetime(2026, 1, 5, 9, 0, 30)
        result = calculate_business_minutes(start, end, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Tests: subtract_pause_minutes
# ---------------------------------------------------------------------------


class TestSubtractPauseMinutes(unittest.TestCase):

    def test_pause_status_compatibility(self):
        """Pause windows overlapping business hours reduce the total correctly.

        Scenario: 300 raw business minutes, 2 pause windows each covering 60
        business minutes → 300 - 120 = 180 minutes.
        """
        # Mon 09:00→14:00 = 300 business minutes
        service_days = _WEEKDAYS_9_18
        # Pause 1: Mon 10:00-11:00 (60 business min)
        pause1 = (_dt(_MONDAY, 10), _dt(_MONDAY, 11))
        # Pause 2: Mon 12:00-13:00 (60 business min)
        pause2 = (_dt(_MONDAY, 12), _dt(_MONDAY, 13))
        result = subtract_pause_minutes(300, [pause1, pause2], service_days, _NO_HOLIDAYS)
        self.assertEqual(result, 180)

    def test_pause_outside_business_hours_ignored(self):
        """Pause windows outside business hours don't subtract anything."""
        # Pause: Mon 19:00-21:00 (outside hours → 0 business minutes)
        pause = (_dt(_MONDAY, 19), _dt(_MONDAY, 21))
        result = subtract_pause_minutes(300, [pause], _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 300)

    def test_pause_clamps_to_zero(self):
        """Result never goes below 0."""
        # 1-minute total but 60-minute pause
        pause = (_dt(_MONDAY, 9), _dt(_MONDAY, 10))
        result = subtract_pause_minutes(1, [pause], _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Tests: get_next_business_start
# ---------------------------------------------------------------------------


class TestGetNextBusinessStart(unittest.TestCase):

    def test_already_in_business_hours(self):
        """When dt is already inside working hours, return dt itself."""
        dt = _dt(_MONDAY, 10)
        result = get_next_business_start(dt, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        # Should return a tz-aware dt equal to Mon 10:00 UTC
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 0)
        # Should be the same day
        self.assertEqual(result.date(), _MONDAY)

    def test_before_business_hours_same_day(self):
        """dt before working hours on a workday → returns opening time that day."""
        dt = _dt(_MONDAY, 7)
        result = get_next_business_start(dt, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.date(), _MONDAY)

    def test_after_business_hours_advances_to_next_day(self):
        """dt after working hours → returns opening of next workday."""
        dt = _dt(_MONDAY, 19)
        result = get_next_business_start(dt, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.date(), _TUESDAY)

    def test_weekend_advances_to_monday(self):
        """dt on Saturday → returns Monday 09:00."""
        dt = _dt(_SATURDAY, 12)
        result = get_next_business_start(dt, _WEEKDAYS_9_18, _NO_HOLIDAYS)
        self.assertEqual(result.date(), _NEXT_MONDAY)
        self.assertEqual(result.hour, 9)

    def test_holiday_advances_past_holiday(self):
        """dt on holiday (Monday) → returns Tuesday 09:00."""
        holidays = {_MONDAY}
        dt = _dt(_MONDAY, 10)
        result = get_next_business_start(dt, _WEEKDAYS_9_18, holidays)
        self.assertEqual(result.date(), _TUESDAY)
        self.assertEqual(result.hour, 9)


if __name__ == "__main__":
    unittest.main()
