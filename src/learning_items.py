import datetime as dt
import json
import os
import sqlite3
from typing import Iterable, Optional

from config import DATABASE_PATH


def get_connection():
    directory = os.path.dirname(DATABASE_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_learning_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decks (
            deck_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            level TEXT NOT NULL,
            item_type TEXT NOT NULL,
            worksheet_name TEXT,
            source TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            description TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            level TEXT NOT NULL,
            item_type TEXT NOT NULL,
            deck_id TEXT NOT NULL,
            source TEXT,
            source_position INTEGER,
            front TEXT NOT NULL,
            back TEXT,
            reading TEXT,
            meaning TEXT,
            hanviet TEXT,
            example_jp TEXT,
            example_vi TEXT,
            tags TEXT,
            extra_json TEXT,
            status TEXT NOT NULL DEFAULT 'ready',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deck_id, item_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_learning_reviews (
            telegram_user_id INTEGER NOT NULL,
            learning_item_id INTEGER NOT NULL,
            state TEXT NOT NULL,
            due_at TEXT,
            interval_days REAL NOT NULL DEFAULT 0,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            repetitions INTEGER NOT NULL DEFAULT 0,
            lapses INTEGER NOT NULL DEFAULT 0,
            last_reviewed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (telegram_user_id, learning_item_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_learning_sessions (
            telegram_user_id INTEGER PRIMARY KEY,
            current_learning_item_id INTEGER,
            current_direction TEXT NOT NULL DEFAULT 'front_to_back',
            shown_at TEXT,
            answer_shown_at TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_learning_settings (
            telegram_user_id INTEGER PRIMARY KEY,
            preset TEXT NOT NULL,
            level TEXT NOT NULL DEFAULT 'N4',
            item_type TEXT,
            deck_id TEXT,
            tags TEXT,
            daily_new_limit INTEGER NOT NULL,
            daily_review_limit INTEGER NOT NULL,
            again_delay_minutes INTEGER NOT NULL,
            stop_new_cards_before_exam_days INTEGER,
            exam_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_items_level_type_deck ON learning_items(level, item_type, deck_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_items_status ON learning_items(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_learning_reviews_due ON user_learning_reviews(telegram_user_id, state, due_at)")
    conn.commit()
    conn.close()


def list_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    rows = cursor.fetchall()
    conn.close()
    return {row["name"] for row in rows}


def normalize_tags(tags):
    if tags is None:
        return None
    if isinstance(tags, str):
        parts = tags.split(",")
    else:
        parts = list(tags)
    normalized = []
    seen = set()
    for part in parts:
        tag = str(part).strip()
        if not tag or tag in seen:
            continue
        normalized.append(tag)
        seen.add(tag)
    return ",".join(normalized) if normalized else None


def normalize_extra(extra):
    if extra is None or extra == "":
        return None
    if isinstance(extra, str):
        return extra
    return json.dumps(extra, ensure_ascii=False, sort_keys=True)


def upsert_learning_item(row):
    init_learning_db()
    tags = normalize_tags(row.get("tags"))
    extra_json = normalize_extra(row.get("extra_json"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO learning_items (
            item_id, level, item_type, deck_id, source, source_position, front, back,
            reading, meaning, hanviet, example_jp, example_vi, tags, extra_json, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(deck_id, item_id) DO UPDATE SET
            level = excluded.level,
            item_type = excluded.item_type,
            source = excluded.source,
            source_position = excluded.source_position,
            front = excluded.front,
            back = excluded.back,
            reading = excluded.reading,
            meaning = excluded.meaning,
            hanviet = excluded.hanviet,
            example_jp = excluded.example_jp,
            example_vi = excluded.example_vi,
            tags = excluded.tags,
            extra_json = excluded.extra_json,
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
    """, (
        row["item_id"], row["level"], row["item_type"], row["deck_id"], row.get("source"),
        row.get("source_position"), row["front"], row.get("back"), row.get("reading"),
        row.get("meaning"), row.get("hanviet"), row.get("example_jp"), row.get("example_vi"),
        tags, extra_json, row.get("status", "ready"),
    ))
    cursor.execute("SELECT id FROM learning_items WHERE deck_id = ? AND item_id = ?", (row["deck_id"], row["item_id"]))
    item_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return item_id


def upsert_learning_items(rows: Iterable[dict]):
    count = 0
    for row in rows:
        upsert_learning_item(row)
        count += 1
    return count


def get_learning_item(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learning_items WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def find_learning_item(deck_id, item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learning_items WHERE deck_id = ? AND item_id = ?", (deck_id, item_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def _legacy_item_id(flashcard_id):
    return f"legacy-flashcard-{flashcard_id}"


def _ensure_default_deck(cursor, deck_id):
    cursor.execute("""
        INSERT INTO decks (
            deck_id, title, level, item_type, worksheet_name, source, status, description,
            created_at, updated_at
        ) VALUES (?, 'N4 Core Vocabulary', 'N4', 'vocab', 'vocab_n4_core', 'legacy', 'active', 'Migrated legacy flashcards', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(deck_id) DO UPDATE SET
            updated_at = CURRENT_TIMESTAMP
    """, (deck_id,))


def migrate_legacy_flashcards(default_deck_id="n4_vocab_core"):
    init_learning_db()
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_default_deck(cursor, default_deck_id)

    cursor.execute("SELECT * FROM flashcards ORDER BY id ASC")
    flashcard_rows = [dict(row) for row in cursor.fetchall()]
    conn.commit()
    conn.close()
    id_map = {}
    for card in flashcard_rows:
        learning_item_id = upsert_learning_item({
            "item_id": _legacy_item_id(card["id"]),
            "level": card["level"],
            "item_type": "vocab",
            "deck_id": default_deck_id,
            "source": card["source"],
            "source_position": card["source_position"],
            "front": card["word"],
            "back": card["meaning"],
            "reading": card["reading"],
            "meaning": card["meaning"],
            "hanviet": card["hanviet"],
            "example_jp": card["example_jp"],
            "example_vi": card["example_vi"],
            "tags": "legacy,vocab",
            "status": "ready",
        })
        id_map[card["id"]] = learning_item_id

    conn = get_connection()
    cursor = conn.cursor()
    reviews = 0
    if id_map:
        cursor.execute("SELECT * FROM user_flashcard_reviews ORDER BY telegram_user_id, flashcard_id")
        for review in cursor.fetchall():
            learning_item_id = id_map.get(review["flashcard_id"])
            if not learning_item_id:
                continue
            cursor.execute("""
                INSERT INTO user_learning_reviews (
                    telegram_user_id, learning_item_id, state, due_at, interval_days, ease_factor,
                    repetitions, lapses, last_reviewed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_user_id, learning_item_id) DO UPDATE SET
                    state = excluded.state,
                    due_at = excluded.due_at,
                    interval_days = excluded.interval_days,
                    ease_factor = excluded.ease_factor,
                    repetitions = excluded.repetitions,
                    lapses = excluded.lapses,
                    last_reviewed_at = excluded.last_reviewed_at,
                    updated_at = excluded.updated_at
            """, (
                review["telegram_user_id"], learning_item_id, review["state"], review["due_at"],
                review["interval_days"], review["ease_factor"], review["repetitions"], review["lapses"],
                review["last_reviewed_at"], review["created_at"], review["updated_at"],
            ))
            reviews += 1

        cursor.execute("SELECT * FROM user_flashcard_sessions ORDER BY telegram_user_id")
        for session in cursor.fetchall():
            current_learning_item_id = id_map.get(session["current_flashcard_id"])
            cursor.execute("""
                INSERT INTO user_learning_sessions (
                    telegram_user_id, current_learning_item_id, current_direction, shown_at, answer_shown_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    current_learning_item_id = excluded.current_learning_item_id,
                    current_direction = excluded.current_direction,
                    shown_at = excluded.shown_at,
                    answer_shown_at = excluded.answer_shown_at,
                    updated_at = excluded.updated_at
            """, (
                session["telegram_user_id"], current_learning_item_id, session["current_direction"],
                session["shown_at"], session["answer_shown_at"], session["updated_at"],
            ))

    settings = 0
    cursor.execute("SELECT * FROM user_flashcard_settings ORDER BY telegram_user_id")
    for setting in cursor.fetchall():
        cursor.execute("""
            INSERT INTO user_learning_settings (
                telegram_user_id, preset, level, item_type, deck_id, tags, daily_new_limit,
                daily_review_limit, again_delay_minutes, stop_new_cards_before_exam_days,
                exam_date, created_at, updated_at
            ) VALUES (?, ?, ?, 'vocab', ?, NULL, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_user_id) DO UPDATE SET
                preset = excluded.preset,
                level = excluded.level,
                item_type = excluded.item_type,
                deck_id = excluded.deck_id,
                tags = excluded.tags,
                daily_new_limit = excluded.daily_new_limit,
                daily_review_limit = excluded.daily_review_limit,
                again_delay_minutes = excluded.again_delay_minutes,
                stop_new_cards_before_exam_days = excluded.stop_new_cards_before_exam_days,
                exam_date = excluded.exam_date,
                updated_at = excluded.updated_at
        """, (
            setting["telegram_user_id"], setting["preset"], setting["level"], default_deck_id,
            setting["daily_new_limit"], setting["daily_review_limit"], setting["again_delay_minutes"],
            setting["stop_new_cards_before_exam_days"], setting["exam_date"], setting["created_at"], setting["updated_at"],
        ))
        settings += 1

    conn.commit()
    conn.close()
    return {"items": len(flashcard_rows), "reviews": reviews, "settings": settings}


VALID_GRADES = {"again", "hard", "good", "easy"}
DEFAULT_SETTINGS = {
    "preset": "jlpt_sprint",
    "level": "N4",
    "item_type": None,
    "deck_id": None,
    "tags": None,
    "daily_new_limit": 15,
    "daily_review_limit": 60,
    "again_delay_minutes": 10,
    "stop_new_cards_before_exam_days": 7,
    "exam_date": "2026-07-05",
}
GOAL_PRESETS = {
    "light": {"preset": "light", "daily_new_limit": 3, "daily_review_limit": 10, "again_delay_minutes": 10, "stop_new_cards_before_exam_days": None, "exam_date": None},
    "steady": {"preset": "steady", "daily_new_limit": 5, "daily_review_limit": 20, "again_delay_minutes": 10, "stop_new_cards_before_exam_days": None, "exam_date": None},
    "heavy": {"preset": "heavy", "daily_new_limit": 10, "daily_review_limit": 40, "again_delay_minutes": 10, "stop_new_cards_before_exam_days": None, "exam_date": None},
    "jlpt_sprint": {"preset": "jlpt_sprint", "daily_new_limit": 15, "daily_review_limit": 60, "again_delay_minutes": 10, "stop_new_cards_before_exam_days": 7, "exam_date": "2026-07-05"},
}


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def _item_filters(alias="li", level="N4", item_type=None, deck_id=None, tags=None):
    clauses = [f"{alias}.status = 'ready'"]
    params = []
    if level:
        clauses.append(f"{alias}.level = ?")
        params.append(level)
    if item_type:
        clauses.append(f"{alias}.item_type = ?")
        params.append(item_type)
    if deck_id:
        clauses.append(f"{alias}.deck_id = ?")
        params.append(deck_id)
    for tag in (normalize_tags(tags) or "").split(","):
        if not tag:
            continue
        clauses.append(f"(',' || COALESCE({alias}.tags, '') || ',') LIKE ?")
        params.append(f"%,{tag},%")
    return " AND ".join(clauses), params


def ensure_user_review(telegram_user_id, learning_item_id, now=None):
    init_learning_db()
    now = now or utc_now()
    timestamp = now.isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO user_learning_reviews (
            telegram_user_id, learning_item_id, state, due_at, interval_days, ease_factor,
            repetitions, lapses, last_reviewed_at, created_at, updated_at
        ) VALUES (?, ?, 'new', NULL, 0, 2.5, 0, 0, NULL, ?, ?)
    """, (telegram_user_id, learning_item_id, timestamp, timestamp))
    cursor.execute("""
        SELECT * FROM user_learning_reviews
        WHERE telegram_user_id = ? AND learning_item_id = ?
    """, (telegram_user_id, learning_item_id))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return dict(row) if row else None


def save_review_state(telegram_user_id, learning_item_id, review):
    now = utc_now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_learning_reviews SET
            state = ?, due_at = ?, interval_days = ?, ease_factor = ?, repetitions = ?,
            lapses = ?, last_reviewed_at = ?, updated_at = ?
        WHERE telegram_user_id = ? AND learning_item_id = ?
    """, (
        review["state"], review.get("due_at"), review["interval_days"], review["ease_factor"],
        review["repetitions"], review["lapses"], review.get("last_reviewed_at"), now,
        telegram_user_id, learning_item_id,
    ))
    conn.commit()
    conn.close()


def apply_review_grade(review, grade, now=None, again_delay_minutes=10):
    if grade not in VALID_GRADES:
        raise ValueError(f"Invalid learning item grade: {grade}")
    now = now or utc_now()
    interval = float(review.get("interval_days") or 0)
    ease = float(review.get("ease_factor") or 2.5)
    repetitions = int(review.get("repetitions") or 0)
    lapses = int(review.get("lapses") or 0)

    due_delta = None
    if grade == "again":
        state = "relearning"
        interval = 0
        due_delta = dt.timedelta(minutes=again_delay_minutes)
        ease = max(1.3, round(ease - 0.2, 2))
        repetitions = 0
        lapses += 1
    elif grade == "hard":
        state = "review"
        interval = max(1, round(interval * 1.2, 2))
        ease = max(1.3, round(ease - 0.15, 2))
        repetitions += 1
    elif grade == "good":
        state = "review"
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 3
        else:
            interval = max(1, round(interval * ease, 2))
    else:
        state = "review"
        repetitions += 1
        if repetitions == 1:
            interval = 4
        elif repetitions == 2:
            interval = 7
        else:
            interval = max(4, round(interval * ease * 1.5, 2))
        ease = round(ease + 0.15, 2)

    due_at = now + (due_delta or dt.timedelta(days=interval))
    return {
        "state": state,
        "due_at": due_at.isoformat(),
        "interval_days": interval,
        "ease_factor": ease,
        "repetitions": repetitions,
        "lapses": lapses,
        "last_reviewed_at": now.isoformat(),
    }


def pick_next_item(telegram_user_id, level="N4", now=None, include_new=True, item_type=None, deck_id=None, tags=None):
    init_learning_db()
    now = now or utc_now()
    filters, params = _item_filters("li", level, item_type, deck_id, tags)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT li.* FROM learning_items li
        JOIN user_learning_reviews r ON r.learning_item_id = li.id AND r.telegram_user_id = ?
        WHERE {filters} AND r.state != 'suspended' AND r.due_at IS NOT NULL AND r.due_at <= ?
        ORDER BY r.due_at ASC, li.source_position ASC, li.id ASC
        LIMIT 1
    """, [telegram_user_id] + params + [now.isoformat()])
    row = cursor.fetchone()
    if not row and include_new:
        cursor.execute(f"""
            SELECT li.* FROM learning_items li
            LEFT JOIN user_learning_reviews r ON r.learning_item_id = li.id AND r.telegram_user_id = ?
            WHERE {filters} AND r.learning_item_id IS NULL
            ORDER BY li.source_position ASC, li.id ASC
            LIMIT 1
        """, [telegram_user_id] + params)
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def pick_new_item(telegram_user_id, level="N4", item_type=None, deck_id=None, tags=None):
    return pick_next_item(telegram_user_id, level, include_new=True, item_type=item_type, deck_id=deck_id, tags=tags)


def pick_due_item(telegram_user_id, level="N4", now=None, item_type=None, deck_id=None, tags=None):
    return pick_next_item(telegram_user_id, level, now=now, include_new=False, item_type=item_type, deck_id=deck_id, tags=tags)


def get_learning_stats(telegram_user_id, level="N4", now=None, item_type=None, deck_id=None, tags=None):
    init_learning_db()
    now = now or utc_now()
    filters, params = _item_filters("li", level, item_type, deck_id, tags)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) AS count FROM learning_items li WHERE {filters}", params)
    total = cursor.fetchone()["count"]
    cursor.execute(f"""
        SELECT COUNT(*) AS count FROM learning_items li
        LEFT JOIN user_learning_reviews r ON r.learning_item_id = li.id AND r.telegram_user_id = ?
        WHERE {filters} AND r.learning_item_id IS NULL
    """, [telegram_user_id] + params)
    new = cursor.fetchone()["count"]
    cursor.execute(f"""
        SELECT
            SUM(CASE WHEN r.due_at IS NOT NULL AND r.due_at <= ? AND r.state != 'suspended' THEN 1 ELSE 0 END) AS due,
            SUM(CASE WHEN r.state IN ('learning', 'relearning') THEN 1 ELSE 0 END) AS learning,
            SUM(CASE WHEN r.state = 'review' THEN 1 ELSE 0 END) AS review,
            SUM(r.lapses) AS lapses
        FROM user_learning_reviews r
        JOIN learning_items li ON li.id = r.learning_item_id
        WHERE r.telegram_user_id = ? AND {filters}
    """, [now.isoformat(), telegram_user_id] + params)
    row = cursor.fetchone()
    conn.close()
    return {
        "total": total,
        "new": new,
        "due": int(row["due"] or 0),
        "learning": int(row["learning"] or 0),
        "review": int(row["review"] or 0),
        "lapses": int(row["lapses"] or 0),
    }


def get_reviewed_items_between(telegram_user_id, level, start_at, end_at, limit=20, item_type=None, deck_id=None, tags=None):
    init_learning_db()
    filters, params = _item_filters("li", level, item_type, deck_id, tags)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT li.*, r.state, r.due_at, r.lapses, r.last_reviewed_at
        FROM user_learning_reviews r
        JOIN learning_items li ON li.id = r.learning_item_id
        WHERE r.telegram_user_id = ? AND {filters}
          AND r.last_reviewed_at IS NOT NULL
          AND r.last_reviewed_at >= ?
          AND r.last_reviewed_at < ?
        ORDER BY r.last_reviewed_at DESC, li.source_position ASC
        LIMIT ?
    """, [telegram_user_id] + params + [start_at, end_at, limit])
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_settings(telegram_user_id):
    init_learning_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_learning_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return dict(DEFAULT_SETTINGS)
    settings = dict(DEFAULT_SETTINGS)
    settings.update(dict(row))
    return settings


def _save_settings(telegram_user_id, settings, now=None):
    now = now or utc_now()
    timestamp = now.isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_learning_settings (
            telegram_user_id, preset, level, item_type, deck_id, tags, daily_new_limit,
            daily_review_limit, again_delay_minutes, stop_new_cards_before_exam_days,
            exam_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET
            preset = excluded.preset,
            level = excluded.level,
            item_type = excluded.item_type,
            deck_id = excluded.deck_id,
            tags = excluded.tags,
            daily_new_limit = excluded.daily_new_limit,
            daily_review_limit = excluded.daily_review_limit,
            again_delay_minutes = excluded.again_delay_minutes,
            stop_new_cards_before_exam_days = excluded.stop_new_cards_before_exam_days,
            exam_date = excluded.exam_date,
            updated_at = excluded.updated_at
    """, (
        telegram_user_id, settings["preset"], settings["level"], settings.get("item_type"),
        settings.get("deck_id"), normalize_tags(settings.get("tags")), settings["daily_new_limit"],
        settings["daily_review_limit"], settings["again_delay_minutes"],
        settings.get("stop_new_cards_before_exam_days"), settings.get("exam_date"), timestamp, timestamp,
    ))
    conn.commit()
    conn.close()
    return settings


def set_user_goal_preset(telegram_user_id, preset, now=None):
    if preset not in GOAL_PRESETS:
        raise ValueError(f"Invalid flashcard goal preset: {preset}")
    settings = get_user_settings(telegram_user_id)
    settings.update(GOAL_PRESETS[preset])
    return _save_settings(telegram_user_id, settings, now=now)


def set_user_learning_filter(telegram_user_id, *, level=None, item_type=None, deck_id=None, tags=None):
    settings = get_user_settings(telegram_user_id)
    if level is not None:
        settings["level"] = level
    if item_type is not None:
        settings["item_type"] = item_type
    if deck_id is not None:
        settings["deck_id"] = deck_id
    if tags is not None:
        settings["tags"] = normalize_tags(tags)
    return _save_settings(telegram_user_id, settings)


def reset_user_learning_progress(telegram_user_id):
    init_learning_db()
    conn = get_connection()
    cursor = conn.cursor()
    deleted = {}
    cursor.execute("DELETE FROM user_learning_reviews WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["reviews"] = cursor.rowcount
    cursor.execute("DELETE FROM user_learning_sessions WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["sessions"] = cursor.rowcount
    cursor.execute("DELETE FROM user_learning_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["settings"] = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def should_allow_new_cards(settings, today=None):
    if not settings.get("exam_date") or settings.get("stop_new_cards_before_exam_days") is None:
        return True
    today = today or utc_now().date()
    exam_date = dt.date.fromisoformat(settings["exam_date"])
    return (exam_date - today).days > int(settings["stop_new_cards_before_exam_days"])


def set_current_session(telegram_user_id, learning_item_id, answer_shown=False, now=None):
    init_learning_db()
    now = now or utc_now()
    shown_at = now.isoformat()
    answer_shown_at = shown_at if answer_shown else None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_learning_sessions (
            telegram_user_id, current_learning_item_id, current_direction, shown_at, answer_shown_at, updated_at
        ) VALUES (?, ?, 'front_to_back', ?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET
            current_learning_item_id = excluded.current_learning_item_id,
            current_direction = excluded.current_direction,
            shown_at = excluded.shown_at,
            answer_shown_at = excluded.answer_shown_at,
            updated_at = excluded.updated_at
    """, (telegram_user_id, learning_item_id, shown_at, answer_shown_at, shown_at))
    conn.commit()
    conn.close()


def reveal_current_session(telegram_user_id, now=None):
    now = now or utc_now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_learning_sessions
        SET answer_shown_at = ?, updated_at = ?
        WHERE telegram_user_id = ? AND current_learning_item_id IS NOT NULL
    """, (now.isoformat(), now.isoformat(), telegram_user_id))
    conn.commit()
    conn.close()


def get_current_session(telegram_user_id):
    init_learning_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_learning_sessions WHERE telegram_user_id = ?", (telegram_user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def clear_current_session(telegram_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_learning_sessions
        SET current_learning_item_id = NULL, answer_shown_at = NULL, updated_at = ?
        WHERE telegram_user_id = ?
    """, (utc_now().isoformat(), telegram_user_id))
    conn.commit()
    conn.close()


def grade_current_item(telegram_user_id, grade, now=None):
    now = now or utc_now()
    session = get_current_session(telegram_user_id)
    if not session or not session.get("current_learning_item_id"):
        return None, "no_pending"
    if not session.get("answer_shown_at"):
        return None, "answer_not_shown"
    item_id = session["current_learning_item_id"]
    review = ensure_user_review(telegram_user_id, item_id, now)
    settings = get_user_settings(telegram_user_id)
    updated = apply_review_grade(review, grade, now, settings["again_delay_minutes"])
    save_review_state(telegram_user_id, item_id, updated)
    clear_current_session(telegram_user_id)
    return updated, None


# Compatibility names for existing flashcard handlers while they move to learning_items.
pick_next_card = pick_next_item
pick_new_card = pick_new_item
pick_due_card = pick_due_item
get_flashcard_stats = get_learning_stats
get_reviewed_cards_between = get_reviewed_items_between
reset_user_flashcard_progress = reset_user_learning_progress
grade_current_card = grade_current_item
get_flashcard = get_learning_item
