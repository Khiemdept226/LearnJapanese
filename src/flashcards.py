import datetime as dt
import os
import sqlite3
from typing import Optional

from config import DATABASE_PATH


VALID_GRADES = {"again", "hard", "good", "easy"}
DEFAULT_SETTINGS = {
    "preset": "jlpt_sprint",
    "level": "N4",
    "daily_new_limit": 15,
    "daily_review_limit": 60,
    "again_delay_minutes": 10,
    "stop_new_cards_before_exam_days": 7,
    "exam_date": "2026-07-05",
}
GOAL_PRESETS = {
    "light": {
        "preset": "light",
        "daily_new_limit": 3,
        "daily_review_limit": 10,
        "again_delay_minutes": 10,
        "stop_new_cards_before_exam_days": None,
        "exam_date": None,
    },
    "steady": {
        "preset": "steady",
        "daily_new_limit": 5,
        "daily_review_limit": 20,
        "again_delay_minutes": 10,
        "stop_new_cards_before_exam_days": None,
        "exam_date": None,
    },
    "heavy": {
        "preset": "heavy",
        "daily_new_limit": 10,
        "daily_review_limit": 40,
        "again_delay_minutes": 10,
        "stop_new_cards_before_exam_days": None,
        "exam_date": None,
    },
    "jlpt_sprint": {
        "preset": "jlpt_sprint",
        "daily_new_limit": 15,
        "daily_review_limit": 60,
        "again_delay_minutes": 10,
        "stop_new_cards_before_exam_days": 7,
        "exam_date": "2026-07-05",
    },
}


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def parse_dt(value):
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def get_connection():
    directory = os.path.dirname(DATABASE_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_flashcard_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            source TEXT NOT NULL,
            source_position INTEGER,
            word TEXT NOT NULL,
            reading TEXT,
            meaning TEXT NOT NULL,
            hanviet TEXT,
            example_jp TEXT,
            example_vi TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(level, source, word, reading)
        )
    """)
    # Migration: Add hanviet column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE flashcards ADD COLUMN hanviet TEXT")
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_flashcard_reviews (
            telegram_user_id INTEGER NOT NULL,
            flashcard_id INTEGER NOT NULL,
            state TEXT NOT NULL,
            due_at TEXT,
            interval_days REAL NOT NULL DEFAULT 0,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            repetitions INTEGER NOT NULL DEFAULT 0,
            lapses INTEGER NOT NULL DEFAULT 0,
            last_reviewed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (telegram_user_id, flashcard_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_flashcard_sessions (
            telegram_user_id INTEGER PRIMARY KEY,
            current_flashcard_id INTEGER,
            current_direction TEXT NOT NULL DEFAULT 'jp_to_vi',
            shown_at TEXT,
            answer_shown_at TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_flashcard_settings (
            telegram_user_id INTEGER PRIMARY KEY,
            preset TEXT NOT NULL,
            level TEXT NOT NULL DEFAULT 'N4',
            daily_new_limit INTEGER NOT NULL,
            daily_review_limit INTEGER NOT NULL,
            again_delay_minutes INTEGER NOT NULL,
            stop_new_cards_before_exam_days INTEGER,
            exam_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def upsert_flashcard(level, source, source_position, word, reading, meaning, hanviet=None, example_jp=None, example_vi=None):
    init_flashcard_db()
    now = utc_now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO flashcards (
            level, source, source_position, word, reading, meaning, hanviet, example_jp, example_vi, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(level, source, word, reading) DO UPDATE SET
            source_position = excluded.source_position,
            meaning = excluded.meaning,
            hanviet = excluded.hanviet,
            example_jp = excluded.example_jp,
            example_vi = excluded.example_vi,
            updated_at = excluded.updated_at
    """, (level, source, source_position, word, reading, meaning, hanviet, example_jp, example_vi, now, now))
    cursor.execute("""
        SELECT id FROM flashcards
        WHERE level = ? AND source = ? AND word = ? AND (reading IS ? OR reading = ?)
    """, (level, source, word, reading, reading))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["id"]



def upsert_flashcards(cards):
    init_flashcard_db()
    now = utc_now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for card in cards:
            cursor.execute("""
                INSERT INTO flashcards (
                    level, source, source_position, word, reading, meaning, hanviet, example_jp, example_vi, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(level, source, word, reading) DO UPDATE SET
                    source_position = excluded.source_position,
                    meaning = excluded.meaning,
                    hanviet = excluded.hanviet,
                    example_jp = excluded.example_jp,
                    example_vi = excluded.example_vi,
                    updated_at = excluded.updated_at
            """, (
                card["level"], card["source"], card.get("source_position"), card["word"], card.get("reading"),
                card["meaning"], card.get("hanviet"), card.get("example_jp"), card.get("example_vi"), now, now,
            ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return len(cards)

def get_flashcard(card_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def ensure_user_review(telegram_user_id, flashcard_id, now=None):
    init_flashcard_db()
    now = now or utc_now()
    timestamp = now.isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO user_flashcard_reviews (
            telegram_user_id, flashcard_id, state, due_at, interval_days, ease_factor,
            repetitions, lapses, last_reviewed_at, created_at, updated_at
        ) VALUES (?, ?, 'new', NULL, 0, 2.5, 0, 0, NULL, ?, ?)
    """, (telegram_user_id, flashcard_id, timestamp, timestamp))
    cursor.execute("""
        SELECT * FROM user_flashcard_reviews
        WHERE telegram_user_id = ? AND flashcard_id = ?
    """, (telegram_user_id, flashcard_id))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return dict(row) if row else None


def save_review_state(telegram_user_id, flashcard_id, review):
    now = utc_now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_flashcard_reviews SET
            state = ?, due_at = ?, interval_days = ?, ease_factor = ?, repetitions = ?,
            lapses = ?, last_reviewed_at = ?, updated_at = ?
        WHERE telegram_user_id = ? AND flashcard_id = ?
    """, (
        review["state"], review.get("due_at"), review["interval_days"], review["ease_factor"],
        review["repetitions"], review["lapses"], review.get("last_reviewed_at"), now,
        telegram_user_id, flashcard_id,
    ))
    conn.commit()
    conn.close()


def apply_review_grade(review, grade, now=None, again_delay_minutes=10):
    if grade not in VALID_GRADES:
        raise ValueError(f"Invalid flashcard grade: {grade}")
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


def pick_next_card(telegram_user_id, level="N4", now=None, include_new=True):
    init_flashcard_db()
    now = now or utc_now()
    now_iso = now.isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.* FROM flashcards f
        JOIN user_flashcard_reviews r ON r.flashcard_id = f.id AND r.telegram_user_id = ?
        WHERE f.level = ? AND r.state != 'suspended' AND r.due_at IS NOT NULL AND r.due_at <= ?
        ORDER BY r.due_at ASC, f.source_position ASC
        LIMIT 1
    """, (telegram_user_id, level, now_iso))
    row = cursor.fetchone()
    if not row and include_new:
        cursor.execute("""
            SELECT f.* FROM flashcards f
            LEFT JOIN user_flashcard_reviews r ON r.flashcard_id = f.id AND r.telegram_user_id = ?
            WHERE f.level = ? AND r.flashcard_id IS NULL
            ORDER BY f.source_position ASC, f.id ASC
            LIMIT 1
        """, (telegram_user_id, level))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None



def pick_new_card(telegram_user_id, level="N4"):
    init_flashcard_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.* FROM flashcards f
        LEFT JOIN user_flashcard_reviews r ON r.flashcard_id = f.id AND r.telegram_user_id = ?
        WHERE f.level = ? AND r.flashcard_id IS NULL
        ORDER BY f.source_position ASC, f.id ASC
        LIMIT 1
    """, (telegram_user_id, level))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
def pick_due_card(telegram_user_id, level="N4", now=None):
    return pick_next_card(telegram_user_id, level, now, include_new=False)


def get_flashcard_stats(telegram_user_id, level="N4", now=None):
    init_flashcard_db()
    now = now or utc_now()
    now_iso = now.isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM flashcards WHERE level = ?", (level,))
    total = cursor.fetchone()["count"]
    cursor.execute("""
        SELECT COUNT(*) AS count FROM flashcards f
        LEFT JOIN user_flashcard_reviews r ON r.flashcard_id = f.id AND r.telegram_user_id = ?
        WHERE f.level = ? AND r.flashcard_id IS NULL
    """, (telegram_user_id, level))
    new = cursor.fetchone()["count"]
    cursor.execute("""
        SELECT
            SUM(CASE WHEN due_at IS NOT NULL AND due_at <= ? AND state != 'suspended' THEN 1 ELSE 0 END) AS due,
            SUM(CASE WHEN state IN ('learning', 'relearning') THEN 1 ELSE 0 END) AS learning,
            SUM(CASE WHEN state = 'review' THEN 1 ELSE 0 END) AS review,
            SUM(lapses) AS lapses
        FROM user_flashcard_reviews r
        JOIN flashcards f ON f.id = r.flashcard_id
        WHERE r.telegram_user_id = ? AND f.level = ?
    """, (now_iso, telegram_user_id, level))
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




def get_reviewed_cards_between(telegram_user_id, level, start_at, end_at, limit=20):
    init_flashcard_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.*, r.state, r.due_at, r.lapses, r.last_reviewed_at
        FROM user_flashcard_reviews r
        JOIN flashcards f ON f.id = r.flashcard_id
        WHERE r.telegram_user_id = ?
          AND f.level = ?
          AND r.last_reviewed_at IS NOT NULL
          AND r.last_reviewed_at >= ?
          AND r.last_reviewed_at < ?
        ORDER BY r.last_reviewed_at DESC, f.source_position ASC
        LIMIT ?
    """, (telegram_user_id, level, start_at, end_at, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_user_settings(telegram_user_id):
    init_flashcard_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_flashcard_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return dict(DEFAULT_SETTINGS)
    settings = dict(DEFAULT_SETTINGS)
    settings.update(dict(row))
    return settings


def set_user_goal_preset(telegram_user_id, preset, now=None):
    if preset not in GOAL_PRESETS:
        raise ValueError(f"Invalid flashcard goal preset: {preset}")
    init_flashcard_db()
    now = now or utc_now()
    timestamp = now.isoformat()
    selected = dict(DEFAULT_SETTINGS)
    selected.update(GOAL_PRESETS[preset])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_flashcard_settings (
            telegram_user_id, preset, level, daily_new_limit, daily_review_limit,
            again_delay_minutes, stop_new_cards_before_exam_days, exam_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET
            preset = excluded.preset,
            level = excluded.level,
            daily_new_limit = excluded.daily_new_limit,
            daily_review_limit = excluded.daily_review_limit,
            again_delay_minutes = excluded.again_delay_minutes,
            stop_new_cards_before_exam_days = excluded.stop_new_cards_before_exam_days,
            exam_date = excluded.exam_date,
            updated_at = excluded.updated_at
    """, (
        telegram_user_id, selected["preset"], selected["level"], selected["daily_new_limit"],
        selected["daily_review_limit"], selected["again_delay_minutes"],
        selected["stop_new_cards_before_exam_days"], selected["exam_date"], timestamp, timestamp,
    ))
    conn.commit()
    conn.close()
    return selected



def reset_user_flashcard_progress(telegram_user_id):
    init_flashcard_db()
    conn = get_connection()
    cursor = conn.cursor()
    deleted = {}
    cursor.execute("DELETE FROM user_flashcard_reviews WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["reviews"] = cursor.rowcount
    cursor.execute("DELETE FROM user_flashcard_sessions WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["sessions"] = cursor.rowcount
    cursor.execute("DELETE FROM user_flashcard_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    deleted["settings"] = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def should_allow_new_cards(settings, today=None):
    if not settings.get("exam_date") or settings.get("stop_new_cards_before_exam_days") is None:
        return True
    today = today or utc_now().date()
    exam_date = dt.date.fromisoformat(settings["exam_date"])
    days_left = (exam_date - today).days
    return days_left > int(settings["stop_new_cards_before_exam_days"])

def set_current_session(telegram_user_id, flashcard_id, answer_shown=False, now=None):
    init_flashcard_db()
    now = now or utc_now()
    shown_at = now.isoformat()
    answer_shown_at = shown_at if answer_shown else None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_flashcard_sessions (
            telegram_user_id, current_flashcard_id, current_direction, shown_at, answer_shown_at, updated_at
        ) VALUES (?, ?, 'jp_to_vi', ?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET
            current_flashcard_id = excluded.current_flashcard_id,
            current_direction = excluded.current_direction,
            shown_at = excluded.shown_at,
            answer_shown_at = excluded.answer_shown_at,
            updated_at = excluded.updated_at
    """, (telegram_user_id, flashcard_id, shown_at, answer_shown_at, shown_at))
    conn.commit()
    conn.close()


def reveal_current_session(telegram_user_id, now=None):
    now = now or utc_now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_flashcard_sessions
        SET answer_shown_at = ?, updated_at = ?
        WHERE telegram_user_id = ? AND current_flashcard_id IS NOT NULL
    """, (now.isoformat(), now.isoformat(), telegram_user_id))
    conn.commit()
    conn.close()


def get_current_session(telegram_user_id):
    init_flashcard_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_flashcard_sessions WHERE telegram_user_id = ?", (telegram_user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def clear_current_session(telegram_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_flashcard_sessions
        SET current_flashcard_id = NULL, answer_shown_at = NULL, updated_at = ?
        WHERE telegram_user_id = ?
    """, (utc_now().isoformat(), telegram_user_id))
    conn.commit()
    conn.close()


def grade_current_card(telegram_user_id, grade, now=None):
    now = now or utc_now()
    session = get_current_session(telegram_user_id)
    if not session or not session.get("current_flashcard_id"):
        return None, "no_pending"
    if not session.get("answer_shown_at"):
        return None, "answer_not_shown"
    card_id = session["current_flashcard_id"]
    review = ensure_user_review(telegram_user_id, card_id, now)
    settings = get_user_settings(telegram_user_id)
    updated = apply_review_grade(review, grade, now, settings["again_delay_minutes"])
    save_review_state(telegram_user_id, card_id, updated)
    clear_current_session(telegram_user_id)
    return updated, None







