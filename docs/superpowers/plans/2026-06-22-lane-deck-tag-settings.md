# Lane Deck Tag Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/lane_settings`, `/lane_deck`, and `/lane_tags` so each study lane can keep its own deck/tag filters.

**Architecture:** Reuse `user_learning_lane_settings.deck_id` and `tags`; add a backend setter that preserves existing lane quota fields. Add Telegram handlers and register commands. Update docs and tests.

**Tech Stack:** Python 3.11, SQLite, python-telegram-bot, pytest, Docker Compose.

---

## Files

- Modify `src/learning_items.py`: add `set_lane_filter()`.
- Modify `src/flashcard_handlers.py`: add formatting and command handlers.
- Modify `src/bot.py`: register lane setting commands.
- Modify `tests/test_learning_lanes.py`: backend tests for lane deck/tag storage and clearing.
- Modify `tests/test_flashcard_handlers.py`: formatter/help tests.
- Modify `docs/learning-lanes-usage.md`: document workflow.
- Modify `README.md`: command summary.

## Tasks

### Task 1: Backend Lane Filter Setter

- [ ] Add tests to `tests/test_learning_lanes.py` proving `set_lane_filter()` stores `deck_id`, normalizes `tags`, preserves other lane settings, and clears values when passed `None`.
- [ ] Run those tests and confirm they fail because `set_lane_filter()` is missing.
- [ ] Implement `set_lane_filter(telegram_user_id, item_type, *, deck_id=None, tags=None, level=None)` in `src/learning_items.py` using existing `get_lane_settings()` and `set_lane_goal()`.
- [ ] Run `tests/test_learning_lanes.py` and confirm pass.

### Task 2: Handler Commands

- [ ] Add tests to `tests/test_flashcard_handlers.py` for `format_lane_settings()`, help text listing lane commands, and usage strings.
- [ ] Run those tests and confirm they fail.
- [ ] Implement `format_lane_settings()`, `/lane_settings`, `/lane_deck`, and `/lane_tags` in `src/flashcard_handlers.py`.
- [ ] Register commands in `src/bot.py`.
- [ ] Run handler tests and confirm pass.

### Task 3: Docs And Verification

- [ ] Update `docs/learning-lanes-usage.md` and `README.md` with `/lane_settings`, `/lane_deck`, `/lane_tags`.
- [ ] Run full `pytest -q` with bundled Python.
- [ ] Run `py_compile` on changed Python files.

## Self-Review

- Spec coverage: commands, all-clearing, per-lane behavior, help text, tests, docs.
- Placeholder scan: no placeholders.
- Scope check: no per-lane mode/preset changes.

