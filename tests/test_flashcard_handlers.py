import flashcard_handlers as handlers


CARD = {
    "word": "石",
    "reading": "いし",
    "meaning": "Đá",
    "example_jp": "一番大きいピラミッドをつくるのに石が270万個も使われました。",
    "example_vi": "270 vạn khối đá đã được sử dụng.",
}


def test_format_front_prompts_show_before_grading():
    text = handlers.format_card_front(CARD)

    assert "言葉: 石" in text
    assert "読み方: いし" in text
    assert "Hiện đáp án" in text
    assert "/again" not in text


def test_format_answer_contains_meaning_examples_and_grades():
    text = handlers.format_card_answer(CARD)

    assert "意味: Đá" in text
    assert "例文:" in text
    assert "Dịch:" in text
    assert "Bạn nhớ mức nào?" in text


def test_format_stats_message():
    text = handlers.format_stats({
        "total": 10,
        "new": 3,
        "due": 2,
        "learning": 1,
        "review": 4,
        "lapses": 1,
    })

    assert "Tổng thẻ: 10" in text
    assert "Đến hạn: 2" in text
    assert "Từ mới: 3" in text


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

