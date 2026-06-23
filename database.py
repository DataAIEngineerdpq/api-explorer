import sqlite3
from datetime import datetime, timezone

DB_PATH = "api_explorer.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            status INTEGER,
            time_ms REAL,
            size_bytes INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_request(method, url, status, time_ms, size_bytes):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO requests (method, url, status, time_ms, size_bytes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (method, url, status, time_ms, size_bytes, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_requests(limit=50):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, method, url, status, time_ms, size_bytes, created_at "
        "FROM requests ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    historial = get_requests()
    for fila in historial:
        print(fila)


