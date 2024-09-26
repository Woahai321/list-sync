ARG PYTHON_VERSION=3.9
# Use official Python image from the Docker Hub
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /usr/src/app

# install poetry
RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./

# poetry settings
ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=true \
  POETRY_CACHE_DIR=/tmp/poetry_cache

# build venv
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main --no-root
RUN poetry install

ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim AS app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/src/app

# copy venv from builder
COPY --from=builder /usr/src/app/.venv .venv

# "activate" venv
ENV PATH="/home/app/renamarr/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Ensure the data directory exists
RUN mkdir -p /usr/src/app/data

# The entrypoint should run the script
ENTRYPOINT ["python", "add.py"]
