# ListSync Development Setup

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ with Poetry
- Node.js 18+
- Existing ListSync database (`data/list_sync.db`)
- Environment configuration (`.env` file)

### Development Commands

#### Option 1: Batch File (Recommended)
```bash
# Start all services in separate windows
start-dev.bat
```

#### Option 2: Manual Commands
```bash
# Terminal 1: ListSync Core Service
python -m list_sync

# Terminal 2: FastAPI Backend
python start_api.py

# Terminal 3: Next.js Frontend
cd listsync-web
npm run dev
```

#### Option 3: PowerShell Scripts
```powershell
# Start all services (separate windows)
.\start-dev.ps1

# Start all services (background jobs)
.\start-dev-simple.ps1

# Stop all services
.\stop-dev.ps1
```

## 🎯 Access Points

- **📊 Dashboard**: http://localhost:3222
- **🔗 API Documentation**: http://localhost:4222/docs
- **❤️ Health Check**: http://localhost:4222/api/system/health

## 🕒 Timestamp Fixes Implemented

### ✅ Fixed Issues

1. **Last Sync Timestamp**
   - Now shows actual sync completion time from logs
   - Looks for patterns: "sync complete", "webhook sent", "discord notification sent"
   - Endpoint: `/api/system/health` and `/api/stats/sync`

2. **Next Sync Calculation**
   - Calculated from last sync + sync interval
   - Includes 10-minute grace period for "overdue" status
   - Shows "due", "scheduled", or "overdue" status

3. **Statistics Last Updated**
   - Now reflects actual last sync time instead of current time
   - Endpoint: `/api/stats/sync`

4. **Overseerr Connection Checks**
   - Real-time checking every 30 seconds
   - Shows actual `lastChecked` timestamp
   - Endpoint: `/api/overseerr/status`

5. **Live System Uptime**
   - Frontend calculates live uptime from server start time
   - Updates every second in the UI
   - Uses `useLiveTime` hook

6. **Live Welcome Message Time**
   - Date and time update every second
   - Dynamic greeting based on time of day
   - Uses `useLiveTime` hook

### 🔧 Technical Implementation

#### Backend Changes (`api_server.py`)
- Enhanced `parse_log_for_sync_info()` function
- Better sync completion detection
- Improved error handling and grace periods
- New `/api/system/time` endpoint for live updates

#### Frontend Changes
- New `useLiveTime` hook for real-time updates
- Live uptime calculation in `SystemStatus` component
- Live time display in dashboard header
- 30-second refresh intervals for all status checks

## 🧪 Testing Endpoints

```bash
# Health check with timestamps
curl http://localhost:4222/api/system/health

# Sync statistics with actual last sync time
curl http://localhost:4222/api/stats/sync

# Overseerr status with real-time checking
curl http://localhost:4222/api/overseerr/status

# System info with uptime
curl http://localhost:4222/api/system/info

# Current server time
curl http://localhost:4222/api/system/time
```

## 📋 Development Workflow

1. **Start Services**: Run `start-dev.bat` or use manual commands
2. **Check Health**: Visit http://localhost:4222/api/system/health
3. **View Dashboard**: Open http://localhost:3222
4. **Monitor Logs**: Check individual terminal windows
5. **Stop Services**: Close terminal windows or run `.\stop-dev.ps1`

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Check what's using ports 3222/4222
netstat -ano | findstr :3222
netstat -ano | findstr :4222

# Kill processes if needed
taskkill /PID <process_id> /F
```

### Frontend Not Starting
```bash
# Install dependencies
cd listsync-web
npm install

# Clear cache and restart
npm run build
npm run dev
```

### API Not Responding
```bash
# Check if Python dependencies are installed
pip install -r api_requirements.txt

# Verify database exists
ls data/list_sync.db

# Check environment file
cat .env
```

## 🎨 UI Features

- **Live Time Updates**: Welcome message time updates every second
- **Real-time System Status**: All status indicators refresh every 30 seconds
- **Live Uptime**: System uptime updates every second
- **Accurate Timestamps**: All timestamps reflect actual sync operations
- **Responsive Design**: Works on desktop and mobile
- **Glassmorphic UI**: Beautiful purple-themed interface 