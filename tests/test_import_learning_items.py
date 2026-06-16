import tools.import_flashcards as importer


def test_import_all_decks_writes_learning_items(monkeypatch):
    rows = [{"item_id": "N4-VOCAB-0001", "level": "N4", "item_type": "vocab", "deck_id": "n4_vocab_core", "source": "sheet", "source_position": 1, "front": "ishi", "meaning": "stone", "status": "ready"}]
    monkeypatch.setattr(importer.learning_sheet_source, "load_all_active_decks", lambda: rows)
    written = {}
    monkeypatch.setattr(importer.learning_items, "upsert_learning_items", lambda items: written.setdefault("items", items) or len(items))
    summary = importer.run_learning_import(all_decks=True, dry_run=False)
    assert summary["imported"] == 1
    assert written["items"] == rows
