import json


def _text(row, key, default=None):
    value = row.get(key, default)
    if value is None:
        return default
    value = str(value).strip()
    return value if value != "" else default


def _int(row, key):
    value = _text(row, key)
    if value is None:
        return None
    return int(value)


def _extra(fields):
    data = {key: value for key, value in fields.items() if value not in (None, "")}
    return json.dumps(data, ensure_ascii=False, sort_keys=True) if data else None


def _base(row, item_type, level, deck_id, source, front, back, **extra):
    return {
        "item_id": _text(row, "item_id"),
        "level": _text(row, "level", level),
        "item_type": item_type,
        "deck_id": _text(row, "deck_id", deck_id),
        "source": source,
        "source_position": _int(row, "source_position"),
        "front": front,
        "back": back,
        "reading": extra.get("reading"),
        "meaning": extra.get("meaning"),
        "hanviet": extra.get("hanviet"),
        "example_jp": extra.get("example_jp"),
        "example_vi": extra.get("example_vi"),
        "tags": _text(row, "tags"),
        "extra_json": extra.get("extra_json"),
        "status": _text(row, "status", "ready"),
    }


def normalize_row(row, item_type, level, deck_id, source):
    if item_type == "vocab":
        meaning = _text(row, "meaning")
        return _base(
            row,
            item_type,
            level,
            deck_id,
            source,
            front=_text(row, "word"),
            back=meaning,
            reading=_text(row, "reading"),
            meaning=meaning,
            hanviet=_text(row, "hanviet"),
            example_jp=_text(row, "example_jp"),
            example_vi=_text(row, "example_vi"),
        )
    if item_type == "kanji":
        meaning = _text(row, "meaning")
        return _base(
            row,
            item_type,
            level,
            deck_id,
            source,
            front=_text(row, "kanji"),
            back=meaning,
            meaning=meaning,
            hanviet=_text(row, "hanviet"),
            extra_json=_extra({
                "onyomi": _text(row, "onyomi"),
                "kunyomi": _text(row, "kunyomi"),
                "examples": _text(row, "examples"),
                "memo": _text(row, "memo"),
                "related_words": _text(row, "related_words"),
            }),
        )
    if item_type == "grammar":
        meaning = _text(row, "meaning")
        return _base(
            row,
            item_type,
            level,
            deck_id,
            source,
            front=_text(row, "pattern"),
            back=meaning,
            meaning=meaning,
            example_jp=_text(row, "example_jp"),
            example_vi=_text(row, "example_vi"),
            extra_json=_extra({"usage": _text(row, "usage")}),
        )
    if item_type == "kaiwa":
        dialogue_jp = _text(row, "dialogue_jp")
        return _base(
            row,
            item_type,
            level,
            deck_id,
            source,
            front=_text(row, "title"),
            back=dialogue_jp,
            extra_json=_extra({
                "dialogue_jp": dialogue_jp,
                "dialogue_vi": _text(row, "dialogue_vi"),
                "vocab": _text(row, "vocab"),
                "grammar": _text(row, "grammar"),
                "shadowing": _text(row, "shadowing"),
                "quiz": _text(row, "quiz"),
                "quiz_answer": _text(row, "quiz_answer"),
            }),
        )
    raise ValueError(f"Unsupported learning item type: {item_type}")
