# 🚀 Signal-Based "Sync Now" Feature

## Overview

The ListSync Web UI now supports triggering immediate syncs via process signals, allowing you to manually start a sync operation without waiting for the scheduled interval.

## How It Works

### 1. **Signal Handler Implementation**
- The main ListSync process (`list_sync/main.py`) now listens for `SIGUSR1` signals
- When received, it immediately triggers a sync operation
- The process continues its normal scheduled operation after the manual sync

### 2. **API Endpoints**
- `POST /api/sync/trigger` - Sends SIGUSR1 signal to running ListSync processes
- `GET /api/sync/status` - Check if ListSync processes are running and can receive signals

### 3. **Web UI Integration**
- **Quick Actions** card now has a functional "Sync Now" button
- Real-time feedback with loading states and success/error notifications
- Automatic process detection and validation

## Usage

### Via Web UI
1. Open the ListSync Web UI dashboard
2. Click the **"Sync Now"** button in the Quick Actions section
3. The system will:
   - Check if ListSync is running
   - Send the signal to trigger immediate sync
   - Show success/error notifications

### Via API
```bash
# Check if sync can be triggered
curl -X GET http://localhost:4222/api/sync/status

# Trigger immediate sync
curl -X POST http://localhost:4222/api/sync/trigger
```

### Via Command Line (Direct Signal)
```bash
# Find ListSync process ID
ps aux | grep list_sync

# Send signal directly (replace PID with actual process ID)
kill -USR1 <PID>
```

## Requirements

### 1. **ListSync Must Be Running in Automated Mode**
```bash
# Start ListSync in automated mode
python -m list_sync --automated --interval 12

# Or with Docker
docker run -d --name listsync \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -e OVERSEERR_URL="http://overseerr:5055" \
  -e OVERSEERR_API_KEY="your-api-key" \
  -e SYNC_INTERVAL_HOURS="12" \
  your-listsync-image
```

### 2. **API Server Running**
```bash
# Start the API server
python api_server.py
```

### 3. **Web UI Running**
```bash
# Start the Next.js frontend
cd listsync-web
npm run dev
```

## Testing

Use the provided test script to verify functionality:

```bash
python test_sync_trigger.py
```

This will:
- Check if ListSync processes are running
- Test the signal trigger functionality
- Provide detailed feedback on success/failure

## Process Flow

```
Web UI Button Click
       ↓
API Client Request
       ↓
API Server (/api/sync/trigger)
       ↓
Find ListSync Processes
       ↓
Send SIGUSR1 Signal
       ↓
ListSync Signal Handler
       ↓
Immediate Sync Execution
       ↓
Continue Normal Schedule
```

## Error Handling

### Common Issues:

1. **"No ListSync process found"**
   - Ensure ListSync is running in automated mode
   - Check process with: `ps aux | grep list_sync`

2. **"Permission denied"**
   - API server needs permission to signal the process
   - Run with appropriate privileges

3. **"Process not found"**
   - ListSync process may have exited
   - Restart ListSync in automated mode

## Logging

### ListSync Logs
- Manual sync triggers are logged with: `"Received SIGUSR1 signal - triggering immediate sync"`
- Sync operations show: `"Immediate sync requested via signal"`

### API Server Logs
- Signal sending is logged with process PID information
- Errors are logged with detailed failure reasons

## Benefits

- ✅ **Immediate Response** - No waiting for scheduled intervals
- ✅ **Non-Disruptive** - Doesn't affect normal scheduling
- ✅ **Safe** - Uses standard Unix signals
- ✅ **Efficient** - No process restart required
- ✅ **User-Friendly** - Simple button click in web UI

## Technical Details

### Signal Choice: SIGUSR1
- User-defined signal safe for custom applications
- Won't interfere with system signals
- Standard practice for triggering custom actions

### Thread Safety
- Uses `threading.Event()` for safe signal handling
- Prevents race conditions between scheduled and manual syncs
- Ensures only one sync runs at a time

### Process Detection
- Dynamically finds ListSync processes by command line
- Filters out API server to avoid self-signaling
- Supports multiple ListSync instances 