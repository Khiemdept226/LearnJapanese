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
    assert "/show" in text
    assert "/again" not in text


def test_format_answer_contains_meaning_examples_and_grades():
    text = handlers.format_card_answer(CARD)

    assert "意味: Đá" in text
    assert "例文:" in text
    assert "Dịch:" in text
    assert "/again /hard /good /easy" in text


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
    assert handlers.grade_error_message("answer_not_shown") == "Bạn cần dùng /show để xem đáp án trước khi chấm."
