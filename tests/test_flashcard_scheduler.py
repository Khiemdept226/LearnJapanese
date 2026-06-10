import flashcard_scheduler as scheduler


def test_format_daily_reminder_with_due_cards():
    text = scheduler.format_daily_reminder({
        "total": 100,
        "new": 5,
        "due": 3,
        "learning": 1,
        "review": 20,
        "lapses": 0,
    })

    assert "Ôn tập flashcard hôm nay" in text
    assert "Đến hạn: 3" in text
    assert "Từ mới còn lại: 5" in text


def test_should_send_daily_flashcard_message_when_due_or_new():
    assert scheduler.should_send_daily_flashcard_message({"due": 1, "new": 0}) is True
    assert scheduler.should_send_daily_flashcard_message({"due": 0, "new": 1}) is True
    assert scheduler.should_send_daily_flashcard_message({"due": 0, "new": 0}) is False
