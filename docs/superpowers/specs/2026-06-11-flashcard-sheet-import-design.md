# Flashcard Sheet Import Design

## Goal

Add a unified flashcard import flow that can read N4 flashcards from Google Sheet tab `flashcards` and sync them into the existing SQLite `flashcards` table. Keep the current PDF import path as fallback.

The bot continues to study from SQLite. Google Sheet and PDF are source data only; user review progress stays in SQLite and must not be reset by import.

## Source Data

Google Sheet access uses the existing configuration:

```env
GOOGLE_SHEET_ID=<existing sheet id>
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
```

Flashcard sheet configuration:

```env
FLASHCARD_IMPORT_SOURCE=sheet
FLASHCARD_SHEET_NAME=flashcards
FLASHCARD_SHEET_LEVEL=N4
FLASHCARD_PDF_PATH=docs/20250312140417_Tài liệu flash N4.pdf
FLASHCARD_PDF_LEVEL=N4
FLASHCARD_PDF_SOURCE=n4_pdf
```

The worksheet schema is:

```text
card_id
level
source
source_position
word
reading
meaning
example_jp
example_vi
tags
status
```

Only rows with `status=ready` are imported.

## Architecture

Add source adapters under `src/flashcard_sources/`:

```text
src/flashcard_sources/__init__.py
src/flashcard_sources/sheet_source.py
src/flashcard_sources/pdf_source.py
src/flashcard_sources/validation.py
```

Add unified CLI:

```text
tools/import_flashcards.py
```

Keep the legacy command:

```text
tools/import_n4_pdf.py
```

`import_n4_pdf.py` becomes a wrapper or remains compatible, but the preferred command is `import_flashcards.py`.

## Data Flow

```text
tools/import_flashcards.py
-> choose source from CLI --source or FLASHCARD_IMPORT_SOURCE
-> source=sheet: sheet_source.load_flashcards()
-> source=pdf: pdf_source.load_flashcards()
-> validation.validate_rows()
-> flashcards.upsert_flashcards()
-> print summary
```

Sheet flow:

```text
Google Sheet by GOOGLE_SHEET_ID
worksheet: flashcards
-> gspread get_all_records()
-> normalize rows to common flashcard schema
-> validate rows
-> upsert into SQLite
```

PDF flow:

```text
PDF file path from FLASHCARD_PDF_PATH or CLI --pdf
-> reuse existing PDF parsing behavior
-> normalize rows to common flashcard schema
-> validate rows
-> upsert into SQLite
```

## Common Row Shape

Each source returns dictionaries shaped like:

```python
{
    "card_id": "N4-0001",
    "level": "N4",
    "source": "n4_md",
    "source_position": 1,
    "word": "石",
    "reading": "いし",
    "meaning": "Đá",
    "example_jp": "一番大きいピラミッドをつくるのに石が270万個も使われました。",
    "example_vi": "270 vạn khối đá đã được sử dụng để xây lên Kim tự tháp lớn nhất.",
    "tags": "",
    "status": "ready",
}
```

SQLite phase keeps the existing table schema. `card_id`, `tags`, and `status` are used by source sync and validation only, not stored in SQLite yet.

## Validation

Rows are skipped with warnings when:

- `status` is not `ready`
- `word` is empty
- `meaning` is empty
- `level` is empty
- `source_position` cannot be converted to an integer

Rows are imported with warnings when:

- `reading` is empty
- `example_jp` is empty
- `example_vi` is empty
- `tags` is empty

Duplicate source rows are keyed by:

```text
level + source + word + reading
```

If duplicates occur in the same source load, the later row wins and validation reports a warning.

## SQLite Behavior

Use the existing `flashcards.upsert_flashcards(cards)` function and current unique constraint:

```text
UNIQUE(level, source, word, reading)
```

No migration is included in this phase. This avoids risk to existing flashcard review state.

## CLI Behavior

Dry run:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

Import from Sheet:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

Import from PDF fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf --dry-run
docker compose run --rm bot python tools/import_flashcards.py --source pdf
```

Expected summary format:

```text
Source: sheet
Fetched: 276
Ready: 275
Imported: 275
Skipped: 1
Warnings: 3
```

Dry run prints the same counts but imports zero rows.

## Error Handling

If Google credentials are missing, sheet source returns a clear error and CLI exits non-zero.

If worksheet `flashcards` does not exist, CLI prints a clear message with the missing worksheet name.

If PDF dependency or file is missing, PDF source raises the same class of clear CLI error.

Validation warnings are printed but do not fail the import unless every row is invalid.

## Tests

Add focused tests for:

- validation normalizes valid rows
- validation skips missing `word`
- validation skips `status=draft`
- validation converts `source_position` string to int
- sheet source reads gspread-like records and sorts by `source_position`
- unified CLI calls sheet source for `--source sheet`
- unified CLI calls PDF source for `--source pdf`
- `--dry-run` avoids SQLite writes

Existing PDF parser tests remain valid.

## Rollout

1. Rename Google worksheet to `flashcards`.
2. Confirm header order matches schema.
3. Run sheet dry-run.
4. Fix warnings in Sheet if needed.
5. Run real sheet import.
6. Restart bot if needed; bot continues using SQLite normally.
