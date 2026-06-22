import learning_items


def test_init_learning_db_creates_core_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    tables = learning_items.list_tables()
    assert {"decks", "learning_items", "user_learning_reviews", "user_learning_sessions", "user_learning_settings"}.issubset(tables)

def test_init_learning_db_creates_lane_settings_table(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    assert "user_learning_lane_settings" in learning_items.list_tables()


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
