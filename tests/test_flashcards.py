import datetime as dt

import flashcards


def _now():
    return dt.datetime(2026, 6, 10, 12, 0, tzinfo=dt.timezone.utc)


def test_apply_good_to_new_card_schedules_tomorrow():
    review = {
        "state": "new",
        "interval_days": 0,
        "ease_factor": 2.5,
        "repetitions": 0,
        "lapses": 0,
    }

    updated = flashcards.apply_review_grade(review, "good", _now())

    assert updated["state"] == "review"
    assert updated["interval_days"] == 1
    assert updated["repetitions"] == 1
    assert updated["lapses"] == 0
    assert updated["due_at"] == "2026-06-11T12:00:00+00:00"


def test_apply_again_moves_card_to_relearning_and_counts_lapse():
    review = {
        "state": "review",
        "interval_days": 10,
        "ease_factor": 2.5,
        "repetitions": 4,
        "lapses": 1,
    }

    updated = flashcards.apply_review_grade(review, "again", _now())

    assert updated["state"] == "relearning"
    assert updated["interval_days"] == 0
    assert updated["due_at"] == "2026-06-10T12:10:00+00:00"
    assert updated["ease_factor"] == 2.3
    assert updated["repetitions"] == 0
    assert updated["lapses"] == 2


def test_pick_next_card_prefers_due_review_before_new(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()
    first_id = flashcards.upsert_flashcard("N4", "unit", 1, "新しい", "あたらしい", "mới", "例文1", "dịch 1")
    due_id = flashcards.upsert_flashcard("N4", "unit", 2, "石", "いし", "đá", "例文2", "dịch 2")
    flashcards.ensure_user_review(123, due_id, _now())
    flashcards.save_review_state(123, due_id, {
        "state": "review",
        "due_at": "2026-06-09T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-08T12:00:00+00:00",
    })

    card = flashcards.pick_next_card(123, "N4", _now())

    assert card["id"] == due_id
    assert card["word"] == "石"


def test_get_stats_counts_new_due_learning_and_review(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()
    due_id = flashcards.upsert_flashcard("N4", "unit", 1, "石", "いし", "đá", None, None)
    learning_id = flashcards.upsert_flashcard("N4", "unit", 2, "経験", "けいけん", "kinh nghiệm", None, None)
    flashcards.upsert_flashcard("N4", "unit", 3, "店員", "てんいん", "nhân viên quán", None, None)
    flashcards.ensure_user_review(123, due_id, _now())
    flashcards.save_review_state(123, due_id, {
        "state": "review",
        "due_at": "2026-06-09T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-08T12:00:00+00:00",
    })
    flashcards.ensure_user_review(123, learning_id, _now())
    flashcards.save_review_state(123, learning_id, {
        "state": "learning",
        "due_at": "2026-06-12T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 0,
        "lapses": 0,
        "last_reviewed_at": None,
    })

    stats = flashcards.get_flashcard_stats(123, "N4", _now())

    assert stats == {
        "total": 3,
        "new": 1,
        "due": 1,
        "learning": 1,
        "review": 1,
        "lapses": 0,
    }


def test_apply_again_schedules_after_ten_minutes():
    review = {
        "state": "review",
        "interval_days": 10,
        "ease_factor": 2.5,
        "repetitions": 4,
        "lapses": 1,
    }

    updated = flashcards.apply_review_grade(review, "again", _now(), again_delay_minutes=10)

    assert updated["state"] == "relearning"
    assert updated["interval_days"] == 0
    assert updated["due_at"] == "2026-06-10T12:10:00+00:00"
    assert updated["lapses"] == 2


def test_goal_preset_jlpt_sprint_is_saved_per_user(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()

    settings = flashcards.set_user_goal_preset(123, "jlpt_sprint", now=_now())
    loaded = flashcards.get_user_settings(123)

    assert settings["preset"] == "jlpt_sprint"
    assert loaded["daily_new_limit"] == 15
    assert loaded["daily_review_limit"] == 60
    assert loaded["again_delay_minutes"] == 10
    assert loaded["stop_new_cards_before_exam_days"] == 7



def test_default_settings_use_jlpt_sprint_for_current_exam_push(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()

    settings = flashcards.get_user_settings(999)

    assert settings["preset"] == "jlpt_sprint"
    assert settings["daily_new_limit"] == 15
    assert settings["daily_review_limit"] == 60
    assert settings["exam_date"] == "2026-07-05"


def test_get_reviewed_cards_between_returns_cards_for_window(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()
    inside_id = flashcards.upsert_flashcard("N4", "unit", 1, "石", "いし", "đá", "例文", "dịch")
    outside_id = flashcards.upsert_flashcard("N4", "unit", 2, "経験", "けいけん", "kinh nghiệm", None, None)
    flashcards.ensure_user_review(123, inside_id, _now())
    flashcards.save_review_state(123, inside_id, {
        "state": "review",
        "due_at": "2026-06-11T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-10T05:00:00+00:00",
    })
    flashcards.ensure_user_review(123, outside_id, _now())
    flashcards.save_review_state(123, outside_id, {
        "state": "review",
        "due_at": "2026-06-11T12:00:00+00:00",
        "interval_days": 1,
        "ease_factor": 2.5,
        "repetitions": 1,
        "lapses": 0,
        "last_reviewed_at": "2026-06-09T23:59:59+00:00",
    })

    cards = flashcards.get_reviewed_cards_between(
        123,
        "N4",
        "2026-06-10T00:00:00+00:00",
        "2026-06-11T00:00:00+00:00",
    )

    assert [card["id"] for card in cards] == [inside_id]
    assert cards[0]["word"] == "石"
    assert cards[0]["last_reviewed_at"] == "2026-06-10T05:00:00+00:00"


def test_reset_user_flashcard_progress_clears_only_selected_user(tmp_path, monkeypatch):
    db_path = tmp_path / "flash.sqlite3"
    monkeypatch.setattr(flashcards, "DATABASE_PATH", str(db_path))
    flashcards.init_flashcard_db()
    card_id = flashcards.upsert_flashcard("N4", "unit", 1, "石", "いし", "đá", None, None)
    flashcards.ensure_user_review(123, card_id, _now())
    flashcards.ensure_user_review(456, card_id, _now())
    flashcards.set_user_goal_preset(123, "light", now=_now())
    flashcards.set_user_goal_preset(456, "heavy", now=_now())
    flashcards.set_current_session(123, card_id, answer_shown=True, now=_now())
    flashcards.set_current_session(456, card_id, answer_shown=True, now=_now())

    deleted = flashcards.reset_user_flashcard_progress(123)

    assert deleted == {"reviews": 1, "sessions": 1, "settings": 1}
    assert flashcards.get_flashcard_stats(123, "N4", _now())["new"] == 1
    assert flashcards.get_flashcard_stats(456, "N4", _now())["new"] == 0
    assert flashcards.get_current_session(123) is None
    assert flashcards.get_current_session(456)["current_flashcard_id"] == card_id
    assert flashcards.get_user_settings(123)["preset"] == "jlpt_sprint"
    assert flashcards.get_user_settings(456)["preset"] == "heavy"
