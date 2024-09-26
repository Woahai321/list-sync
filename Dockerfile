# Use specific Python version
ARG PYTHON_VERSION=3.9

# Stage 1: Builder
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /usr/src/app

# Install Poetry
RUN pip install poetry==1.8.3

# Copy Poetry configuration
COPY pyproject.toml poetry.lock ./

# Poetry settings
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Build virtual environment with dependencies
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main --no-root

# Stage 2: App stage
FROM python:${PYTHON_VERSION}-slim AS app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/src/app

# Copy the virtual environment from the builder stage
COPY --from=builder /usr/src/app/.venv .venv

# "activate" venv
ENV PATH="/usr/src/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Ensure the data directory exists
RUN mkdir -p /usr/src/app/data

# The entrypoint should run the script
ENTRYPOINT ["python", "add.py"]
