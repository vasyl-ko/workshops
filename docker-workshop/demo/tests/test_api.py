"""Runs in the `test` build stage (and locally via `uv run pytest`)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_reports_storage():
    body = client.get("/").json()
    assert body["storage"] == "in-memory"


def test_add_and_list_notes():
    created = client.post("/notes", params={"text": "hello"}).json()
    assert created["text"] == "hello"
    notes = client.get("/notes").json()
    assert notes[-1]["text"] == "hello"
