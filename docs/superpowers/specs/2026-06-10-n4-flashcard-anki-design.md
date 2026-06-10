# N4 Flashcard Anki Design

## Goal

Add N4 vocabulary flashcard learning to the existing Telegram Japanese bot. The feature uses the readable PDF source `docs/20250312140417_Tài liệu flash N4.pdf`, stores cards and per-user review state in SQLite, and supports both daily automatic reminders and manual study commands.

## Selected Approach

Use the existing `LearnJapanese` Telegram bot and add a separate flashcard module inside the same project. This keeps deployment simple while preventing the existing Google Sheet lesson flow from becoming tangled with spaced repetition logic.

Rejected alternatives:

- Put all flashcard logic directly into `handlers.py`: faster initially, but it would make handler code too large and harder to test.
- Build a separate bot/app: cleaner isolation, but it adds another Telegram token, deploy target, database, scheduler, and user flow.

## Files and Modules

New modules:

```text
src/flashcards.py
src/flashcard_handlers.py
src/flashcard_scheduler.py
tools/import_n4_pdf.py
```

Existing modules touched:

```text
src/bot.py
src/config.py
src/db.py
requirements.txt
.env.example
```

Responsibilities:

- `flashcards.py`: flashcard queries, review scheduling, SM-2 style interval updates.
- `flashcard_handlers.py`: Telegram commands for study/review/stats.
- `flashcard_scheduler.py`: daily flashcard reminder job.
- `tools/import_n4_pdf.py`: one-off/idempotent importer from the N4 PDF into SQLite.
- `db.py`: schema creation for flashcard tables, or small connection helpers reused by `flashcards.py`.
- `config.py`: flashcard environment variables.
- `bot.py`: command registration and daily flashcard job registration.

## Configuration

Add these environment variables:

```env
FLASHCARD_ENABLED=true
FLASHCARD_DAILY_TIME=20:30
FLASHCARD_DAILY_NEW_LIMIT=5
FLASHCARD_DAILY_REVIEW_LIMIT=20
FLASHCARD_LEVEL=N4
FLASHCARD_TIMEZONE=Asia/Bangkok
```

Rules:

- `FLASHCARD_ENABLED=false` disables only the automatic daily flashcard job. Manual commands still work.
- `FLASHCARD_DAILY_TIME` controls the reminder job time.
- `FLASHCARD_DAILY_NEW_LIMIT` caps new cards offered per day by scheduled flow.
- `FLASHCARD_DAILY_REVIEW_LIMIT` caps due review cards included in daily flow.
- `FLASHCARD_LEVEL` defaults new study sessions to `N4`.
- `FLASHCARD_TIMEZONE` defaults to `TIMEZONE` when unset.

## Data Model

Add `flashcards`:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
level TEXT NOT NULL
source TEXT NOT NULL
source_position INTEGER
word TEXT NOT NULL
reading TEXT
meaning TEXT NOT NULL
example_jp TEXT
example_vi TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
UNIQUE(level, source, word, reading)
```

Add `user_flashcard_reviews`:

```text
telegram_user_id INTEGER NOT NULL
flashcard_id INTEGER NOT NULL
state TEXT NOT NULL
due_at TEXT
interval_days REAL NOT NULL DEFAULT 0
ease_factor REAL NOT NULL DEFAULT 2.5
repetitions INTEGER NOT NULL DEFAULT 0
lapses INTEGER NOT NULL DEFAULT 0
last_reviewed_at TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
PRIMARY KEY (telegram_user_id, flashcard_id)
```

`state` values:

```text
new
learning
review
relearning
suspended
```

## Import Flow

The importer reads `docs/20250312140417_Tài liệu flash N4.pdf` using a PDF text extraction library. The PDF has already been verified as extractable with clean Japanese and Vietnamese text.

Importer behavior:

- Extract page text from all 30 pages.
- Parse rows containing number, word, reading, meaning, example Japanese, and example Vietnamese.
- Preserve source order in `source_position`.
- Insert or update rows idempotently using `UNIQUE(level, source, word, reading)`.
- Print import summary: inserted, updated, skipped, parse warnings.

The importer should tolerate multi-line meanings and examples because the PDF wraps long Vietnamese and Japanese text.

## Telegram Commands

Add commands:

```text
/flash_start
/flash
/flash_new
/flash_review
/flash_stats
/show
/again
/hard
/good
/easy
```

Behavior:

- `/flash_start`: initializes flashcard state for the user and explains the available commands briefly.
- `/flash`: sends one due review card first; if none are due, sends one new card.
- `/flash_new`: sends one new N4 card.
- `/flash_review`: sends one due review card only.
- `/flash_stats`: shows counts for new, due today, learning, review, lapses.
- `/show`: reveals the answer for the current pending card and shows grading commands.
- `/again`, `/hard`, `/good`, `/easy`: grade the last revealed card for that user and schedule the next due time.

To avoid needing inline keyboard callback plumbing in the first version, grading uses commands. The bot stores the pending/revealed flashcard per user in a small state table or in `context.user_data`; SQLite is preferred so restarts do not lose the pending card.

Add `user_flashcard_sessions`:

```text
telegram_user_id INTEGER PRIMARY KEY
current_flashcard_id INTEGER
current_direction TEXT NOT NULL DEFAULT 'jp_to_vi'
shown_at TEXT
answer_shown_at TEXT
updated_at TEXT NOT NULL
```

## Card Display

Default direction is Japanese to Vietnamese.

Front from `/flash`, `/flash_new`, or `/flash_review`:

```text
N4 Flashcard
言葉: 石
読み方: いし

Tự nhớ nghĩa, rồi dùng /show để xem đáp án.
```

Answer from `/show`:

```text
意味: Đá
例文: 一番大きいピラミッドをつくるのに石が270万個も使われました。
Dịch: 270 vạn khối đá đã được sử dụng để xây lên Kim tự tháp lớn nhất.

Bạn nhớ mức nào?
/again /hard /good /easy
```

After grading, bot replies with the next due estimate:

```text
Next review: 2026-06-11 20:30
```

## Spaced Repetition

Use a simple SM-2 inspired algorithm. It is intentionally small and deterministic so it is easy to test and adjust.

Initial values:

```text
state = new
interval_days = 0
ease_factor = 2.5
repetitions = 0
lapses = 0
```

Grade behavior:

- `again`: state becomes `relearning`, interval becomes same-day or next-day short interval, ease decreases, lapses increments.
- `hard`: interval grows slowly, ease decreases slightly.
- `good`: interval grows normally, repetitions increments.
- `easy`: interval grows faster, ease increases slightly.

Minimum scheduling:

- First `good`: due tomorrow.
- Second `good`: due in 3 days.
- Later `good`: multiply interval by ease factor.
- `hard`: at least 1 day, then about 1.2x current interval.
- `easy`: at least 4 days, then about 1.5x normal interval.

All due timestamps use configured flashcard timezone for user-facing display and UTC ISO strings for storage.

## Daily Scheduler

Register a second job in `bot.py`:

```text
daily_lesson_job
daily_flashcard_job
```

Daily flashcard job behavior:

- Skip if `FLASHCARD_ENABLED=false`.
- For each registered user, compute due card count and available new card count.
- Send a concise reminder with counts.
- If reviews are due, send the first due card.
- If no reviews are due and new cards remain, optionally send one new card, capped by `FLASHCARD_DAILY_NEW_LIMIT`.

The flashcard job should run at `FLASHCARD_DAILY_TIME`, separate from the lesson job to avoid noisy combined messages.

## Error Handling

- If no flashcards are imported, commands return a clear message telling the operator to run the importer.
- If a user grades without a pending card, bot tells them to use `/flash` first.
- If PDF parsing has warnings, importer still inserts valid rows and prints skipped positions.
- If scheduler fails for one user, log the error and continue with other users.

## Testing

Add focused tests where the project test setup allows it:

- PDF parser extracts the first several known cards: `石`, `経験`, `店員`.
- Importer is idempotent when run twice.
- SM-2 grade updates produce expected state, interval, repetitions, and lapses.
- `/flash` chooses due review before new card.
- Grading before /show or without a pending card returns a safe message.
- Bot startup still registers existing lesson commands.

If full Telegram integration tests are too heavy, keep handler tests at helper-function level and smoke test startup locally.

## Rollout

1. Add config and schema.
2. Add importer and import N4 PDF into SQLite.
3. Add flashcard scheduling logic and tests.
4. Add Telegram handlers and command registration.
5. Add daily flashcard scheduler.
6. Run import + smoke test bot startup.

## Out of Scope

- Inline keyboard grading.
- Audio pronunciation.
- Reverse cards Vietnamese to Japanese.
- Web dashboard.
- Multi-user admin controls.
- AI-generated example sentences.




