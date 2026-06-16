import argparse
import learning_items


def main(argv=None):
    parser = argparse.ArgumentParser(description="Migrate legacy flashcards into learning_items.")
    parser.add_argument("--default-deck-id", default="n4_vocab_core")
    args = parser.parse_args(argv)
    summary = learning_items.migrate_legacy_flashcards(default_deck_id=args.default_deck_id)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
