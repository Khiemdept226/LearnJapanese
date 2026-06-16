import argparse
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

import flashcards

DEFAULT_PDF = Path("docs/20250312140417_Tﾃi li盻㎡ flash N4.pdf")
ENTRY_RE = re.compile(r"^(\d+)\s+(\S+)\s+(\S+)\s+(.+)$")
SKIP_LINES = (
    "逡ｪ蜿ｷ ",
    "Nh盻ｯng Ch盻ｯ Hﾃ｡n",
)


def _is_entry_line(line):
    match = ENTRY_RE.match(line.strip())
    if not match:
        return False
    return match.group(1).isdigit() and not line.strip().startswith("--")


def _clean_text(value):
    return " ".join(value.split()).strip()


def _looks_japanese(value):
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", value))


def _is_standalone_furigana(value):
    compact = value.strip()
    return bool(re.fullmatch(r"[\u3040-\u30ffー]{1,12}", compact))


def _looks_vietnamese(value):
    return not _looks_japanese(value) and bool(re.search(r"[A-Za-zÀ-ỹ0-9]", value))


def _split_example(lines):
    jp = []
    vi = []
    seen_vi = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("--") or line.isdigit():
            continue
        if line.startswith("・") or line.startswith("繝ｻ"):
            line = line[1:].strip()
        if not line:
            continue
        if _looks_japanese(line) and not seen_vi:
            if _is_standalone_furigana(line):
                continue
            jp.append(line)
        elif _looks_vietnamese(line):
            seen_vi = True
            vi.append(line)
        elif jp and not seen_vi:
            jp.append(line)
        elif vi:
            vi.append(line)
    return _clean_text(" ".join(jp)) or None, _clean_text(" ".join(vi)) or None


def _build_card(entry, level, source):
    position, word, reading, meaning, body = entry
    if "・" in meaning or "繝ｻ" in meaning:
        separator = "・" if "・" in meaning else "繝ｻ"
        meaning_part, inline_example = meaning.split(separator, 1)
        meaning = meaning_part.strip()
        body = [inline_example.strip()] + body
    example_jp, example_vi = _split_example(body)
    return {
        "level": level,
        "source": source,
        "source_position": int(position),
        "word": word,
        "reading": reading,
        "meaning": _clean_text(meaning),
        "example_jp": example_jp,
        "example_vi": example_vi,
    }


def parse_cards_from_text(text, level="N4", source="n4_pdf"):
    entries = []
    current = None
    lines = [line.strip() for line in text.splitlines()]
    for line in lines:
        if not line or any(line.startswith(prefix) for prefix in SKIP_LINES):
            continue
        if line.startswith("--"):
            continue
        match = ENTRY_RE.match(line)
        if match:
            number, word, reading, meaning = match.groups()
            if _looks_japanese(word):
                if current:
                    entries.append(current)
                current = [number, word, reading, meaning, []]
                continue
        if current:
            current[4].append(line)
    if current:
        entries.append(current)
    return [_build_card(entry, level, source) for entry in entries]


def extract_pdf_text(pdf_path):
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is required. Build/run through Docker image with requirements installed.")
    chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def import_cards(cards, dry_run=False):
    if dry_run:
        return {"parsed": len(cards), "imported": 0}
    imported = flashcards.upsert_flashcards(cards)
    return {"parsed": len(cards), "imported": imported}


def main():
    parser = argparse.ArgumentParser(description="Import N4 flashcards from PDF into SQLite.")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF))
    parser.add_argument("--level", default="N4")
    parser.add_argument("--source", default="n4_pdf")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    text = extract_pdf_text(pdf_path)
    cards = parse_cards_from_text(text, level=args.level, source=args.source)
    result = import_cards(cards, dry_run=args.dry_run)
    print(f"Parsed: {result['parsed']}")
    print(f"Imported: {result['imported']}")
    if cards:
        first = cards[0]
        print(f"First card: {first['word']} {first['reading']} {first['meaning']}")


if __name__ == "__main__":
    main()








