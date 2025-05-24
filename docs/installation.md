# 🚀 Complete Installation Guide

This comprehensive guide covers all installation methods, configuration options, and deployment scenarios for ListSync. Choose the method that best fits your technical expertise and infrastructure setup.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Recommended)](#quick-start-recommended)
3. [Docker Installation](#docker-installation)
4. [Manual Installation](#manual-installation)
5. [Environment Configuration](#environment-configuration)
6. [Advanced Configuration](#advanced-configuration)
7. [Verification and Testing](#verification-and-testing)
8. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, Windows (Docker recommended for Windows)
- **Python**: 3.9+ (for manual installation)
- **Docker**: Latest version (for Docker installation)
- **Memory**: Minimum 512MB RAM, 1GB+ recommended
- **Storage**: 100MB+ free space for application and data
- **Network**: Internet access for API calls and web scraping

### Required Services

- **Overseerr or Jellyseerr**: Running instance with API access
- **List Services**: Account on IMDb, Trakt, Letterboxd, or MDBList (depending on your needs)

### API Prerequisites

Before installation, ensure you have:
1. **Overseerr/Jellyseerr URL**: The web address of your media server
2. **API Key**: Generated from your Overseerr/Jellyseerr settings
3. **List IDs**: From your preferred list services (see [List ID Guide](#obtaining-list-ids))

## ⚡ Quick Start (Recommended)

The fastest way to get started is using our interactive Docker one-liner:

### For Unix/Linux/macOS:
```bash
docker pull ghcr.io/woahai321/list-sync:main && \
docker run -it --rm \
  -v "$(pwd)/data:/usr/src/app/data" \
  -e TERM=xterm-256color \
  ghcr.io/woahai321/list-sync:main
```

### For Windows PowerShell:
```powershell
docker pull ghcr.io/woahai321/list-sync:main
docker run -it --rm -v "${PWD}/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
```

### For Windows Command Prompt:
```cmd
docker pull ghcr.io/woahai321/list-sync:main
docker run -it --rm -v "%cd%/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
```

This will:
1. Pull the latest ListSync image
2. Run in interactive mode
3. Create a local `data/` directory for persistence
4. Prompt you for configuration during first run

## 🐳 Docker Installation

Docker provides the most reliable and consistent experience across different platforms.

### Method 1: Interactive Mode (Beginner-Friendly)

Perfect for initial setup and testing:

```bash
# Create a dedicated directory
mkdir listsync && cd listsync

# Run in interactive mode
docker run -it --rm \
  -v "$(pwd)/data:/usr/src/app/data" \
  -e TERM=xterm-256color \
  ghcr.io/woahai321/list-sync:main
```

**Features:**
- Guided setup process
- Credential encryption
- Interactive list management
- Manual sync triggers

### Method 2: Automated Mode with Docker Compose

Ideal for production deployments and automation:

1. **Create project directory:**
   ```bash
   mkdir listsync && cd listsync
   ```

2. **Create `.env` file:**
   ```bash
   # Overseerr Configuration
   OVERSEERR_URL=https://your-overseerr-instance.com
   OVERSEERR_API_KEY=your-api-key-here
   OVERSEERR_USER_ID=1

   # Automation Settings
   AUTOMATED_MODE=true
   SYNC_INTERVAL=24
   OVERSEERR_4K=false
   TRAKT_SPECIAL_ITEMS_LIMIT=20

   # Lists (comma-separated)
   IMDB_LISTS=ls123456789,top,boxoffice
   TRAKT_LISTS=12345,67890
   TRAKT_SPECIAL_LISTS=trending:movies,popular:shows
   LETTERBOXD_LISTS=https://letterboxd.com/username/list/listname/
   MDBLIST_LISTS=username/listname
   STEVENLU_LISTS=stevenlu

   # Optional: Discord notifications
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
   ```

3. **Create `docker-compose.yml`:**
   ```yaml
   version: "3.8"
   
   services:
     listsync:
       image: ghcr.io/woahai321/list-sync:main
       container_name: listsync
       environment:
         - OVERSEERR_URL=${OVERSEERR_URL}
         - OVERSEERR_API_KEY=${OVERSEERR_API_KEY}
         - OVERSEERR_USER_ID=${OVERSEERR_USER_ID:-1}
         - SYNC_INTERVAL=${SYNC_INTERVAL:-24}
         - AUTOMATED_MODE=true
         - OVERSEERR_4K=${OVERSEERR_4K:-false}
         - TRAKT_SPECIAL_ITEMS_LIMIT=${TRAKT_SPECIAL_ITEMS_LIMIT:-20}
         - IMDB_LISTS=${IMDB_LISTS}
         - TRAKT_LISTS=${TRAKT_LISTS}
         - TRAKT_SPECIAL_LISTS=${TRAKT_SPECIAL_LISTS}
         - LETTERBOXD_LISTS=${LETTERBOXD_LISTS}
         - MDBLIST_LISTS=${MDBLIST_LISTS}
         - STEVENLU_LISTS=${STEVENLU_LISTS}
         - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
       volumes:
         - ./data:/usr/src/app/data
         - ./.env:/usr/src/app/.env
       restart: unless-stopped
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

4. **Deploy:**
   ```bash
   docker-compose up -d
   ```

5. **Monitor logs:**
   ```bash
   docker-compose logs -f listsync
   ```

### Method 3: Direct Docker Commands

For custom deployments or CI/CD integration:

```bash
# Automated mode with environment variables
docker run -d \
  --name listsync \
  --restart unless-stopped \
  -v "$(pwd)/data:/usr/src/app/data" \
  -e OVERSEERR_URL="https://your-overseerr.com" \
  -e OVERSEERR_API_KEY="your-api-key" \
  -e AUTOMATED_MODE="true" \
  -e SYNC_INTERVAL="12" \
  -e IMDB_LISTS="ls123456789,top" \
  -e TRAKT_LISTS="12345" \
  ghcr.io/woahai321/list-sync:main
```

## 📦 Manual Installation

For developers or users who prefer local Python environments.

### Method 1: Using Poetry (Recommended)

Poetry provides excellent dependency management and environment isolation:

1. **Install Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   poetry install
   ```

3. **Run:**
   ```bash
   # Interactive mode
   poetry run python -m list_sync

   # Or with environment variables
   OVERSEERR_URL="..." OVERSEERR_API_KEY="..." poetry run python -m list_sync
   ```

### Method 2: Using pip

Standard Python package installation:

1. **Clone repository:**
   ```bash
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv listsync-env
   source listsync-env/bin/activate  # On Windows: listsync-env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run:**
   ```bash
   python -m list_sync
   ```

### Method 3: Development Setup

For contributing or advanced customization:

1. **Fork and clone:**
   ```bash
   git clone https://github.com/yourusername/list-sync.git
   cd list-sync
   ```

2. **Install development dependencies:**
   ```bash
   poetry install --with dev
   # or
   pip install -r requirements.txt
   pip install ruff  # for linting
   ```

3. **Setup pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

## 🔧 Environment Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OVERSEERR_URL` | ✅ | - | Your Overseerr/Jellyseerr URL |
| `OVERSEERR_API_KEY` | ✅ | - | API key from Overseerr/Jellyseerr |
| `OVERSEERR_USER_ID` | ❌ | `1` | User ID for requests |
| `AUTOMATED_MODE` | ❌ | `false` | Enable automated syncing |
| `SYNC_INTERVAL` | ❌ | `24` | Hours between syncs (supports decimals) |
| `OVERSEERR_4K` | ❌ | `false` | Request 4K quality |
| `TRAKT_SPECIAL_ITEMS_LIMIT` | ❌ | `20` | Items from special Trakt lists |
| `DISCORD_WEBHOOK_URL` | ❌ | - | Discord webhook for notifications |

### List Configuration Variables

| Variable | Format | Example |
|----------|--------|---------|
| `IMDB_LISTS` | Comma-separated | `ls123456789,ur987654321,top,boxoffice` |
| `TRAKT_LISTS` | Comma-separated | `12345,67890,https://trakt.tv/users/user/lists/name` |
| `TRAKT_SPECIAL_LISTS` | Comma-separated | `trending:movies,popular:shows,anticipated:movies` |
| `LETTERBOXD_LISTS` | Comma-separated | `https://letterboxd.com/user/list/name/` |
| `MDBLIST_LISTS` | Comma-separated | `username/listname,https://mdblist.com/lists/user/list` |
| `STEVENLU_LISTS` | Fixed value | `stevenlu` |

### Configuration Methods Priority

1. **Environment Variables** (highest priority)
2. **Encrypted config file** (`data/config.enc`)
3. **Interactive prompts** (lowest priority)

## ⚙️ Advanced Configuration

### Custom Sync Intervals

ListSync supports flexible scheduling:

```bash
SYNC_INTERVAL=0.5    # 30 minutes
SYNC_INTERVAL=1.5    # 1.5 hours
SYNC_INTERVAL=6      # 6 hours
SYNC_INTERVAL=24     # Daily (default)
SYNC_INTERVAL=168    # Weekly
```

### Quality Profiles

Configure request quality:

```bash
OVERSEERR_4K=false   # Standard quality (default)
OVERSEERR_4K=true    # 4K quality requests
```

### Trakt Special Lists Configuration

Customize Trakt trending/popular lists:

```bash
# List types: trending, popular, anticipated, watched, collected, boxoffice, streaming, recommendations, favorited
# Media types: movies, shows
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows,anticipated:movies,boxoffice:movies
TRAKT_SPECIAL_ITEMS_LIMIT=50  # Increase from default 20
```

### Discord Notifications

Enable real-time sync notifications:

1. **Create Discord webhook:**
   - Go to your Discord server settings
   - Navigate to Integrations → Webhooks
   - Create a new webhook and copy the URL

2. **Configure ListSync:**
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijk
   ```

### Logging Configuration

Control logging verbosity:

```bash
# Environment variable
export LOG_LEVEL=DEBUG    # DEBUG, INFO, WARNING, ERROR

# Or in .env file
LOG_LEVEL=INFO
```

### Security Configuration

For enhanced security in shared environments:

1. **Use environment variables instead of config files**
2. **Restrict file permissions:**
   ```bash
   chmod 600 .env  # Owner read/write only
   ```
3. **Use Docker secrets for sensitive data**

## ✅ Verification and Testing

### Test Installation

1. **Check Docker installation:**
   ```bash
   docker run --rm ghcr.io/woahai321/list-sync:main --version
   ```

2. **Test API connectivity:**
   ```bash
   # Set environment variables
   export OVERSEERR_URL="https://your-overseerr.com"
   export OVERSEERR_API_KEY="your-api-key"
   
   # Test connection
   curl -H "X-Api-Key: $OVERSEERR_API_KEY" "$OVERSEERR_URL/api/v1/status"
   ```

3. **Verify list access:**
   - IMDb: Ensure lists are public or you're logged in
   - Trakt: Verify list visibility settings
   - Letterboxd: Check list privacy settings

### Dry Run Mode

Test configuration without making actual requests:

```bash
# Interactive mode
docker run -it --rm \
  -v "$(pwd)/data:/usr/src/app/data" \
  -e TERM=xterm-256color \
  ghcr.io/woahai321/list-sync:main

# Then select "Dry Run" from the menu
```

### Log Analysis

Monitor logs for successful operation:

```bash
# Docker Compose
docker-compose logs -f

# Direct Docker
docker logs -f listsync

# Look for key indicators:
# ✅ "API connection successful!"
# ✅ "Found X items in Y list"
# ✅ "Sync completed successfully"
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. **API Connection Failures**

**Symptoms:**
- "API connection failed" errors
- 401/403 HTTP errors

**Solutions:**
```bash
# Verify URL format (no trailing slash)
OVERSEERR_URL=https://overseerr.example.com  # ✅ Correct
OVERSEERR_URL=https://overseerr.example.com/ # ❌ Incorrect

# Test API key manually
curl -H "X-Api-Key: YOUR_KEY" "YOUR_URL/api/v1/status"

# Check network connectivity
ping overseerr.example.com
```

#### 2. **Selenium WebDriver Issues**

**Symptoms:**
- "WebDriver creation failed"
- Browser timeout errors

**Solutions:**
```bash
# Update Docker image
docker pull ghcr.io/woahai321/list-sync:main

# Increase timeout in environment
export SELENIUM_TIMEOUT=30

# For manual installation, update selenium
pip install --upgrade seleniumbase
```

#### 3. **List Access Problems**

**Symptoms:**
- "No items found" for public lists
- Permission denied errors

**Solutions:**
- Verify list privacy settings (must be public)
- Check list URL format and accessibility
- For IMDb: Use list ID format (ls123456789)
- For Trakt: Ensure list is public or shared

#### 4. **Docker Permission Issues**

**Symptoms:**
- "Permission denied" on data directory
- File ownership problems

**Solutions:**
```bash
# Fix permissions
sudo chown -R $(id -u):$(id -g) ./data/

# Or use Docker user mapping
docker run --user $(id -u):$(id -g) ...
```

#### 5. **Memory/Resource Issues**

**Symptoms:**
- Container exits unexpectedly
- "Out of memory" errors

**Solutions:**
```bash
# Increase Docker memory limits
docker run --memory=1g ...

# Or in docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

### Debug Mode

Enable comprehensive debugging:

```bash
# With Docker
docker run -e LOG_LEVEL=DEBUG ...

# With environment
export LOG_LEVEL=DEBUG
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs** for specific error messages
2. **Search existing issues** on GitHub
3. **Create detailed issue report** including:
   - Installation method used
   - Full error messages
   - Configuration (without API keys)
   - Log excerpts

### Performance Optimization

For large deployments:

```bash
# Reduce sync frequency for large lists
SYNC_INTERVAL=48  # Every 2 days

# Limit special list items
TRAKT_SPECIAL_ITEMS_LIMIT=10

# Use SSD storage for database
# Mount data directory on fast storage
```

## 🔄 Upgrading

### Docker Upgrades

```bash
# Pull latest image
docker pull ghcr.io/woahai321/list-sync:main

# Restart container
docker-compose down && docker-compose up -d
```

### Manual Installation Upgrades

```bash
# With Git
git pull origin main
poetry install  # or pip install -r requirements.txt

# Check for breaking changes in CHANGELOG.md
```

## 📚 Next Steps

After successful installation:

1. **Configure your lists** - See [List ID Guide](obtaining-list-ids.md)
2. **Set up automation** - Configure sync intervals
3. **Enable notifications** - Set up Discord webhooks
4. **Monitor performance** - Check logs regularly
5. **Read advanced docs** - Explore [How It Works](how-it-works.md)
