from __future__ import annotations

from datetime import date, datetime, timedelta

_TEMPORAL_KINDS = {"month", "iso_week", "day", "daypart_6h"}


def parse_event_datetime(date_value: str, time_value: str) -> datetime | None:
    try:
        event_date = date.fromisoformat(date_value)
    except ValueError:
        return None

    event_time = None
    for pattern in ("%H:%M:%S", "%H:%M"):
        try:
            event_time = datetime.strptime(time_value, pattern).time()
            break
        except ValueError:
            continue
    if event_time is None:
        event_time = datetime.min.time()
    return datetime.combine(event_date, event_time)


def period_id(moment: datetime, kind: str) -> str:
    if kind not in _TEMPORAL_KINDS:
        raise ValueError(f"Unsupported temporal representation: {kind}")
    if kind == "month":
        return moment.strftime("%Y-%m")
    if kind == "iso_week":
        iso_year, iso_week, _ = moment.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if kind == "day":
        return moment.date().isoformat()
    band_start = (moment.hour // 6) * 6
    return f"{moment.date().isoformat()}T{band_start:02d}"


def enumerate_period_ids(start: date, end: date, kind: str) -> list[str]:
    if start > end:
        raise ValueError("start must be on or before end")
    if kind not in _TEMPORAL_KINDS:
        raise ValueError(f"Unsupported temporal representation: {kind}")

    if kind == "month":
        values: list[str] = []
        year = start.year
        month = start.month
        while (year, month) <= (end.year, end.month):
            values.append(f"{year:04d}-{month:02d}")
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
        return values

    if kind == "iso_week":
        cursor = start - timedelta(days=start.weekday())
        final = end - timedelta(days=end.weekday())
        values = []
        while cursor <= final:
            iso_year, iso_week, _ = cursor.isocalendar()
            values.append(f"{iso_year}-W{iso_week:02d}")
            cursor += timedelta(days=7)
        return values

    if kind == "day":
        values = []
        cursor = start
        while cursor <= end:
            values.append(cursor.isoformat())
            cursor += timedelta(days=1)
        return values

    values = []
    cursor = start
    while cursor <= end:
        values.extend(f"{cursor.isoformat()}T{hour:02d}" for hour in (0, 6, 12, 18))
        cursor += timedelta(days=1)
    return values
