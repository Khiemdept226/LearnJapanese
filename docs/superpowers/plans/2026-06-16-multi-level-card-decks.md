# Learning Items Deck Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the N4-only vocabulary flashcard storage with a long-term `learning_items` model that supports levels, item types, decks, and tag filters while preserving current vocab progress through migration.

**Architecture:** Create new canonical tables (`decks`, `learning_items`, `user_learning_reviews`, `user_learning_sessions`, `user_learning_settings`) and migrate legacy `flashcards` data into them. Keep legacy tables during rollout as fallback; move import, SRS picking, stats, sessions, and handlers to the new model.

**Tech Stack:** Python 3.11, SQLite, python-telegram-bot, gspread, pytest, Docker Compose.

---

## Design Decision

Use a new clean model, not extra columns on `flashcards`.

Old tables stay temporarily:

```text
flashcards
user_flashcard_reviews
user_flashcard_sessions
user_flashcard_settings
```

New canonical tables:

```text
decks
learning_items
user_learning_reviews
user_learning_sessions
user_learning_settings
```

Do not drop old tables in this plan.

## Google Sheet Changes Required

Use one spreadsheet from `GOOGLE_SHEET_ID`. Keep the current daily lesson sheet as-is. Add these worksheets for the long-term learning item system.

### `deck_catalog`

Create worksheet: `deck_catalog`

Columns:

```text
deck_id
title
level
item_type
worksheet_name
source
status
description
```

Example rows:

```text
n4_vocab_core | N4 Core Vocabulary | N4 | vocab | vocab_n4_core | manual | active | Core N4 vocabulary
n4_kanji_core | N4 Core Kanji | N4 | kanji | kanji_n4_core | manual | active | Core N4 kanji
n4_grammar_core | N4 Core Grammar | N4 | grammar | grammar_n4_core | manual | active | Core N4 grammar
n4_kaiwa_daily | N4 Daily Kaiwa | N4 | kaiwa | kaiwa_n4_daily | manual | active | Daily N4 conversation
```

Rules:

- `deck_id` is stable and unique.
- `status=active` means importer reads the deck.
- `worksheet_name` must match another worksheet in the same spreadsheet.

### `vocab_n4_core`

Create worksheet: `vocab_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
word
reading
meaning
hanviet
example_jp
example_vi
tags
status
```

Rules:

- `item_id` required, stable, example `N4-VOCAB-0001`.
- `deck_id` should be `n4_vocab_core`.
- `status=ready` means import.
- `tags` comma-separated, example `noun,material,lesson-01`.

### `kanji_n4_core`

Create worksheet: `kanji_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
kanji
onyomi
kunyomi
hanviet
meaning
examples
tags
status
```

Rules:

- `item_id` required, stable, example `N4-KANJI-0001`.
- `kanji` becomes item front.
- `onyomi`, `kunyomi`, `examples` go into `extra_json`.

### `grammar_n4_core`

Create worksheet: `grammar_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
pattern
meaning
usage
example_jp
example_vi
tags
status
```

Rules:

- `item_id` required, stable, example `N4-GRAMMAR-0001`.
- `pattern` becomes item front.
- `usage` goes into `extra_json`.

### `kaiwa_n4_daily`

Create worksheet: `kaiwa_n4_daily`

Columns:

```text
item_id
level
deck_id
source_position
title
dialogue_jp
dialogue_vi
vocab
grammar
shadowing
quiz
quiz_answer
tags
status
```

Rules:

- `item_id` required, stable, example `N4-KAIWA-0001`.
- `title` becomes item front.
- dialogue, vocab, grammar, shadowing, quiz, and answer go into `extra_json`.

### Legacy `flashcards`

Keep the existing `flashcards` worksheet for fallback during migration. New data should move to per-deck worksheets.

## Database Target

`decks` columns:

```text
deck_id PRIMARY KEY
title
level
item_type
worksheet_name
source
status
description
created_at
updated_at
```

`learning_items` columns:

```text
id PRIMARY KEY
item_id
level
item_type
deck_id
source
source_position
front
back
reading
meaning
hanviet
example_jp
example_vi
tags
extra_json
status
created_at
updated_at
UNIQUE(deck_id, item_id)
```

`user_learning_reviews` mirrors current SRS fields but uses `learning_item_id` instead of `flashcard_id`.

`user_learning_sessions` stores current `learning_item_id` for a user.

`user_learning_settings` stores selected `level`, `item_type`, `deck_id`, and `tags`, plus existing daily limits/preset fields.

## Files

- Create `src/learning_items.py`: canonical DB, migration, SRS, stats, settings.
- Create `src/learning_sources/__init__.py`.
- Create `src/learning_sources/normalizers.py`: normalize vocab/kanji/grammar/kaiwa rows.
- Create `src/learning_sources/deck_catalog.py`: parse/load `deck_catalog`.
- Create `src/learning_sources/sheet_source.py`: load all active deck worksheets.
- Create `tools/migrate_flashcards_to_learning_items.py`: one-time legacy migration helper.
- Modify `tools/import_flashcards.py`: import into `learning_items`, keep legacy fallback.
- Modify `src/flashcard_handlers.py`: use `learning_items` while keeping existing `/flash*` commands.
- Modify `src/flashcard_scheduler.py`: use learning item settings and pickers.
- Modify `src/bot.py`: register study selection commands.
- Update docs and `.env.example`.

---

### Task 1: Create Learning Items Schema

**Files:**
- Create: `src/learning_items.py`
- Create: `tests/test_learning_items_schema.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_learning_items_schema.py`:

```python
import learning_items

def test_init_learning_db_creates_core_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    tables = learning_items.list_tables()
    assert {"decks", "learning_items", "user_learning_reviews", "user_learning_sessions", "user_learning_settings"}.issubset(tables)

def test_upsert_learning_item_uses_deck_item_identity(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    first_id = learning_items.upsert_learning_item({"item_id": "N4-VOCAB-0001", "level": "N4", "item_type": "vocab", "deck_id": "n4_vocab_core", "source": "sheet", "source_position": 1, "front": "ishi", "reading": "ishi", "meaning": "stone", "tags": "noun,material", "status": "ready"})
    second_id = learning_items.upsert_learning_item({"item_id": "N4-VOCAB-0001", "level": "N4", "item_type": "vocab", "deck_id": "n4_vocab_core", "source": "sheet", "source_position": 9, "front": "ishi", "reading": "ishi", "meaning": "stone updated", "tags": "noun", "status": "ready"})
    item = learning_items.get_learning_item(first_id)
    assert second_id == first_id
    assert item["source_position"] == 9
    assert item["meaning"] == "stone updated"
```

- [ ] **Step 2: Verify failure**

```powershell
docker compose run --rm bot pytest tests/test_learning_items_schema.py -q
```

Expected: FAIL because `learning_items.py` does not exist.

- [ ] **Step 3: Implement `src/learning_items.py`**

Implement:

- `get_connection()` using `DATABASE_PATH`.
- `init_learning_db()` creating all new tables and indexes.
- `list_tables()` for tests.
- `normalize_tags(tags)`.
- `normalize_extra(extra)`.
- `upsert_learning_item(row)` using `UNIQUE(deck_id, item_id)`.
- `upsert_learning_items(rows)`.
- `get_learning_item(id)`.
- `find_learning_item(deck_id, item_id)`.

- [ ] **Step 4: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_learning_items_schema.py -q
git add src/learning_items.py tests/test_learning_items_schema.py
git commit -m "feat: add learning items schema"
```

Expected: PASS.

---

### Task 2: Migrate Legacy Flashcards

**Files:**
- Modify: `src/learning_items.py`
- Create: `tools/migrate_flashcards_to_learning_items.py`
- Create: `tests/test_learning_items_migration.py`

- [ ] **Step 1: Write migration test**

Create `tests/test_learning_items_migration.py`:

```python
import flashcards
import learning_items

def test_migrate_flashcards_copies_vocab_and_reviews(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()
    card_id = flashcards.upsert_flashcard("N4", "n4_pdf", 1, "ishi", "ishi", "stone", "Thach", "example", "translation")
    flashcards.ensure_user_review(123, card_id)
    summary = learning_items.migrate_legacy_flashcards(default_deck_id="n4_vocab_core")
    assert summary["items"] == 1
    assert summary["reviews"] == 1
    item = learning_items.find_learning_item("n4_vocab_core", "legacy-flashcard-1")
    assert item["item_type"] == "vocab"
    assert item["front"] == "ishi"
```

- [ ] **Step 2: Implement migration**

Add `migrate_legacy_flashcards(default_deck_id="n4_vocab_core")` to `src/learning_items.py`.

Map old card fields:

- `item_id = legacy-flashcard-{old.id}`.
- `item_type = vocab`.
- `deck_id = default_deck_id`.
- `front = old.word`.
- `back = old.meaning`.
- `reading`, `meaning`, `hanviet`, `example_jp`, `example_vi` copied directly.
- `tags = legacy,vocab`.

Copy progress:

- `user_flashcard_reviews` -> `user_learning_reviews`.
- `user_flashcard_sessions` -> `user_learning_sessions`.
- `user_flashcard_settings` -> `user_learning_settings` with `item_type=vocab`, `deck_id=default_deck_id`.

- [ ] **Step 3: Add migration CLI**

Create `tools/migrate_flashcards_to_learning_items.py`:

```python
import argparse
import learning_items

def main(argv=None):
    parser = argparse.ArgumentParser(description="Migrate legacy flashcards into learning_items.")
    parser.add_argument("--default-deck-id", default="n4_vocab_core")
    args = parser.parse_args(argv)
    summary = learning_items.migrate_legacy_flashcards(default_deck_id=args.default_deck_id)
    for key, value in summary.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_learning_items_migration.py -q
git add src/learning_items.py tools/migrate_flashcards_to_learning_items.py tests/test_learning_items_migration.py
git commit -m "feat: migrate flashcards to learning items"
```

Expected: PASS.

---

### Task 3: Load Sheet Decks Into Learning Items

**Files:**
- Create: `src/learning_sources/__init__.py`
- Create: `src/learning_sources/normalizers.py`
- Create: `src/learning_sources/deck_catalog.py`
- Create: `src/learning_sources/sheet_source.py`
- Create: `tests/test_learning_source_normalizers.py`
- Create: `tests/test_learning_deck_catalog.py`

- [ ] **Step 1: Write tests**

Create tests covering:

- `vocab` row -> `front=word`.
- `kanji` row -> `front=kanji`, `extra_json` has `onyomi`, `kunyomi`, `examples`.
- `grammar` row -> `front=pattern`, `extra_json` has `usage`.
- `kaiwa` row -> `front=title`, `back=dialogue_jp`, `extra_json` has dialogue/shadowing/quiz.
- `deck_catalog` parser only returns `status=active` decks.

- [ ] **Step 2: Implement normalizers and catalog loader**

Implement:

- `learning_sources.normalizers.normalize_row(row, item_type, level, deck_id, source)`.
- `learning_sources.deck_catalog.DeckConfig`.
- `learning_sources.deck_catalog.parse_deck_catalog(records)`.
- `learning_sources.sheet_source.load_deck_catalog(sheet_id=None)`.
- `learning_sources.sheet_source.load_items_for_deck(deck, sheet_id=None)`.
- `learning_sources.sheet_source.load_all_active_decks(sheet_id=None)`.

- [ ] **Step 3: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_learning_source_normalizers.py tests/test_learning_deck_catalog.py -q
git add src/learning_sources tests/test_learning_source_normalizers.py tests/test_learning_deck_catalog.py
git commit -m "feat: load learning items from deck sheets"
```

Expected: PASS.

---

### Task 4: Import Into `learning_items`

**Files:**
- Modify: `tools/import_flashcards.py`
- Create: `tests/test_import_learning_items.py`

- [ ] **Step 1: Write import test**

Create `tests/test_import_learning_items.py`:

```python
import tools.import_flashcards as importer

def test_import_all_decks_writes_learning_items(monkeypatch):
    rows = [{"item_id": "N4-VOCAB-0001", "level": "N4", "item_type": "vocab", "deck_id": "n4_vocab_core", "source": "sheet", "source_position": 1, "front": "ishi", "meaning": "stone", "status": "ready"}]
    monkeypatch.setattr(importer.learning_sheet_source, "load_all_active_decks", lambda: rows)
    written = {}
    monkeypatch.setattr(importer.learning_items, "upsert_learning_items", lambda items: written.setdefault("items", items) or len(items))
    summary = importer.run_learning_import(all_decks=True, dry_run=False)
    assert summary["imported"] == 1
    assert written["items"] == rows
```

- [ ] **Step 2: Update CLI**

Modify `tools/import_flashcards.py`:

- Keep legacy `--source sheet|pdf`.
- Add `--model legacy|learning`.
- Add `--all-decks` for learning model.
- Add `run_learning_import(all_decks=False, dry_run=False)`.

Commands:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks --dry-run
docker compose run --rm bot python tools/import_flashcards.py --model legacy --source sheet --dry-run
```

- [ ] **Step 3: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_import_learning_items.py tests/test_import_flashcards.py -q
git add tools/import_flashcards.py tests/test_import_learning_items.py
git commit -m "feat: import deck sheets into learning items"
```

Expected: PASS.

---

### Task 5: Switch Study Flow To `learning_items`

**Files:**
- Modify: `src/learning_items.py`
- Modify: `src/flashcard_handlers.py`
- Modify: `src/flashcard_scheduler.py`
- Modify: `src/bot.py`
- Create: `tests/test_learning_srs.py`
- Modify: `tests/test_flashcard_handlers.py`
- Modify: `tests/test_flashcard_scheduler.py`

- [ ] **Step 1: Port SRS tests**

Create `tests/test_learning_srs.py` by porting core `tests/test_flashcards.py` cases to `learning_items`:

- `apply_review_grade()` schedules `good` tomorrow.
- `again` schedules relearning in 10 minutes.
- picker prefers due review before new item.
- stats count total/new/due/learning/review/lapses.
- reset clears only selected user.

- [ ] **Step 2: Implement SRS functions**

In `src/learning_items.py`, implement SRS/session/settings functions equivalent to current `flashcards.py`, but using `learning_item_id`.

Selection filters:

- `level`
- `item_type`
- `deck_id`
- `tags`

- [ ] **Step 3: Update handlers and scheduler**

Modify `src/flashcard_handlers.py` and `src/flashcard_scheduler.py` to import `learning_items` and use new functions.

Keep current user commands:

```text
/flash
/flash_new
/flash_review
/flash_stats
/flash_goal
/flash_reset
```

Add study selection commands:

```text
/flash_settings
/flash_level N4
/flash_type vocab|kanji|grammar|kaiwa
/flash_deck n4_vocab_core
/flash_tags food,verb
```

- [ ] **Step 4: Register commands**

Modify `src/bot.py` to register selection commands.

- [ ] **Step 5: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_learning_srs.py tests/test_flashcard_handlers.py tests/test_flashcard_scheduler.py -q
git add src/learning_items.py src/flashcard_handlers.py src/flashcard_scheduler.py src/bot.py tests/test_learning_srs.py tests/test_flashcard_handlers.py tests/test_flashcard_scheduler.py
git commit -m "feat: use learning items for study flow"
```

Expected: PASS.

---

### Task 6: Format Item Types

**Files:**
- Modify: `src/flashcard_handlers.py`
- Modify: `tests/test_flashcard_handlers.py`

- [ ] **Step 1: Add formatter tests**

Add tests for `format_item_answer()`:

- `vocab`: shows front, reading, meaning, hanviet, examples.
- `kanji`: reads `onyomi`, `kunyomi`, `examples` from `extra_json`.
- `grammar`: reads `usage` from `extra_json`.
- `kaiwa`: reads dialogue, shadowing, quiz from `extra_json`.

- [ ] **Step 2: Implement formatters**

Add:

```python
def item_extra(item):
    ...

def format_item_front(item):
    ...

def format_item_answer(item):
    ...
```

Keep wrappers `format_card_front()` and `format_card_answer()` if current callers/tests still use them.

- [ ] **Step 3: Run tests and commit**

```powershell
docker compose run --rm bot pytest tests/test_flashcard_handlers.py -q
git add src/flashcard_handlers.py tests/test_flashcard_handlers.py
git commit -m "feat: format learning item types"
```

Expected: PASS.

---

### Task 7: Update Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/agent-handoff.md`
- Modify: `docs/flashcard-import-source-plan.md`
- Modify: `docs/docker-deployment-guide.md`
- Modify: `.env.example`

- [ ] **Step 1: Document Sheet changes**

Copy the Google Sheet Changes Required section from this plan into user-facing docs.

- [ ] **Step 2: Document commands**

Add:

```text
/flash_settings
/flash_level N4
/flash_type vocab|kanji|grammar|kaiwa
/flash_deck n4_vocab_core
/flash_tags food,verb
```

- [ ] **Step 3: Document import and migration**

Add:

```powershell
docker compose run --rm bot python tools/migrate_flashcards_to_learning_items.py --default-deck-id n4_vocab_core
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks --dry-run
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks
```

- [ ] **Step 4: Run docs check and commit**

```powershell
Select-String -Path README.md,docs\agent-handoff.md,docs\docker-deployment-guide.md,docs\flashcard-import-source-plan.md -Pattern "learning_items", "deck_catalog", "vocab_n4_core", "flash_type"
git add README.md docs/agent-handoff.md docs/flashcard-import-source-plan.md docs/docker-deployment-guide.md .env.example
git commit -m "docs: document learning items deck model"
```

Expected: patterns found and commit succeeds.

---

### Task 8: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run targeted tests**

```powershell
docker compose run --rm bot pytest tests/test_learning_items_schema.py tests/test_learning_items_migration.py tests/test_learning_source_normalizers.py tests/test_learning_deck_catalog.py tests/test_import_learning_items.py tests/test_learning_srs.py tests/test_flashcard_handlers.py tests/test_flashcard_scheduler.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

```powershell
docker compose run --rm bot pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run compile check**

```powershell
docker compose run --rm bot python -m py_compile src/bot.py src/learning_items.py src/flashcard_handlers.py src/flashcard_scheduler.py tools/import_flashcards.py tools/migrate_flashcards_to_learning_items.py
```

Expected: exit code 0 with no output.

- [ ] **Step 4: Run dry-runs**

```powershell
docker compose run --rm bot python tools/migrate_flashcards_to_learning_items.py --default-deck-id n4_vocab_core
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks --dry-run
```

Expected: migration prints copied counts; import prints deck/item summary with `Imported: 0` for dry-run.

- [ ] **Step 5: Inspect git status**

```powershell
git status --short
```

Expected: no unstaged changes.

---

## Self-Review

- Plan uses new `learning_items` design instead of adding columns to `flashcards`.
- Plan includes exact Google Sheet worksheet names and columns.
- Plan preserves existing data through migration and keeps old tables during rollout.
- Plan keeps existing `/flash*` command surface while backend changes.
