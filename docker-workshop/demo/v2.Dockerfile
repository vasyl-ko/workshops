# v2 — v1 on a slim base. Same naive layer order, ~1.4 GB lighter.
# Fixed over v1: the base image (python:3.12-slim) and the uv flags
#   (--frozen: exactly the lockfile; --no-dev: no pytest in the image;
#    --no-cache: don't ship uv's download cache in the layer).
# Still wrong: code is copied BEFORE the dependency sync, so ANY code
# edit invalidates the COPY layer and every dependency re-syncs.
# v2.1.Dockerfile fixes exactly that — and nothing else.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /bin/uv

WORKDIR /code

COPY . .

RUN uv sync --frozen --no-dev --no-cache

ENV PATH="/code/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
