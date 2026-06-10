# N4 Flashcard Anki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add N4 flashcard learning with Anki-style spaced repetition to the existing Telegram bot.

**Architecture:** Keep one Telegram bot and one SQLite database. Add isolated flashcard modules for parsing/import, scheduling, persistence, Telegram commands, and daily reminders.

**Tech Stack:** Python 3.11, python-telegram-bot, APScheduler, SQLite, pdfplumber, pytest, Docker for verification.

---

### Task 1: Test Harness and Flashcard Core

**Files:**
- Create: `tests/test_flashcards.py`
- Create: `src/flashcards.py`
- Modify: `requirements.txt`

- [ ] Write failing tests for SM-2 style scheduling, due-before-new selection, and stats.
- [ ] Run `docker compose run --rm bot pytest -q` and confirm missing module/test failure.
- [ ] Implement minimal flashcard core functions and SQLite helpers.
- [ ] Run tests until green.

### Task 2: PDF Importer

**Files:**
- Create: `tests/test_import_n4_pdf.py`
- Create: `tools/import_n4_pdf.py`
- Modify: `requirements.txt`

- [ ] Write failing parser tests for known text sample containing `石`, `経験`, `店員`.
- [ ] Implement parser for PDF-extracted text blocks and idempotent import.
- [ ] Run importer tests until green.

### Task 3: Telegram Handlers

**Files:**
- Create: `tests/test_flashcard_handlers.py`
- Create: `src/flashcard_handlers.py`
- Modify: `src/bot.py`

- [ ] Write failing handler helper tests for front, answer, grade-before-show, no-card messages.
- [ ] Implement command handlers `/flash_start`, `/flash`, `/flash_new`, `/flash_review`, `/flash_stats`, `/show`, `/again`, `/hard`, `/good`, `/easy`.
- [ ] Register handlers in `bot.py`.
- [ ] Run tests until green.

### Task 4: Scheduler and Config

**Files:**
- Create: `tests/test_flashcard_scheduler.py`
- Create: `src/flashcard_scheduler.py`
- Modify: `src/config.py`
- Modify: `src/bot.py`
- Modify: `.env.example`

- [ ] Write failing tests for daily message decision and disabled scheduler config.
- [ ] Implement flashcard config variables and scheduler job.
- [ ] Register daily job in `bot.py` only when enabled.
- [ ] Run tests until green.

### Task 5: Verification

**Files:**
- Modify as needed from failures only.

- [ ] Run `docker compose build`.
- [ ] Run `docker compose run --rm bot pytest -q`.
- [ ] Run `docker compose run --rm bot python tools/import_n4_pdf.py --dry-run`.
- [ ] Run `docker compose run --rm bot python -m py_compile src/bot.py src/flashcards.py src/flashcard_handlers.py src/flashcard_scheduler.py tools/import_n4_pdf.py`.
- [ ] Commit all changes.
