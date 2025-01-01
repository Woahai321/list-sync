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

# Install required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    libgbm-dev \
    libgtk-3-0 \
    libx11-xcb1 \
    libxtst6 \
    xdg-utils \
    libglib2.0-0 \
    libdrm2 \
    libxrandr2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install specific versions of Chrome and ChromeDriver
RUN wget -O /tmp/chrome-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    mv /opt/chrome-linux64 /opt/chrome && \
    ln -sf /opt/chrome/chrome /usr/bin/google-chrome && \
    chmod +x /usr/bin/google-chrome && \
    rm /tmp/chrome-linux64.zip && \
    \
    wget -O /tmp/chromedriver-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver-linux64.zip

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_DRIVER_PATH=/usr/local/bin/chromedriver \
    RUNNING_IN_DOCKER=true \
    DISPLAY=:99 \
    PYTHONPATH=/usr/src/app/.venv/lib/python3.9/site-packages \
    SELENIUM_DRIVER_PATH=/usr/local/bin/chromedriver

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

# Add a startup script
COPY <<'EOF' /usr/src/app/startup.sh
#!/bin/bash
echo "Chrome version:"
google-chrome --version
echo "ChromeDriver version:"
chromedriver --version
echo "ChromeDriver location:"
which chromedriver
echo "Starting application..."
python add.py
EOF

RUN chmod +x /usr/src/app/startup.sh

# The entrypoint should run the startup script
ENTRYPOINT ["/usr/src/app/startup.sh"]