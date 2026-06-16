from learning_sources.deck_catalog import parse_deck_catalog


def test_parse_deck_catalog_returns_only_active_decks():
    decks = parse_deck_catalog([
        {
            "deck_id": "n4_vocab_core",
            "title": "N4 Core Vocabulary",
            "level": "N4",
            "item_type": "vocab",
            "worksheet_name": "vocab_n4_core",
            "source": "manual",
            "status": "active",
            "description": "Core N4 vocabulary",
        },
        {
            "deck_id": "n4_old",
            "title": "Old",
            "level": "N4",
            "item_type": "vocab",
            "worksheet_name": "old",
            "source": "manual",
            "status": "inactive",
            "description": "Skip me",
        },
    ])

    assert len(decks) == 1
    assert decks[0].deck_id == "n4_vocab_core"
    assert decks[0].worksheet_name == "vocab_n4_core"
    assert decks[0].item_type == "vocab"
