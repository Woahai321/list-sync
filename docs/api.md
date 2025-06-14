# API Documentation

ListSync provides a comprehensive REST API for monitoring, configuration, and control. The API is built with FastAPI and includes automatic OpenAPI documentation.

## 📋 Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [System Endpoints](#system-endpoints)
4. [List Management](#list-management)
5. [Sync Operations](#sync-operations)
6. [Analytics & Statistics](#analytics--statistics)
7. [Logging & Monitoring](#logging--monitoring)
8. [Configuration](#configuration)
9. [Response Formats](#response-formats)
10. [Error Handling](#error-handling)

## 🌐 API Overview

**Base URL**: `http://localhost:4222/api` (default Docker setup)

**Documentation**: 
- Interactive docs: `http://localhost:4222/docs`
- OpenAPI spec: `http://localhost:4222/openapi.json`

**Content Type**: `application/json`

**Rate Limiting**: No explicit rate limiting (designed for internal use)

## 🔐 Authentication

Currently, the API does not require authentication as it's designed for internal use within the Docker container environment. For production deployments, consider implementing proper authentication and authorization.

## 🖥️ System Endpoints

### Health & Status

#### Get System Health
```http
GET /api/system/health
```

Simple health check endpoint returning basic system status.

**Response**:
```json
{
  "database": true,
  "process": true,
  "sync_status": "running",
  "last_sync": "2024-01-15T10:30:00Z",
  "next_sync": "2024-01-15T22:30:00Z"
}
```

#### Get Detailed System Status
```http
GET /api/system/status
```

Comprehensive system health check with detailed information.

**Response**:
```json
{
  "database": {
    "connected": true,
    "file_exists": true,
    "file_size": 1024000,
    "last_modified": "2024-01-15T10:30:00Z",
    "error": null
  },
  "process": {
    "running": true,
    "processes": [
      {
        "pid": 1234,
        "name": "python -m list_sync",
        "status": "running",
        "cpu_percent": 2.5,
        "memory_mb": 128.5
      }
    ],
    "error": null
  },
  "sync": {
    "status": "idle",
    "last_sync": "2024-01-15T10:30:00Z",
    "next_sync": "2024-01-15T22:30:00Z",
    "interval_hours": 12,
    "error": null
  },
  "overall_health": "healthy"
}
```

#### Get System Time
```http
GET /api/system/time
```

Returns current system time and timezone information.

#### Test Database Connection
```http
GET /api/system/database/test
```

Tests database connectivity.

### Process Management

#### Get Running Processes
```http
GET /api/system/processes
```

Returns information about running ListSync processes.

#### Get System Logs
```http
GET /api/system/logs
```

Returns recent system logs for debugging.

## 📚 List Management

### Get All Lists
```http
GET /api/lists
```

Returns all configured lists with their metadata.

**Response**:
```json
{
  "lists": [
    {
      "id": "top",
      "type": "imdb",
      "url": "https://www.imdb.com/chart/top",
      "item_count": 250,
      "last_synced": "2024-01-15T10:30:00Z",
      "status": "active"
    }
  ],
  "total_count": 1,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Add New List
```http
POST /api/lists
```

Adds a new list to the configuration.

**Request Body**:
```json
{
  "list_type": "imdb",
  "list_id": "top",
  "list_url": "https://www.imdb.com/chart/top"
}
```

**Response**:
```json
{
  "success": true,
  "message": "List added successfully",
  "list": {
    "id": "top",
    "type": "imdb",
    "url": "https://www.imdb.com/chart/top",
    "item_count": 0,
    "last_synced": null,
    "status": "pending"
  }
}
```

### Delete List
```http
DELETE /api/lists/{list_type}/{list_id}
```

Removes a list from the configuration.

**Parameters**:
- `list_type`: Type of list (imdb, trakt, letterboxd, etc.)
- `list_id`: List identifier

**Response**:
```json
{
  "success": true,
  "message": "List deleted successfully"
}
```

## 🔄 Sync Operations

### Trigger Manual Sync
```http
POST /api/sync/trigger
```

Triggers an immediate sync of all configured lists.

**Request Body** (optional):
```json
{
  "dry_run": false,
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Sync triggered successfully",
  "sync_id": "sync_20240115_103000"
}
```

### Trigger Single List Sync
```http
POST /api/sync/single
```

Syncs a specific list immediately.

**Request Body**:
```json
{
  "list_type": "imdb",
  "list_id": "top",
  "dry_run": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Single list sync completed",
  "items_processed": 250,
  "items_requested": 25,
  "errors": 0,
  "list_info": {
    "type": "imdb",
    "id": "top",
    "url": "https://www.imdb.com/chart/top",
    "item_count": 250
  }
}
```

### Get Sync Status
```http
GET /api/sync/status
```

Returns current sync operation status.

**Response**:
```json
{
  "active": false,
  "status": "idle",
  "current_operation": null,
  "progress": {
    "current": 0,
    "total": 0,
    "percentage": 0
  },
  "last_sync": {
    "timestamp": "2024-01-15T10:30:00Z",
    "duration": 120,
    "items_processed": 250,
    "success_count": 245,
    "error_count": 5
  }
}
```

### Get Live Sync Status
```http
GET /api/sync/status/live
```

Server-sent events endpoint for real-time sync status updates.

**Response**: Stream of JSON events
```
data: {"status": "running", "progress": 25, "current_list": "imdb:top"}
data: {"status": "completed", "results": {...}}
```

## 📊 Analytics & Statistics

### Get Analytics Overview
```http
GET /api/analytics/overview
```

**Query Parameters**:
- `time_range`: `1h`, `24h`, `7d`, `30d` (default: `24h`)

**Response**:
```json
{
  "total_items": 1500,
  "success_rate": 95.2,
  "avg_processing_time": 2.3,
  "active_sync": false,
  "total_sync_operations": 12,
  "total_errors": 8,
  "last_sync_time": "2024-01-15T10:30:00Z"
}
```

### Get Comprehensive Analytics
```http
GET /api/analytics
```

**Query Parameters**:
- `time_range`: `1h`, `24h`, `7d`, `30d` (default: `24h`)
- `category`: `all`, `sync`, `fetching`, `matching`, `scraping` (default: `all`)

Returns comprehensive analytics including all sub-categories.

### Media Addition Analytics
```http
GET /api/analytics/media-additions
```

Returns data about media items added over time.

### List Fetch Analytics
```http
GET /api/analytics/list-fetches
```

Returns statistics about list fetching operations.

### Matching Analytics
```http
GET /api/analytics/matching
```

Returns title matching accuracy statistics.

**Response**:
```json
{
  "perfect_matches": 450,
  "partial_matches": 45,
  "failed_matches": 5,
  "average_score": 0.92,
  "low_confidence_matches": [
    {
      "title": "Ambiguous Title",
      "year": 2023,
      "score": 0.65,
      "source": "imdb",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Source Distribution
```http
GET /api/analytics/source-distribution
```

Returns distribution of media by source (IMDb, Trakt, etc.).

### Year Distribution
```http
GET /api/analytics/year-distribution
```

Returns distribution of media by release year.

## 📈 Data Endpoints

### Get Recent Activity
```http
GET /api/activity/recent
```

**Query Parameters**:
- `limit`: Number of activities to return (default: 50)
- `offset`: Pagination offset (default: 0)

Returns recent sync activities and operations.

### Get Processed Items
```http
GET /api/processed
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)
- `status_filter`: Filter by status
- `media_type_filter`: Filter by media type

Returns items that have been processed.

### Get Failed Items
```http
GET /api/failures
```

Returns items that failed to sync with error details.

### Get Successful Items
```http
GET /api/successful
```

Returns items that were successfully requested.

### Get Requested Items
```http
GET /api/requested
```

Returns items that were requested in Overseerr.

## 📝 Logging & Monitoring

### Get Log Entries
```http
GET /api/logs/entries
```

**Query Parameters**:
- `limit`: Number of entries (default: 100)
- `offset`: Pagination offset (default: 0)
- `level`: Log level filter (INFO, WARNING, ERROR)
- `category`: Category filter
- `search`: Text search in log messages

Returns structured log entries.

### Get Live Log Stream
```http
GET /api/logs/stream
```

**Query Parameters**:
- `last_position`: Last known file position
- `level_filter`: Log level filter
- `category_filters`: Category filters (comma-separated)
- `search`: Text search

Server-sent events endpoint for real-time log streaming.

### Get Log Categories
```http
GET /api/logs/categories
```

Returns available log categories and their counts.

### Get Log Statistics
```http
GET /api/logs/stats
```

Returns log file statistics and recent activity summary.

## ⚙️ Configuration

### Get Sync Interval
```http
GET /api/sync-interval
```

Returns current sync interval configuration.

**Response**:
```json
{
  "interval_hours": 24,
  "next_sync": "2024-01-15T22:30:00Z",
  "last_sync": "2024-01-15T10:30:00Z"
}
```

### Update Sync Interval
```http
PUT /api/sync-interval
```

**Request Body**:
```json
{
  "interval_hours": 12
}
```

Updates the sync interval.

### Sync Interval from Environment
```http
POST /api/sync-interval/sync-from-env
```

Synchronizes sync interval from environment variables.

### Get Overseerr Status
```http
GET /api/overseerr/status
```

Returns Overseerr connection status and configuration.

### Get Overseerr Configuration
```http
GET /api/overseerr/config
```

Returns Overseerr configuration details.

## 🌍 Timezone & Localization

### Get Supported Timezones
```http
GET /api/timezone/supported
```

Returns list of supported timezones.

### Get Current Timezone
```http
GET /api/timezone/current
```

Returns current system timezone information.

### Validate Timezone
```http
POST /api/timezone/validate
```

**Request Body**:
```json
{
  "timezone": "America/New_York"
}
```

Validates a timezone identifier.

## 📁 Response Formats

### Standard Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Pagination Response
```json
{
  "items": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 250,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "detail": "Detailed error information",
  "error_code": "ERROR_CODE"
}
```

## ⚠️ Error Handling

### HTTP Status Codes

- `200 OK` - Successful operation
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `OVERSEERR_CONNECTION_ERROR` | Cannot connect to Overseerr | Check Overseerr URL and API key |
| `DATABASE_ERROR` | Database operation failed | Check database file permissions |
| `INVALID_LIST_FORMAT` | List ID format is invalid | Verify list ID format |
| `SYNC_IN_PROGRESS` | Sync already running | Wait for current sync to complete |
| `LIST_NOT_FOUND` | Specified list doesn't exist | Check list ID and type |

### Error Response Example
```json
{
  "detail": "Cannot connect to Overseerr API",
  "error_code": "OVERSEERR_CONNECTION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456"
}
```

## 🔧 Usage Examples

### Python Example
```python
import requests

base_url = "http://localhost:4222/api"

# Get system health
response = requests.get(f"{base_url}/system/health")
health = response.json()

# Trigger manual sync
sync_response = requests.post(f"{base_url}/sync/trigger", 
                             json={"dry_run": False})

# Add new list
new_list = requests.post(f"{base_url}/lists", 
                        json={
                            "list_type": "imdb",
                            "list_id": "top",
                            "list_url": "https://www.imdb.com/chart/top"
                        })
```

### JavaScript Example
```javascript
const baseUrl = 'http://localhost:4222/api';

// Get analytics overview
fetch(`${baseUrl}/analytics/overview?time_range=24h`)
  .then(response => response.json())
  .then(data => console.log(data));

// Stream live logs
const eventSource = new EventSource(`${baseUrl}/logs/stream`);
eventSource.onmessage = function(event) {
  const logEntry = JSON.parse(event.data);
  console.log(logEntry);
};
```

### curl Examples
```bash
# Get system status
curl http://localhost:4222/api/system/status

# Trigger sync
curl -X POST http://localhost:4222/api/sync/trigger \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# Get recent activity
curl "http://localhost:4222/api/activity/recent?limit=10"

# Update sync interval
curl -X PUT http://localhost:4222/api/sync-interval \
  -H "Content-Type: application/json" \
  -d '{"interval_hours": 6}'
```