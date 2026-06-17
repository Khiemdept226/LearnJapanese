import flashcard_handlers as handlers

CARD = {
    "id": 7,
    "front": "石",
    "reading": "いし",
    "meaning": "đá",
    "example_jp": "石があります。",
    "example_vi": "Có đá.",
}


def test_format_front_prompts_show_before_grading_without_reading():
    text = handlers.format_card_front(CARD)

    assert "Mặt trước: 石" in text
    assert "Cách đọc: いし" not in text
    assert "Hiện đáp án" in text
    assert "/again" not in text


def test_format_answer_contains_reading_meaning_examples_and_grades():
    text = handlers.format_card_answer(CARD)

    assert "Mặt trước: 石" in text
    assert "Cách đọc: いし" in text
    assert "Nghĩa: đá" in text
    assert "Ví dụ:" in text
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
    assert "Thẻ mới: 3" in text
    assert "Hôm nay" in text
    assert "Đã chấm: 5" in text


def test_format_help_lists_flashcard_flow_and_settings_commands():
    text = handlers.format_help()

    assert "/flash - học thông minh" in text
    assert "/flash_new" in text
    assert "/flash_review" in text
    assert "/flash_stats" in text
    assert "/flash_reset" in text
    assert "/flash_settings" in text
    assert "/flash_level N4" in text
    assert "/flash_type vocab|kanji|grammar|kaiwa" in text
    assert "/flash_deck n4_vocab_core" in text
    assert "/flash_tags food,verb" in text


def test_format_next_review_uses_flashcard_timezone(monkeypatch):
    monkeypatch.setattr(handlers, "FLASHCARD_TIMEZONE", "Asia/Bangkok")

    text = handlers.format_next_review({"due_at": "2026-06-10T12:10:00+00:00"})

    assert text == "Next review: 2026-06-10 19:10 (Asia/Bangkok)"


def test_format_today_card_list():
    text = handlers.format_today_card_list([CARD])

    assert "Các thẻ đã chấm hôm nay" in text
    assert "1. 石 / いし / đá" in text


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


def test_reset_keyboard_requires_confirmation():
    markup = handlers.reset_keyboard()
    buttons = [button for row in markup.inline_keyboard for button in row]

    assert [(button.text, button.callback_data) for button in buttons] == [
        ("Hủy", "flash:reset:cancel"),
        ("Reset tiến độ", "flash:reset:confirm"),
    ]


def test_format_reset_confirm_message():
    text = handlers.format_reset_confirm()

    assert "xóa tiến độ flashcard" in text
    assert "Không xóa dữ liệu thẻ" in text


def test_format_settings_lists_learning_filters():
    text = handlers.format_settings({
        "preset": "jlpt_sprint",
        "level": "N4",
        "item_type": "vocab",
        "deck_id": "n4_vocab_core",
        "tags": "food,verb",
    })

    assert "Level: N4" in text
    assert "Type: vocab" in text
    assert "Deck: n4_vocab_core" in text
    assert "Tags: food,verb" in text


def test_format_card_front_accepts_legacy_card_shape():
    text = handlers.format_card_front({"id": 1, "word": "石", "meaning": "đá"})

    assert "石" in text

def test_format_item_answer_vocab_shows_core_fields():
    text = handlers.format_item_answer({
        "item_type": "vocab",
        "front": "石",
        "reading": "いし",
        "meaning": "đá",
        "hanviet": "Thạch",
        "example_jp": "石があります。",
        "example_vi": "Có đá.",
    })

    assert "Mặt trước: 石" in text
    assert "Cách đọc: いし" in text
    assert "Hán Việt: Thạch" in text
    assert "Nghĩa: đá" in text
    assert "Ví dụ: 石があります。" in text


def test_format_item_answer_kanji_reads_extra_json():
    text = handlers.format_item_answer({
        "item_type": "kanji",
        "front": "石",
        "meaning": "đá",
        "hanviet": "Thạch",
        "extra_json": '{"onyomi":"セキ","kunyomi":"いし","examples":"石, 宝石"}',
    })

    assert "Onyomi: セキ" in text
    assert "Kunyomi: いし" in text
    assert "Ví dụ: 石, 宝石" in text

def test_format_item_answer_kanji_shows_memo_and_related_words():
    text = handlers.format_item_answer({
        "item_type": "kanji",
        "front": "回",
        "meaning": "xoay, quay, lần",
        "hanviet": "Hồi",
        "extra_json": '{"onyomi":"カイ","kunyomi":"まわる, まわす","examples":"回す, 回る","memo":"Xoay tình hình xung quanh chỉ bằng một lời nói.","related_words":"回す|まわす|xoay, vặn, chuyển\\n回る|まわる|xoay quanh, đi vòng quanh"}',
    })

    assert "Cách nhớ:" in text
    assert "Xoay tình hình xung quanh chỉ bằng một lời nói." in text
    assert "Từ liên quan:" in text
    assert "1. 回す（まわす）- xoay, vặn, chuyển" in text
    assert "2. 回る（まわる）- xoay quanh, đi vòng quanh" in text

def test_format_item_answer_kanji_falls_back_for_malformed_related_words():
    text = handlers.format_item_answer({
        "item_type": "kanji",
        "front": "回",
        "meaning": "xoay, quay, lần",
        "extra_json": '{"related_words":"回収|かいしゅう|thu hồi, thu gom\\nmalformed related word"}',
    })

    assert "1. 回収（かいしゅう）- thu hồi, thu gom" in text
    assert "2. malformed related word" in text

def test_format_item_answer_kanji_omits_empty_memo_and_related_words_sections():
    text = handlers.format_item_answer({
        "item_type": "kanji",
        "front": "石",
        "meaning": "đá",
        "extra_json": '{"onyomi":"セキ"}',
    })

    assert "Cách nhớ:" not in text
    assert "Từ liên quan:" not in text


def test_format_item_answer_grammar_reads_usage():
    text = handlers.format_item_answer({
        "item_type": "grammar",
        "front": "〜たことがある",
        "meaning": "đã từng",
        "extra_json": '{"usage":"Vた + ことがある"}',
    })

    assert "Cách dùng: Vた + ことがある" in text


def test_format_item_answer_kaiwa_reads_dialogue_shadowing_and_quiz():
    text = handlers.format_item_answer({
        "item_type": "kaiwa",
        "front": "At the shop",
        "extra_json": '{"dialogue_jp":"いらっしゃいませ。","dialogue_vi":"Xin chào quý khách.","shadowing":"repeat x3","quiz":"Clerk says?","quiz_answer":"Welcome"}',
    })

    assert "Hội thoại JP: いらっしゃいませ。" in text
    assert "Hội thoại VI: Xin chào quý khách." in text
    assert "Shadowing: repeat x3" in text
    assert "Quiz: Clerk says?" in text
    assert "Đáp án: Welcome" in text
