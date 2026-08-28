# v2.1 — cache-friendly layer order. IDENTICAL to v2.Dockerfile — same
# slim base, same uv flags — except for one thing: pyproject.toml + uv.lock
# are copied and synced BEFORE the code. Code edits reuse the cached
# dependency layer, so rebuilds drop from ~30s to ~1s.
# (.dockerignore keeps junk out of the build context either way.)
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /bin/uv

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

ENV PATH="/code/.venv/bin:$PATH"

COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
