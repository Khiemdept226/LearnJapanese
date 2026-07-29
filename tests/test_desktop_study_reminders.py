import datetime as dt

from desktop_app import study_reminders


BASE_SETTINGS = {
    "reminder_enabled": True,
    "reminder_mode": "workday_balanced",
    "study_window_start": "09:00",
    "study_window_end": "18:00",
    "reminder_interval_minutes": 60,
    "snooze_minutes": 15,
    "mini_session_card_limit": 8,
    "quiet_after_target_done": True,
    "skip_until": None,
    "snooze_until": None,
    "last_reminder_at": None,
    "last_mini_session_completed_at": None,
}


def at(hour, minute):
    return dt.datetime(2026, 7, 29, hour, minute)


def test_no_reminder_outside_study_window():
    decision = study_reminders.should_send_study_reminder(
        BASE_SETTINGS,
        {"due": 3, "new": 5},
        at(8, 59),
    )

    assert decision.should_notify is False
    assert decision.reason == "outside_window"


def test_reminder_when_due_cards_exist_and_interval_passed():
    settings = dict(BASE_SETTINGS, last_reminder_at="2026-07-29T09:00:00")

    decision = study_reminders.should_send_study_reminder(
        settings,
        {"due": 4, "new": 5},
        at(10, 1),
    )

    assert decision.should_notify is True
    assert decision.reason == "due_available"
    assert "4" in decision.title
    assert "on" in decision.message


def test_no_reminder_during_snooze():
    settings = dict(BASE_SETTINGS, snooze_until="2026-07-29T10:15:00")

    decision = study_reminders.should_send_study_reminder(
        settings,
        {"due": 4, "new": 5},
        at(10, 0),
    )

    assert decision.should_notify is False
    assert decision.reason == "snoozed"


def test_no_reminder_during_skip_today():
    settings = dict(BASE_SETTINGS, skip_until="2026-07-29T23:59:59")

    decision = study_reminders.should_send_study_reminder(
        settings,
        {"due": 4, "new": 5},
        at(10, 0),
    )

    assert decision.should_notify is False
    assert decision.reason == "skipped"


def test_no_reminder_when_no_cards_available():
    decision = study_reminders.should_send_study_reminder(
        BASE_SETTINGS,
        {"due": 0, "new": 0},
        at(10, 0),
    )

    assert decision.should_notify is False
    assert decision.reason == "no_cards"


def test_interval_blocks_repeat_reminder():
    settings = dict(BASE_SETTINGS, last_reminder_at="2026-07-29T10:00:00")

    decision = study_reminders.should_send_study_reminder(
        settings,
        {"due": 4, "new": 5},
        at(10, 30),
    )

    assert decision.should_notify is False
    assert decision.reason == "interval_wait"


def test_snooze_until_uses_configured_minutes():
    now = at(10, 0)

    value = study_reminders.snooze_until(BASE_SETTINGS, now)

    assert value == "2026-07-29T10:15:00"


def test_skip_until_end_of_day():
    value = study_reminders.skip_until_end_of_day(at(10, 0))

    assert value == "2026-07-29T23:59:59"
