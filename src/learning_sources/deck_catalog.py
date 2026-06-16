from dataclasses import dataclass


@dataclass(frozen=True)
class DeckConfig:
    deck_id: str
    title: str
    level: str
    item_type: str
    worksheet_name: str
    source: str
    status: str
    description: str = ""


def _text(row, key, default=""):
    value = row.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def parse_deck_catalog(records):
    decks = []
    for row in records:
        status = _text(row, "status").lower()
        if status != "active":
            continue
        decks.append(DeckConfig(
            deck_id=_text(row, "deck_id"),
            title=_text(row, "title"),
            level=_text(row, "level"),
            item_type=_text(row, "item_type"),
            worksheet_name=_text(row, "worksheet_name"),
            source=_text(row, "source"),
            status=status,
            description=_text(row, "description"),
        ))
    return decks
