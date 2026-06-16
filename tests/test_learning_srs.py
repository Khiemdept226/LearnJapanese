import datetime as dt

import learning_items


def _now():
    return dt.datetime(2026, 6, 10, 12, 0, tzinfo=dt.timezone.utc)


def _item(**overrides):
    row = {
        "item_id": "N4-VOCAB-0001",
        "level": "N4",
        "item_type": "vocab",
        "deck_id": "n4_vocab_core",
        "source": "unit",
        "source_position": 1,
        "front": "石",
        "reading": "いし",
        "meaning": "đá",
        "status": "ready",
        "tags": "noun,material",
    }
    row.update(overrides)
    return row


def test_apply_good_to_new_item_schedules_tomorrow():
    review = {
        "state": "new",
        "interval_days": 0,
        "ease_factor": 2.5,
        "repetitions": 0,
        "lapses": 0,
    }

    updated = learning_items.apply_review_grade(review, "good", _now())

    assert updated["state"] == "review"
    assert updated["interval_days"] == 1
    assert updated["repetitions"] == 1
    assert updated["lapses"] == 0
    assert updated["due_at"] == "2026-06-11T12:00:00+00:00"


def test_apply_again_schedules_relearning_in_ten_minutes():
    review = {
        "state": "review",
        "interval_days": 10,
        "ease_factor": 2.5,
        "repetitions": 4,
        "lapses": 1,
    }

    updated = learning_items.apply_review_grade(review, "again", _now(), again_delay_minutes=10)

    assert updated["state"] == "relearning"
    assert updated["interval_days"] == 0
    assert updated["due_at"] == "2026-06-10T12:10:00+00:00"
    assert updated["ease_factor"] == 2.3
    assert updated["repetitions"] == 0
    assert updated["lapses"] == 2


def test_pick_next_item_prefers_due_review_before_new(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    learning_items.upsert_learning_item(_item(item_id="N4-VOCAB-0001", source_position=1, front="新しい"))
    due_id = learning_items.upsert_learning_item(_item(item_id="N4-VOCAB-0002", source_position=2, front="石"))
    learning_items.ensure_user_review(123, due_id, _now())
    learning_items.save_review_state(123, due_id, {
        "state": "review",
        "due_at": "2026-06-09T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-08T12:00:00+00:00",
    })

    item = learning_items.pick_next_item(123, level="N4", item_type="vocab", deck_id="n4_vocab_core", now=_now())

    assert item["id"] == due_id
    assert item["front"] == "石"


def test_get_learning_stats_counts_new_due_learning_review_and_lapses(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    due_id = learning_items.upsert_learning_item(_item(item_id="N4-VOCAB-0001", source_position=1, front="石"))
    learning_id = learning_items.upsert_learning_item(_item(item_id="N4-VOCAB-0002", source_position=2, front="経験", meaning="kinh nghiệm"))
    learning_items.upsert_learning_item(_item(item_id="N4-VOCAB-0003", source_position=3, front="店員", meaning="nhân viên quán"))
    learning_items.ensure_user_review(123, due_id, _now())
    learning_items.save_review_state(123, due_id, {
        "state": "review",
        "due_at": "2026-06-09T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 2,
        "last_reviewed_at": "2026-06-08T12:00:00+00:00",
    })
    learning_items.ensure_user_review(123, learning_id, _now())
    learning_items.save_review_state(123, learning_id, {
        "state": "learning",
        "due_at": "2026-06-12T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 0,
        "lapses": 0,
        "last_reviewed_at": None,
    })

    stats = learning_items.get_learning_stats(123, level="N4", item_type="vocab", deck_id="n4_vocab_core", now=_now())

    assert stats == {
        "total": 3,
        "new": 1,
        "due": 1,
        "learning": 1,
        "review": 1,
        "lapses": 2,
    }


def test_reset_user_learning_progress_clears_only_selected_user(tmp_path, monkeypatch):
    db_path = tmp_path / "learning.sqlite3"
    monkeypatch.setattr(learning_items, "DATABASE_PATH", str(db_path))
    learning_items.init_learning_db()
    item_id = learning_items.upsert_learning_item(_item())
    learning_items.ensure_user_review(123, item_id, _now())
    learning_items.ensure_user_review(456, item_id, _now())
    learning_items.set_user_goal_preset(123, "light", now=_now())
    learning_items.set_user_goal_preset(456, "heavy", now=_now())
    learning_items.set_current_session(123, item_id, answer_shown=True, now=_now())
    learning_items.set_current_session(456, item_id, answer_shown=True, now=_now())

    deleted = learning_items.reset_user_learning_progress(123)

    assert deleted == {"reviews": 1, "sessions": 1, "settings": 1}
    assert learning_items.get_learning_stats(123, level="N4", item_type="vocab", deck_id="n4_vocab_core", now=_now())["new"] == 1
    assert learning_items.get_learning_stats(456, level="N4", item_type="vocab", deck_id="n4_vocab_core", now=_now())["new"] == 0
    assert learning_items.get_current_session(123) is None
    assert learning_items.get_current_session(456)["current_learning_item_id"] == item_id
    assert learning_items.get_user_settings(123)["preset"] == "jlpt_sprint"
    assert learning_items.get_user_settings(456)["preset"] == "heavy"
