# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Pure Python business hours calculator.

No Frappe imports — this module can be imported and tested standalone.
All Frappe integration (caching, DB) lives in the SLA controller, not here.

Primary API
-----------
calculate_business_minutes(start, end, service_days, holidays, timezone) -> int
    Returns total business minutes elapsed between start and end.

get_next_business_start(dt, service_days, holidays, timezone) -> datetime
    Returns the next business hours start from a given datetime.
"""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

import pytz


def calculate_business_minutes(
    start: datetime,
    end: datetime,
    service_days: list[dict],
    holidays: set[date],
    timezone: str = "UTC",
) -> int:
    """Return integer business minutes elapsed between *start* and *end*.

    The calculation is timezone-aware: both *start* and *end* are converted to
    *timezone* before comparison against the configured service windows.

    Args:
        start: Interval start (naive UTC or tz-aware).
        end: Interval end (naive UTC or tz-aware).
        service_days: List of dicts, each with keys:
            - ``weekday`` (int): 0 = Monday … 6 = Sunday (Python weekday).
            - ``start_time`` (datetime.time): Start of service window.
            - ``end_time`` (datetime.time): End of service window.
        holidays: Set of ``datetime.date`` objects to exclude entirely.
        timezone: IANA timezone string, e.g. ``"US/Eastern"``.

    Returns:
        Total business minutes (non-negative integer).  Zero if start >= end or
        no service days / windows overlap the interval.
    """
    if not service_days:
        # No service-day config — fall back to calendar minutes
        delta = (end - start).total_seconds()
        return max(0, int(math.floor(delta / 60)))

    tz = pytz.timezone(timezone)
    start_local = _to_local(start, tz)
    end_local = _to_local(end, tz)

    if start_local >= end_local:
        return 0

    # Build a fast lookup: weekday (0-6) -> list of (start_time, end_time)
    windows_by_weekday: dict[int, list[tuple[time, time]]] = {}
    for sd in service_days:
        wd = _normalize_weekday(sd["weekday"])
        st = _normalize_time(sd["start_time"])
        et = _normalize_time(sd["end_time"])
        if st >= et:
            continue  # Invalid window — skip
        windows_by_weekday.setdefault(wd, []).append((st, et))

    total_minutes = 0
    current_date = start_local.date()
    end_date = end_local.date()

    while current_date <= end_date:
        if current_date in holidays:
            current_date += timedelta(days=1)
            continue

        weekday = current_date.weekday()
        windows = windows_by_weekday.get(weekday)
        if not windows:
            current_date += timedelta(days=1)
            continue

        for (svc_start, svc_end) in windows:
            # Build tz-aware window boundaries for this calendar day
            win_start = tz.localize(datetime.combine(current_date, svc_start))
            win_end = tz.localize(datetime.combine(current_date, svc_end))

            # Clamp to [start_local, end_local]
            overlap_start = max(win_start, start_local)
            overlap_end = min(win_end, end_local)

            if overlap_end > overlap_start:
                diff_seconds = (overlap_end - overlap_start).total_seconds()
                total_minutes += int(math.floor(diff_seconds / 60))

        current_date += timedelta(days=1)

    return total_minutes


def get_next_business_start(
    dt: datetime,
    service_days: list[dict],
    holidays: set[date],
    timezone: str = "UTC",
) -> datetime:
    """Return the earliest business-hours start moment on or after *dt*.

    Useful for computing SLA deadlines: after adding the target duration in
    business minutes, snap back to the window start if the result falls
    outside working hours.

    Returns:
        A timezone-aware datetime in *timezone*.  If no suitable day is found
        within 365 days, raises ``ValueError``.
    """
    tz = pytz.timezone(timezone)
    dt_local = _to_local(dt, tz)

    windows_by_weekday: dict[int, list[tuple[time, time]]] = {}
    for sd in service_days:
        wd = _normalize_weekday(sd["weekday"])
        st = _normalize_time(sd["start_time"])
        et = _normalize_time(sd["end_time"])
        if st < et:
            windows_by_weekday.setdefault(wd, []).append((st, et))

    for day_offset in range(366):
        check_date = dt_local.date() + timedelta(days=day_offset)
        if check_date in holidays:
            continue
        weekday = check_date.weekday()
        windows = windows_by_weekday.get(weekday)
        if not windows:
            continue
        for (svc_start, svc_end) in sorted(windows):
            candidate = tz.localize(datetime.combine(check_date, svc_start))
            if candidate >= dt_local:
                return candidate
            # dt_local is inside this window
            win_end = tz.localize(datetime.combine(check_date, svc_end))
            if dt_local < win_end:
                return dt_local  # Already inside working hours

    raise ValueError(
        f"No business day found within 365 days from {dt_local} "
        f"(timezone={timezone})"
    )


def subtract_pause_minutes(
    business_minutes: int,
    pause_windows: list[tuple[datetime, datetime]],
    service_days: list[dict],
    holidays: set[date],
    timezone: str = "UTC",
) -> int:
    """Subtract pause windows from a business minute total.

    Used for pause-on-status compatibility: given a list of (pause_start,
    pause_end) intervals during which the ticket was on hold, compute the
    overlap with business hours and subtract from *business_minutes*.

    Args:
        business_minutes: Raw elapsed business minutes before deducting hold.
        pause_windows: List of (pause_start, pause_end) datetime pairs.
        service_days: Same format as ``calculate_business_minutes``.
        holidays: Same format as ``calculate_business_minutes``.
        timezone: IANA timezone string.

    Returns:
        Non-negative integer after subtracting pause overlap.
    """
    total_pause = 0
    for (ps, pe) in pause_windows:
        total_pause += calculate_business_minutes(ps, pe, service_days, holidays, timezone)
    return max(0, business_minutes - total_pause)


# ---------------------------------------------------------------------------
# Private helpers (no Frappe dependencies)
# ---------------------------------------------------------------------------


def _to_local(dt: datetime, tz: pytz.BaseTzInfo) -> datetime:
    """Convert *dt* to tz-aware local time in *tz*.

    If *dt* is naive, it is assumed to be UTC.
    """
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz)


def _normalize_weekday(value) -> int:
    """Normalise weekday to Python int (0=Monday … 6=Sunday).

    Accepts:
        - int already in range 0-6
        - str name like "Monday", "Tuesday" … (case-insensitive)
    """
    if isinstance(value, int):
        return value % 7
    _DAYS = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    return _DAYS[value.strip().lower()]


def _normalize_time(value) -> time:
    """Normalise value to ``datetime.time``.

    Accepts:
        - ``datetime.time`` — returned as-is
        - ``datetime.timedelta`` — converted via total_seconds()
        - ``str`` — parsed as "HH:MM" or "HH:MM:SS"
    """
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return time(hours % 24, minutes, seconds)
    if isinstance(value, str):
        parts = value.split(":")
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
        return time(h, m, s)
    raise TypeError(f"Cannot convert {type(value)} to datetime.time")
