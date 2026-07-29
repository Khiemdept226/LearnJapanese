import json

import desktop_app.settings_store as settings_store


def test_load_settings_adds_study_reminder_defaults(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_store, "SETTINGS_FILE", str(settings_file))

    settings = settings_store.load_settings()

    assert settings["reminder_mode"] == "workday_balanced"
    assert settings["study_window_start"] == "09:00"
    assert settings["study_window_end"] == "18:00"
    assert settings["reminder_interval_minutes"] == 60
    assert settings["snooze_minutes"] == 15
    assert settings["mini_session_card_limit"] == 8
    assert settings["quiet_after_target_done"] is True
    assert settings["skip_until"] is None
    assert settings["snooze_until"] is None
    assert settings["last_reminder_at"] is None
    assert settings["last_mini_session_completed_at"] is None


def test_apply_preset_updates_effective_values():
    settings = settings_store.apply_reminder_preset({"reminder_mode": "jlpt_sprint"})

    assert settings["reminder_mode"] == "jlpt_sprint"
    assert settings["study_window_start"] == "09:00"
    assert settings["study_window_end"] == "22:00"
    assert settings["reminder_interval_minutes"] == 45
    assert settings["snooze_minutes"] == 15
    assert settings["mini_session_card_limit"] == 12


def test_normalize_settings_repairs_invalid_values():
    raw = {
        "reminder_mode": "unknown",
        "study_window_start": "bad",
        "study_window_end": "25:99",
        "reminder_interval_minutes": "0",
        "snooze_minutes": "-3",
        "mini_session_card_limit": "abc",
        "quiet_after_target_done": "yes",
    }

    settings = settings_store.normalize_settings(raw)

    assert settings["reminder_mode"] == "workday_balanced"
    assert settings["study_window_start"] == "09:00"
    assert settings["study_window_end"] == "18:00"
    assert settings["reminder_interval_minutes"] == 60
    assert settings["snooze_minutes"] == 15
    assert settings["mini_session_card_limit"] == 8
    assert settings["quiet_after_target_done"] is True


def test_save_settings_persists_normalized_json(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_store, "SETTINGS_FILE", str(settings_file))

    settings_store.save_settings({"reminder_mode": "gentle", "reminder_interval_minutes": 120})

    saved = json.loads(settings_file.read_text(encoding="utf-8"))
    assert saved["reminder_mode"] == "gentle"
    assert saved["study_window_start"] == "18:00"
    assert saved["study_window_end"] == "22:00"
    assert saved["reminder_interval_minutes"] == 120
