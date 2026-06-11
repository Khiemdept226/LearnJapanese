from config import FLASHCARD_SHEET_LEVEL, FLASHCARD_SHEET_NAME, GOOGLE_SHEET_ID
from sheets import get_client

from .validation import validate_rows


DEFAULT_SHEET_SOURCE = "n4_md"


def load_flashcards(sheet_id=None, worksheet_name=None, default_level=None, default_source=DEFAULT_SHEET_SOURCE):
    client = get_client()
    if not client:
        raise RuntimeError("Google Sheet client is not available")

    selected_sheet_id = sheet_id or GOOGLE_SHEET_ID
    selected_worksheet = worksheet_name or FLASHCARD_SHEET_NAME
    selected_level = default_level or FLASHCARD_SHEET_LEVEL

    book = client.open_by_key(selected_sheet_id)
    worksheet = book.worksheet(selected_worksheet)
    records = worksheet.get_all_records()
    return validate_rows(records, default_level=selected_level, default_source=default_source)
