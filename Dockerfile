# ─── Stage 1: Build dependencies ────────────────────────────────
FROM python:3.11-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml ./

# Install dependencies into a virtual environment
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python -e ".[dev]"

# ─── Stage 2: Runtime ───────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Ensure the venv is on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY agents/ ./agents/
COPY ingestion/ ./ingestion/
COPY scripts/ ./scripts/
COPY db/ ./db/

EXPOSE 8080

CMD ["uvicorn", "agents.api:app", "--host", "0.0.0.0", "--port", "8080"]
