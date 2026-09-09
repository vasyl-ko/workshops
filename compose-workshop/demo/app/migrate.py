"""One-shot schema job.

Compose runs it as the `migrate` service before `api` starts
(`condition: service_completed_successfully`). It is idempotent on purpose:
Compose re-runs it on every `up`, so "already applied" must be a no-op.
Also usable by hand: `docker compose run --rm migrate`.
"""

import os

import psycopg

SCHEMA = "CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT NOT NULL)"

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    conn.execute(SCHEMA)
print("migrate: schema is up to date")
