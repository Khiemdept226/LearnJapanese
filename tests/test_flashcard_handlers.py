import flashcard_handlers as handlers

CARD = {
    "id": 7,
    "word": "石",
    "reading": "いし",
    "meaning": "Đá",
    "example_jp": "一番大きいピラミッドをつくるのに石が270万個も使われました。",
    "example_vi": "270 vạn khối đá đã được sử dụng.",
}


def test_format_front_prompts_show_before_grading_without_reading():
    text = handlers.format_card_front(CARD)

    assert "言葉: 石" in text
    assert "読み方: いし" not in text
    assert "Tự nhớ cách đọc + nghĩa" in text
    assert "/again" not in text


def test_format_answer_contains_reading_meaning_examples_and_grades():
    text = handlers.format_card_answer(CARD)

    assert "読み方: いし" in text
    assert "意味: Đá" in text
    assert "例文:" in text
    assert "Dịch:" in text
    assert "Bạn nhớ mức nào?" in text


def test_format_stats_message_includes_today_count():
    text = handlers.format_stats({
        "total": 10,
        "new": 3,
        "due": 2,
        "learning": 1,
        "review": 4,
        "lapses": 1,
    }, today_count=5)

    assert "Tổng thẻ: 10" in text
    assert "Đến hạn: 2" in text
    assert "Từ mới: 3" in text
    assert "Hôm nay" in text
    assert "Đã chấm: 5" in text


def test_format_help_lists_flashcard_flow():
    text = handlers.format_help()

    assert "/flash - học thẻ tiếp theo" in text
    assert "/flash_stats - xem tiến độ" in text
    assert "Bấm Hiện đáp án" in text
    assert "Quên / Khó / Nhớ / Dễ" in text


def test_format_next_review_uses_flashcard_timezone(monkeypatch):
    monkeypatch.setattr(handlers, "FLASHCARD_TIMEZONE", "Asia/Bangkok")

    text = handlers.format_next_review({"due_at": "2026-06-10T12:10:00+00:00"})

    assert text == "Next review: 2026-06-10 19:10 (Asia/Bangkok)"


def test_format_today_card_list():
    text = handlers.format_today_card_list([CARD])

    assert "Các thẻ đã chấm hôm nay" in text
    assert "1. 石 / いし / Đá" in text


def test_today_cards_keyboard_links_to_card_detail():
    markup = handlers.today_cards_keyboard([CARD])

    assert markup.inline_keyboard[0][0].text == "石"
    assert markup.inline_keyboard[0][0].callback_data == "flash:card:7"


def test_grade_error_messages():
    assert handlers.grade_error_message("no_pending") == "Chưa có thẻ nào. Dùng /flash trước."
    assert handlers.grade_error_message("answer_not_shown") == "Bạn cần bấm Hiện đáp án trước khi chấm."


def test_front_keyboard_has_show_button():
    markup = handlers.front_keyboard()

    assert markup.inline_keyboard[0][0].text == "Hiện đáp án"
    assert markup.inline_keyboard[0][0].callback_data == "flash:show"


def test_answer_keyboard_maps_buttons_to_anki_grades():
    markup = handlers.answer_keyboard()
    buttons = [button for row in markup.inline_keyboard for button in row]

    assert [(button.text, button.callback_data) for button in buttons] == [
        ("Quên", "flash:grade:again"),
        ("Khó", "flash:grade:hard"),
        ("Nhớ", "flash:grade:good"),
        ("Dễ", "flash:grade:easy"),
    ]


def test_goal_keyboard_includes_jlpt_sprint():
    markup = handlers.goal_keyboard()
    buttons = [button for row in markup.inline_keyboard for button in row]

    assert any(button.text == "Nước rút JLPT" and button.callback_data == "flash:goal:jlpt_sprint" for button in buttons)
