# Flashcard Sheet Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified flashcard import CLI that imports rows from Google Sheet worksheet `flashcards` into the existing SQLite flashcards table, while keeping PDF import as fallback.

**Architecture:** Add small source adapters under `src/flashcard_sources/`, a shared validation layer, and a unified CLI in `tools/import_flashcards.py`. Keep SQLite schema unchanged and reuse `flashcards.upsert_flashcards()` so existing user review progress remains untouched.

**Tech Stack:** Python 3.11, gspread, google-auth, pdfplumber, SQLite, pytest, Docker Compose.

---

## File Structure

- `src/config.py`: Add flashcard import env settings with safe defaults.
- `src/flashcard_sources/__init__.py`: Package marker and exported helpers.
- `src/flashcard_sources/validation.py`: Normalize rows, filter `status=ready`, convert `source_position`, collect warnings, handle duplicates.
- `src/flashcard_sources/sheet_source.py`: Read worksheet `FLASHCARD_SHEET_NAME` from existing `GOOGLE_SHEET_ID` using existing service-account config.
- `src/flashcard_sources/pdf_source.py`: Wrap the existing PDF parser behavior behind the same source adapter interface.
- `tools/import_flashcards.py`: CLI entry point for `--source sheet|pdf`, `--dry-run`, summary output, and import calls.
- `tools/import_n4_pdf.py`: Keep existing PDF command behavior backward compatible; do not rewrite it during this phase.
- `.env.example`: Document new flashcard import settings.
- `docs/docker-deployment-guide.md`: Document sheet import and PDF fallback commands.
- `tests/test_flashcard_validation.py`: Unit tests for row validation.
- `tests/test_flashcard_sheet_source.py`: Unit tests for worksheet read and sort behavior.
- `tests/test_flashcard_pdf_source.py`: Unit tests for PDF source adapter.
- `tests/test_import_flashcards.py`: Unit tests for CLI source dispatch and dry-run behavior.

## Task 1: Config Defaults

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add import config constants**

Modify `src/config.py` after existing flashcard settings:

```python
FLASHCARD_IMPORT_SOURCE = os.getenv("FLASHCARD_IMPORT_SOURCE", "sheet").strip().lower()
FLASHCARD_PDF_PATH = os.getenv("FLASHCARD_PDF_PATH", "docs/20250312140417_Tài liệu flash N4.pdf")
FLASHCARD_PDF_LEVEL = os.getenv("FLASHCARD_PDF_LEVEL", "N4")
FLASHCARD_PDF_SOURCE = os.getenv("FLASHCARD_PDF_SOURCE", "n4_pdf")
FLASHCARD_SHEET_NAME = os.getenv("FLASHCARD_SHEET_NAME", "flashcards")
FLASHCARD_SHEET_LEVEL = os.getenv("FLASHCARD_SHEET_LEVEL", "N4")
```

- [ ] **Step 2: Document env variables**

Modify `.env.example` flashcard section to include:

```env
FLASHCARD_IMPORT_SOURCE=sheet
FLASHCARD_PDF_PATH=docs/20250312140417_Tài liệu flash N4.pdf
FLASHCARD_PDF_LEVEL=N4
FLASHCARD_PDF_SOURCE=n4_pdf
FLASHCARD_SHEET_NAME=flashcards
FLASHCARD_SHEET_LEVEL=N4
```

- [ ] **Step 3: Run import syntax check**

Run:

```powershell
docker compose run --rm bot python -c "import config; print(config.FLASHCARD_SHEET_NAME)"
```

Expected:

```text
flashcards
```

- [ ] **Step 4: Commit config docs**

Run:

```powershell
git add src/config.py .env.example
git commit -m "feat: add flashcard import config"
```

## Task 2: Validation Layer

**Files:**
- Create: `src/flashcard_sources/__init__.py`
- Create: `src/flashcard_sources/validation.py`
- Create: `tests/test_flashcard_validation.py`

- [ ] **Step 1: Write failing validation tests**

Create `tests/test_flashcard_validation.py`:

```python
from flashcard_sources.validation import validate_rows


def test_validate_rows_normalizes_ready_row():
    rows = [{
        "card_id": " N4-0001 ",
        "level": "N4",
        "source": " n4_md ",
        "source_position": "1",
        "word": " 石 ",
        "reading": " いし ",
        "meaning": " Đá ",
        "example_jp": " 例文 ",
        "example_vi": " ví dụ ",
        "tags": " noun ",
        "status": " ready ",
    }]

    result = validate_rows(rows, default_level="N4", default_source="n4_md")

    assert result.fetched == 1
    assert result.ready == 1
    assert result.skipped == 0
    assert result.rows == [{
        "card_id": "N4-0001",
        "level": "N4",
        "source": "n4_md",
        "source_position": 1,
        "word": "石",
        "reading": "いし",
        "meaning": "Đá",
        "example_jp": "例文",
        "example_vi": "ví dụ",
        "tags": "noun",
        "status": "ready",
    }]
    assert result.warnings == []


def test_validate_rows_skips_missing_word():
    rows = [{
        "level": "N4",
        "source": "n4_md",
        "source_position": "1",
        "word": "",
        "meaning": "Đá",
        "status": "ready",
    }]

    result = validate_rows(rows, default_level="N4", default_source="n4_md")

    assert result.rows == []
    assert result.skipped == 1
    assert "row 1 skipped: missing word" in result.warnings


def test_validate_rows_skips_non_ready_status():
    rows = [{
        "level": "N4",
        "source": "n4_md",
        "source_position": "1",
        "word": "石",
        "meaning": "Đá",
        "status": "draft",
    }]

    result = validate_rows(rows, default_level="N4", default_source="n4_md")

    assert result.ready == 0
    assert result.rows == []
    assert result.skipped == 1
    assert "row 1 skipped: status=draft" in result.warnings


def test_validate_rows_warns_for_optional_missing_fields():
    rows = [{
        "level": "N4",
        "source": "n4_md",
        "source_position": "1",
        "word": "石",
        "meaning": "Đá",
        "status": "ready",
    }]

    result = validate_rows(rows, default_level="N4", default_source="n4_md")

    assert len(result.rows) == 1
    assert "row 1 warning: missing reading" in result.warnings
    assert "row 1 warning: missing example_jp" in result.warnings
    assert "row 1 warning: missing example_vi" in result.warnings
    assert "row 1 warning: missing tags" in result.warnings


def test_validate_rows_later_duplicate_wins():
    rows = [
        {
            "level": "N4",
            "source": "n4_md",
            "source_position": "1",
            "word": "石",
            "reading": "いし",
            "meaning": "old",
            "status": "ready",
        },
        {
            "level": "N4",
            "source": "n4_md",
            "source_position": "2",
            "word": "石",
            "reading": "いし",
            "meaning": "new",
            "status": "ready",
        },
    ]

    result = validate_rows(rows, default_level="N4", default_source="n4_md")

    assert len(result.rows) == 1
    assert result.rows[0]["meaning"] == "new"
    assert "row 2 warning: duplicate key N4|n4_md|石|いし overwrites earlier row" in result.warnings
```

- [ ] **Step 2: Run failing validation tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_validation.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'flashcard_sources'`.

- [ ] **Step 3: Implement validation package**

Create `src/flashcard_sources/__init__.py`:

```python
"""Flashcard source adapters."""
```

Create `src/flashcard_sources/validation.py`:

```python
from dataclasses import dataclass


OPTIONAL_WARNING_FIELDS = ("reading", "example_jp", "example_vi", "tags")
REQUIRED_FIELDS = ("level", "source_position", "word", "meaning")


@dataclass
class ValidationResult:
    rows: list[dict]
    warnings: list[str]
    fetched: int
    ready: int
    skipped: int


def _clean(value):
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _normalize_raw_row(row, default_level, default_source):
    normalized = {
        "card_id": _clean(row.get("card_id")),
        "level": _clean(row.get("level")) or default_level,
        "source": _clean(row.get("source")) or default_source,
        "source_position": _clean(row.get("source_position")),
        "word": _clean(row.get("word")),
        "reading": _clean(row.get("reading")),
        "meaning": _clean(row.get("meaning")),
        "example_jp": _clean(row.get("example_jp")),
        "example_vi": _clean(row.get("example_vi")),
        "tags": _clean(row.get("tags")),
        "status": (_clean(row.get("status")) or "ready").lower(),
    }
    return normalized


def validate_rows(rows, default_level="N4", default_source="n4_pdf"):
    warnings = []
    valid_by_key = {}
    ready = 0
    skipped = 0

    for index, raw_row in enumerate(rows, start=1):
        row = _normalize_raw_row(raw_row, default_level, default_source)
        if row["status"] != "ready":
            skipped += 1
            warnings.append(f"row {index} skipped: status={row['status']}")
            continue

        ready += 1
        missing = next((field for field in REQUIRED_FIELDS if not row.get(field)), None)
        if missing:
            skipped += 1
            warnings.append(f"row {index} skipped: missing {missing}")
            continue

        try:
            row["source_position"] = int(row["source_position"])
        except ValueError:
            skipped += 1
            warnings.append(f"row {index} skipped: invalid source_position={row['source_position']}")
            continue

        for field in OPTIONAL_WARNING_FIELDS:
            if not row.get(field):
                warnings.append(f"row {index} warning: missing {field}")

        key = (row["level"], row["source"], row["word"], row["reading"])
        if key in valid_by_key:
            joined = "|".join(key)
            warnings.append(f"row {index} warning: duplicate key {joined} overwrites earlier row")
        valid_by_key[key] = row

    rows_out = sorted(valid_by_key.values(), key=lambda item: item["source_position"])
    return ValidationResult(
        rows=rows_out,
        warnings=warnings,
        fetched=len(rows),
        ready=ready,
        skipped=skipped,
    )
```

- [ ] **Step 4: Run validation tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_validation.py -v
```

Expected: PASS all 5 tests.

- [ ] **Step 5: Commit validation layer**

Run:

```powershell
git add src/flashcard_sources/__init__.py src/flashcard_sources/validation.py tests/test_flashcard_validation.py
git commit -m "feat: validate flashcard source rows"
```

## Task 3: Sheet Source Adapter

**Files:**
- Create: `src/flashcard_sources/sheet_source.py`
- Create: `tests/test_flashcard_sheet_source.py`

- [ ] **Step 1: Write failing sheet source tests**

Create `tests/test_flashcard_sheet_source.py`:

```python
from flashcard_sources import sheet_source


class FakeWorksheet:
    def __init__(self, records):
        self.records = records

    def get_all_records(self):
        return self.records


class FakeBook:
    def __init__(self, records):
        self.records = records
        self.requested = []

    def worksheet(self, name):
        self.requested.append(name)
        return FakeWorksheet(self.records)


class FakeClient:
    def __init__(self, records):
        self.book = FakeBook(records)
        self.opened_key = None

    def open_by_key(self, sheet_id):
        self.opened_key = sheet_id
        return self.book


def test_load_flashcards_reads_named_worksheet_and_sorts(monkeypatch):
    records = [
        {
            "card_id": "N4-0002",
            "level": "N4",
            "source": "n4_md",
            "source_position": "2",
            "word": "経験",
            "reading": "けいけん",
            "meaning": "Kinh nghiệm",
            "status": "ready",
        },
        {
            "card_id": "N4-0001",
            "level": "N4",
            "source": "n4_md",
            "source_position": "1",
            "word": "石",
            "reading": "いし",
            "meaning": "Đá",
            "status": "ready",
        },
    ]
    client = FakeClient(records)
    monkeypatch.setattr(sheet_source, "get_client", lambda: client)

    result = sheet_source.load_flashcards(
        sheet_id="sheet-123",
        worksheet_name="flashcards",
        default_level="N4",
        default_source="n4_md",
    )

    assert client.opened_key == "sheet-123"
    assert client.book.requested == ["flashcards"]
    assert [row["word"] for row in result.rows] == ["石", "経験"]
    assert result.fetched == 2


def test_load_flashcards_raises_when_client_missing(monkeypatch):
    monkeypatch.setattr(sheet_source, "get_client", lambda: None)

    try:
        sheet_source.load_flashcards(
            sheet_id="sheet-123",
            worksheet_name="flashcards",
            default_level="N4",
            default_source="n4_md",
        )
    except RuntimeError as exc:
        assert str(exc) == "Google Sheet client is not available"
    else:
        raise AssertionError("RuntimeError was not raised")
```

After creating the file, remove the two accidental leading `+` characters before `self.requested = []` and `default_source="n4_md",` if your editor inserted them from this plan text.

- [ ] **Step 2: Run failing sheet tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_sheet_source.py -v
```

Expected: FAIL with `ImportError` for missing `sheet_source`.

- [ ] **Step 3: Implement sheet source**

Create `src/flashcard_sources/sheet_source.py`:

```python
from config import FLASHCARD_SHEET_LEVEL, FLASHCARD_SHEET_NAME, GOOGLE_SHEET_ID
from sheets import get_client

from .validation import validate_rows


DEFAULT_SHEET_SOURCE = "n4_md"


def load_flashcards(sheet_id=None, worksheet_name=None, default_level=None, default_source=DEFAULT_SHEET_SOURCE):
    client = get_client()
    if not client:
        raise RuntimeError("Google Sheet client is not available")

    selected_sheet_id = sheet_id or GOOGLE_SHEET_ID
    selected_worksheet = worksheet_name or FLASHCARD_SHEET_NAME
    selected_level = default_level or FLASHCARD_SHEET_LEVEL

    book = client.open_by_key(selected_sheet_id)
    worksheet = book.worksheet(selected_worksheet)
    records = worksheet.get_all_records()
    return validate_rows(records, default_level=selected_level, default_source=default_source)
```

- [ ] **Step 4: Run sheet tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_sheet_source.py -v
```

Expected: PASS both tests.

- [ ] **Step 5: Commit sheet adapter**

Run:

```powershell
git add src/flashcard_sources/sheet_source.py tests/test_flashcard_sheet_source.py
git commit -m "feat: load flashcards from sheet"
```

## Task 4: PDF Source Adapter

**Files:**
- Create: `src/flashcard_sources/pdf_source.py`
- Create: `tests/test_flashcard_pdf_source.py`

- [ ] **Step 1: Write failing PDF adapter test**

Create `tests/test_flashcard_pdf_source.py`:

```python
from flashcard_sources import pdf_source


PDF_TEXT = """
番号 言葉 読み方 意味 例文
1 石 いし Đá
・一番大きいピラミッドをつくるのに石が
270万個も使われました。
270 vạn khối đá đã được sử dụngして xây lên
Kim tự tháp lớn nhất.
2 経験 けいけん Kinh nghiệm
・先生は面白
おもしろ
いし、親切
しんせつ
だし、それに経験も
あります。
Thầy giáo tôi vừa thân thiện, thú vị lại còn có
nhiều kinh nghiệm.
"""


def test_load_flashcards_from_text_uses_common_validation():
    result = pdf_source.load_flashcards_from_text(PDF_TEXT, level="N4", source="n4_pdf")

    assert result.fetched == 2
    assert result.ready == 2
    assert [row["word"] for row in result.rows] == ["石", "経験"]
    assert result.rows[0]["level"] == "N4"
    assert result.rows[0]["source"] == "n4_pdf"
    assert result.rows[0]["status"] == "ready"
```

- [ ] **Step 2: Run failing PDF adapter test**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_pdf_source.py -v
```

Expected: FAIL with `ImportError` for missing `pdf_source`.

- [ ] **Step 3: Implement PDF source wrapper**

Create `src/flashcard_sources/pdf_source.py`:

```python
from pathlib import Path

from config import FLASHCARD_PDF_LEVEL, FLASHCARD_PDF_PATH, FLASHCARD_PDF_SOURCE
from tools.import_n4_pdf import extract_pdf_text, parse_cards_from_text

from .validation import validate_rows


def _with_ready_status(cards):
    rows = []
    for card in cards:
        row = dict(card)
        row.setdefault("card_id", "")
        row.setdefault("tags", "")
        row["status"] = "ready"
        rows.append(row)
    return rows


def load_flashcards_from_text(text, level="N4", source="n4_pdf"):
    cards = parse_cards_from_text(text, level=level, source=source)
    return validate_rows(_with_ready_status(cards), default_level=level, default_source=source)


def load_flashcards(pdf_path=None, level=None, source=None):
    selected_path = Path(pdf_path or FLASHCARD_PDF_PATH)
    selected_level = level or FLASHCARD_PDF_LEVEL
    selected_source = source or FLASHCARD_PDF_SOURCE
    if not selected_path.exists():
        raise RuntimeError(f"PDF not found: {selected_path}")
    text = extract_pdf_text(selected_path)
    return load_flashcards_from_text(text, level=selected_level, source=selected_source)
```

- [ ] **Step 4: Run PDF adapter test**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_pdf_source.py tests/test_import_n4_pdf.py -v
```

Expected: PASS all PDF-related tests.

- [ ] **Step 5: Commit PDF adapter**

Run:

```powershell
git add src/flashcard_sources/pdf_source.py tests/test_flashcard_pdf_source.py
git commit -m "feat: add flashcard pdf source adapter"
```

## Task 5: Unified Import CLI

**Files:**
- Create: `tools/import_flashcards.py`
- Create: `tests/test_import_flashcards.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_import_flashcards.py`:

```python
import tools.import_flashcards as importer
from flashcard_sources.validation import ValidationResult


def _result(rows):
    return ValidationResult(rows=rows, warnings=[], fetched=len(rows), ready=len(rows), skipped=0)


def test_run_import_sheet_dry_run_does_not_write(monkeypatch):
    card = {
        "level": "N4",
        "source": "n4_md",
        "source_position": 1,
        "word": "石",
        "reading": "いし",
        "meaning": "Đá",
        "example_jp": "例文",
        "example_vi": "dịch",
        "card_id": "N4-0001",
        "tags": "",
        "status": "ready",
    }
    monkeypatch.setattr(importer.sheet_source, "load_flashcards", lambda: _result([card]))

    called = {"value": False}
    monkeypatch.setattr(importer.flashcards, "upsert_flashcards", lambda rows: called.update(value=True))

    summary = importer.run_import(source="sheet", dry_run=True)

    assert summary == {
        "source": "sheet",
        "fetched": 1,
        "ready": 1,
        "imported": 0,
        "skipped": 0,
        "warnings": 0,
    }
    assert called["value"] is False


def test_run_import_pdf_writes_rows(monkeypatch):
    card = {
        "level": "N4",
        "source": "n4_pdf",
        "source_position": 1,
        "word": "石",
        "reading": "いし",
        "meaning": "Đá",
        "example_jp": "例文",
        "example_vi": "dịch",
        "card_id": "",
        "tags": "",
        "status": "ready",
    }
    monkeypatch.setattr(importer.pdf_source, "load_flashcards", lambda: _result([card]))

    written = {}
    monkeypatch.setattr(importer.flashcards, "upsert_flashcards", lambda rows: written.setdefault("rows", rows) or len(rows))

    summary = importer.run_import(source="pdf", dry_run=False)

    assert written["rows"] == [card]
    assert summary["imported"] == 1
    assert summary["source"] == "pdf"


def test_run_import_rejects_unknown_source():
    try:
        importer.run_import(source="bad", dry_run=True)
    except ValueError as exc:
        assert str(exc) == "Unsupported flashcard import source: bad"
    else:
        raise AssertionError("ValueError was not raised")
```

- [ ] **Step 2: Run failing CLI tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_import_flashcards.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.import_flashcards'`.

- [ ] **Step 3: Implement unified CLI**

Create `tools/import_flashcards.py`:

```python
import argparse

import flashcards
from config import FLASHCARD_IMPORT_SOURCE
from flashcard_sources import pdf_source, sheet_source


IMPORT_FIELDS = (
    "level",
    "source",
    "source_position",
    "word",
    "reading",
    "meaning",
    "example_jp",
    "example_vi",
)


def _select_source(source):
    selected = (source or FLASHCARD_IMPORT_SOURCE).strip().lower()
    if selected not in {"sheet", "pdf"}:
        raise ValueError(f"Unsupported flashcard import source: {selected}")
    return selected


def _db_rows(rows):
    return [{field: row.get(field) for field in IMPORT_FIELDS} for row in rows]


def run_import(source=None, dry_run=False):
    selected = _select_source(source)
    if selected == "sheet":
        result = sheet_source.load_flashcards()
    else:
        result = pdf_source.load_flashcards()

    imported = 0
    if not dry_run and result.rows:
        imported = flashcards.upsert_flashcards(_db_rows(result.rows))

    return {
        "source": selected,
        "fetched": result.fetched,
        "ready": result.ready,
        "imported": imported,
        "skipped": result.skipped,
        "warnings": len(result.warnings),
    }, result.warnings


def print_summary(summary, warnings):
    print(f"Source: {summary['source']}")
    print(f"Fetched: {summary['fetched']}")
    print(f"Ready: {summary['ready']}")
    print(f"Imported: {summary['imported']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Warnings: {summary['warnings']}")
    for warning in warnings:
        print(f"Warning: {warning}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import flashcards from Sheet or PDF into SQLite.")
    parser.add_argument("--source", choices=("sheet", "pdf"), default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    summary, warnings = run_import(source=args.source, dry_run=args.dry_run)
    print_summary(summary, warnings)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_import_flashcards.py -v
```

Expected: PASS all 3 tests.

- [ ] **Step 5: Commit unified CLI**

Run:

```powershell
git add tools/import_flashcards.py tests/test_import_flashcards.py
git commit -m "feat: add unified flashcard import cli"
```

## Task 6: Legacy PDF Command Compatibility

**Files:**
- Modify: `tools/import_n4_pdf.py`
- Modify: `tests/test_import_n4_pdf.py`

- [ ] **Step 1: Add backward compatibility test**

Append to `tests/test_import_n4_pdf.py`:

```python

def test_legacy_import_cards_uses_existing_dry_run_behavior():
    result = importer.import_cards([{"word": "石"}], dry_run=True)

    assert result == {"parsed": 1, "imported": 0}
```

- [ ] **Step 2: Run legacy tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_import_n4_pdf.py -v
```

Expected: PASS existing tests and new test before refactor.

- [ ] **Step 3: Verify legacy command stays unchanged**

Run:

```powershell
git diff -- tools/import_n4_pdf.py
```

Expected: no diff for `tools/import_n4_pdf.py`. The legacy command already imports from PDF and remains supported while `tools/import_flashcards.py` becomes the preferred command.

- [ ] **Step 4: Run legacy tests again**

Run:

```powershell
docker compose run --rm bot pytest tests/test_import_n4_pdf.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit legacy compatibility test**

Run:

```powershell
git add tests/test_import_n4_pdf.py
git commit -m "test: cover legacy pdf import dry run"
```

## Task 7: Deployment Docs

**Files:**
- Modify: `docs/docker-deployment-guide.md`

- [ ] **Step 1: Update import section**

In `docs/docker-deployment-guide.md`, replace or extend the flashcard import section with:

```markdown
## Import flashcard N4

Preferred source is Google Sheet worksheet `flashcards` in the spreadsheet configured by `GOOGLE_SHEET_ID`.

Required worksheet header:

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

Dry-run Sheet import:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

Import from Sheet:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

PDF fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf --dry-run
docker compose run --rm bot python tools/import_flashcards.py --source pdf
```

Legacy PDF command still works:

```powershell
docker compose run --rm bot python tools/import_n4_pdf.py --dry-run
```
```

- [ ] **Step 2: Run docs grep check**

Run:

```powershell
Select-String -Path docs/docker-deployment-guide.md -Pattern "tools/import_flashcards.py --source sheet", "worksheet `flashcards`"
```

Expected: both patterns found.

- [ ] **Step 3: Commit docs**

Run:

```powershell
git add docs/docker-deployment-guide.md
git commit -m "docs: document flashcard sheet import"
```

## Task 8: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_validation.py tests/test_flashcard_sheet_source.py tests/test_flashcard_pdf_source.py tests/test_import_flashcards.py tests/test_import_n4_pdf.py -v
```

Expected: all selected tests PASS.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
docker compose run --rm bot pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run Sheet dry-run against configured Google Sheet**

Run after worksheet is renamed to `flashcards`:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

Expected summary shape:

```text
Source: sheet
Fetched: 276
Ready: 276
Imported: 0
Skipped: 0
Warnings: <number based on blank optional fields>
```

- [ ] **Step 4: Inspect git status**

Run:

```powershell
git status --short
```

Expected: no unstaged implementation changes. `docs/flashcards_n4_sheet.tsv` may remain untracked from earlier manual Sheet export and should not be committed unless explicitly requested.

- [ ] **Step 5: Commit final verification note if any doc changed during verification**

Only run this if verification changed docs:

```powershell
git add docs/docker-deployment-guide.md
git commit -m "docs: clarify flashcard import verification"
```


