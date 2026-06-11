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
