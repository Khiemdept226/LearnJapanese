import json

from learning_sources.normalizers import normalize_row


def test_normalize_vocab_row_uses_word_as_front():
    item = normalize_row({
        "item_id": "N4-VOCAB-0001",
        "source_position": "1",
        "word": "石",
        "reading": "いし",
        "meaning": "stone",
        "hanviet": "Thach",
        "example_jp": "石があります。",
        "example_vi": "Có đá.",
        "tags": "noun,material",
        "status": "ready",
    }, item_type="vocab", level="N4", deck_id="n4_vocab_core", source="sheet")

    assert item["front"] == "石"
    assert item["back"] == "stone"
    assert item["reading"] == "いし"
    assert item["meaning"] == "stone"
    assert item["source_position"] == 1


def test_normalize_kanji_row_stores_readings_in_extra_json():
    item = normalize_row({
        "item_id": "N4-KANJI-0001",
        "source_position": "2",
        "kanji": "石",
        "onyomi": "セキ",
        "kunyomi": "いし",
        "hanviet": "Thach",
        "meaning": "stone",
        "examples": "石, 宝石",
        "tags": "kanji",
        "status": "ready",
    }, item_type="kanji", level="N4", deck_id="n4_kanji_core", source="sheet")

    assert item["front"] == "石"
    assert item["back"] == "stone"
    extra = json.loads(item["extra_json"])
    assert extra["onyomi"] == "セキ"
    assert extra["kunyomi"] == "いし"
    assert extra["examples"] == "石, 宝石"

def test_normalize_kanji_row_stores_memo_and_related_words_in_extra_json():
    item = normalize_row({
        "item_id": "N4-KANJI-0002",
        "source_position": "3",
        "kanji": "回",
        "onyomi": "カイ",
        "kunyomi": "まわる, まわす",
        "hanviet": "Hồi",
        "meaning": "xoay, quay, lần",
        "examples": "回す, 回る",
        "memo": "Xoay tình hình xung quanh chỉ bằng một lời nói.",
        "related_words": "回す|まわす|xoay, vặn, chuyển\n回る|まわる|xoay quanh, đi vòng quanh",
        "tags": "kanji",
        "status": "ready",
    }, item_type="kanji", level="N4", deck_id="n4_kanji_core", source="sheet")

    extra = json.loads(item["extra_json"])
    assert extra["memo"] == "Xoay tình hình xung quanh chỉ bằng một lời nói."
    assert extra["related_words"] == "回す|まわす|xoay, vặn, chuyển\n回る|まわる|xoay quanh, đi vòng quanh"

def test_normalize_kanji_row_omits_empty_memo_and_related_words():
    item = normalize_row({
        "item_id": "N4-KANJI-0003",
        "source_position": "4",
        "kanji": "石",
        "onyomi": "セキ",
        "kunyomi": "いし",
        "meaning": "stone",
        "memo": "",
        "related_words": "",
        "status": "ready",
    }, item_type="kanji", level="N4", deck_id="n4_kanji_core", source="sheet")

    extra = json.loads(item["extra_json"])
    assert "memo" not in extra
    assert "related_words" not in extra


def test_normalize_grammar_row_stores_usage_in_extra_json():
    item = normalize_row({
        "item_id": "N4-GRAMMAR-0001",
        "source_position": "3",
        "pattern": "〜たことがある",
        "meaning": "have done",
        "usage": "past verb + ことがある",
        "example_jp": "日本へ行ったことがあります。",
        "example_vi": "Tôi từng đi Nhật.",
        "tags": "experience",
        "status": "ready",
    }, item_type="grammar", level="N4", deck_id="n4_grammar_core", source="sheet")

    assert item["front"] == "〜たことがある"
    assert item["back"] == "have done"
    extra = json.loads(item["extra_json"])
    assert extra["usage"] == "past verb + ことがある"


def test_normalize_kaiwa_row_stores_dialogue_shadowing_and_quiz():
    item = normalize_row({
        "item_id": "N4-KAIWA-0001",
        "source_position": "4",
        "title": "At the shop",
        "dialogue_jp": "いらっしゃいませ。",
        "dialogue_vi": "Xin chào quý khách.",
        "vocab": "店員",
        "grammar": "〜ください",
        "shadowing": "repeat x3",
        "quiz": "What did clerk say?",
        "quiz_answer": "Welcome",
        "tags": "daily,shop",
        "status": "ready",
    }, item_type="kaiwa", level="N4", deck_id="n4_kaiwa_daily", source="sheet")

    assert item["front"] == "At the shop"
    assert item["back"] == "いらっしゃいませ。"
    extra = json.loads(item["extra_json"])
    assert extra["dialogue_jp"] == "いらっしゃいませ。"
    assert extra["dialogue_vi"] == "Xin chào quý khách."
    assert extra["shadowing"] == "repeat x3"
    assert extra["quiz"] == "What did clerk say?"
    assert extra["quiz_answer"] == "Welcome"
