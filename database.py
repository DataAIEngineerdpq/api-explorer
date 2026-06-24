import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timezone

# Datos de conexión al PostgreSQL del contenedor
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "api_explorer",
    "user": "postgres",
    "password": "devpassword",
}


def get_connection():
    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
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
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (method, url, status, time_ms, size_bytes, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_requests(limit=50):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, method, url, status, time_ms, size_bytes, created_at "
        "FROM requests ORDER BY id DESC LIMIT %s",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    save_request("GET", "https://api.github.com/zen", 200, 123.4, 56)
    print("Guardado. Historial actual:")
    for fila in get_requests():
        print(fila)


