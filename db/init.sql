-- Schema for API Explorer.
-- Runs automatically on first container start (empty volume).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS requests (
    id          SERIAL PRIMARY KEY,
    method      TEXT NOT NULL,
    url         TEXT NOT NULL,
    status      INTEGER,
    time_ms     REAL,
    size_bytes  INTEGER,
    created_at  TEXT NOT NULL,
    source      TEXT DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS api_embeddings (
    id          SERIAL PRIMARY KEY,
    source_url  TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(384),
    created_at  TEXT NOT NULL
);