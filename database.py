import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timezone
from embeddings import generate_embedding

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


def save_request(method, url, status, time_ms, size_bytes, source="manual"):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO requests (method, url, status, time_ms, size_bytes, created_at, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (method, url, status, time_ms, size_bytes, datetime.now(timezone.utc).isoformat(), source),
    )
    conn.commit()
    conn.close()


def get_requests(limit=50):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, method, url, status, time_ms, size_bytes, created_at, source "
        "FROM requests ORDER BY id DESC LIMIT %s",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_embedding(source_url, content):
    embedding = generate_embedding(content)
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO api_embeddings (source_url, content, embedding, created_at)
        VALUES (%s, %s, %s, %s)
        """,
        (source_url, content, str(embedding), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def search_similar(query, limit=5):
    query_embedding = generate_embedding(query)
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT source_url, content, embedding <=> %s AS distance
        FROM api_embeddings
        ORDER BY distance
        LIMIT %s
        """,
        (str(query_embedding), limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    consulta = "información de personas y usuarios"
    print(f"Buscando: '{consulta}'\n")
    resultados = search_similar(consulta)
    for r in resultados:
        print(f"  distancia {r['distance']:.3f}  →  {r['source_url']}")
        print(f"     {r['content'][:70]}...\n")


