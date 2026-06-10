import tools.import_n4_pdf as importer


SAMPLE = """
1
Những Chữ Hán, Từ vựng xuất hiện trong đề N4 - 2012
番号 言葉 読み方 意味 例文
1 石 いし Đá
・一番大きいピラミッドをつくるのに石が
270 万個も使われました。
270 vạn khối đá đã được sử dụng để xây lên
Kim tự tháp lớn nhất.
2 経験 けいけん Kinh nghiệm
・先生は面白
おもしろ
いし、親切
しんせつ
だし、それに経験も
あります。
Thầy giáo tôi vừa thân thiện, thú vị lại còn có
nhiều kinh nghiệm.
3 店員 てんいん Nhân viên quán
・あの店 員はいつも優
やさ
しい。
Nhân viên quán đó lúc nào cũng hiền lành tốt
bụng.
4 食堂 しょくどう Nhà ăn ・この大学には食堂がない。
Trường học này không có nhà ăn.
"""


def test_parse_cards_from_pdf_text_sample():
    cards = importer.parse_cards_from_text(SAMPLE, level="N4", source="n4_pdf")

    assert cards[0] == {
        "level": "N4",
        "source": "n4_pdf",
        "source_position": 1,
        "word": "石",
        "reading": "いし",
        "meaning": "Đá",
        "example_jp": "一番大きいピラミッドをつくるのに石が 270 万個も使われました。",
        "example_vi": "270 vạn khối đá đã được sử dụng để xây lên Kim tự tháp lớn nhất.",
    }
    assert cards[1]["word"] == "経験"
    assert cards[1]["reading"] == "けいけん"
    assert cards[1]["meaning"] == "Kinh nghiệm"
    assert "先生は面白" in cards[1]["example_jp"]
    assert "nhiều kinh nghiệm" in cards[1]["example_vi"]
    assert cards[2]["word"] == "店員"
    assert cards[2]["meaning"] == "Nhân viên quán"
    assert cards[3]["word"] == "食堂"
    assert cards[3]["example_jp"] == "この大学には食堂がない。"
