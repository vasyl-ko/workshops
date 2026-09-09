# Compose Workshop — Demo Stack

The notes API from the Docker basics workshop, now run as a Compose stack:
FastAPI (`api`) + a one-shot schema job (`migrate`) + Postgres (`db`), plus
Adminer behind a profile.

```bash
docker compose up --build                        # db healthy → migrate exits 0 → api starts
curl -X POST "localhost:8000/notes?text=hello"   # note: no spaces in the text
curl localhost:8000/notes
docker compose run --rm api pytest               # tests against the real db (dev build target)
docker compose --profile tools up -d             # + Adminer at http://localhost:8080
```

Files:

- `compose.yaml` — the committed, prod-shaped contract: pinned project name
  (`demo`), `api` + `migrate` sharing one image, healthchecks on api and db,
  `service_healthy` / `service_completed_successfully` gates, `${API_PORT:-8000}`
- `compose.override.yaml` — dev extras, merged automatically by `docker compose up`:
  the `dev` build target, the bind mount, `--reload`, `develop.watch` rules,
  and Adminer under `profiles: ["tools"]`
- `compose.ci.yaml` — the CI difference (`build.target: dev`), used with
  explicit `-f`, which skips the override
- `compose.race.yaml` — opt-in only (`-f`): a slow database and no health gate
  (`!override`, Compose ≥ 2.24.4), to show "started ≠ ready" failing live
- `Dockerfile` — the cache-friendly slim build from the basics workshop, with
  named stages: `base`, `dev` (pytest + tests), `runtime` (default)
- `app/migrate.py` — the idempotent schema job; `app/main.py` fails fast on
  boot if the database is unreachable
- `tests/test_api.py` — runs in-memory locally (`uv run pytest`) and against
  Postgres inside the stack
- `.env.example` — copy to `.env` (gitignored): `POSTGRES_PASSWORD` (Postgres
  reads it into an empty volume only — change it and you need `down -v`) and
  `API_PORT`

`docker compose config` prints the merged, substituted file. Notes survive
`docker compose down` (the `demo_pgdata` volume); `down -v` resets.
