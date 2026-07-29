import copy
import json
import os
import re

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

PRESET_SETTINGS = {
    "workday_balanced": {
        "study_window_start": "09:00",
        "study_window_end": "18:00",
        "reminder_interval_minutes": 60,
        "snooze_minutes": 15,
        "mini_session_card_limit": 8,
    },
    "jlpt_sprint": {
        "study_window_start": "09:00",
        "study_window_end": "22:00",
        "reminder_interval_minutes": 45,
        "snooze_minutes": 15,
        "mini_session_card_limit": 12,
    },
    "gentle": {
        "study_window_start": "18:00",
        "study_window_end": "22:00",
        "reminder_interval_minutes": 120,
        "snooze_minutes": 30,
        "mini_session_card_limit": 5,
    },
}

DEFAULT_SETTINGS = {
    "reminder_enabled": True,
    "reminder_interval_hours": 2,
    "daily_reminder_enabled": True,
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
    "last_studied_at": None,
    "last_mini_session_completed_at": None,
}

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _valid_time(value, default):
    return value if isinstance(value, str) and TIME_RE.match(value) else default


def _bool_value(value, default=True):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if value is None:
        return default
    return bool(value)


def apply_reminder_preset(settings):
    normalized = dict(settings or {})
    mode = normalized.get("reminder_mode", DEFAULT_SETTINGS["reminder_mode"])
    if mode not in PRESET_SETTINGS and mode != "custom":
        mode = DEFAULT_SETTINGS["reminder_mode"]
    normalized["reminder_mode"] = mode
    if mode in PRESET_SETTINGS:
        normalized.update(PRESET_SETTINGS[mode])
    return normalized


def normalize_settings(settings):
    normalized = copy.deepcopy(DEFAULT_SETTINGS)
    normalized.update(settings or {})

    mode = normalized.get("reminder_mode")
    if mode not in PRESET_SETTINGS and mode != "custom":
        mode = DEFAULT_SETTINGS["reminder_mode"]
    normalized["reminder_mode"] = mode

    if mode in PRESET_SETTINGS:
        normalized.update(PRESET_SETTINGS[mode])

    normalized["study_window_start"] = _valid_time(
        normalized.get("study_window_start"),
        DEFAULT_SETTINGS["study_window_start"],
    )
    normalized["study_window_end"] = _valid_time(
        normalized.get("study_window_end"),
        DEFAULT_SETTINGS["study_window_end"],
    )
    normalized["reminder_interval_hours"] = _positive_int(
        normalized.get("reminder_interval_hours"),
        DEFAULT_SETTINGS["reminder_interval_hours"],
    )
    normalized["reminder_interval_minutes"] = _positive_int(
        normalized.get("reminder_interval_minutes"),
        DEFAULT_SETTINGS["reminder_interval_minutes"],
    )
    normalized["snooze_minutes"] = _positive_int(
        normalized.get("snooze_minutes"),
        DEFAULT_SETTINGS["snooze_minutes"],
    )
    normalized["mini_session_card_limit"] = _positive_int(
        normalized.get("mini_session_card_limit"),
        DEFAULT_SETTINGS["mini_session_card_limit"],
    )
    normalized["reminder_enabled"] = _bool_value(normalized.get("reminder_enabled"), True)
    normalized["daily_reminder_enabled"] = _bool_value(
        normalized.get("daily_reminder_enabled"),
        True,
    )
    normalized["quiet_after_target_done"] = _bool_value(
        normalized.get("quiet_after_target_done"),
        True,
    )
    return normalized


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        settings = normalize_settings(DEFAULT_SETTINGS)
        save_settings(settings)
        return settings

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return normalize_settings(json.load(f))
    except Exception as e:
        print(f"Error loading settings: {e}")
        return normalize_settings(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        normalized = normalize_settings(settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")
