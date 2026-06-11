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
    "hanviet",
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
