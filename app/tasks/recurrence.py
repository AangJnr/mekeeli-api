from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter
from dateutil.rrule import rrulestr


def compute_next_run_at(schedule_type: str, schedule_value: str | None, timezone: str) -> datetime | None:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Unsupported timezone") from exc
    now = datetime.now(tz)

    if schedule_type == "once":
        if not schedule_value:
            return None
        try:
            run_at = datetime.fromisoformat(schedule_value)
        except ValueError as exc:
            raise ValueError("Invalid schedule_value for once") from exc
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=tz)
        return run_at

    if schedule_type == "cron":
        if not schedule_value:
            return None
        try:
            iterator = croniter(schedule_value, now)
        except Exception as exc:
            raise ValueError("Invalid cron schedule_value") from exc
        return iterator.get_next(datetime)

    if schedule_type == "rrule":
        if not schedule_value:
            return None
        try:
            rule = rrulestr(schedule_value, dtstart=now)
        except Exception as exc:
            raise ValueError("Invalid rrule schedule_value") from exc
        return rule.after(now, inc=False)

    raise ValueError("Unsupported schedule_type")
