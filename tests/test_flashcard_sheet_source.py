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
            "example_jp": "例文2",
            "example_vi": "dịch 2",
            "tags": "noun",
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
            "example_jp": "例文1",
            "example_vi": "dịch 1",
            "tags": "noun",
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
