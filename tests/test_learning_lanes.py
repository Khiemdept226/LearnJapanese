import datetime as dt

import learning_items


def _now():
    return dt.datetime(2026, 6, 22, 12, 0, tzinfo=dt.timezone.utc)


def _item(item_id, item_type, source_position):
    return {
        "item_id": item_id,
        "level": "N4",
        "item_type": item_type,
        "deck_id": f"n4_{item_type}_core",
        "source": "unit",
        "source_position": source_position,
        "front": item_id,
        "meaning": "meaning",
        "status": "ready",
    }


def test_get_lane_settings_uses_type_defaults(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))

    settings = learning_items.get_lane_settings(123, "kanji")

    assert settings["item_type"] == "kanji"
    assert settings["level"] == "N4"
    assert settings["daily_new_limit"] == 3
    assert settings["daily_review_limit"] == 30


def test_set_lane_goal_preserves_other_lane(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))

    learning_items.set_lane_goal(123, "vocab", daily_new_limit=10, daily_review_limit=50)
    learning_items.set_lane_goal(123, "grammar", daily_new_limit=2, daily_review_limit=20)

    vocab = learning_items.get_lane_settings(123, "vocab")
    grammar = learning_items.get_lane_settings(123, "grammar")

    assert vocab["daily_new_limit"] == 10
    assert vocab["daily_review_limit"] == 50
    assert grammar["daily_new_limit"] == 2
    assert grammar["daily_review_limit"] == 20


def test_get_lane_stats_filters_by_item_type(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.upsert_learning_item(_item("VOCAB-1", "vocab", 1))
    learning_items.upsert_learning_item(_item("KANJI-1", "kanji", 2))

    vocab_stats = learning_items.get_lane_stats(123, "neword", now=_now())
    kanji_stats = learning_items.get_lane_stats(123, "kanji", now=_now())

    assert vocab_stats["total"] == 1
    assert vocab_stats["new"] == 1
    assert kanji_stats["total"] == 1
    assert kanji_stats["new"] == 1


def test_pick_next_lane_item_only_returns_requested_lane(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.upsert_learning_item(_item("VOCAB-1", "vocab", 1))
    learning_items.upsert_learning_item(_item("KANJI-1", "kanji", 2))

    item = learning_items.pick_next_lane_item(123, "kanji", now=_now())

    assert item["item_type"] == "kanji"
    assert item["front"] == "KANJI-1"


def test_pick_mix_item_prefers_due_lane_before_new(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    vocab_id = learning_items.upsert_learning_item(_item("VOCAB-1", "vocab", 1))
    learning_items.upsert_learning_item(_item("KANJI-1", "kanji", 2))
    learning_items.ensure_user_review(123, vocab_id, _now())
    learning_items.save_review_state(123, vocab_id, {
        "state": "review",
        "due_at": "2026-06-21T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-20T12:00:00+00:00",
    })

    item = learning_items.pick_mix_item(123, now=_now())

    assert item["item_type"] == "vocab"
    assert item["id"] == vocab_id


def test_pick_mix_item_returns_none_when_no_lane_has_cards(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))

    assert learning_items.pick_mix_item(123, now=_now()) is None
