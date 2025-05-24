# 🔌 API Reference and Integration Guide

This document provides comprehensive technical reference for ListSync's APIs, data structures, and integration interfaces.

## 📚 Table of Contents

1. [Provider API Interface](#provider-api-interface)
2. [Overseerr API Integration](#overseerr-api-integration)
3. [Database Schema](#database-schema)
4. [Configuration API](#configuration-api)
5. [Data Structures](#data-structures)
6. [Error Handling](#error-handling)
7. [Extension Points](#extension-points)

## 🔗 Provider API Interface

### Provider Registration

All list providers must be registered using the decorator pattern:

```python
from list_sync.providers import register_provider
from typing import List, Dict, Any

@register_provider("service_name")
def fetch_service_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch media items from a list service.
    
    Args:
        list_id (str): Service-specific list identifier or URL
        
    Returns:
        List[Dict[str, Any]]: Media items with standardized structure
        
    Raises:
        ValueError: For invalid list IDs or inaccessible lists
        ConnectionError: For network-related failures
        Exception: For service-specific errors
    """
    pass
```

### Required Return Data Structure

Each provider must return a list of dictionaries with the following structure:

```python
{
    "title": str,           # Required: Media title
    "media_type": str,      # Required: "movie" or "tv"
    "year": int,            # Optional: Release year
    "imdb_id": str,         # Optional but recommended: IMDb ID (tt1234567)
    "description": str,     # Optional: Media description
    "genres": List[str],    # Optional: Genre list
    "rating": float,        # Optional: Rating (0.0-10.0)
    "runtime": int,         # Optional: Runtime in minutes
    "poster_url": str,      # Optional: Poster image URL
}
```

### Provider Implementation Examples

#### Basic HTTP Provider

```python
import requests
from . import register_provider

@register_provider("jsonapi")
def fetch_jsonapi_list(list_id: str) -> List[Dict[str, Any]]:
    """Example JSON API provider."""
    response = requests.get(f"https://api.example.com/lists/{list_id}")
    response.raise_for_status()
    
    data = response.json()
    return [
        {
            "title": item["name"],
            "media_type": "movie" if item["type"] == "film" else "tv",
            "year": item.get("release_year"),
            "imdb_id": item.get("imdb"),
        }
        for item in data["items"]
    ]
```

#### Selenium-Based Provider

```python
from seleniumbase import SB
from . import register_provider

@register_provider("webservice")
def fetch_webservice_list(list_id: str) -> List[Dict[str, Any]]:
    """Example Selenium-based provider."""
    media_items = []
    
    with SB(uc=True, headless=True) as sb:
        sb.open(f"https://example.com/list/{list_id}")
        sb.wait_for_element(".media-item", timeout=10)
        
        items = sb.find_elements(".media-item")
        for item in items:
            title = item.find_element("css selector", ".title").text
            media_type = "movie" if "movie" in item.get_attribute("class") else "tv"
            
            media_items.append({
                "title": title,
                "media_type": media_type,
            })
    
    return media_items
```

### Provider Error Handling

Providers should handle errors gracefully:

```python
@register_provider("robust_service")
def fetch_robust_list(list_id: str) -> List[Dict[str, Any]]:
    """Example with comprehensive error handling."""
    try:
        # Validate list_id format
        if not list_id or not isinstance(list_id, str):
            raise ValueError("Invalid list ID provided")
        
        # Attempt to fetch data
        data = fetch_data_from_service(list_id)
        
        if not data:
            logging.warning(f"No data found for list {list_id}")
            return []
            
        return process_data(data)
        
    except requests.exceptions.Timeout:
        raise ConnectionError(f"Timeout accessing list {list_id}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"List {list_id} not found")
        elif e.response.status_code == 403:
            raise ValueError(f"Access denied to list {list_id}")
        else:
            raise ConnectionError(f"HTTP error {e.response.status_code}")
    except Exception as e:
        logging.error(f"Unexpected error in provider: {str(e)}")
        raise
```

## 🎬 Overseerr API Integration

### OverseerrClient Class

The main interface for Overseerr/Jellyseerr communication:

```python
class OverseerrClient:
    def __init__(self, overseerr_url: str, api_key: str, requester_user_id: str = "1"):
        """Initialize Overseerr client."""
        
    def test_connection(self) -> bool:
        """Test API connectivity."""
        
    def search_media(self, media_title: str, media_type: str, release_year: int = None) -> Optional[Dict[str, Any]]:
        """Search for media in Overseerr."""
        
    def get_media_status(self, media_id: int, media_type: str) -> Tuple[bool, bool, int]:
        """Get media availability status."""
        
    def request_media(self, media_id: int, media_type: str, is_4k: bool = False) -> str:
        """Request media from Overseerr."""
```

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/status` | GET | Health check and version info |
| `/api/v1/user` | GET | User management and requester setup |
| `/api/v1/search` | GET | Media search functionality |
| `/api/v1/movie/{id}` | GET | Movie details and status |
| `/api/v1/tv/{id}` | GET | TV series details and status |
| `/api/v1/request` | POST | Create new media requests |

### Request Headers

```python
headers = {
    "X-Api-Key": "your-api-key",
    "X-Api-User": "requester-user-id",  # For POST requests
    "Content-Type": "application/json"
}
```

### Search Algorithm

The search implementation uses sophisticated matching:

```python
def calculate_match_score(search_title: str, result_title: str, search_year: int, result_year: int) -> float:
    """
    Calculate matching score for search results.
    
    Returns:
        float: Score from 0.0 to 2.0+ (higher is better)
    """
    # Base similarity using Levenshtein distance
    base_similarity = calculate_title_similarity(search_title, result_title)
    
    # Year weighting
    if search_year and result_year:
        if search_year == result_year:
            return base_similarity * 2.0  # Exact year match
        elif abs(search_year - result_year) <= 1:
            return base_similarity * 1.5  # Close year match
    
    return base_similarity
```

### Request Payloads

#### Movie Request

```json
{
    "mediaType": "movie",
    "mediaId": 12345,
    "is4k": false,
    "serverId": 1,
    "profileId": 1
}
```

#### TV Series Request

```json
{
    "mediaType": "tv",
    "mediaId": 67890,
    "is4k": false,
    "serverId": 1,
    "profileId": 1,
    "seasons": [1, 2, 3]
}
```

## 🗄️ Database Schema

### Tables Overview

```sql
-- Lists configuration
CREATE TABLE lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_type TEXT NOT NULL,        -- Provider type (imdb, trakt, etc.)
    list_id TEXT NOT NULL,          -- Provider-specific list ID/URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(list_type, list_id)
);

-- Processed media tracking
CREATE TABLE synced_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    media_type TEXT NOT NULL,       -- "movie" or "tv"
    imdb_id TEXT,                   -- External reference
    overseerr_id INTEGER,           -- Internal Overseerr ID
    status TEXT NOT NULL,           -- "requested", "available", "error"
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,             -- Error details if status = "error"
    year INTEGER,                   -- Release year
    provider_source TEXT            -- Which provider added this item
);

-- Automation settings
CREATE TABLE sync_interval (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interval_hours REAL NOT NULL,  -- Supports decimal values
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync history and statistics
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_completed TIMESTAMP,
    items_processed INTEGER DEFAULT 0,
    items_requested INTEGER DEFAULT 0,
    items_skipped INTEGER DEFAULT 0,
    items_errored INTEGER DEFAULT 0,
    sync_mode TEXT DEFAULT 'manual'  -- 'manual', 'automated', 'dry_run'
);
```

### Database Operations

#### Core Functions

```python
def init_database() -> None:
    """Initialize database with required tables."""

def save_list_id(list_id: str, list_type: str) -> None:
    """Store list configuration."""

def load_list_ids() -> List[Dict[str, str]]:
    """Retrieve all configured lists."""

def save_sync_result(title: str, media_type: str, imdb_id: Optional[str], 
                    overseerr_id: Optional[int], status: str) -> None:
    """Record sync operation result."""

def should_sync_item(overseerr_id: int) -> bool:
    """Check if item needs syncing based on last sync time."""

def get_sync_stats() -> Dict[str, int]:
    """Retrieve sync statistics."""

def cleanup_old_sync_results(days: int = 30) -> int:
    """Remove old sync records."""
```

#### Query Examples

```python
# Get items synced in last 24 hours
cursor.execute("""
    SELECT title, status, COUNT(*) 
    FROM synced_items 
    WHERE last_synced > datetime('now', '-24 hours')
    GROUP BY status
""")

# Find items needing re-sync
cursor.execute("""
    SELECT * FROM synced_items 
    WHERE status = 'error' 
    AND last_synced < datetime('now', '-7 days')
""")

# Get provider statistics
cursor.execute("""
    SELECT provider_source, COUNT(*), 
           SUM(CASE WHEN status = 'requested' THEN 1 ELSE 0 END) as successful
    FROM synced_items 
    GROUP BY provider_source
""")
```

## ⚙️ Configuration API

### Environment Variable Loading

```python
def load_env_config() -> Tuple[Optional[str], Optional[str], Optional[str], float, bool, bool]:
    """
    Load configuration from environment variables.
    
    Returns:
        Tuple containing:
        - overseerr_url: str
        - api_key: str  
        - user_id: str
        - sync_interval: float
        - automated_mode: bool
        - is_4k: bool
    """
```

### Configuration Hierarchy

1. **Environment Variables** (highest priority)
2. **Encrypted Config File** (`data/config.enc`)
3. **Interactive Input** (lowest priority)

### Encrypted Configuration

```python
def encrypt_config(data: dict, password: str) -> bytes:
    """Encrypt configuration with user password."""

def decrypt_config(encrypted_data: bytes, password: str) -> dict:
    """Decrypt configuration with user password."""

def save_config(overseerr_url: str, api_key: str, requester_user_id: str) -> None:
    """Save encrypted configuration to file."""

def load_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Load and decrypt configuration from file."""
```

### List Configuration

```python
def load_env_lists() -> bool:
    """
    Load list configurations from environment variables.
    
    Environment variables parsed:
    - IMDB_LISTS: "ls123,ur456,top,boxoffice"
    - TRAKT_LISTS: "12345,67890,https://trakt.tv/..."
    - TRAKT_SPECIAL_LISTS: "trending:movies,popular:shows"
    - LETTERBOXD_LISTS: "https://letterboxd.com/..."
    - MDBLIST_LISTS: "user/list,https://mdblist.com/..."
    - STEVENLU_LISTS: "stevenlu"
    
    Returns:
        bool: True if any lists were loaded
    """
```

## 📋 Data Structures

### Media Item Structure

```python
class MediaItem(TypedDict):
    title: str                  # Required
    media_type: str            # Required: "movie" or "tv"
    year: NotRequired[int]     # Optional: Release year
    imdb_id: NotRequired[str]  # Optional: IMDb ID (tt1234567)
    description: NotRequired[str]
    genres: NotRequired[List[str]]
    rating: NotRequired[float]
    runtime: NotRequired[int]
    poster_url: NotRequired[str]
```

### Search Result Structure

```python
class SearchResult(TypedDict):
    id: int                    # Overseerr internal ID
    mediaType: str            # "movie" or "tv"
    title: NotRequired[str]   # For movies
    name: NotRequired[str]    # For TV shows
    releaseDate: NotRequired[str]
    firstAirDate: NotRequired[str]
    overview: NotRequired[str]
    posterPath: NotRequired[str]
```

### Sync Result Structure

```python
class SyncResults:
    def __init__(self):
        self.total_items = 0
        self.requested_items = []
        self.already_available = []
        self.already_requested = []
        self.errors = []
        self.skipped_items = []
        self.synced_lists = []
        
    def add_result(self, result_type: str, item: Dict[str, Any]):
        """Add sync result for tracking."""
        
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
```

### Configuration Structure

```python
class Config:
    overseerr_url: str
    api_key: str
    user_id: str = "1"
    sync_interval: float = 24.0
    automated_mode: bool = False
    is_4k: bool = False
    trakt_special_limit: int = 20
    discord_webhook: Optional[str] = None
    
    lists: Dict[str, List[str]] = {
        "imdb": [],
        "trakt": [],
        "trakt_special": [],
        "letterboxd": [],
        "mdblist": [],
        "stevenlu": []
    }
```

## ⚠️ Error Handling

### Exception Hierarchy

```python
class ListSyncError(Exception):
    """Base exception for ListSync errors."""
    pass

class ProviderError(ListSyncError):
    """Error in list provider operation."""
    pass

class APIError(ListSyncError):
    """Error in API communication."""
    pass

class ConfigurationError(ListSyncError):
    """Error in configuration or setup."""
    pass

class DatabaseError(ListSyncError):
    """Error in database operation."""
    pass
```

### Error Response Structure

```python
class ErrorResult:
    def __init__(self, error_type: str, message: str, details: Optional[Dict] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
```

### Retry Logic

```python
def with_retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for automatic retry with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator
```

## 🔧 Extension Points

### Custom Provider Development

1. **Create provider function:**
   ```python
   @register_provider("myservice")
   def fetch_myservice_list(list_id: str) -> List[Dict[str, Any]]:
       # Implementation
   ```

2. **Handle different input formats:**
   ```python
   def fetch_myservice_list(list_id: str) -> List[Dict[str, Any]]:
       if list_id.startswith("http"):
           return fetch_from_url(list_id)
       else:
           return fetch_from_id(list_id)
   ```

3. **Add to environment configuration:**
   ```python
   # In config.py
   myservice_lists = os.getenv('MYSERVICE_LISTS', '').split(',')
   for list_id in myservice_lists:
       if list_id.strip():
           save_list_id(list_id.strip(), "myservice")
   ```

### Custom Media Server Support

1. **Implement client interface:**
   ```python
   class CustomServerClient:
       def search_media(self, title: str, media_type: str, year: int = None):
           # Implementation
           
       def get_media_status(self, media_id: int, media_type: str):
           # Implementation
           
       def request_media(self, media_id: int, media_type: str, is_4k: bool = False):
           # Implementation
   ```

2. **Adapt main sync logic:**
   ```python
   # Replace OverseerrClient with CustomServerClient
   client = CustomServerClient(url, api_key, user_id)
   ```

### Notification Extensions

```python
class NotificationHandler:
    def send_sync_summary(self, results: SyncResults):
        """Send sync completion notification."""
        
    def send_error_alert(self, error: ErrorResult):
        """Send error notification."""
        
    def send_item_requested(self, item: Dict[str, Any]):
        """Send individual item notification."""

# Register notification handlers
handlers = [
    DiscordNotificationHandler(),
    SlackNotificationHandler(),
    EmailNotificationHandler()
]
```

### Database Extensions

```python
# Custom migrations
def migrate_database(current_version: int, target_version: int):
    """Handle database schema migrations."""
    
# Custom queries
def get_provider_performance() -> Dict[str, Any]:
    """Analyze provider success rates."""
    
def get_trending_requests() -> List[Dict[str, Any]]:
    """Find most requested items."""
```

## 📊 Monitoring and Metrics

### Performance Metrics

```python
class MetricsCollector:
    def track_sync_duration(self, duration: float):
        """Track sync operation timing."""
        
    def track_provider_success_rate(self, provider: str, success: bool):
        """Track provider reliability."""
        
    def track_api_response_time(self, endpoint: str, duration: float):
        """Track API performance."""
        
    def export_metrics(self) -> Dict[str, Any]:
        """Export collected metrics."""
```

### Health Checks

```python
def health_check() -> Dict[str, Any]:
    """Comprehensive health check."""
    return {
        "database": check_database_connectivity(),
        "overseerr_api": check_overseerr_connectivity(),
        "selenium": check_selenium_availability(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }
``` 