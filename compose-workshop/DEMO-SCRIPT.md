# Demo Script — Docker Compose for the Team (~90 min: 20+25+25+15, Q&A inside section 4)

Run-sheet for the Compose workshop. Slides in `slides/index.html` (arrow keys).
All commands run from `demo/`. Prerequisite for attendees: the Docker basics
workshop (images, docker run, volumes, networks).

Requirements: Docker Compose ≥ 2.24.4 (`!override` in the race file, `--wait`,
profiles, `develop.watch`). Verified on Compose v5.3.1 / Docker Desktop on
macOS; attendees on Linux get the UID note on the volumes slide.

## Pre-workshop checklist (on the presenting machine, the morning of)

- [ ] Docker running; pre-pull: `docker pull postgres:16-alpine`,
  `docker pull python:3.12-slim`, `docker pull ghcr.io/astral-sh/uv:0.7.19`,
  `docker pull adminer`, `docker pull alpine:3.20`
- [ ] Build once to warm the cache: `docker compose build` (builds the `dev`
  target via the override) and `docker compose -f compose.yaml build` (the
  lean `runtime` target — so the CI demo's `--build` is instant too)
- [ ] Full dry run of Demos 1–4 below, top to bottom, then
  `docker compose --profile tools down -v`
- [ ] No `.env` in `demo/`, and **no `API_PORT` / `POSTGRES_PASSWORD` in your
  shell** — Demo 3's `.env` step relies on the file winning, and shell
  variables beat the file
- [ ] Ports 8000, 8001 and 8080 free: `lsof -i :8000 -i :8001 -i :8080` and
  `docker ps --format '{{.Names}} {{.Ports}}'`. Another Compose project on
  8000 makes `up` fail with "port is already allocated" — stop it; don't
  work around it with `API_PORT` in the shell (see above)
- [ ] `docker compose ps -a` shows nothing; no stale `demo-*` containers from
  Part 1 either (`docker ps -a | grep demo`)
- [ ] Terminal: big font, two panes side by side (logs left, commands right)
- [ ] Editor open on `app/main.py`; browser tab ready for http://localhost:8080
- [ ] To show raw build logs during `up --build`, prefix with `BUILDKIT_PROGRESS=plain`

> **Timing plan:** 20 / 25 / 25 / 15. If behind, cut in this order: the
> `events` line of Demo 4 → the "Shutdown, restarts, limits" slide (one
> sentence: "SIGTERM, then SIGKILL after 10 s; limits are the same knobs as
> docker run") → the `--scale` bullet on the networks slide → the "Where
> Compose sits" bullets (keep the two cards) → the `run --rm migrate` line
> of Demo 2. Never cut Demo 1, the race in Demo 2, or the persistence half of
> Demo 3.

## Concept → live evidence → file

| concept (slide) | shown by | backed by |
|---|---|---|
| `up` order and gates | Demo 1 `up --build` output, `ps -a` | `compose.yaml` depends_on |
| project naming, `name:` | Demo 1 `ps`, Demo 3 `-p review config` | `compose.yaml` top |
| DNS + network membership | Demo 1 `getent`, Demo 2 `docker run … alpine` | project `default` network |
| named volume lifecycle | Demo 3 down / up / down -v | `pgdata` volume |
| healthcheck fields, unhealthy state | Demo 2 race (`ps` turns unhealthy) | api + db healthchecks |
| `service_completed_successfully` | Demo 1 `migrate Exited`, Demo 4 gate failure | `migrate` service, `app/migrate.py` |
| `service_started` vs `service_healthy` | Demo 2 race | `compose.race.yaml` |
| build target per environment | Demo 2 `run --rm api pytest`, CI slide | `Dockerfile` stages, override, `compose.ci.yaml` |
| `.env` read from a file, `up` recreates only what changed | Demo 3 `API_PORT` | `.env.example`, `${API_PORT:-8000}` |
| override merge, `-f` skips it | Demo 3 `diff` of two `config`s | `compose.override.yaml` |
| profiles | Demo 3 Adminer | `profiles: ["tools"]` |
| status → logs → config playbook | Demo 4 | `migrate` failing auth |
| not demoed, slide-only | aliases, `host.docker.internal`, anonymous/external volumes, UID mismatch, shutdown, limits | — |

---

## Demo 1 — The whole stack, one command (~8 min, closes section 1)

**Precondition:** nothing running (`docker compose ps -a` empty), no `.env`.
**Point:** one file, one command = the whole dev environment — and the startup
order is *gated*, not hoped for.

```bash
docker compose up --build      # foreground — the interleaved logs teach
```
- Point at the order in the first lines: `db Healthy` → `migrate Exited` →
  `api Started`. Then service names prefixing every log line, and
  `migrate-1 | migrate: schema is up to date` followed by
  `migrate-1 exited with code 0`.

Second pane:
```bash
docker compose ps -a           # api, db "(healthy)"; migrate "Exited (0)" — say: without -a you'd never see the job
curl -X POST "localhost:8000/notes?text=hello-team"     # NB: no spaces in the
curl -X POST "localhost:8000/notes?text=docker-is-fine"  # text — curl rejects a
curl localhost:8000/notes                                # URL with a raw space
docker compose exec db psql -U workshop notes -c 'select * from notes'
docker compose exec api getent hosts db   # DNS live: db → a container IP
```
- Say on psql: "The notes are in Postgres, in the volume — the api container
  holds nothing. And the table exists because a *job* created it, not the app."

**Live reload through the bind mount:** edit `app/main.py` — change the `hint`
text in `root()` — save, watch uvicorn reload in the left pane, `curl localhost:8000`.
- Say: "I did not rebuild the image. The bind mount mirrors my editor into the
  container — it comes from the override file, section 3."
- Fallback if the editor save doesn't trigger a reload: `touch app/main.py`.

**Postcondition:** Ctrl+C the foreground `up` (say: "stopped, not removed"),
then `docker compose up -d --wait`. Stack up, healthy, two notes in the volume.

## Demo 2 — Jobs, networks, and a deliberate crash (~8 min, closes section 2)

**Precondition:** stack up and healthy with notes.

```bash
docker compose ps -a                   # migrate: Exited (0) — the job that ran before api
docker compose run --rm migrate        # again, by hand: "schema is up to date". Idempotent — up runs it every time
docker compose run --rm api pytest     # one-off container, same network + env: 2 passed, against the real db
```
- Say: "`run` gave that container the service's image, env and network — but
  not its ports. It's how you run migrations, seeders, tests. pytest exists
  only because the override picks the `dev` build target — the CI slide."

**Network membership:**
```bash
docker run --rm alpine:3.20 getent hosts db                       # nothing — exit 2
docker run --rm --network demo_default alpine:3.20 getent hosts db  # 172.x.x.x db
```
- Say: "Same daemon, same DNS. Membership is the whole story — `expose:` in a
  file changes nothing here."

**Break it (~3 min):**
```bash
docker compose down -v         # fresh volume: Postgres will initdb, slower still
docker compose -f compose.yaml -f compose.override.yaml -f compose.race.yaml up
```
- `compose.race.yaml` = db sleeps 5 s before starting + `!override` on api's
  depends_on: `service_started` only. Say what `!override` does: "without it
  the maps would merge and api would still wait for migrate, which waits for a
  healthy db — no race".
- Watch for: `psycopg.OperationalError: connection refused` then
  `ERROR: Application startup failed. Exiting.` The container stays "Up"
  (uvicorn's reloader survives) — in the second pane `docker compose ps` shows
  `health: starting` then `(unhealthy)` after ~20 s.
- Say: "Started is not ready. Without the gate you get a container that is up
  and useless — and without the api healthcheck you wouldn't even see that."
- Verified: the race is reliable only with the sleep — on a fast laptop
  Postgres wins a plain race by ~0.4 s.

**Back to normal:** Ctrl+C (containers stop), then
```bash
docker compose up -d --wait    # explicit -f list gone: override loads again, race file doesn't
docker compose ps -a           # db Recreated (its entrypoint changed), api merely started — and healthy
curl -X POST "localhost:8000/notes?text=survivor"   # the down -v above emptied the volume: Demo 3 needs a note
```
- If you skipped Ctrl+C and the old api is still *running* unhealthy: `up`
  leaves it alone (config unchanged) and `--wait` fails — `docker compose
  restart api` fixes it. Good teaching moment if it happens.

**Postcondition:** stack up, healthy, `curl localhost:8000/notes` shows `survivor`.

## Demo 3 — Override, .env, profiles, data (~8 min, closes section 3)

**Precondition:** stack up with ≥ 1 note; no `.env`; port 8001 free.

**Override & project, without touching state:**
```bash
diff <(docker compose -f compose.yaml config) <(docker compose config)   # exactly what the override adds
docker compose -p review config | grep 'name:'      # review, review_default, review_pgdata
```
- Say: "Target dev, the bind mount, the reload command, Adminer — that's the
  override. Pass `-f` explicitly and none of it loads; that's what CI does."

**.env, read from a real file:**
```bash
cp .env.example .env
sed -i '' 's/^API_PORT=8000/API_PORT=8001/' .env    # or edit it in the editor
docker compose config --environment | grep API_PORT   # API_PORT=8001 — from the file. (unfiltered, it dumps your whole shell env)
docker compose config | grep published              # "8001"
docker compose up -d --wait                         # only api is "Recreated" — the only config that changed
curl localhost:8001/notes
rm .env && docker compose up -d --wait              # back to 8000 — again only api recreated
```
- Say: "Nothing in my shell, no flags: the file next to compose.yaml did it.
  And `up` touched exactly one container."
- Do NOT change `POSTGRES_PASSWORD` in that file: the volume was initialised
  with `workshop`; a changed password fails auth until `down -v`. Say it out
  loud — it's the gotcha on the .env slide, and Demo 4 shows it.

**Profiles, then the payoff in the browser:**
```bash
docker compose --profile tools up -d --wait          # adminer joins the stack
```
- Open http://localhost:8080 — System PostgreSQL, Server `db`, User `workshop`,
  Password `workshop`, Database `notes` — click the `notes` table.
- Say: "Server is `db` — Adminer is a container on the project network, so the
  name resolves for it too. Behind a profile: nobody gets it unless they ask."

**Data survives (both directions):**
```bash
docker compose --profile tools down    # containers and network: gone (profile again, or adminer stays)
docker compose ps -a                   # nothing
docker compose up -d --wait
curl localhost:8000/notes              # notes still there — demo_pgdata volume
docker compose down -v                 # the reset button
docker compose up -d --wait
curl localhost:8000/notes              # [] — migrate recreated the table, empty
```

**Postcondition:** stack up, healthy, empty notes. No `.env` left behind (`ls -a`).

## Demo 4 — Break it, then find it (~6 min, before the recap)

**Precondition:** stack up and healthy.

```bash
POSTGRES_PASSWORD=wrong docker compose up -d
#   → service "migrate" didn't complete successfully: exit 1
docker compose ps -a            # migrate Exited (1); api Created — never started; db Up (recreated: its env changed)
docker compose logs migrate     # "FATAL: password authentication failed for user workshop"
docker compose config | grep DATABASE_URL      # …workshop:workshop@db… — wait, why? because the shell var is gone now
POSTGRES_PASSWORD=wrong docker compose config | grep DATABASE_URL   # …workshop:wrong@db… — the value it really ran with
docker compose events --since 3m --until 1s | grep -E 'health_status|die'   # the daemon's view, bounded (no Ctrl+C needed)
```
- Say: "The gate did its job: api never started against a broken database.
  `ps -a` names the culprit, `logs` gives the reason, `config` shows what was
  substituted — note it depends on the shell you run it from. And why did the
  *database* reject it? It was recreated with the new env, but the volume was
  initialised with the old password. Init vars only apply to an empty volume."
- Fix = fix the config:
```bash
docker compose up -d --wait && docker compose ps    # migrate re-runs and exits 0, api starts, all healthy
```

Wrap up: recap slide → Q&A. Afterwards: `docker compose --profile tools down -v`.
