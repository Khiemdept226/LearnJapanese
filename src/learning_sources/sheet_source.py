from config import GOOGLE_SHEET_ID
from sheets import get_client

from .deck_catalog import parse_deck_catalog
from .normalizers import normalize_row

DECK_CATALOG_WORKSHEET = "deck_catalog"


def _open_book(sheet_id=None):
    client = get_client()
    if not client:
        raise RuntimeError("Google Sheet client is not available")
    return client.open_by_key(sheet_id or GOOGLE_SHEET_ID)


def load_deck_catalog(sheet_id=None):
    book = _open_book(sheet_id)
    records = book.worksheet(DECK_CATALOG_WORKSHEET).get_all_records()
    return parse_deck_catalog(records)


def load_items_for_deck(deck, sheet_id=None):
    book = _open_book(sheet_id)
    records = book.worksheet(deck.worksheet_name).get_all_records()
    items = []
    for row in records:
        if str(row.get("status", "")).strip().lower() != "ready":
            continue
        items.append(normalize_row(row, deck.item_type, deck.level, deck.deck_id, deck.source))
    items.sort(key=lambda item: (item.get("source_position") is None, item.get("source_position") or 0, item["item_id"]))
    return items


def load_all_active_decks(sheet_id=None):
    book = _open_book(sheet_id)
    decks = parse_deck_catalog(book.worksheet(DECK_CATALOG_WORKSHEET).get_all_records())
    items = []
    for deck in decks:
        records = book.worksheet(deck.worksheet_name).get_all_records()
        for row in records:
            if str(row.get("status", "")).strip().lower() != "ready":
                continue
            items.append(normalize_row(row, deck.item_type, deck.level, deck.deck_id, deck.source))
    items.sort(key=lambda item: (item["deck_id"], item.get("source_position") is None, item.get("source_position") or 0, item["item_id"]))
    return items
