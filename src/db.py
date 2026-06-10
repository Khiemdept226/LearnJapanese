import sqlite3
import datetime
import os
from .config import DATABASE_PATH

def get_connection():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            current_lesson_order INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Create sent_lessons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER,
            lesson_id TEXT,
            sent_at TEXT
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(telegram_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_or_update_user(telegram_user_id, chat_id, username, initial_order=1):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    cursor.execute("SELECT telegram_user_id FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE users SET chat_id = ?, username = ?, updated_at = ?
            WHERE telegram_user_id = ?
        ''', (chat_id, username, now, telegram_user_id))
    else:
        cursor.execute('''
            INSERT INTO users (telegram_user_id, chat_id, username, current_lesson_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (telegram_user_id, chat_id, username, initial_order, now, now))
        
    conn.commit()
    conn.close()

def update_user_lesson_order(telegram_user_id, new_order):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute('''
        UPDATE users SET current_lesson_order = ?, updated_at = ?
        WHERE telegram_user_id = ?
    ''', (new_order, now, telegram_user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def record_sent_lesson(telegram_user_id, lesson_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute('''
        INSERT INTO sent_lessons (telegram_user_id, lesson_id, sent_at)
        VALUES (?, ?, ?)
    ''', (telegram_user_id, lesson_id, now))
    conn.commit()
    conn.close()

def get_latest_sent_lesson(telegram_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT lesson_id FROM sent_lessons
        WHERE telegram_user_id = ?
        ORDER BY sent_at DESC LIMIT 1
    ''', (telegram_user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['lesson_id'] if row else None
