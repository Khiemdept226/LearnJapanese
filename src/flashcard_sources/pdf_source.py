from pathlib import Path

from config import FLASHCARD_PDF_LEVEL, FLASHCARD_PDF_PATH, FLASHCARD_PDF_SOURCE
from tools.import_n4_pdf import extract_pdf_text, parse_cards_from_text

from .validation import validate_rows


def _with_ready_status(cards):
    rows = []
    for card in cards:
        row = dict(card)
        row.setdefault("card_id", "")
        row.setdefault("tags", "")
        row["status"] = "ready"
        rows.append(row)
    return rows


def load_flashcards_from_text(text, level="N4", source="n4_pdf"):
    cards = parse_cards_from_text(text, level=level, source=source)
    return validate_rows(_with_ready_status(cards), default_level=level, default_source=source)


def load_flashcards(pdf_path=None, level=None, source=None):
    selected_path = Path(pdf_path or FLASHCARD_PDF_PATH)
    selected_level = level or FLASHCARD_PDF_LEVEL
    selected_source = source or FLASHCARD_PDF_SOURCE
    if not selected_path.exists():
        raise RuntimeError(f"PDF not found: {selected_path}")
    text = extract_pdf_text(selected_path)
    return load_flashcards_from_text(text, level=selected_level, source=selected_source)
