# Dockerfile for the FastAPI backend service (optimized)

# 1) Builder stage: install uv and resolve dependencies once
FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh -s

# Ensure uv is on PATH in this stage
ENV PATH="/root/.local/bin:${PATH}"

# Sync project dependencies into a local virtual environment (.venv)
# Using pyproject.toml; if you add uv.lock to the repo later, also COPY it and add --frozen.
COPY pyproject.toml /app/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev

# 2) Runtime stage: copy only what we need and run as a non-root user
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Copy the virtual environment from builder and ensure it's used by default
COPY --from=builder /app/.venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Create an unprivileged user
RUN useradd -u 10001 -r -m appuser

# Copy application code and Alembic migrations
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Adjust ownership so the non-root user can access files
RUN chown -R appuser:appuser /app
USER appuser

# Expose the backend port
EXPOSE 8000

# Add and use an entrypoint to handle DB wait + migrations
USER root
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]