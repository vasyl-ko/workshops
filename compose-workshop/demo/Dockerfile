# The cache-friendly slim build from the basics workshop (v2.1 there), now with
# named stages so Compose can pick one with `build.target`:
#   base    — deps (no dev group) + code + CMD
#   dev     — base + the dev dependency group (pytest, httpx) + the tests
#   runtime — the default (last stage wins when no target is given): lean
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /bin/uv

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

ENV PATH="/code/.venv/bin:$PATH"

COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Selected by compose.override.yaml (dev) and compose.ci.yaml (CI).
FROM base AS dev
RUN uv sync --frozen --no-cache
COPY tests/ tests/

# Selected when nothing says otherwise: `docker compose -f compose.yaml build`.
FROM base AS runtime
