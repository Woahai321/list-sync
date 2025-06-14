# ListSync Web UI - Startup Guide

## 🚀 Complete System Startup

You need to run **3 components** in this order:

### **Step 1: Start ListSync Application** ✅
```bash
# Terminal 1 - Start the core ListSync service
python -m list_sync
```

**What this does:**
- Starts the core synchronization service
- Creates/updates the SQLite database (`data/list_sync.db`)
- Runs continuous sync cycles based on your `SYNC_INTERVAL`
- **Keep this running** - it's the heart of the system

### **Step 2: Start API Server** 🔗
```bash
# Terminal 2 - Start the FastAPI backend
python start_api.py
```

**What this does:**
- Starts the REST API on `http://localhost:4222`
- Connects to the ListSync database
- Provides endpoints for the dashboard
- Auto-installs dependencies if needed

**Verify API is working:**
```bash
# Test in a new terminal
curl http://localhost:4222/api/system/health
# Should return: {"database":true,"process":true,"sync_status":"scheduled",...}
```

### **Step 3: Start Dashboard** 🎨
```bash
# Terminal 3 - Start the Next.js frontend
cd listsync-web
npm run dev
```

**What this does:**
- Starts the dashboard on `http://localhost:3222`
- Connects to the API server
- Provides the beautiful web interface

## 📋 Quick Startup Checklist

- [ ] **Terminal 1**: `python -m list_sync` (keep running)
- [ ] **Terminal 2**: `python start_api.py` (keep running)  
- [ ] **Terminal 3**: `cd listsync-web && npm run dev` (keep running)
- [ ] **Browser**: Open `http://localhost:3222`

## 🔧 Environment Setup

Make sure the dashboard can connect to the API:

```bash
# In listsync-web directory
echo "NEXT_PUBLIC_API_URL=http://localhost:4222/api" > .env.local
```

## 🎯 Expected Results

When everything is running:

1. **ListSync Service** (`python -m list_sync`)
   - ✅ Syncing media items every 24 hours
   - ✅ Database being updated
   - ✅ Logs showing sync activity

2. **API Server** (`python start_api.py`)
   - ✅ Available at `http://localhost:4222/api`
   - ✅ Interactive docs at `http://localhost:4222/docs`
   - ✅ Health check returns `{"database":true,"process":true}`

3. **Dashboard** (`npm run dev`)
   - ✅ Available at `http://localhost:3222`
   - ✅ Shows real data from your ListSync instance
   - ✅ Beautiful glassmorphic purple interface

## 🐛 Troubleshooting

### ListSync Won't Start
```bash
# Check if you have the right environment
python -c "import list_sync"
# If error, make sure you're in the right directory
```

### API Server Issues
```bash
# Check dependencies
python -c "import fastapi, uvicorn, psutil"
# If error, run: pip install -r api_requirements.txt
```

### Dashboard Issues
```bash
# Check Node.js and dependencies
cd listsync-web
npm install
# Make sure .env.local has the API URL
```

### Port Conflicts
If ports are in use:
- **ListSync**: Uses no web ports (just database)
- **API**: Change port in `start_api.py` (default 4222)
- **Dashboard**: Change port with `npm run dev -- -p 3002`

## 🔄 Development Workflow

For active development:

1. **Keep ListSync running** - provides real data
2. **API auto-reloads** - changes to `api_server.py` restart automatically
3. **Dashboard hot-reloads** - changes to React components update instantly

## 🎉 Success Indicators

You'll know everything is working when:

- ✅ ListSync logs show sync activity
- ✅ API health check returns all green
- ✅ Dashboard loads with real statistics
- ✅ All three terminals show active processes
- ✅ No error messages in any terminal

**🎯 Final URL**: http://localhost:3222 (your beautiful dashboard!)

---

## 📝 Quick Commands Reference

```bash
# Start everything (3 terminals)
python -m list_sync                    # Terminal 1
python start_api.py                    # Terminal 2  
cd listsync-web && npm run dev         # Terminal 3

# Test API
curl http://localhost:4222/api/system/health

# View dashboard
open http://localhost:3222
``` 