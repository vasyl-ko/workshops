"""Workshop Notes API.

Runs standalone with an in-memory store (Docker basics workshop), or against
Postgres when DATABASE_URL is set (Compose workshop). The schema is NOT created
here: that is the `migrate` job's work (app/migrate.py), which Compose runs
before this service starts.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

DATABASE_URL = os.getenv("DATABASE_URL")

# In-memory fallback so the app works before we introduce Postgres.
_notes: list[str] = []


def _db():
    import psycopg

    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fail fast: a misconfigured or too-early api should crash on boot, not
    # sit there "Up" and answer 503s. This is what the race demo trips over.
    if DATABASE_URL:
        with _db() as conn:
            conn.execute("SELECT 1")
    yield


app = FastAPI(title="Workshop Notes API", lifespan=lifespan)


@app.get("/")
def root():
    return {
        "app": "Workshop Notes API",
        "storage": "postgres" if DATABASE_URL else "in-memory",
        "hint": "GET /notes, POST /notes?text=hello",
    }


@app.get("/health")
def health():
    if DATABASE_URL:
        try:
            with _db() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # pragma: no cover - demo diagnostics
            raise HTTPException(status_code=503, detail=f"database unreachable: {exc}")
    return {"status": "ok"}


@app.get("/notes")
def list_notes():
    if DATABASE_URL:
        with _db() as conn:
            rows = conn.execute("SELECT id, text FROM notes ORDER BY id").fetchall()
        return [{"id": r[0], "text": r[1]} for r in rows]
    return [{"id": i + 1, "text": t} for i, t in enumerate(_notes)]


@app.post("/notes")
def add_note(text: str):
    if DATABASE_URL:
        with _db() as conn:
            row = conn.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id", (text,)).fetchone()
        return {"id": row[0], "text": text}
    _notes.append(text)
    return {"id": len(_notes), "text": text}

# glkdjfng fdjksdflkjn