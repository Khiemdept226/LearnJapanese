import tools.import_flashcards as importer
from flashcard_sources.validation import ValidationResult


def _result(rows, warnings=None):
    return ValidationResult(rows=rows, warnings=warnings or [], fetched=len(rows), ready=len(rows), skipped=0)


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

    summary, warnings = importer.run_import(source="sheet", dry_run=True)

    assert summary == {
        "source": "sheet",
        "fetched": 1,
        "ready": 1,
        "imported": 0,
        "skipped": 0,
        "warnings": 0,
    }
    assert warnings == []
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

    summary, warnings = importer.run_import(source="pdf", dry_run=False)

    assert written["rows"] == [{
        "level": "N4",
        "source": "n4_pdf",
        "source_position": 1,
        "word": "石",
        "reading": "いし",
        "meaning": "Đá",
        "example_jp": "例文",
        "example_vi": "dịch",
    }]
    assert warnings == []
    assert summary["imported"] == 1
    assert summary["source"] == "pdf"


def test_run_import_rejects_unknown_source():
    try:
        importer.run_import(source="bad", dry_run=True)
    except ValueError as exc:
        assert str(exc) == "Unsupported flashcard import source: bad"
    else:
        raise AssertionError("ValueError was not raised")
