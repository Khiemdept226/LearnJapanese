import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class ReminderDecision:
    should_notify: bool
    reason: str
    title: str = ""
    message: str = ""


def parse_iso(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _minutes_since(value, now):
    parsed = parse_iso(value)
    if not parsed:
        return None
    return (now - parsed).total_seconds() / 60


def _time_in_window(now, start, end):
    try:
        start_time = dt.time.fromisoformat(start)
        end_time = dt.time.fromisoformat(end)
    except (TypeError, ValueError):
        start_time = dt.time(9, 0)
        end_time = dt.time(18, 0)

    current = now.time().replace(second=0, microsecond=0)
    if start_time <= end_time:
        return start_time <= current <= end_time
    return current >= start_time or current <= end_time


def _is_future(value, now):
    parsed = parse_iso(value)
    return bool(parsed and parsed > now)


def _message_for(settings, stats):
    due = int(stats.get("due") or 0)
    new = int(stats.get("new") or 0)
    mode = settings.get("reminder_mode")

    if due > 0:
        if mode == "jlpt_sprint":
            return (
                "JLPT sprint",
                f"Con {due} the can on. Tranh thu luc doi AI nhe.",
                "due_available",
            )
        return (
            f"Con {due} the can on",
            f"Con {due} the can on. Hoc 5 phut nhe?",
            "due_available",
        )

    return (
        f"Con {new} the moi",
        f"Con {new} the moi. Lam 1 phien ngan nhe?",
        "new_available",
    )


def should_send_study_reminder(settings, stats, now=None):
    now = now or dt.datetime.now()
    if not settings.get("reminder_enabled", True):
        return ReminderDecision(False, "disabled")

    if not _time_in_window(
        now,
        settings.get("study_window_start", "09:00"),
        settings.get("study_window_end", "18:00"),
    ):
        return ReminderDecision(False, "outside_window")

    if _is_future(settings.get("skip_until"), now):
        return ReminderDecision(False, "skipped")

    if _is_future(settings.get("snooze_until"), now):
        return ReminderDecision(False, "snoozed")

    due = int(stats.get("due") or 0)
    new = int(stats.get("new") or 0)
    if due <= 0 and new <= 0:
        return ReminderDecision(False, "no_cards")

    if settings.get("quiet_after_target_done") and stats.get("target_done"):
        return ReminderDecision(False, "target_done")

    interval = int(settings.get("reminder_interval_minutes") or 60)
    for key in ("last_mini_session_completed_at", "last_reminder_at"):
        elapsed = _minutes_since(settings.get(key), now)
        if elapsed is not None and elapsed < interval:
            return ReminderDecision(False, "interval_wait")

    title, message, reason = _message_for(settings, stats)
    return ReminderDecision(True, reason, title, message)


def snooze_until(settings, now=None):
    now = now or dt.datetime.now()
    minutes = int(settings.get("snooze_minutes") or 15)
    return (now + dt.timedelta(minutes=minutes)).replace(microsecond=0).isoformat()


def skip_until_end_of_day(now=None):
    now = now or dt.datetime.now()
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return end.isoformat()
