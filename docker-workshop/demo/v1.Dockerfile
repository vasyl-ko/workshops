# v1 — the naive Dockerfile most people write first.
# Problems (revealed live in the workshop):
#   - full python image: ~1 GB base
#   - COPY . . before uv sync: ANY code change busts the cache
#     and re-resolves/reinstalls every dependency
#   - uv's download cache ships inside the layer
#   - runs as root
FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /bin/uv

WORKDIR /code

COPY . .

RUN uv sync

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
