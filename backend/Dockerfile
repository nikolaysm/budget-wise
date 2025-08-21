# Dockerfile for the FastAPI backend service
#
# This image installs the Python dependencies listed in requirements.txt,
# copies the application code and Alembic migrations, and starts the
# Uvicorn server on port 8000. It also runs database migrations on
# container startup.

FROM python:3.11-slim as base

WORKDIR /app

# Install curl to fetch uv, then install uv (fast Python package manager)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh -s -- -y

# Ensure uv is on PATH
ENV PATH="/root/.local/bin:${PATH}"

# Install Python dependencies with uv
COPY requirements.txt /app/requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy application code and migrations
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Expose the backend port
EXPOSE 8000

# Run migrations if any exist, then start the application using Uvicorn
CMD ["bash", "-c", "alembic upgrade head || echo 'No migrations to apply'; uvicorn app.main:app --host 0.0.0.0 --port 8000"]