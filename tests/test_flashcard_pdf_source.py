from flashcard_sources import pdf_source


PDF_TEXT = """
番号 言葉 読み方 意味 例文
1 石 いし Đá
・一番大きいピラミッドをつくるのに石が
270万個も使われました。
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
"""


def test_load_flashcards_from_text_uses_common_validation():
    result = pdf_source.load_flashcards_from_text(PDF_TEXT, level="N4", source="n4_pdf")

    assert result.fetched == 2
    assert result.ready == 2
    assert [row["word"] for row in result.rows] == ["石", "経験"]
    assert result.rows[0]["level"] == "N4"
    assert result.rows[0]["source"] == "n4_pdf"
    assert result.rows[0]["status"] == "ready"
