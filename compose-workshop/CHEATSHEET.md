# Docker Compose Cheat Sheet

From the "Docker Compose for the Team" workshop.

## Daily drivers

```bash
docker compose up -d --build   # start stack; --build after Dockerfile changes, --wait until healthy
docker compose ps -a           # status + health (-a: exited containers too — jobs!)
docker compose logs -f api     # follow one service
docker compose exec api bash   # shell into a RUNNING service
docker compose run --rm api …  # one-off container: migrations, tests, scripts (no ports published)
docker compose down            # stop + remove (volumes SURVIVE)
docker compose down -v         # ...and wipe the project's volumes = reset the database
docker compose config          # the resolved file: env substituted, overrides merged
docker compose up --watch      # rebuild/sync per develop.watch rules in the file
```

`docker compose` (the plugin, v2 onwards) is the current tool; the old
`docker-compose` binary is v1, retired. Prefer the filename `compose.yaml`;
drop the obsolete `version:` line.

## The file

- A **service** = recipe for a container of one role; `build:` builds
  locally, `image:` pulls (both together: `image:` names the built image;
  `up` won't rebuild it without `--build`)
- Services reach each other **by service name** (`db:5432`) — Docker DNS
- Top-level `volumes:` / `networks:` declare; the lines under a service use them
- Everything is named after the **project**: `demo-api-1`, `demo_default`,
  `demo_pgdata`. Folder name, or top-level `name:`; `-p` /
  `COMPOSE_PROJECT_NAME` win. Same name = same project. Published ports are
  never isolated
- `up` is a reconcile: creates what's missing, **recreates what changed**,
  leaves the rest alone, starts in gate order

## Networks

- No `networks:` → everyone on the project's `default` network
- Isolation = **membership**: put `db` on `backend` only. `expose:` is
  documentation; `ports:` is a hole to the host
- Aliases: `networks: { backend: { aliases: [postgres] } }`
- Laptop from a container: `host.docker.internal` (Linux: add
  `extra_hosts: ["host.docker.internal:host-gateway"]`)
- `--scale` needs a free host port per replica: `ports: ["8000"]` →
  `docker compose port --index=1 api 8000`

## Volumes

- **named** (`pgdata:`): survives `down`, dies with `down -v`
- **bind** (`./app:/code/app`): relative to the compose file; on Linux the
  container writes as its UID
- **anonymous** (`VOLUME` in an image, `- /data`): survives a recreate, but
  nothing reattaches it after `down` — name it
- **external: true**: yours to create and delete; `down -v` never touches it

## Health and dependencies

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U workshop -d notes"]   # runs INSIDE the container
  interval: 2s
  timeout: 2s
  retries: 15
  start_period: 10s   # failures here don't count
```
- starting → healthy → (retries × interval failures) → unhealthy. Unhealthy
  restarts nothing; it's a signal for `ps`, `depends_on`, `--wait`, you
- `depends_on` conditions: `service_started` (process runs) ·
  `service_healthy` (check passed) · `service_completed_successfully`
  (one-shot job exited 0 — migrations, seeders)
- Gates apply at **startup only**. Reconnect in the app; `restart:` only
  helps if the process exits
- `docker inspect -f '{{json .State.Health}}' demo-db-1` — why it never went green

## Build

- One Dockerfile, named stages; `build: { target: dev }` in the override /
  CI file picks the stage. No target → last stage
- `build:` + `image: name` → other services reuse it (`migrate`)
- `up --build` after Dockerfile changes; `develop.watch` for automatic rebuilds

## Lifecycle gotchas

- `Ctrl+C` on `up` stops containers but doesn't remove them — `down` does
- `up -d` recreates only what changed; `restart` reuses the old container —
  an edited `environment:` needs `up`
- Dockerfile changed → `up --build`; new image tag → `pull`, then `up`
- `up -d --wait` = block until every gate is green (or fail)

## Config & secrets

- Compose auto-reads `.env` next to compose.yaml; `${VAR}` substitutes in the
  file, `env_file:` injects a file into the container — `.env` itself never
  enters a container
- `${VAR:-default}` fallback · `${VAR:?message}` fail-loudly
- Precedence: shell > `.env`; inside a service `environment:` > `env_file:`
- Commit `compose.yaml` and `.env.example`; **never** commit `.env`. `.env`
  is local config, not a vault (values show in `config`/`inspect`) — real
  secrets: Compose `secrets:`
- Postgres reads `POSTGRES_*` only into an **empty** volume — a changed
  password needs `down -v`

## The override pattern

- `compose.yaml` = committed contract (prod-shaped)
- `compose.override.yaml` = dev extras, merged automatically by `up`
- Merge rules: maps merge, lists append (keyed lists like `ports`/`volumes`
  merge on their target), scalars and `command:` replace; `!override`
  replaces a whole map
- Optional services: `profiles: ["tools"]` + `docker compose --profile tools up`
  (`down` needs the profile too)
- Explicit stacks: `docker compose -f compose.yaml -f compose.ci.yaml up`
  (merges left→right, ignores the override file, relative paths from the
  first file). `COMPOSE_FILE=a.yaml:b.yaml` saves the typing

## Compose in CI

```bash
docker compose -f compose.yaml -f compose.ci.yaml up -d --build --wait
docker compose -f compose.yaml -f compose.ci.yaml run --rm api pytest
docker compose -f compose.yaml -f compose.ci.yaml down -v   # always
```

## Debugging a stack

`ps -a` → `logs` → `config` → `exec` / `inspect`. Also: `run --rm --no-deps
api sh` when it won't start, `docker compose events`, `top`, `stats`.

- *dependency failed / didn't complete successfully*: a gate stayed shut — `ps -a`, then `logs <service>`
- *port is already allocated*: another stack on that host port
- *orphan containers*: renamed/removed service — `--remove-orphans`
- *works after `down -v` only*: stale volume state (Postgres init vars!)
- *my change isn't there*: no `--build`, used `restart`, or wrong project

## Shutdown & limits

- `stop`/`down`: SIGTERM, `stop_grace_period` (10 s), SIGKILL. PID 1 must
  handle signals — `init: true` if it can't
- `restart: unless-stopped` for things that must come back; off in dev
- `cpus: 1.5` · `mem_limit: 512m` · `pids_limit: 200` — verify with `compose stats`
