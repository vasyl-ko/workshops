# v3 — multi-stage build + non-root user. Production-shaped.
# Fixes over v2:
#   - build stage keeps uv itself (and any build tooling) out of the final
#     image; only the synced .venv is copied across
#   - runs as a non-root user
#   - HEALTHCHECK so orchestrators/compose know when the app is actually up

# ---- build stage ----
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /bin/uv

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# ---- runtime stage ----
FROM python:3.12-slim

RUN useradd --create-home appuser
USER appuser
WORKDIR /code

# same absolute path as in the builder, so the venv's interpreter links hold
COPY --from=builder /code/.venv .venv
ENV PATH="/code/.venv/bin:$PATH"

COPY app/ app/

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
