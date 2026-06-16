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
