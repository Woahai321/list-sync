# ListSync Complete Application - Docker Setup

## 🐳 Single Container, Complete Solution

This Docker setup runs the **entire ListSync application** in one container:
- **ListSync Core Service** (media synchronization)
- **FastAPI Backend** (REST API on port 4222)
- **Next.js Frontend** (web dashboard on port 3222)

All services are managed by **Supervisor** for reliability and automatic restarts.

## 🚀 Quick Start

### 1. **Environment Setup**
Make sure your `.env` file is configured:

```bash
# Required: Overseerr Configuration
OVERSEERR_URL=http://your-overseerr-instance:5055
OVERSEERR_API_KEY=your-api-key-here
OVERSEERR_USER_ID=1

# Required: Sync Configuration
SYNC_INTERVAL=24
AUTOMATED_MODE=true

# Required: At least one list source
TRAKT_LISTS=popular-movies,trending-shows
# OR
IMDB_LISTS=ls123456789
# OR
MDBLIST_LISTS=your-mdblist-id
# etc.

# Optional: Discord notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 2. **Build and Run**
```bash
# Build the complete application
docker-compose -f docker-compose.local.yml build

# Start the application
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f
```

### 3. **Access Your Application**
- **🎨 Web Dashboard**: http://localhost:3222
- **🔗 API Documentation**: http://localhost:4222/docs
- **❤️ Health Check**: http://localhost:4222/api/system/health

## 📊 What's Running Inside

The container runs **4 processes** managed by Supervisor:

1. **Xvfb** (Virtual Display)
   - Provides display for Chrome/Selenium
   - Priority: 100 (starts first)

2. **ListSync Core** (`python -m list_sync`)
   - Main synchronization service
   - Creates and updates SQLite database
   - Priority: 200

3. **FastAPI API** (`python start_api.py`)
   - REST API backend on port 4222
   - Connects to ListSync database
   - Priority: 300

4. **Next.js Frontend** (`npm start`)
   - Web dashboard on port 3222
   - Connects to API backend
   - Priority: 400

## 🔍 Monitoring & Debugging

### Check Container Status
```bash
# Container health
docker-compose -f docker-compose.local.yml ps

# All service logs
docker-compose -f docker-compose.local.yml logs -f

# Specific service logs
docker-compose -f docker-compose.local.yml logs -f listsync-app
```

### Check Individual Services
```bash
# Enter the container
docker exec -it listsync-complete bash

# Check supervisor status
supervisorctl status

# View individual service logs
tail -f /var/log/supervisor/listsync-core.log
tail -f /var/log/supervisor/listsync-api.log
tail -f /var/log/supervisor/listsync-frontend.log
```

### Health Checks
```bash
# API health check
curl http://localhost:4222/api/system/health

# Frontend check
curl http://localhost:3222

# Database check
curl http://localhost:4222/api/system/database/test
```

## 📁 Data Persistence

Your data is persisted in these mounted volumes:

```bash
./data/          # ListSync database and logs
./logs/          # Supervisor service logs (optional)
./.env           # Environment configuration
```

**Important**: The `./data/` directory contains your SQLite database and sync logs. This is mounted as a volume so your data persists between container restarts.

## 🔧 Configuration

### Environment Variables
All ListSync configuration is done via environment variables in your `.env` file:

```bash
# Core Settings
OVERSEERR_URL=http://overseerr:5055
OVERSEERR_API_KEY=your-key
SYNC_INTERVAL=24
AUTOMATED_MODE=true

# List Sources (comma-separated)
TRAKT_LISTS=popular-movies,trending-shows
IMDB_LISTS=ls123456789,ls987654321
LETTERBOXD_LISTS=username/list-name
MDBLIST_LISTS=123456
STEVENLU_LISTS=all

# Optional Features
OVERSEERR_4K=false
DISCORD_WEBHOOK_URL=https://discord.com/...
```

### Port Configuration
- **Frontend**: `3222:3222` (Next.js dashboard)
- **Backend**: `4222:4222` (FastAPI server)

To change ports, modify the `docker-compose.local.yml` file:
```yaml
ports:
  - "8080:3222"  # Frontend on port 8080
  - "8081:4222"  # API on port 8081
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check build logs
docker-compose -f docker-compose.local.yml build --no-cache

# Check startup logs
docker-compose -f docker-compose.local.yml up
```

### Services Not Responding
```bash
# Check supervisor status
docker exec -it listsync-complete supervisorctl status

# Restart specific service
docker exec -it listsync-complete supervisorctl restart listsync-api
docker exec -it listsync-complete supervisorctl restart listsync-frontend
```

### Database Issues
```bash
# Check if database exists
docker exec -it listsync-complete ls -la /usr/src/app/data/

# Check database content
docker exec -it listsync-complete sqlite3 /usr/src/app/data/list_sync.db ".tables"
```

### Chrome/Selenium Issues
```bash
# Check Xvfb display
docker exec -it listsync-complete ps aux | grep Xvfb

# Check Chrome installation
docker exec -it listsync-complete google-chrome --version
docker exec -it listsync-complete chromedriver --version
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml build --no-cache
docker-compose -f docker-compose.local.yml up -d
```

### Backup Data
```bash
# Backup database and logs
tar -czf listsync-backup-$(date +%Y%m%d).tar.gz ./data/
```

### Clean Up
```bash
# Stop and remove containers
docker-compose -f docker-compose.local.yml down

# Remove images (optional)
docker-compose -f docker-compose.local.yml down --rmi all

# Clean up volumes (⚠️ deletes data)
docker-compose -f docker-compose.local.yml down -v
```

## ✅ Success Indicators

You'll know everything is working when:

- ✅ Container health check passes
- ✅ Dashboard loads at http://localhost:3222
- ✅ API responds at http://localhost:4222/api/system/health
- ✅ All 4 supervisor processes show "RUNNING"
- ✅ Database shows sync statistics
- ✅ Logs show sync activity

## 🎯 Production Deployment

For production deployment:

1. **Use production compose file**:
   ```bash
   cp docker-compose.local.yml docker-compose.prod.yml
   # Edit for production settings
   ```

2. **Set production environment**:
   ```bash
   NODE_ENV=production
   NEXT_PUBLIC_API_URL=https://your-domain.com/api
   ```

3. **Add reverse proxy** (nginx/traefik) for HTTPS and domain routing

4. **Configure monitoring** and log aggregation

## 📋 **Log Management**

The container uses **intelligent log separation**:

### **Docker Logs (Main Output)**
```bash
docker-compose -f docker-compose.local.yml logs -f
```
Shows **only ListSync core service logs** - the actual sync operations, media processing, and important status updates.

### **Individual Service Logs**
If you need to debug specific services:

```bash
# API Backend logs
docker exec listsync-complete tail -f /var/log/supervisor/api.log

# Frontend logs  
docker exec listsync-complete tail -f /var/log/supervisor/frontend.log

# Virtual display logs
docker exec listsync-complete tail -f /var/log/supervisor/xvfb.log

# All supervisor logs
docker exec listsync-complete tail -f /var/log/supervisor/supervisord.log
```

### **Why This Setup?**
- **Clean Docker logs**: Only see what matters - your media sync operations
- **Separate debugging**: Access frontend/API logs when needed for troubleshooting  
- **Log rotation**: Prevents log files from growing too large (10MB max per service)
- **Performance**: Reduces log noise and improves container performance

---

**🎉 Your complete ListSync application is now running in Docker!**

Access your beautiful dashboard at **http://localhost:3222** and start managing your media synchronization with style! 🚀 