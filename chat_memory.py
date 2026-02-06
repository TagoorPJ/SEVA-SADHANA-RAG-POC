import sqlite3
from datetime import datetime
from pathlib import Path
# ⚠️ IMPORTANT:
# Use SAME DB path used by your agents
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR /"converted.db"



def init_chat_table():
    """Create conversations table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_message(role, message):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO conversations (role, message, created_at) VALUES (?, ?, ?)",
        (role, message, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_last_messages(limit=8):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT role, message
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    rows.reverse()

    return [{"role": r[0], "content": r[1]} for r in rows]
