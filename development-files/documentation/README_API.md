# ListSync Web UI API

A FastAPI backend that provides a REST API for the ListSync Web UI dashboard, integrating seamlessly with the existing ListSync Python application.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- ListSync application running (or at least database created)
- Required Python packages (auto-installed)

### Start the API Server
```bash
# Simple startup (auto-installs dependencies)
python start_api.py

# Or manually
pip install -r api_requirements.txt
python api_server.py
```

The API will be available at:
- **API Base**: http://localhost:4222/api
- **Documentation**: http://localhost:4222/docs
- **Health Check**: http://localhost:4222/api/system/health

## 📊 Features Implemented

### ✅ All Issues Addressed

1. **✅ Sync Interval Database Population**
   - Detects sync interval from environment (`SYNC_INTERVAL`)
   - Populates database via `POST /api/sync-interval/sync-from-env`
   - Tracks source (database/environment/default)

2. **✅ Dynamic Process Detection**
   - No hardcoded PIDs
   - Searches for `python -m list_sync` processes
   - Handles multiple instances gracefully

3. **✅ Smart Sync Status Logic**
   - Multi-factor health assessment
   - Process + Database + Log parsing + Timing analysis
   - Distinguishes between database connectivity and service health

4. **✅ Data Deduplication**
   - Deduplicates by `title_mediatype` key
   - Prefers items with `overseerr_id` and recent sync dates
   - Provides both raw and deduplicated statistics

5. **✅ Proper Status Mapping**
   - **Success**: `already_available`, `already_requested`, `available`, `requested`
   - **Failure**: `not_found`, `error`
   - Accurate success rate calculation

## 🔗 API Endpoints

### System Status
- `GET /api/system/status` - Comprehensive system health
- `GET /api/system/processes` - ListSync process information
- `GET /api/system/logs` - Log file analysis
- `GET /api/system/health` - Simple health check

### Sync Interval Management
- `GET /api/sync-interval` - Current interval with source tracking
- `PUT /api/sync-interval` - Update interval in database
- `POST /api/sync-interval/sync-from-env` - Populate from environment

### Statistics (Deduplicated)
- `GET /api/stats/sync` - Deduplicated sync statistics
- `GET /api/stats/data-quality` - Raw vs deduplicated analysis
- `GET /api/stats/status-breakdown` - Success/failure categorization

### Activity & Lists
- `GET /api/activity/recent` - Recent sync activity
- `GET /api/lists` - Configured lists
- `POST /api/lists` - Add new list
- `DELETE /api/lists/{type}/{id}` - Delete list

### Items Management
- `GET /api/items` - Paginated items (deduplicated)
- `GET /api/items/search` - Search items

## 📈 Current System Status

Based on your actual ListSync instance:

```json
{
  "database": {
    "connected": true,
    "file_size": 32768,
    "items": 78
  },
  "process": {
    "running": true,
    "pid": 29172,
    "command": "python -m list_sync"
  },
  "sync": {
    "status": "scheduled",
    "last_sync": "2025-05-25 20:28:23",
    "next_sync": "2025-05-26 20:28:23",
    "interval_hours": 24.0
  },
  "statistics": {
    "total_items": 78,
    "successful_items": 78,
    "failed_items": 0,
    "success_rate": 100.0
  }
}
```

## 🔧 Configuration

### Environment Variables
The API automatically detects these from your existing ListSync setup:
- `SYNC_INTERVAL` - Sync interval in hours (default: 12)
- `OVERSEERR_URL` - Overseerr instance URL
- `OVERSEERR_API_KEY` - Overseerr API key

### Database Integration
Uses the existing ListSync database at `data/list_sync.db`:
- **Tables**: `lists`, `synced_items`, `sync_interval`
- **Functions**: Integrates with existing `list_sync.database` module
- **Deduplication**: Smart logic for handling duplicate entries

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:4222/api/system/health
# Returns: {"database":true,"process":true,"sync_status":"scheduled",...}
```

### Sync Interval Management
```bash
# Get current interval
curl http://localhost:4222/api/sync-interval
# Returns: {"interval_hours":24.0,"source":"environment",...}

# Populate database from environment
curl -X POST http://localhost:4222/api/sync-interval/sync-from-env
# Returns: {"success":true,"message":"Sync interval populated..."}
```

### Statistics
```bash
# Get deduplicated statistics
curl http://localhost:4222/api/stats/sync
# Returns: {"total_items":78,"successful_items":78,"success_rate":100.0,...}

# Data quality analysis
curl http://localhost:4222/api/stats/data-quality
# Returns: {"total_raw_items":78,"duplicates_found":0,...}
```

### Lists Management
```bash
# Get configured lists
curl http://localhost:4222/api/lists
# Returns: [{"list_type":"trakt_special","list_id":"popular:movies",...}]

# Add new list
curl -X POST http://localhost:4222/api/lists \
  -H "Content-Type: application/json" \
  -d '{"list_type":"imdb","list_id":"top"}'
```

## 🏗️ Architecture

### Integration with ListSync
- **Database**: Direct SQLite integration with existing schema
- **Configuration**: Uses existing config loading functions
- **Process Detection**: Dynamic discovery of ListSync processes
- **Log Parsing**: Analyzes existing log files for sync status

### Deduplication Logic
```python
# Create unique key: title + media_type (case insensitive)
key = f"{title}_{media_type}".lower()

# Prefer items with:
# 1. overseerr_id (successfully processed)
# 2. More recent last_synced timestamp
if key not in unique_items or \
   (overseerr_id and not unique_items[key].overseerr_id) or \
   last_synced > unique_items[key].last_synced:
    unique_items[key] = item
```

### Status Mapping
```python
SUCCESS_STATUSES = ['already_available', 'already_requested', 'available', 'requested']
FAILURE_STATUSES = ['not_found', 'error']
```

## 🔄 Next Steps

### Phase 1: Frontend Integration ✅
- [x] API endpoints implemented
- [x] TypeScript interfaces created
- [x] Integration tested
- [ ] Connect Next.js dashboard to API

### Phase 2: Advanced Features
- [ ] Real-time sync monitoring
- [ ] Manual sync triggering
- [ ] Advanced filtering and search
- [ ] Sync job status tracking

### Phase 3: Production Features
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] Caching layer
- [ ] Monitoring and alerting

## 🐛 Troubleshooting

### API Server Won't Start
```bash
# Check dependencies
python -c "import fastapi, uvicorn, psutil"

# Check database
ls -la data/list_sync.db

# Check ListSync process
ps aux | grep list_sync
```

### Database Issues
```bash
# Verify database structure
python -c "import sqlite3; conn = sqlite3.connect('data/list_sync.db'); print([x[0] for x in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])"
```

### Sync Interval Issues
```bash
# Check environment variable
echo $SYNC_INTERVAL

# Populate database manually
curl -X POST http://localhost:4222/api/sync-interval/sync-from-env
```

## 📝 API Documentation

Full interactive API documentation is available at http://localhost:4222/docs when the server is running.

The API follows REST conventions and returns JSON responses with proper HTTP status codes and error handling. 