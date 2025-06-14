# Multi-stage Dockerfile for Complete ListSync Web Application
# Includes: ListSync Core Service + FastAPI Backend + Next.js Frontend

# Use specific Python version
ARG PYTHON_VERSION=3.9
ARG NODE_VERSION=18

# Stage 1: Python Builder (ListSync + API)
FROM python:${PYTHON_VERSION}-slim AS python-builder

WORKDIR /usr/src/app

# Install build dependencies for Python packages that need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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

# Install additional API dependencies
COPY api_requirements.txt ./
RUN .venv/bin/pip install -r api_requirements.txt

# Stage 2: Node.js Builder (Frontend)
FROM node:${NODE_VERSION}-slim AS node-builder

WORKDIR /app/frontend

# Accept API URL as build argument and set as environment variable
ARG NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:4222/api}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:4222/api}

# Copy package files
COPY listsync-web/package*.json ./

# Install all dependencies (including dev dependencies for build) - clean install for Linux
RUN npm ci

# Copy frontend source (excluding node_modules to avoid Windows-specific files)
COPY listsync-web/src ./src
COPY listsync-web/public ./public
COPY listsync-web/next.config.ts ./
COPY listsync-web/postcss.config.mjs ./
COPY listsync-web/tsconfig.json ./
COPY listsync-web/next-env.d.ts ./
COPY listsync-web/eslint.config.mjs ./

# Ensure proper permissions for Node.js binaries
RUN chmod +x node_modules/.bin/*

# Build the Next.js application with the API URL baked in
RUN npm run build

# Stage 3: Final Runtime Image
FROM python:${PYTHON_VERSION}-slim AS runtime

# Install system dependencies for Chrome, Node.js, and process management
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome dependencies
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
    xvfb \
    dbus-x11 \
    xauth \
    # Node.js
    curl \
    # Process management
    supervisor \
    # Log rotation
    logrotate \
    # Timezone support
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone - use environment variable if provided, otherwise try to detect from host
ENV TZ=${TZ:-UTC}

# Enhanced timezone setup with abbreviation support
RUN if [ "$TZ" = "UTC" ]; then \
        # Try to detect timezone from host if mounted
        if [ -f /etc/timezone ]; then \
            TZ=$(cat /etc/timezone); \
        elif [ -L /etc/localtime ]; then \
            TZ=$(readlink /etc/localtime | sed 's|/usr/share/zoneinfo/||'); \
        fi; \
    fi && \
    # Create a simple timezone validation script
    echo '#!/bin/bash' > /tmp/validate_tz.sh && \
    echo 'python3 -c "' >> /tmp/validate_tz.sh && \
    echo 'import sys, os' >> /tmp/validate_tz.sh && \
    echo 'sys.path.insert(0, \"/usr/src/app\")' >> /tmp/validate_tz.sh && \
    echo 'try:' >> /tmp/validate_tz.sh && \
    echo '    from list_sync.utils.timezone_utils import normalize_timezone_input' >> /tmp/validate_tz.sh && \
    echo '    tz = normalize_timezone_input(os.environ.get(\"TZ\", \"UTC\"))' >> /tmp/validate_tz.sh && \
    echo '    print(tz)' >> /tmp/validate_tz.sh && \
    echo 'except:' >> /tmp/validate_tz.sh && \
    echo '    print(\"UTC\")' >> /tmp/validate_tz.sh && \
    echo '"' >> /tmp/validate_tz.sh && \
    chmod +x /tmp/validate_tz.sh && \
    # Set the timezone (will be validated later when Python modules are available)
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Download and install Chrome and ChromeDriver
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

# Set environment variables for the final image
ENV TZ=GMT \
    SELENIUM_HOST=localhost \
    SELENIUM_PORT=4444 \
    RUNNING_IN_DOCKER=true \
    DISPLAY=:99 \
    SELENIUM_DRIVER_PATH=/usr/local/bin/chromedriver \
    PYTHONPATH=/usr/src/app \
    NO_SANDBOX=1

# Set working directory
WORKDIR /usr/src/app

# Copy Python virtual environment from builder
COPY --from=python-builder /usr/src/app/.venv .venv

# Copy built Next.js application from builder
COPY --from=node-builder /app/frontend/.next ./frontend/.next
COPY --from=node-builder /app/frontend/public ./frontend/public
COPY --from=node-builder /app/frontend/package*.json ./frontend/
COPY --from=node-builder /app/frontend/node_modules ./frontend/node_modules

# Ensure proper permissions for Node.js binaries in the final image
RUN chmod +x ./frontend/node_modules/.bin/*

# Copy application source code
COPY . .

# Copy frontend configuration files
COPY listsync-web/next.config.ts ./frontend/
COPY listsync-web/postcss.config.mjs ./frontend/

# "activate" Python venv
ENV PATH="/usr/src/app/.venv/bin:$PATH"

# Create necessary directories
RUN mkdir -p /usr/src/app/data /tmp/.X11-unix /var/log/supervisor && \
    chmod 1777 /tmp/.X11-unix

# Create wrapper script for listsync-core to output to both file and stdout
RUN echo '#!/bin/bash' > /usr/src/app/run-listsync-core.sh && \
    echo 'exec /usr/src/app/.venv/bin/python -m list_sync 2>&1 | while IFS= read -r line; do echo "$(date "+%Y-%m-%d %H:%M:%S") $line"; done | tee -a /var/log/supervisor/listsync-core.log' >> /usr/src/app/run-listsync-core.sh && \
    chmod +x /usr/src/app/run-listsync-core.sh

# Create timezone setup script that runs at startup
RUN echo '#!/bin/bash' > /usr/src/app/setup-timezone.sh && \
    echo '# Validate and set timezone using our timezone utilities' >> /usr/src/app/setup-timezone.sh && \
    echo 'cd /usr/src/app' >> /usr/src/app/setup-timezone.sh && \
    echo 'export PYTHONPATH=/usr/src/app' >> /usr/src/app/setup-timezone.sh && \
    echo 'VALIDATED_TZ=$(/usr/src/app/.venv/bin/python3 -c "' >> /usr/src/app/setup-timezone.sh && \
    echo 'import os, sys' >> /usr/src/app/setup-timezone.sh && \
    echo 'sys.path.insert(0, \"/usr/src/app\")' >> /usr/src/app/setup-timezone.sh && \
    echo 'try:' >> /usr/src/app/setup-timezone.sh && \
    echo '    from list_sync.utils.timezone_utils import normalize_timezone_input, set_system_timezone' >> /usr/src/app/setup-timezone.sh && \
    echo '    tz_input = os.environ.get(\"TZ\", \"UTC\")' >> /usr/src/app/setup-timezone.sh && \
    echo '    validated_tz = normalize_timezone_input(tz_input)' >> /usr/src/app/setup-timezone.sh && \
    echo '    set_system_timezone(validated_tz)' >> /usr/src/app/setup-timezone.sh && \
    echo '    print(f\"Timezone set to: {validated_tz} (from input: {tz_input})\", file=sys.stderr)' >> /usr/src/app/setup-timezone.sh && \
    echo '    print(validated_tz)' >> /usr/src/app/setup-timezone.sh && \
    echo 'except Exception as e:' >> /usr/src/app/setup-timezone.sh && \
    echo '    print(f\"Timezone setup failed: {e}, using UTC\", file=sys.stderr)' >> /usr/src/app/setup-timezone.sh && \
    echo '    print(\"UTC\")' >> /usr/src/app/setup-timezone.sh && \
    echo '"' >> /usr/src/app/setup-timezone.sh && \
    echo ')' >> /usr/src/app/setup-timezone.sh && \
    echo 'if [ "$VALIDATED_TZ" != "" ]; then' >> /usr/src/app/setup-timezone.sh && \
    echo '    export TZ="$VALIDATED_TZ"' >> /usr/src/app/setup-timezone.sh && \
    echo '    echo "Final timezone: $TZ"' >> /usr/src/app/setup-timezone.sh && \
    echo 'fi' >> /usr/src/app/setup-timezone.sh && \
    chmod +x /usr/src/app/setup-timezone.sh

# Create logrotate configuration for listsync-core.log
RUN echo '/var/log/supervisor/listsync-core.log {' > /etc/logrotate.d/listsync-core && \
    echo '    daily' >> /etc/logrotate.d/listsync-core && \
    echo '    rotate 30' >> /etc/logrotate.d/listsync-core && \
    echo '    compress' >> /etc/logrotate.d/listsync-core && \
    echo '    delaycompress' >> /etc/logrotate.d/listsync-core && \
    echo '    missingok' >> /etc/logrotate.d/listsync-core && \
    echo '    notifempty' >> /etc/logrotate.d/listsync-core && \
    echo '    create 644 root root' >> /etc/logrotate.d/listsync-core && \
    echo '    size 50M' >> /etc/logrotate.d/listsync-core && \
    echo '}' >> /etc/logrotate.d/listsync-core

# Create supervisor configuration
RUN echo "[supervisord]" > /etc/supervisor/conf.d/listsync.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "user=root" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "logfile=/var/log/supervisor/supervisord.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "pidfile=/var/run/supervisord.pid" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "silent=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "loglevel=warn" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "[program:timezone-setup]" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "command=/usr/src/app/setup-timezone.sh" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "directory=/usr/src/app" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autorestart=false" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "startsecs=0" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "startretries=1" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "exitcodes=0" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile=/var/log/supervisor/timezone-setup.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile=/var/log/supervisor/timezone-setup.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile_maxbytes=1MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile_maxbytes=1MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "redirect_stderr=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "priority=100" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "[program:xvfb]" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "command=/usr/bin/Xvfb :99 -screen 0 1024x768x24" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile=/var/log/supervisor/xvfb.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile=/var/log/supervisor/xvfb.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile_maxbytes=1MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile_maxbytes=1MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "redirect_stderr=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "priority=200" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "[program:listsync-api]" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "command=/usr/src/app/.venv/bin/python start_api.py" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "directory=/usr/src/app" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile=/var/log/supervisor/api.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile=/var/log/supervisor/api.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "redirect_stderr=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "priority=300" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "[program:listsync-frontend]" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "command=npm start" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "directory=/usr/src/app/frontend" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile=/var/log/supervisor/frontend.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile=/var/log/supervisor/frontend.log" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "redirect_stderr=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "priority=400" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "[program:listsync-core]" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "command=/usr/src/app/run-listsync-core.sh" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "directory=/usr/src/app" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/conf.d/listsync.conf && \
    echo "priority=500" >> /etc/supervisor/conf.d/listsync.conf

# Expose ports
EXPOSE 3222 4222

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:4222/api/system/health && curl -f http://localhost:3222 || exit 1

# Start all services with supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/listsync.conf"]
