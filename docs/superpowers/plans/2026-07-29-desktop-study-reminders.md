# Desktop Study Reminders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add preset plus custom desktop study reminders that help the user study during workday gaps without noisy repeated notifications.

**Architecture:** Keep reminder configuration in `desktop_app/settings_store.py`, put pure decision logic in a new `desktop_app/study_reminders.py`, and keep `desktop_app/main.py` responsible only for polling stats and sending notifications. Settings UI edits live in `desktop_app/gui/settings_frame.py`; mini-session state lives in `desktop_app/gui/flashcard_frame.py`.

**Tech Stack:** Python 3.11, `customtkinter`, `pystray`, SQLite-backed `learning_items`, pytest.

---

## File Structure

- Modify `desktop_app/settings_store.py`: add preset defaults, normalization, preset application, timestamp helpers, and safe save behavior.
- Create `desktop_app/study_reminders.py`: pure reminder policy functions that take settings, stats, and `now`, then return a decision.
- Modify `desktop_app/main.py`: replace ad hoc periodic reminder checks with policy calls and notification state updates.
- Modify `desktop_app/gui/settings_frame.py`: add reminder mode controls, custom fields, snooze, and skip-today controls.
- Modify `desktop_app/gui/flashcard_frame.py`: count graded cards in a mini-session and record completion.
- Modify `desktop_app/gui/main_window.py`: expose small methods to switch to the Flashcards tab when `Hoc ngay` is clicked.
- Create `tests/test_desktop_settings_store.py`: cover defaults, presets, and normalization.
- Create `tests/test_desktop_study_reminders.py`: cover reminder decision behavior.

---

### Task 1: Settings Defaults And Presets

**Files:**
- Modify: `desktop_app/settings_store.py`
- Create: `tests/test_desktop_settings_store.py`

- [ ] **Step 1: Write failing settings tests**

Create `tests/test_desktop_settings_store.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_settings_store.py -q
```

Expected: failure because `apply_reminder_preset` and `normalize_settings` do not exist.

- [ ] **Step 3: Implement settings defaults and normalization**

Update `desktop_app/settings_store.py` with these structures and helpers:

```python
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
    normalized["quiet_after_target_done"] = bool(normalized.get("quiet_after_target_done", True))
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
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_settings_store.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit settings changes**

Run:

```powershell
git add desktop_app/settings_store.py tests/test_desktop_settings_store.py
git commit -m "feat: add desktop reminder settings presets"
```

---

### Task 2: Pure Study Reminder Policy

**Files:**
- Create: `desktop_app/study_reminders.py`
- Create: `tests/test_desktop_study_reminders.py`

- [ ] **Step 1: Write failing policy tests**

Create `tests/test_desktop_study_reminders.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_study_reminders.py -q
```

Expected: failure because `desktop_app.study_reminders` does not exist.

- [ ] **Step 3: Implement reminder policy**

Create `desktop_app/study_reminders.py`:

```python
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
        return ("Den gio on tap", f"Con {due} the can on. Hoc 5 phut nhe?", "due_available")

    return ("The moi dang cho", f"Con {new} the moi. Lam 1 phien ngan nhe?", "new_available")


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
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_study_reminders.py -q
```

Expected: `8 passed`.

- [ ] **Step 5: Commit policy changes**

Run:

```powershell
git add desktop_app/study_reminders.py tests/test_desktop_study_reminders.py
git commit -m "feat: add desktop study reminder policy"
```

---

### Task 3: Wire Scheduler To Reminder Policy

**Files:**
- Modify: `desktop_app/main.py`

- [ ] **Step 1: Refactor imports and helper methods**

Update `desktop_app/main.py`:

```python
import study_reminders


class DesktopApp:
    ...
    def _learning_filters(self):
        settings = get_user_settings(1)
        return {
            "level": settings.get("level"),
            "item_type": settings.get("item_type"),
            "deck_id": settings.get("deck_id"),
            "tags": settings.get("tags"),
        }

    def _learning_stats(self):
        return get_learning_stats(1, **self._learning_filters())

    def _save_desktop_setting(self, key, value):
        config = settings_store.load_settings()
        config[key] = value
        settings_store.save_settings(config)
```

- [ ] **Step 2: Replace periodic review notification block**

Replace the current `# 3. Periodic Review Notifications` block in `scheduler_loop` with:

```python
            if config.get("reminder_enabled", True):
                try:
                    stats = self._learning_stats()
                    decision = study_reminders.should_send_study_reminder(config, stats, now)
                    if decision.should_notify:
                        self.show_notification(decision.title, decision.message)
                        self._save_desktop_setting("last_reminder_at", now.replace(microsecond=0).isoformat())
                except Exception as e:
                    print(f"Study reminder check failed: {e}")
```

Keep daily lesson and daily flashcard reminders unchanged for this task.

- [ ] **Step 3: Compile desktop app files**

Run:

```powershell
.\.portable_python\python.exe -m py_compile desktop_app\main.py desktop_app\study_reminders.py desktop_app\settings_store.py
```

Expected: no output and exit code `0`.

- [ ] **Step 4: Run desktop reminder tests**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_settings_store.py tests\test_desktop_study_reminders.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit scheduler changes**

Run:

```powershell
git add desktop_app/main.py
git commit -m "feat: wire desktop scheduler to study reminders"
```

---

### Task 4: Settings UI For Presets And Custom Values

**Files:**
- Modify: `desktop_app/gui/settings_frame.py`

- [ ] **Step 1: Add mode labels and preset mapping near imports**

Add:

```python
MODE_LABELS = {
    "Workday Balanced": "workday_balanced",
    "JLPT Sprint": "jlpt_sprint",
    "Gentle": "gentle",
    "Custom": "custom",
}
MODE_NAMES = {value: label for label, value in MODE_LABELS.items()}
```

- [ ] **Step 2: Add UI variables**

In `__init__`, before reminder controls:

```python
        self.reminder_mode_var = ctk.StringVar(value="Workday Balanced")
        self.study_window_start_var = ctk.StringVar(value="09:00")
        self.study_window_end_var = ctk.StringVar(value="18:00")
        self.reminder_interval_minutes_var = ctk.StringVar(value="60")
        self.snooze_minutes_var = ctk.StringVar(value="15")
        self.mini_session_card_limit_var = ctk.StringVar(value="8")
        self.quiet_after_target_done_var = ctk.BooleanVar(value=True)
```

- [ ] **Step 3: Add controls to reminder frame**

In the reminder frame, after the existing daily reminder checkbox:

```python
        mode_row = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(mode_row, text="Che do nhac:", anchor="w").pack(side="left")
        self.reminder_mode_dropdown = ctk.CTkComboBox(
            mode_row,
            values=list(MODE_LABELS.keys()),
            variable=self.reminder_mode_var,
            command=self.on_reminder_mode_changed,
            width=160,
        )
        self.reminder_mode_dropdown.pack(side="right")

        self._add_reminder_entry("Bat dau:", self.study_window_start_var)
        self._add_reminder_entry("Ket thuc:", self.study_window_end_var)
        self._add_reminder_entry("Moi lan nhac (phut):", self.reminder_interval_minutes_var)
        self._add_reminder_entry("Nhac lai sau (phut):", self.snooze_minutes_var)
        self._add_reminder_entry("So the/phien ngan:", self.mini_session_card_limit_var)

        self.quiet_after_target_cb = ctk.CTkCheckBox(
            self.reminder_frame,
            text="Im khi xong muc tieu hom nay",
            variable=self.quiet_after_target_done_var,
        )
        self.quiet_after_target_cb.pack(pady=5, anchor="w", padx=20)

        action_row = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(action_row, text="Nhac sau 15 phut", command=self.snooze_now).pack(side="left", padx=5)
        ctk.CTkButton(action_row, text="Bo qua hom nay", command=self.skip_today).pack(side="left", padx=5)
```

- [ ] **Step 4: Add UI helper methods**

Add methods inside `SettingsFrame`:

```python
    def _add_reminder_entry(self, label_text, var):
        frame = ctk.CTkFrame(self.reminder_frame, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(frame, textvariable=var, width=100).pack(side="right")

    def on_reminder_mode_changed(self, _choice=None):
        mode = MODE_LABELS.get(self.reminder_mode_var.get(), "workday_balanced")
        settings = settings_store.load_settings()
        settings["reminder_mode"] = mode
        settings = settings_store.apply_reminder_preset(settings)
        self._set_reminder_fields(settings)

    def _set_reminder_fields(self, settings):
        self.reminder_mode_var.set(MODE_NAMES.get(settings.get("reminder_mode"), "Workday Balanced"))
        self.study_window_start_var.set(settings.get("study_window_start", "09:00"))
        self.study_window_end_var.set(settings.get("study_window_end", "18:00"))
        self.reminder_interval_minutes_var.set(str(settings.get("reminder_interval_minutes", 60)))
        self.snooze_minutes_var.set(str(settings.get("snooze_minutes", 15)))
        self.mini_session_card_limit_var.set(str(settings.get("mini_session_card_limit", 8)))
        self.quiet_after_target_done_var.set(bool(settings.get("quiet_after_target_done", True)))
```

- [ ] **Step 5: Update load and save reminders**

In `load_settings`, after loading `rem_settings`:

```python
        self._set_reminder_fields(rem_settings)
```

Replace `save_reminders` settings payload with:

```python
            rem_settings = settings_store.load_settings()
            rem_settings.update({
                "reminder_enabled": self.reminder_enabled_var.get(),
                "daily_reminder_enabled": self.daily_reminder_enabled_var.get(),
                "reminder_interval_hours": hours,
                "reminder_mode": MODE_LABELS.get(self.reminder_mode_var.get(), "workday_balanced"),
                "study_window_start": self.study_window_start_var.get(),
                "study_window_end": self.study_window_end_var.get(),
                "reminder_interval_minutes": self.reminder_interval_minutes_var.get(),
                "snooze_minutes": self.snooze_minutes_var.get(),
                "mini_session_card_limit": self.mini_session_card_limit_var.get(),
                "quiet_after_target_done": self.quiet_after_target_done_var.get(),
            })
            settings_store.save_settings(rem_settings)
```

- [ ] **Step 6: Add snooze and skip actions**

Add import near top:

```python
import datetime
from desktop_app import study_reminders
```

Add methods:

```python
    def snooze_now(self):
        settings = settings_store.load_settings()
        settings["snooze_until"] = study_reminders.snooze_until(settings, datetime.datetime.now())
        settings_store.save_settings(settings)
        self.sync_status.configure(text="Da nhac lai sau theo thoi gian snooze.")

    def skip_today(self):
        settings = settings_store.load_settings()
        settings["skip_until"] = study_reminders.skip_until_end_of_day(datetime.datetime.now())
        settings_store.save_settings(settings)
        self.sync_status.configure(text="Da bo qua nhac hoc den het hom nay.")
```

- [ ] **Step 7: Compile settings UI**

Run:

```powershell
.\.portable_python\python.exe -m py_compile desktop_app\gui\settings_frame.py
```

Expected: no output and exit code `0`.

- [ ] **Step 8: Commit UI settings changes**

Run:

```powershell
git add desktop_app/gui/settings_frame.py
git commit -m "feat: add study reminder settings UI"
```

---

### Task 5: Flashcard Mini-Session Tracking

**Files:**
- Modify: `desktop_app/gui/main_window.py`
- Modify: `desktop_app/gui/flashcard_frame.py`

- [ ] **Step 1: Add tab navigation method**

In `desktop_app/gui/main_window.py`, add method to `AppWindow`:

```python
    def show_flashcards(self):
        self.tabview.set("Flashcards")
        self.flashcard_frame.load_next_card()
```

- [ ] **Step 2: Add mini-session fields**

In `FlashcardFrame.__init__`, after `self.current_card = None`:

```python
        self.session_count = 0
        self.session_limit = 8
        self.session_status = ctk.CTkLabel(self, text="")
        self.session_status.pack(pady=(0, 10))
```

- [ ] **Step 3: Load session limit from settings**

Add imports:

```python
from desktop_app import settings_store
```

Add method:

```python
    def _load_session_limit(self):
        settings = settings_store.load_settings()
        try:
            self.session_limit = int(settings.get("mini_session_card_limit", 8))
        except (TypeError, ValueError):
            self.session_limit = 8
```

Call `_load_session_limit()` at the start of `load_next_card`.

- [ ] **Step 4: Record mini-session completion**

Add imports:

```python
import datetime
```

Update `grade_card`:

```python
    def grade_card(self, grade):
        updated, error = learning_items.grade_current_item(LOCAL_USER_ID, grade)
        if error:
            print(f"Error grading card: {error}")
        else:
            self.session_count += 1
            self._record_session_progress()
        self.load_next_card()

    def _record_session_progress(self):
        if self.session_count < self.session_limit:
            self.session_status.configure(text=f"Phien ngan: {self.session_count}/{self.session_limit} the")
            return

        settings = settings_store.load_settings()
        settings["last_mini_session_completed_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
        settings["last_studied_at"] = settings["last_mini_session_completed_at"]
        settings_store.save_settings(settings)
        self.session_status.configure(text="Da xong 1 phien ngan. Co the nghi mot chut.")
        self.session_count = 0
```

- [ ] **Step 5: Compile flashcard UI**

Run:

```powershell
.\.portable_python\python.exe -m py_compile desktop_app\gui\main_window.py desktop_app\gui\flashcard_frame.py
```

Expected: no output and exit code `0`.

- [ ] **Step 6: Commit mini-session changes**

Run:

```powershell
git add desktop_app/gui/main_window.py desktop_app/gui/flashcard_frame.py
git commit -m "feat: track desktop flashcard mini sessions"
```

---

### Task 6: Verification And Cleanup

**Files:**
- Check: `desktop_app/main.py`
- Check: `desktop_app/settings_store.py`
- Check: `desktop_app/study_reminders.py`
- Check: `desktop_app/gui/settings_frame.py`
- Check: `desktop_app/gui/flashcard_frame.py`
- Check: `tests/test_desktop_settings_store.py`
- Check: `tests/test_desktop_study_reminders.py`

- [ ] **Step 1: Run desktop compile check**

Run:

```powershell
.\.portable_python\python.exe -m py_compile desktop_app\main.py desktop_app\settings_store.py desktop_app\study_reminders.py desktop_app\gui\main_window.py desktop_app\gui\settings_frame.py desktop_app\gui\flashcard_frame.py
```

Expected: no output and exit code `0`.

- [ ] **Step 2: Run targeted desktop tests**

Run:

```powershell
.\.portable_python\python.exe -m pytest tests\test_desktop_settings_store.py tests\test_desktop_study_reminders.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run full test suite if runtime allows**

Run:

```powershell
.\.portable_python\python.exe -m pytest -q
```

Expected: all tests pass. If environment-specific Google Sheet credential tests fail, record the exact failing tests and run the non-network/unit subset that covers desktop changes.

- [ ] **Step 4: Scan for mojibake in newly touched reminder text**

Run:

```powershell
rg -n "Con |Hoc |Nhac |Bo qua|Phien ngan|Da xong|JLPT sprint" desktop_app/settings_store.py desktop_app/study_reminders.py desktop_app/main.py desktop_app/gui/settings_frame.py desktop_app/gui/flashcard_frame.py
```

Expected: newly added reminder text stays ASCII-safe until Vietnamese Unicode cleanup is handled separately.

- [ ] **Step 5: Check git status**

Run:

```powershell
git status --short
```

Expected: only intended source/test changes plus existing runtime DB dirty state if it still exists.

- [ ] **Step 6: Commit final cleanup if needed**

If verification required small fixes, commit them:

```powershell
git add desktop_app tests
git commit -m "fix: polish desktop study reminders"
```

---

## Self-Review Notes

- Spec coverage: settings presets, custom values, scheduler policy, in-app snooze/skip controls, mini-session counting, error handling, and tests all map to tasks.
- Placeholder scan: all implementation steps include concrete file paths, code snippets, commands, and expected results.
- Type consistency: setting keys match the design spec and repeat consistently across tests, policy, UI, and scheduler tasks.
