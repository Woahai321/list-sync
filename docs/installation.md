# Installation Guide

This guide provides detailed installation instructions for ListSync, covering both Docker and manual installation methods.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Installation (Recommended)](#docker-installation-recommended)
3. [Manual Installation](#manual-installation)
4. [Post-Installation Setup](#post-installation-setup)
5. [Verification](#verification)
6. [Updating](#updating)
7. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### For Docker Installation
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Requirements**: 
  - 2GB RAM minimum (4GB recommended)
  - 1GB free disk space
  - Internet connection for fetching lists

### For Manual Installation
- **Python**: Version 3.8 or higher
- **Node.js**: Version 18 or higher (for web interface)
- **System Requirements**:
  - 4GB RAM minimum
  - 2GB free disk space
  - Chrome/Chromium browser (for Selenium)
  - Internet connection

### Common Requirements
- **Overseerr Instance**: Running and accessible
- **Network Access**: To IMDb, Trakt, Letterboxd, MDBList, and other list providers

## 🐳 Docker Installation (Recommended)

Docker installation provides the easiest setup with all dependencies pre-configured.

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/soluify/list-sync.git
   cd list-sync
   ```

2. **Create environment file**:
   ```bash
   cp env.example .env
   ```

3. **Configure your settings**:
   ```bash
   nano .env  # or use your preferred editor
   ```
   
   Minimum required configuration:
   ```bash
   OVERSEERR_URL=https://your-overseerr-url.com
   OVERSEERR_API_KEY=your_api_key_here
   IMDB_LISTS=top  # Start with just one list
   ```

4. **Deploy**:
   ```bash
   docker-compose up -d
   ```

5. **Access the application**:
   - Web Dashboard: http://localhost:3222
   - API Backend: http://localhost:4222

### Docker Deployment Options

#### Production Deployment
Uses the pre-built image from GitHub Container Registry:

```bash
# Use the main docker-compose.yml file
docker-compose up -d
```

#### Local Development
Builds the image locally for development:

```bash
# Use the local development compose file
docker-compose -f docker-compose.local.yml up -d
```

#### Component-Specific Deployment

Deploy only specific components:

```bash
# Core sync functionality only
docker-compose -f docker-compose.core.yml up -d

# Domain services (Web UI + API)
docker-compose -f docker-compose.proddomain.yml up -d
```

### Docker Configuration

#### Environment Variables

All configuration is done through environment variables in your `.env` file. See our [Configuration Guide](configuration.md) for complete details.

#### Volume Mapping

The default Docker setup includes these volume mappings:

```yaml
volumes:
  - ./data:/usr/src/app/data          # Data persistence
  - ./.env:/usr/src/app/.env          # Configuration
  - ./logs:/var/log/supervisor        # Logs (optional)
```

#### Port Configuration

Default ports:
- **3222**: Web Dashboard (Next.js frontend)
- **4222**: API Backend (FastAPI)

To change ports, modify the `docker-compose.yml`:

```yaml
services:
  listsync-full:
    ports:
      - "8080:3222"  # Web dashboard on port 8080
      - "8081:4222"  # API on port 8081
```

## 💻 Manual Installation

For advanced users who prefer manual installation or need custom configurations.

### System Preparation

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git

# Install Node.js (for web interface)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Chrome (for Selenium)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install google-chrome-stable
```

#### CentOS/RHEL/Fedora
```bash
# Install Python and dependencies
sudo dnf install python3 python3-pip git nodejs npm

# Install Chrome
sudo dnf install google-chrome-stable
```

#### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 node git
brew install --cask google-chrome
```

### Backend Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/soluify/list-sync.git
   cd list-sync
   ```

2. **Create Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp envsample.txt .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   python -m list_sync.database
   ```

### Frontend Installation

1. **Navigate to frontend directory**:
   ```bash
   cd listsync-web
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

4. **Build frontend**:
   ```bash
   npm run build
   ```

### Manual Service Setup

#### Using Systemd (Linux)

Create service files for automatic startup:

**Backend Service** (`/etc/systemd/system/listsync-backend.service`):
```ini
[Unit]
Description=ListSync Backend Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/list-sync
Environment=PATH=/path/to/list-sync/venv/bin
ExecStart=/path/to/list-sync/venv/bin/python -m list_sync
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend Service** (`/etc/systemd/system/listsync-frontend.service`):
```ini
[Unit]
Description=ListSync Frontend Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/list-sync/listsync-web
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl enable listsync-backend listsync-frontend
sudo systemctl start listsync-backend listsync-frontend
```

#### Using PM2 (Node.js Process Manager)

```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start "python -m list_sync" --name listsync-backend --cwd /path/to/list-sync

# Start frontend
pm2 start npm --name listsync-frontend --cwd /path/to/list-sync/listsync-web -- start

# Save PM2 configuration
pm2 save
pm2 startup
```

## 🔧 Post-Installation Setup

### Initial Configuration

1. **Test Overseerr connection**:
   ```bash
   # Using curl
   curl -H "X-Api-Key: your-api-key" http://your-overseerr-url/api/v1/status
   ```

2. **Add your first list**:
   - Via environment variable: Add `IMDB_LISTS=top` to your `.env`
   - Via web interface: Navigate to http://localhost:3222/dashboard/lists

3. **Configure sync interval**:
   ```bash
   # Set in .env file
   SYNC_INTERVAL=24  # Sync once per day
   ```

### Optional Setup

#### Discord Notifications

1. Create a Discord webhook in your server
2. Add to your `.env` file:
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
   ```

#### Reverse Proxy Setup

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3222;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:4222;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## ✅ Verification

### Health Checks

1. **Check system health**:
   ```bash
   curl http://localhost:4222/api/system/health
   ```

2. **Verify database**:
   ```bash
   curl http://localhost:4222/api/lists
   ```

3. **Test web interface**:
   Open http://localhost:3222 in your browser

### Manual Sync Test

1. **Trigger a manual sync**:
   ```bash
   curl -X POST http://localhost:4222/api/sync/trigger
   ```

2. **Check sync results**:
   ```bash
   curl http://localhost:4222/api/processed?limit=10
   ```

### Log Verification

Check logs for any errors:

```bash
# Docker
docker-compose logs -f listsync-full

# Manual installation
tail -f data/list_sync.log
```

## 🔄 Updating

### Docker Update

```bash
# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d
```

### Manual Update

```bash
# Backup your configuration
cp .env .env.backup

# Pull latest code
git pull origin main

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd listsync-web
npm install
npm run build
cd ..

# Restart services
sudo systemctl restart listsync-backend listsync-frontend
```

## 🔧 Troubleshooting

### Common Installation Issues

#### Docker Issues

**Port already in use**:
```bash
# Check what's using the port
sudo netstat -tlnp | grep :3222

# Change port in docker-compose.yml
ports:
  - "8080:3222"
```

**Permission denied**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**Container won't start**:
```bash
# Check logs
docker-compose logs listsync-full

# Check container status
docker-compose ps
```

#### Manual Installation Issues

**Python version too old**:
```bash
# Check Python version
python3 --version

# Install newer Python (Ubuntu)
sudo apt install python3.9
```

**Chrome/Selenium issues**:
```bash
# Install Chrome dependencies
sudo apt install libxss1 libappindicator1 libindicator7

# Test Chrome headless
google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://google.com
```

**Node.js build failures**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Performance Issues

**High memory usage**:
- Reduce `TRAKT_SPECIAL_ITEMS_LIMIT`
- Increase `SYNC_INTERVAL`
- Use fewer concurrent lists

**Slow list fetching**:
- Check network connectivity
- Verify list URLs are accessible
- Enable debug logging to identify bottlenecks

### Network Issues

**Cannot connect to Overseerr**:
```bash
# Test connectivity
curl -v http://your-overseerr-url/api/v1/status

# Check Docker networking
docker network ls
docker network inspect list-sync_default
```

**CORS errors in web interface**:
- Verify `CORS_ALLOWED_ORIGINS` includes your domain
- Check `NEXT_PUBLIC_API_URL` is correct

### Getting Help

If you encounter issues not covered here:

1. **Check logs** for detailed error messages
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Installation method (Docker/manual)
   - Operating system
   - Error messages
   - Configuration (sanitized)

For more troubleshooting help, see our [Troubleshooting Guide](troubleshooting.md). 