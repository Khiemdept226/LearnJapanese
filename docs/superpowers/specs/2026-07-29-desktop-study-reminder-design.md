# Desktop Study Reminder Design

## Goal

Improve the desktop app's learning reminders so it helps the user study during workday gaps, especially while waiting for AI tasks, without becoming noisy. The first version should use good defaults plus user customization. It should prepare the app for smarter adaptive reminders later, but avoid unnecessary complexity now.

## Current State

The project already has:

- A Telegram bot for daily lessons and flashcards.
- A desktop app using `customtkinter`.
- SQLite-backed learning items and SRS state.
- Desktop reminder settings in `desktop_app/settings.json`.
- A scheduler loop in `desktop_app/main.py` that checks every 30 seconds.
- Reminder controls in `desktop_app/gui/settings_frame.py`.

Current desktop reminders are coarse:

- Daily lesson notification at `DAILY_SEND_TIME`.
- Daily flashcard notification at `FLASHCARD_DAILY_TIME`.
- Periodic review notification every configured number of hours.

The missing part is a workday-oriented study reminder mode with presets, snooze, quiet periods, mini-session limits, and target-aware behavior.

## Non-Goals

- Do not change the Telegram bot reminder behavior.
- Do not add a new SQLite schema for this version.
- Do not build a full adaptive ML scheduler.
- Do not change learning item SRS grading rules.
- Do not require the app to run when the computer is off or the desktop app is closed.

## Recommended Approach

Use preset-based reminders with custom overrides.

This keeps the app easy to use while still letting the user tune reminder frequency, study window, snooze length, and mini-session size. It is a better first step than a fully adaptive system because the existing app already has simple JSON settings and a scheduler loop.

## Reminder Modes

Add `reminder_mode` with these values:

| Mode | Window | Interval | Snooze | Mini-session | Intended use |
|---|---:|---:|---:|---:|---|
| `workday_balanced` | 09:00-18:00 | 60 min | 15 min | 8 cards | Default. Workday study during short gaps. |
| `jlpt_sprint` | 09:00-22:00 | 45 min | 15 min | 12 cards | Aggressive study before exam. |
| `gentle` | 18:00-22:00 | 120 min | 30 min | 5 cards | Low-pressure habit support. |
| `custom` | user setting | user setting | user setting | user setting | Fully user-tuned. |

Default mode should be `workday_balanced`.

## Settings Data

Extend `desktop_app/settings.json` with these keys:

```json
{
  "reminder_mode": "workday_balanced",
  "study_window_start": "09:00",
  "study_window_end": "18:00",
  "reminder_interval_minutes": 60,
  "snooze_minutes": 15,
  "mini_session_card_limit": 8,
  "quiet_after_target_done": true,
  "skip_until": null,
  "snooze_until": null,
  "last_reminder_at": null,
  "last_studied_at": null,
  "last_mini_session_completed_at": null
}
```

Preset modes should write these effective values into settings when selected. Custom mode should keep the user's edited values.

Datetime values should use ISO strings in local time. Missing or invalid values should fall back to safe defaults.

## Reminder Decision Logic

The scheduler should decide whether to show a study reminder in this order:

1. Desktop app is running.
2. Reminder feature is enabled.
3. Current time is inside the configured study window.
4. Current time is not before `skip_until`.
5. Current time is not before `snooze_until`.
6. User has due cards or new cards matching current learning filters.
7. If `quiet_after_target_done` is true and today's target is complete, do not notify.
8. If the user completed a mini-session recently, wait at least `reminder_interval_minutes`.
9. If enough time has passed since `last_reminder_at`, show notification.

The scheduler should keep checking every 30 seconds, but it should not notify more than once per decision window.

## Target-Aware Behavior

For version 1, target completion can be approximated from existing learning stats and settings:

- If `due == 0` and `new == 0`, do not notify.
- If due cards exist, prioritize review in notification copy.
- If no due cards exist but new cards exist, invite the user to learn new cards.
- If a mini-session was completed and `quiet_after_target_done` is true, stay quiet until the next interval unless due cards remain.

Exact per-day target accounting can be improved later if existing stats cannot reliably answer "done today."

## Notification Copy

Notifications should be short and action-oriented:

- Due cards: `Con 8 the can on. Hoc 5 phut nhe?`
- New cards only: `Con the moi de hoc. Lam 1 phien ngan nhe?`
- Sprint mode: `JLPT sprint: con 18 the. Tranh thu luc doi AI nhe.`

Keep desktop notification text ASCII-safe in code if the current encoding problem is not fixed in the same implementation. If Vietnamese Unicode is fixed first, use proper Vietnamese text.

## App Actions

Add reminder action controls in the app UI:

- `Hoc ngay`: switch to Flashcards tab and load the next card.
- `Nhac sau 15 phut`: set `snooze_until`.
- `Bo qua hom nay`: set `skip_until` to the end of the current day.

If native notification action buttons are not reliable through `pystray`, implement these controls inside the Settings or Flashcards tab first. The notification can tell the user to open the app.

## Settings UI

Add a `Study Reminder Mode` section in `desktop_app/gui/settings_frame.py`.

Controls:

- Mode dropdown: `Workday Balanced`, `JLPT Sprint`, `Gentle`, `Custom`.
- Start time input.
- End time input.
- Reminder interval minutes dropdown or entry.
- Snooze minutes dropdown or entry.
- Mini-session card limit dropdown or entry.
- Toggle: quiet after target done.
- Buttons: save settings, snooze, skip today.

When the user selects a preset, fields should update to the preset values. Editing any preset field should switch mode to `Custom`.

## Flashcard Session Behavior

The flashcard UI should count cards graded in the current mini-session.

- Start count when the user clicks `Hoc ngay` or starts loading cards manually.
- Increment when a card is graded.
- When count reaches `mini_session_card_limit`, show a short completion message.
- Set `last_mini_session_completed_at`.
- Do not block the user from continuing.

This keeps the app encouraging without forcing a hard stop.

## Error Handling

- Invalid time strings fall back to preset defaults.
- Negative or zero interval values fall back to default values.
- Corrupt `settings.json` falls back to defaults and rewrites on next save.
- If stats lookup fails, log the error and skip reminder for that scheduler tick.
- If notification fails, keep the app running.

## Testing

Add focused tests where possible:

- Settings defaults include new reminder keys.
- Preset selection maps to expected effective values.
- Invalid time and interval values fall back safely.
- Reminder decision suppresses notifications outside window.
- Reminder decision suppresses notifications during snooze and skip.
- Reminder decision notifies when due cards exist and interval has passed.
- Mini-session completion records `last_mini_session_completed_at`.

If GUI behavior is hard to test directly, isolate reminder decisions into a small pure module so tests can cover the rules without rendering `customtkinter`.

## Implementation Shape

Prefer adding a small reminder policy module instead of growing `desktop_app/main.py`.

Suggested boundaries:

- `desktop_app/settings_store.py`: defaults, preset values, load/save normalization.
- `desktop_app/study_reminders.py`: pure reminder decision logic.
- `desktop_app/main.py`: scheduler loop calls policy and sends notifications.
- `desktop_app/gui/settings_frame.py`: controls for mode and custom values.
- `desktop_app/gui/flashcard_frame.py`: mini-session count and completion marker.

This keeps scheduling, settings, and UI responsibilities separated.

## Rollout

1. Add settings defaults and pure reminder policy.
2. Wire scheduler to policy.
3. Add Settings UI controls.
4. Add Flashcards mini-session tracking.
5. Add tests for policy/settings.
6. Run compile and targeted tests.

## Open Risks

- Current desktop app has Vietnamese mojibake in several files. Reminder copy may need to stay ASCII-safe unless that is fixed as part of implementation.
- `pystray` notifications may not support reliable action buttons. In-app buttons should be treated as the reliable path.
- The app uses a local desktop user id `1`; this is acceptable for this desktop app version but should stay explicit.
