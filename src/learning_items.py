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
