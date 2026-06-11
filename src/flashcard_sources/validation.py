from dataclasses import dataclass


OPTIONAL_WARNING_FIELDS = ("reading", "example_jp", "example_vi", "tags")
REQUIRED_FIELDS = ("level", "source_position", "word", "meaning")


@dataclass
class ValidationResult:
    rows: list[dict]
    warnings: list[str]
    fetched: int
    ready: int
    skipped: int


def _clean(value):
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _normalize_raw_row(row, default_level, default_source):
    return {
        "card_id": _clean(row.get("card_id")),
        "level": _clean(row.get("level")) or default_level,
        "source": _clean(row.get("source")) or default_source,
        "source_position": _clean(row.get("source_position")),
        "word": _clean(row.get("word")),
        "reading": _clean(row.get("reading")),
        "meaning": _clean(row.get("meaning")),
        "hanviet": _clean(row.get("hanviet")),
        "example_jp": _clean(row.get("example_jp")),
        "example_vi": _clean(row.get("example_vi")),
        "tags": _clean(row.get("tags")),
        "status": (_clean(row.get("status")) or "ready").lower(),
    }


def validate_rows(rows, default_level="N4", default_source="n4_pdf"):
    warnings = []
    valid_by_key = {}
    ready = 0
    skipped = 0

    for index, raw_row in enumerate(rows, start=1):
        row = _normalize_raw_row(raw_row, default_level, default_source)
        if row["status"] != "ready":
            skipped += 1
            warnings.append(f"row {index} skipped: status={row['status']}")
            continue

        ready += 1
        missing = next((field for field in REQUIRED_FIELDS if not row.get(field)), None)
        if missing:
            skipped += 1
            warnings.append(f"row {index} skipped: missing {missing}")
            continue

        try:
            row["source_position"] = int(row["source_position"])
        except ValueError:
            skipped += 1
            warnings.append(f"row {index} skipped: invalid source_position={row['source_position']}")
            continue

        for field in OPTIONAL_WARNING_FIELDS:
            if not row.get(field):
                warnings.append(f"row {index} warning: missing {field}")

        key = (row["level"], row["source"], row["word"], row["reading"])
        if key in valid_by_key:
            joined = "|".join(key)
            warnings.append(f"row {index} warning: duplicate key {joined} overwrites earlier row")
        valid_by_key[key] = row

    rows_out = sorted(valid_by_key.values(), key=lambda item: item["source_position"])
    return ValidationResult(
        rows=rows_out,
        warnings=warnings,
        fetched=len(rows),
        ready=ready,
        skipped=skipped,
    )
