# API Explorer

A local-first tool to explore, profile, and model REST APIs — with an AI layer
(semantic search, RAG, and a ReAct agent) running entirely on local models.

## Stack

- **Backend:** FastAPI (HTTP proxy, profiling, export, AI endpoints)
- **Frontend:** single-file vanilla JS (`static/index.html`), no build step
- **Database:** PostgreSQL 16 + pgvector (Docker)
- **AI:** local LLMs via Ollama, local embeddings via sentence-transformers

## Requirements

- Docker Desktop
- Python 3.12+
- [Ollama](https://ollama.com) with the model pulled:
ollama pull qwen2.5-coder:7b

## Getting started

```powershell
.\setup.ps1    # once, after cloning
.\start.ps1    # every session
```

Then open http://localhost:8000

`setup.ps1` creates the virtual environment and installs dependencies.
`start.ps1` checks Docker, starts the database, waits until Postgres accepts
connections, activates the venv, and launches the API.

## Database

The schema lives in `db/init.sql` and is applied automatically the first time
the container starts on an empty volume — no manual setup required.

To reset the database (this destroys all stored requests and embeddings):

```powershell
docker compose down -v
docker compose up -d
```

## Features

- **Explorer:** HTTP proxy (solves CORS), dynamic headers, recursive JSON
  flattening with semantic type detection, suggested transformations, interactive
  graph view, CSV/Parquet export, and star-schema data model suggestions.
- **AI:** semantic search over past responses, RAG question answering, and a
  ReAct agent that can explore APIs on its own (GET-only).
- **History:** every request is persisted, tagged by source (`manual` or `agent`).