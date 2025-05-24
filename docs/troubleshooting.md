# 🛠️ Comprehensive Troubleshooting Guide

This guide provides detailed solutions for common issues, debugging techniques, and diagnostic procedures for ListSync.

## 📋 Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Installation Issues](#installation-issues)
3. [Configuration Problems](#configuration-problems)
4. [Provider-Specific Issues](#provider-specific-issues)
5. [API and Network Issues](#api-and-network-issues)
6. [Database and Storage Problems](#database-and-storage-problems)
7. [Performance Issues](#performance-issues)
8. [Docker-Specific Problems](#docker-specific-problems)
9. [Debugging Techniques](#debugging-techniques)
10. [Log Analysis](#log-analysis)
11. [Getting Help](#getting-help)

## ✅ Quick Diagnostic Checklist

Before diving into specific issues, run through this checklist:

### Basic Connectivity
- [ ] Can you access your Overseerr/Jellyseerr web interface?
- [ ] Is your API key valid and not expired?
- [ ] Are your list URLs accessible in a web browser?
- [ ] Is Docker running (if using Docker installation)?

### Configuration Verification
- [ ] Are environment variables set correctly?
- [ ] Is the config file readable/encrypted properly?
- [ ] Are list IDs in the correct format?
- [ ] Is the sync interval configured appropriately?

### Resource Availability
- [ ] Is there sufficient disk space (>100MB)?
- [ ] Is there adequate memory (>512MB)?
- [ ] Are network connections stable?
- [ ] Are required ports accessible?

## 🚀 Installation Issues

### Docker Installation Problems

#### Issue: "Docker command not found"
```bash
# Check if Docker is installed
docker --version

# Install Docker on Ubuntu/Debian
sudo apt update && sudo apt install docker.io

# Install Docker on macOS
brew install --cask docker

# Install Docker on Windows
# Download from https://docs.docker.com/desktop/windows/install/
```

#### Issue: "Permission denied" errors with Docker
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker run ...

# For Windows/macOS, ensure Docker Desktop is running
```

#### Issue: "Failed to pull Docker image"
```bash
# Check network connectivity
ping ghcr.io

# Try alternative registries or manual download
docker pull ghcr.io/woahai321/list-sync:main

# Clear Docker cache if needed
docker system prune -a
```

### Manual Installation Problems

#### Issue: "Python version not supported"
```bash
# Check Python version
python --version
python3 --version

# Install Python 3.9+ on Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-pip

# Install Python 3.9+ on macOS
brew install python@3.9

# Windows: Download from python.org
```

#### Issue: "Poetry installation failed"
```bash
# Install Poetry with alternative method
pip install poetry

# Or use official installer
curl -sSL https://install.python-poetry.org | python3 -

# Verify installation
poetry --version
```

#### Issue: "Dependency conflicts"
```bash
# Create clean virtual environment
python -m venv listsync-env
source listsync-env/bin/activate  # Linux/macOS
# or
listsync-env\Scripts\activate     # Windows

# Install with pip
pip install --upgrade pip
pip install -r requirements.txt

# Or use Poetry in isolation
poetry config virtualenvs.create true
poetry install
```

## ⚙️ Configuration Problems

### Environment Variable Issues

#### Issue: "Environment variables not loading"
```bash
# Verify .env file exists and is readable
ls -la .env
cat .env

# Check file permissions
chmod 644 .env

# Test environment loading
docker run --env-file .env alpine printenv | grep OVERSEERR
```

#### Issue: "Invalid environment variable format"
```bash
# Correct format examples
OVERSEERR_URL=https://overseerr.example.com  # No trailing slash
IMDB_LISTS=ls123456789,ur987654321,top       # Comma-separated, no spaces
SYNC_INTERVAL=24.5                           # Decimal values allowed

# Invalid formats
OVERSEERR_URL=https://overseerr.example.com/ # ❌ Trailing slash
IMDB_LISTS=ls123456789, ur987654321          # ❌ Spaces after comma
SYNC_INTERVAL=24h                            # ❌ Use numeric values only
```

### Credential Issues

#### Issue: "Encrypted config file corrupted"
```bash
# Delete corrupted config
rm data/config.enc

# Restart application to reconfigure
docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" ghcr.io/woahai321/list-sync:main
```

#### Issue: "API key authentication failed"
```bash
# Test API key manually
curl -H "X-Api-Key: YOUR_API_KEY" "https://your-overseerr.com/api/v1/status"

# Generate new API key in Overseerr
# Settings → General → API Key → Generate New

# Verify URL format (no trailing slash)
OVERSEERR_URL=https://overseerr.example.com
```

### List Configuration Issues

#### Issue: "No lists configured in automated mode"
```bash
# Verify environment variables are set
echo $IMDB_LISTS
echo $TRAKT_LISTS

# Check for typos in variable names
printenv | grep -i list

# Ensure proper format
IMDB_LISTS=ls123456789,top,boxoffice
TRAKT_LISTS=12345,67890
```

## 🔗 Provider-Specific Issues

### IMDb Issues

#### Issue: "IMDb list not found or access denied"
```bash
# Verify list is public and accessible
curl -I "https://www.imdb.com/list/ls123456789/"

# Check list ID format
# Valid: ls123456789, ur123456789, top, boxoffice
# Invalid: 123456789 (missing prefix)
```

#### Issue: "IMDb bot detection / CAPTCHA"
```bash
# Update to latest Docker image
docker pull ghcr.io/woahai321/list-sync:main

# Increase delays between requests
# This is handled automatically in the provider code

# Check if list requires login
# Ensure list privacy is set to "Public"
```

#### Issue: "Selenium timeout on IMDb"
```bash
# Increase timeout in environment
export SELENIUM_TIMEOUT=60

# Check IMDb service status
curl -I https://www.imdb.com/

# Try different list format
# URL: https://www.imdb.com/list/ls123456789/
# ID: ls123456789
```

### Trakt Issues

#### Issue: "Trakt list access problems"
```bash
# Verify list visibility (must be public)
curl -I "https://trakt.tv/users/username/lists/listname"

# Check list ID vs URL format
# URL: https://trakt.tv/users/user/lists/name
# ID: 12345678 (from share link)
```

#### Issue: "Trakt special lists not working"
```bash
# Verify correct format
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows

# Valid combinations:
# trending:movies, popular:movies, anticipated:movies
# trending:shows, popular:shows, anticipated:shows
# boxoffice:movies (movies only)

# Check item limit
TRAKT_SPECIAL_ITEMS_LIMIT=20  # Default, can increase
```

### Letterboxd Issues

#### Issue: "Letterboxd pagination problems"
```bash
# Verify list URL format
https://letterboxd.com/username/list/listname/

# Check if list is public
# Private lists cannot be accessed

# For watchlists
https://letterboxd.com/username/watchlist/
```

### MDBList Issues

#### Issue: "MDBList infinite scroll timeout"
```bash
# Try both URL formats
# Full URL: https://mdblist.com/lists/username/listname
# Short format: username/listname

# Check list accessibility
curl -I "https://mdblist.com/lists/username/listname"
```

## 🌐 API and Network Issues

### Overseerr API Problems

#### Issue: "Connection refused / timeout"
```bash
# Test basic connectivity
ping your-overseerr-domain.com
telnet your-overseerr-domain.com 443

# Check if Overseerr is accessible
curl -I https://your-overseerr.com

# Verify internal vs external URLs
# Internal: http://overseerr:5055
# External: https://overseerr.example.com
```

#### Issue: "SSL certificate problems"
```bash
# For self-signed certificates, test with curl
curl -k https://your-overseerr.com/api/v1/status

# Add certificate exception or use HTTP
OVERSEERR_URL=http://overseerr.local:5055  # If using HTTP
```

#### Issue: "Rate limiting (429 errors)"
```bash
# Reduce concurrent requests in code
# This is handled automatically with backoff

# Check Overseerr logs for rate limit settings
# Adjust sync frequency
SYNC_INTERVAL=48  # Reduce frequency

# Limit list sizes
TRAKT_SPECIAL_ITEMS_LIMIT=10  # Reduce items
```

### Network Connectivity Issues

#### Issue: "DNS resolution problems"
```bash
# Test DNS resolution
nslookup your-overseerr.com
dig your-overseerr.com

# Use IP address if DNS fails
OVERSEERR_URL=https://192.168.1.100:5055

# Configure DNS servers
# Add to docker-compose.yml:
# dns:
#   - 8.8.8.8
#   - 1.1.1.1
```

#### Issue: "Proxy/VPN interference"
```bash
# Bypass proxy for local services
export NO_PROXY=localhost,127.0.0.1,overseerr.local

# Configure proxy in Docker
docker run --env HTTP_PROXY=http://proxy:8080 ...

# Test without proxy
unset HTTP_PROXY HTTPS_PROXY
```

## 💾 Database and Storage Problems

### Database Issues

#### Issue: "Database locked"
```bash
# Stop all ListSync instances
docker stop listsync

# Check for stale lock files
ls -la data/
rm data/list_sync.db-wal data/list_sync.db-shm  # If present

# Restart with fresh database
docker start listsync
```

#### Issue: "Database corruption"
```bash
# Backup existing data
cp data/list_sync.db data/list_sync.db.backup

# Check database integrity
sqlite3 data/list_sync.db "PRAGMA integrity_check;"

# Rebuild database if corrupted
rm data/list_sync.db
# Restart application to recreate
```

#### Issue: "Permission denied accessing database"
```bash
# Fix file permissions
sudo chown -R $(id -u):$(id -g) data/
chmod 755 data/
chmod 644 data/*

# For Docker
docker run --user $(id -u):$(id -g) ...
```

### Storage Issues

#### Issue: "Insufficient disk space"
```bash
# Check available space
df -h ./data/

# Clean up old logs
find data/ -name "*.log" -mtime +30 -delete

# Clean up old Docker images
docker system prune -a

# Move data directory to larger partition
mv data/ /path/to/larger/partition/
ln -s /path/to/larger/partition/data/ ./data
```

## 🚀 Performance Issues

### Slow Sync Performance

#### Issue: "Syncing takes too long"
```bash
# Reduce list sizes
TRAKT_SPECIAL_ITEMS_LIMIT=10  # Default: 20

# Increase sync interval for large lists
SYNC_INTERVAL=48  # Every 2 days instead of daily

# Monitor resource usage
docker stats listsync
top -p $(pgrep -f list-sync)
```

#### Issue: "High memory usage"
```bash
# Set memory limits
docker run --memory=1g --memory-swap=2g ...

# Or in docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 1G

# Monitor memory usage
docker exec listsync ps aux
```

### Selenium Performance

#### Issue: "Browser timeouts"
```bash
# Increase timeouts
export SELENIUM_TIMEOUT=60

# Update to latest Chrome/Selenium
docker pull ghcr.io/woahai321/list-sync:main

# Reduce parallel browser instances
# This is controlled internally by the providers
```

## 🐳 Docker-Specific Problems

### Container Issues

#### Issue: "Container exits immediately"
```bash
# Check container logs
docker logs listsync

# Run interactively to debug
docker run -it --rm \
  -v "$(pwd)/data:/usr/src/app/data" \
  ghcr.io/woahai321/list-sync:main \
  /bin/bash

# Check entry point
docker inspect ghcr.io/woahai321/list-sync:main
```

#### Issue: "Volume mount problems"
```bash
# Check mount permissions
ls -la data/

# Create data directory explicitly
mkdir -p data
chmod 755 data

# Use absolute paths
docker run -v "/full/path/to/data:/usr/src/app/data" ...
```

#### Issue: "Environment variables not passed"
```bash
# Use --env-file
docker run --env-file .env ...

# Or individual variables
docker run -e OVERSEERR_URL="..." -e OVERSEERR_API_KEY="..." ...

# Debug environment
docker run --rm ghcr.io/woahai321/list-sync:main printenv
```

### Docker Compose Issues

#### Issue: "Service won't start"
```bash
# Check compose file syntax
docker-compose config

# View service logs
docker-compose logs -f listsync

# Restart specific service
docker-compose restart listsync

# Rebuild with no cache
docker-compose build --no-cache listsync
```

## 🔍 Debugging Techniques

### Enable Debug Logging

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG

# View logs in real-time
docker-compose logs -f listsync

# Save logs to file
docker logs listsync > debug.log 2>&1
```

### Manual Testing

```bash
# Test individual components
docker run -it --rm \
  -v "$(pwd)/data:/usr/src/app/data" \
  -e OVERSEERR_URL="..." \
  -e OVERSEERR_API_KEY="..." \
  ghcr.io/woahai321/list-sync:main \
  python -c "from list_sync.api.overseerr import OverseerrClient; client = OverseerrClient('url', 'key'); print(client.test_connection())"

# Test provider directly
docker run -it --rm \
  ghcr.io/woahai321/list-sync:main \
  python -c "from list_sync.providers.imdb import fetch_imdb_list; print(len(fetch_imdb_list('top')))"
```

### Network Debugging

```bash
# Test from within container
docker run -it --rm ghcr.io/woahai321/list-sync:main bash
# Then run: curl -I https://your-overseerr.com

# Check container networking
docker network ls
docker inspect bridge

# Test with host networking
docker run --network host ...
```

## 📊 Log Analysis

### Key Log Patterns

#### Successful Operations
```
✅ API connection successful!
✅ Found X items in Y list
✅ Sync completed successfully
🎉 Requested: Movie/TV Title (Year)
```

#### Error Indicators
```
❌ API connection failed
❌ Error fetching [provider] list
❌ No matching results found
⚠️ Rate limited, waiting
🔄 Retrying operation
```

#### Performance Indicators
```
📊 Total unique media items ready for sync: X
🔄 Processing X items with Y threads
⏱️ Sync completed in X.X seconds
```

### Log Analysis Commands

```bash
# Filter for errors
docker logs listsync 2>&1 | grep -E "❌|ERROR|Failed"

# Count requests by status
docker logs listsync 2>&1 | grep -c "🎉 Requested"

# Find rate limiting issues
docker logs listsync 2>&1 | grep -E "429|Rate limited"

# Monitor sync timing
docker logs listsync 2>&1 | grep -E "Sync completed|sync duration"
```

### Log Rotation

```bash
# Configure log rotation in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

# Manual log cleanup
docker logs listsync --since 24h > recent.log
```

## 🆘 Getting Help

### Before Reporting Issues

1. **Check existing issues** on GitHub
2. **Search documentation** for similar problems
3. **Test with minimal configuration** to isolate the issue
4. **Collect debug logs** with `LOG_LEVEL=DEBUG`

### Information to Include

When reporting issues, provide:

```
**Environment:**
- Installation method (Docker/Manual)
- Operating system and version
- ListSync version/Docker tag
- Python version (if manual install)

**Configuration:**
- Deployment method (compose/direct docker/manual)
- Environment variables (sanitized)
- List types and approximate sizes

**Issue Details:**
- Expected behavior
- Actual behavior
- Steps to reproduce
- Error messages (full text)
- Relevant log excerpts

**Debugging Attempted:**
- Solutions tried from this guide
- Any workarounds discovered
```

### Debug Information Collection

```bash
# Collect system information
echo "=== System Info ===" > debug-info.txt
uname -a >> debug-info.txt
docker --version >> debug-info.txt

echo "=== ListSync Info ===" >> debug-info.txt
docker inspect ghcr.io/woahai321/list-sync:main | grep -A5 "Config" >> debug-info.txt

echo "=== Recent Logs ===" >> debug-info.txt
docker logs listsync --tail 100 >> debug-info.txt 2>&1

echo "=== Environment ===" >> debug-info.txt
docker exec listsync printenv | grep -E "(OVERSEERR|SYNC|LIST)" | sed 's/API_KEY=.*/API_KEY=***REDACTED***/' >> debug-info.txt
```

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: General questions and community support
- **Documentation**: Comprehensive guides and references
- **Discord/Forums**: Real-time community help (if available)

### Professional Support

For enterprise deployments or complex issues:
- Consider professional support options
- Engage with the development team
- Contribute back to the project with improvements

## 🔄 Recovery Procedures

### Complete Reset

If all else fails, perform a complete reset:

```bash
# Stop all ListSync instances
docker stop listsync
docker-compose down

# Backup important data
cp -r data/ data-backup/

# Remove all ListSync data
rm -rf data/

# Remove Docker images
docker rmi ghcr.io/woahai321/list-sync:main

# Start fresh
docker pull ghcr.io/woahai321/list-sync:main
mkdir data
# Reconfigure from scratch
```

### Selective Recovery

For partial issues:

```bash
# Reset only configuration
rm data/config.enc

# Reset only database
rm data/list_sync.db

# Reset only logs
rm data/*.log

# Keep lists but reset sync history
sqlite3 data/list_sync.db "DELETE FROM synced_items;"
```
