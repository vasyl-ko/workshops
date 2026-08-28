# Docker Workshop — Demo App

A tiny FastAPI "notes" API used throughout the workshop. It stores notes
in memory when run alone, and in Postgres when `DATABASE_URL` is set.

## The Dockerfile evolution

| File | What it shows |
|------|---------------|
| `v1.Dockerfile` | The naive first attempt: huge base image, cache-busting layer order, runs as root |
| `v2.Dockerfile` | v1 on a slim base — ~1.4 GB lighter, but still the naive layer order |
| `v2.1.Dockerfile` | Deps synced from `uv.lock` **before** code is copied → fast cached rebuilds |
| `v3.Dockerfile` | Multi-stage build, non-root user, healthcheck — production-shaped |

Build and compare:

```bash
docker build -f v1.Dockerfile -t notes:v1 .
docker build -f v2.Dockerfile -t notes:v2 .
docker build -f v2.1.Dockerfile -t notes:v2.1 .
docker build -f v3.Dockerfile -t notes:v3 .
docker images notes
```

Run one:

```bash
docker run --rm -p 8000:8000 notes:v2.1
curl localhost:8000
```

## The full stack, by hand (section 3 of the workshop)

```bash
docker network create demo
docker run -d --name db --network demo -v pgdata:/var/lib/postgresql/data \
    -e POSTGRES_USER=workshop -e POSTGRES_PASSWORD=workshop -e POSTGRES_DB=notes \
    postgres:16-alpine
docker run -d --name api --network demo -p 8000:8000 \
    -e DATABASE_URL=postgresql://workshop:workshop@db:5432/notes notes:v2.1
curl -X POST "localhost:8000/notes?text=hello"   # note: no spaces in the text
```

Cleanup: `docker rm -f api db && docker network rm demo && docker volume rm pgdata`.

Turning this stack into one committed file is the follow-up workshop —
see `../../compose-workshop/`.

Also here: `tests/` (used by the multi-stage `test` stage story — `uv run pytest`),
`scratch/` (the FROM-scratch demo), `Dockerfile.whiteout` → `whiteout.Dockerfile`
(deleting doesn't shrink an image).
