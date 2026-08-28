# Docker Cheat Sheet

One page to keep. From the "Docker for the Team" workshop.

## Containers

```bash
docker run -it --rm IMAGE bash      # throwaway interactive container
docker run -d -p 8000:8000 --name api IMAGE   # background, port published
docker ps                # running containers
docker ps -a             # ...including dead ones (check exit codes here)
docker stop api          # graceful stop
docker rm api            # remove (add -f to stop+remove)
```

Key `docker run` flags: `-it` interactive · `--rm` self-cleaning ·
`-d` background · `-p HOST:CONTAINER` publish port · `-e KEY=val` env var ·
`-v src:dst` mount · `--name` a sane name.

## Images

```bash
docker build -t name:tag .          # build from ./Dockerfile
docker build -f v2.Dockerfile -t name:tag .
docker build --progress=plain …     # raw daemon logs, nothing collapses
                                    # (env alternative: BUILDKIT_PROGRESS=plain)
docker images                       # local images + sizes
docker pull python:3.12-slim        # tags don't auto-update; pull explicitly
docker rmi name:tag
docker history name:tag             # layers + sizes: which instruction cost what
dive name:tag                       # x-ray: browse each layer's files, spot waste
docker build --platform linux/amd64 …          # cross-build for prod's CPU
docker image inspect -f '{{.Architecture}}' …  # what arch is this image?
```

Dockerfile rules of thumb:
1. Slim, version-pinned base (`python:3.12-slim`, never bare `python`)
2. `COPY pyproject.toml uv.lock` + `uv sync --frozen` **before** `COPY`ing code (cache!)
3. Keep a `.dockerignore` (.git, venv, __pycache__)
4. Multi-stage when there's a build step; non-root `USER` at the end
5. Layers are append-only: `rm` in a later layer hides bytes, it doesn't remove
   them — clean up in the same `RUN` (and `uv sync --no-cache`)
6. Secrets never go in a layer — not even if you delete them later (see rule 5)

## Wiring containers by hand

```bash
docker network create demo                    # containers on the same network
docker run -d --name db --network demo …      # …reach each other BY NAME (db:5432)
docker run -e KEY=val --env-file .env IMAGE   # config via env — never baked in
docker run -v pgdata:/var/lib/postgresql/data IMAGE   # named volume: state survives
docker run -v ./app:/code/app IMAGE           # bind mount: live-edit your code
docker volume ls / inspect pgdata
```

Networking: `localhost` inside a container = that container, not your host.
Apps must bind `0.0.0.0` to be reachable via `-p`. Prefix to keep ports
private: `-p 127.0.0.1:5432:5432`.

Storage: **code in bind mounts, state in named volumes.**
(Composing all this into one committed file = the Docker Compose workshop.)

## When it breaks — in this order

```bash
docker ps -a                        # 1. what died? exit code?
docker logs -f --tail 100 api       # 2. what did it say?
docker exec -it api sh              # 3. look around inside
docker inspect api                  # 4. env, mounts, networks — the truth
docker stats                        # who's eating CPU/RAM
```

Deeper cuts:

```bash
docker run -it --entrypoint sh IMAGE   # container won't start? debug the image
docker logs --since 10m --timestamps api
docker cp api:/path/file .             # extract files (works on stopped containers)
docker diff api                        # files changed vs the image
docker top api                         # processes inside, no exec needed
docker inspect -f '{{.State.ExitCode}}' api
docker events --since 10m              # daemon feed: OOM kills, restarts, dies
```

| Symptom | Usual cause |
|---|---|
| `port is already allocated` | forgotten container (`docker ps`) or host process (`lsof -i :PORT`) |
| `Exited (1)` instantly | app crashed on boot — read `docker logs` |
| `Exited (137)` / OOMKilled | out of memory — raise limit or fix leak |
| API can't reach db | `localhost` instead of service name, or db not ready (use healthcheck + `condition: service_healthy`) |
| works on host, not in container | app binds `127.0.0.1` instead of `0.0.0.0` |

## Disk space

```bash
docker system df            # what's using space
docker system prune         # safe-ish: stopped containers, dangling images, cache
docker system prune -a --volumes   # aggressive: read the prompt before yes
```
