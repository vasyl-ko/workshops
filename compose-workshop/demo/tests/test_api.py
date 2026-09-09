"""Runs against whatever DATABASE_URL says.

- locally, `uv run pytest`: no DATABASE_URL -> in-memory store
- inside the stack, `docker compose run --rm api pytest`: Postgres via the
  project network (needs the `dev` build target, which the override and the
  CI file select)
"""

import os
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_reports_storage():
    expected = "postgres" if os.getenv("DATABASE_URL") else "in-memory"
    assert client.get("/").json()["storage"] == expected


def test_add_then_list_contains_note():
    text = f"test-{uuid.uuid4().hex[:8]}"   # unique: the presenter's volume may hold old notes
    created = client.post("/notes", params={"text": text}).json()
    assert created["text"] == text
    assert text in [n["text"] for n in client.get("/notes").json()]
