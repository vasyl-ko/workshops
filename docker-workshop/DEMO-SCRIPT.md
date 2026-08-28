# Demo Script — Docker for the Team (~90 min: 15+20+20+20 + intro/Q&A)

Your run-sheet. Slides are in `slides/index.html` (open in a browser, arrow keys
to navigate). All commands run from `demo/`.

## Pre-workshop checklist (do this the day before, on the presenting machine)

- [ ] Docker Desktop running, `docker version` OK
- [ ] Pre-pull images so you're not fighting the venue wifi:
  ```bash
  docker pull python:3.12 && docker pull python:3.12-slim
  docker pull postgres:16-alpine && docker pull nginx
  docker pull ghcr.io/astral-sh/uv:0.7.19    # every build COPYs uv from this
  docker pull busybox:musl                   # for the optional scratch demo
  ```
- [ ] Pre-build all four images once (warms the cache; you'll rebuild live anyway):
  ```bash
  cd demo
  docker build --progress=plain -f v1.Dockerfile -t notes:v1 .
  docker build --progress=plain -f v2.Dockerfile -t notes:v2 .
  docker build --progress=plain -f v2.1.Dockerfile -t notes:v2.1 .
  docker build --progress=plain -f v3.Dockerfile -t notes:v3 .
  docker build --platform linux/amd64 -f v2.1.Dockerfile -t notes:amd64 .  # warms the amd64 base layers
  ```
- [ ] Dry-run Demo 3's manual stack once (commands below), check
  `curl localhost:8000/health`, then clean up (`docker rm -f api db`,
  `docker network rm demo`, `docker volume rm pgdata`)
- [ ] Reset the dockerignore-demo state:
  `rm -rf demo/data && sed -i '' '/^data\/$/d' demo/.dockerignore`
  (the demo creates `data/` live and appends to `.dockerignore` — starting with
  `data/` already present would inflate the v1 numbers in the earlier segments)
- [ ] `dive` installed (`brew install dive`) and `docker pull alpine:3.20` for the
  whiteout demo
- [ ] Nothing else listening on port 8000 (`lsof -i :8000`)
- [ ] Terminal: big font (18pt+), light-on-dark, ONE window, full screen
- [ ] Share the repo link with attendees in advance

> **Timing plan:** the agenda (15/20/20/20) is tight — it assumes the CORE
> demos, brisk slide pacing, and one-sentence treatment of "deep dive" slides.
> The optional segments (scratch, dive tour, whiteout build, Demo 4's bonus
> round) are stretch material: do them only if ahead of schedule, cut them in
> that order if behind. If a section overruns, cut its remaining deep dives,
> not the next section's demo. Never cut Demo 3 — Compose is the segment
> people use the next day.

---

## Demo 1 — First contact (~8 min, closes section 1 — after the "Images vs containers" slide)

**Point of the demo:** containers are instant, disposable, and leave nothing on the host.

```bash
docker run -it --rm python:3.12-slim python
```
- Say: "This machine does not have this Python installed. Two seconds, and I'm in a REPL."
- In the REPL: `import sys; sys.version`, then `exit()`. Note `--rm`: it's gone.

```bash
docker run -d -p 8000:80 --name web nginx
docker ps                     # point at NAMES, PORTS, STATUS
curl localhost:8000           # nginx welcome page
docker stop web
docker ps                     # empty!
docker ps -a                  # ...but the corpse is here — Exited (0)
docker rm web
```
- Point out: `ps` vs `ps -a` — this distinction saves people daily.
- Segue: "So where did nginx come from? An image. Let's talk about what that is." → back to slides.

## Demo 2 — Shrinking the image (~8 min core; +10 with the optional extras — interleaved through section 2, cue points per segment below)

**Point of the demo:** base images, layer order, and multi-stage are not theory — watch the numbers.

**Base images: v1 vs v2** (after the "Base images" slide):
```bash
cd demo
grep ^FROM v1.Dockerfile v2.Dockerfile           # python:3.12 vs -slim
docker build --progress=plain -f v1.Dockerfile -t notes:v1 .      # narrate the layer output
docker build --progress=plain -f v2.Dockerfile -t notes:v2 .
docker images notes && docker images python
```
- Expected (verified): notes:v1 ≈ 1.72 GB vs notes:v2 ≈ 319 MB; the bases
  themselves: python:3.12 = 1.62 GB vs slim = 205 MB (alpine = 79.5 MB).
- Say: "Same app, same naive Dockerfile — only the FROM line changed. v2 still
  has v1's layer-order problem; that's the next few slides."

**Dockerignore: the 120 MB stowaway** (after the ".dockerignore" slide, ~3 min):
```bash
mkdir -p data && dd if=/dev/urandom of=data/dataset.bin bs=1m count=120
docker build --progress=plain -f v1.Dockerfile -t notes:v1 .   # transferring context: 125.87MB
docker images notes                           # v1 grew 1.72 → 1.98 GB
docker build --progress=plain -f v2.1.Dockerfile -t notes:v2.1 .  # transferring context: 265B (!)
echo "data/" >> .dockerignore
docker build --progress=plain -f v1.Dockerfile -t notes:v1 .   # tiny context, 1.72 GB again
```
- Say: "The dataset is gitignored — code review never sees it. Docker doesn't
  read .gitignore. v2.1 escaped only because its COPYs are targeted; the
  .dockerignore line protects every Dockerfile, including tomorrow's."
- Leave `data/` in `.dockerignore` for the rest of the session (keeps later
  rebuilds fast); the pre-workshop checklist resets it next time.

**The cache race** (the money moment — after the "Layer cache: order is everything" slide):
```bash
grep -E '^(COPY|RUN)' v2.Dockerfile v2.1.Dockerfile   # only the order differs
docker build --progress=plain -f v2.1.Dockerfile -t notes:v2.1 .   # warm it once
# make a trivial edit
sed -i '' 's/Workshop Notes API/Workshop Notes API v2/' app/main.py
time docker build --progress=plain -f v2.Dockerfile -t notes:v2 .       # re-syncs — slow (verified: 3.2s)
time docker build --progress=plain -f v2.1.Dockerfile -t notes:v2.1 .   # CACHED (verified: 0.5s)
sed -i '' 's/Notes API v2/Notes API/' app/main.py   # undo the edit
# (git checkout works instead once the repo is committed)
```
- Say: "Same base, same flags, same edit — v2 re-syncs every dependency, v2.1
  rebuilds from cache. The ONLY difference is the order of two lines. On this
  toy app that's 6×; with a real dependency list it's minutes vs seconds."

**Layer anatomy + whiteouts** (after the "deleting doesn't shrink" slide):
```bash
docker history notes:v2.1        # our layers: uv sync = 49 MB, uv itself = 36 MB, code = 25 kB
docker build --progress=plain -f whiteout.Dockerfile -t notes:whiteout .
docker images notes:whiteout   # 119 MB — alpine is ~8 MB and big.bin was DELETED
docker history notes:whiteout  # the dd layer keeps its 105 MB; rm is a 4.1 kB whiteout
```
- Say: "Layers are append-only. `rm` in a later layer hides the file, it doesn't
  unship it. Clean up in the same RUN, or multi-stage."
- Optional flourish: `docker save notes:v3 | tar -t | head` — "an image is just
  tarballs and JSON, nothing magic."

**Optional: FROM scratch live** (~3 min, backs the "bottom of the stack" slide;
commands also sit in `demo/scratch/scratch.Dockerfile`):
```bash
cd scratch
C=$(docker create busybox:musl) && docker cp $C:/bin/busybox . && docker rm $C
docker build --progress=plain -f scratch.Dockerfile -t scratch-test .
docker run --rm scratch-test           # hello from scratch — a 2 MB image
```
- Encore if time: repeat the extraction with plain `busybox` (dynamically
  linked) — the run fails with "no such file or directory": no libc, no linker
  in scratch. That error on the slide, live.

**dive walkthrough** (~3 min):
```bash
dive notes:v1
```
- Tour: layers on the left with sizes; Tab into the file tree; Ctrl+U to show
  only this layer's files. Navigate to the uv-sync layer, find
  `/root/.cache` — 49 MB of uv cache v1 ships for nothing (v2 and v2.1 avoid it
  with `--no-cache`).
- Honest note if someone reads the header: dive says v1 is "99% efficient" —
  that score only counts cross-layer waste (duplicated/deleted files). v1's real
  problem is the fat base and in-layer junk, which you find by browsing, not
  from the score. `dive notes:whiteout` shows the score catching real waste.
- Mention `CI=true dive --ci IMAGE` as the CI guardrail, then quit (q).

**Platforms: cross-building** (after the "One image name, many CPUs" slide, ~3 min):
```bash
docker image inspect notes:v2.1 --format '{{.Os}}/{{.Architecture}}'   # linux/arm64
docker build --progress=plain --platform linux/amd64 -f v2.1.Dockerfile -t notes:amd64 .
docker image inspect notes:amd64 --format '{{.Os}}/{{.Architecture}}'  # linux/amd64
docker run --rm notes:amd64 python -c "import platform; print(platform.machine())"
```
- Expected: the run prints the platform-mismatch WARNING, then `x86_64` —
  x86 code executing on ARM via emulation.
- Say: "Same Dockerfile, different CPU target. The warning is the thing to
  respect: in prod it means someone shipped the wrong architecture."
- Note: the cross-build re-pulls amd64 base layers — slower on venue wifi;
  it's pre-warmed by the checklist below.

**Multi-stage, measured** (after "Multi-stage, level 2" — multi-stage now closes
the section, right before tags):
```bash
docker build --progress=plain -f v3.Dockerfile -t notes:v3 .
docker images notes            # 1.7 GB → 318 MB → 265 MB — v3 left uv behind
docker run --rm -d -p 8000:8000 --name api notes:v3 && curl localhost:8000
docker stop api
```
- If asked why v3 < v2: the builder stage keeps the uv binary (~36 MB) and its
  bootstrap out of the final image — only the synced `.venv` is copied across.

## Demo 3 — The stack, by hand (~8 min, after the "Networks: containers talk by name" slide)

**Point of the demo:** -p, -e, -v, --network are enough to wire a real stack —
and it's painful enough to sell the Compose workshop.

```bash
docker network create demo
docker run -d --name db --network demo -v pgdata:/var/lib/postgresql/data \
    -e POSTGRES_USER=workshop -e POSTGRES_PASSWORD=workshop -e POSTGRES_DB=notes \
    postgres:16-alpine
docker run -d --name api --network demo -p 8000:8000 \
    -e DATABASE_URL=postgresql://workshop:workshop@db:5432/notes notes:v2.1
curl -X POST "localhost:8000/notes?text=by-hand"   # NB: no spaces — curl rejects them
curl localhost:8000/notes
curl localhost:8000            # "storage": "postgres" — one env var flipped it
docker exec api getent hosts db   # DNS live: db → a container IP. Nothing published.
```
- Say: "Same image as before. `-e` reconfigured it, `--network` + a name wired
  it to Postgres, `-v` gave the db real storage."

**The volume outlives the database:**
```bash
docker rm -f db                # kill the database entirely
docker run -d --name db --network demo -v pgdata:/var/lib/postgresql/data \
    -e POSTGRES_USER=workshop -e POSTGRES_PASSWORD=workshop -e POSTGRES_DB=notes \
    postgres:16-alpine
sleep 3 && curl localhost:8000/notes   # notes still there — pgdata survived
```
- **Leave the stack running** — Demo 4 breaks it.
- Segue on the "This doesn't scale" slide: "four commands, a paragraph of flags,
  zero code review. The fix is Docker Compose — that's the follow-up workshop."

## Demo 4 — Break it, then find it (~10 min, after the "limits & disk" slide)

**Point of the demo:** the status → logs → exec → inspect playbook.

Sabotage the running stack (do it openly — "I'm the intern now"):
```bash
docker rm -f api
docker run -d --name api --network demo -p 8000:8000 \
    -e DATABASE_URL=postgresql://workshop:WRONG@db:5432/notes notes:v2.1
curl localhost:8000/health     # 503, database unreachable
docker ps                      # both "Up" — the picture lies
docker logs api                # ← password authentication failed. There it is.
docker exec -it api sh         # optional: env | grep DATABASE — see the bad value
docker inspect api | grep -A2 DATABASE
```
Fix: recreate `api` with the right password, `curl /health` → ok.

**Bonus round if time allows** — port conflict:
```bash
python3 -m http.server 8000 &  # occupy the port on the host
docker run --rm -d -p 8000:8000 --name clash nginx   # "port is already allocated"
kill %1
```

Cleanup: `docker rm -f api db && docker network rm demo` (keep or drop the
`pgdata` volume — `docker volume rm pgdata` for a full reset).

Wrap up: recap slide → cheat sheet → Q&A. Pitch the Compose workshop as the
sequel: "everything we typed today becomes one file."
