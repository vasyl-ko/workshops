"""Workshop Notes API v2.

Runs standalone with an in-memory store (segments 1-2 of the workshop),
or against Postgres when DATABASE_URL is set (segment 3, via Compose).
"""

import os

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Workshop Notes AsdfgsfgPI v2 lsg gjkf s")

DATABASE_URL = os.getenv("DATABASE_URL")

# In-memory fallback so the app works before we introduce Postgres.
_notes: list[str] = []


def _db():
    import psycopg

    return psycopg.connect(DATABASE_URL)


@app.on_event("startup")
def init_db() -> None:
    if not DATABASE_URL:
        return
    with _db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT NOT NULL)")


@app.get("/")
def root():
    return {
        "app": "Workshop Notes API v2",
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


