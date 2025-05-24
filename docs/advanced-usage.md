# 🚀 Advanced Usage Guide

This comprehensive guide covers advanced deployment patterns, automation scenarios, integration examples, and power user features for ListSync.

## 📋 Table of Contents

1. [Multi-Instance Deployments](#multi-instance-deployments)
2. [Advanced Automation Patterns](#advanced-automation-patterns)
3. [Integration Examples](#integration-examples)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Performance Optimization](#performance-optimization)
6. [Custom Provider Development](#custom-provider-development)
7. [Database Management](#database-management)
8. [Security Hardening](#security-hardening)
9. [CI/CD Integration](#cicd-integration)
10. [Enterprise Deployment](#enterprise-deployment)

## 🔄 Multi-Instance Deployments

### Scenario 1: Multiple Overseerr Instances

Deploy ListSync for multiple Overseerr servers:

```yaml
# docker-compose-multi.yml
version: "3.8"

services:
  listsync-main:
    image: ghcr.io/woahai321/list-sync:main
    container_name: listsync-main
    environment:
      - OVERSEERR_URL=https://overseerr-main.example.com
      - OVERSEERR_API_KEY=${MAIN_API_KEY}
      - AUTOMATED_MODE=true
      - SYNC_INTERVAL=24
      - IMDB_LISTS=ls123456789,top
    volumes:
      - ./data-main:/usr/src/app/data
    restart: unless-stopped

  listsync-4k:
    image: ghcr.io/woahai321/list-sync:main
    container_name: listsync-4k
    environment:
      - OVERSEERR_URL=https://overseerr-4k.example.com
      - OVERSEERR_API_KEY=${4K_API_KEY}
      - AUTOMATED_MODE=true
      - SYNC_INTERVAL=12
      - OVERSEERR_4K=true
      - IMDB_LISTS=top,boxoffice
      - TRAKT_SPECIAL_LISTS=trending:movies
    volumes:
      - ./data-4k:/usr/src/app/data
    restart: unless-stopped

  listsync-tv:
    image: ghcr.io/woahai321/list-sync:main
    container_name: listsync-tv
    environment:
      - OVERSEERR_URL=https://overseerr-tv.example.com
      - OVERSEERR_API_KEY=${TV_API_KEY}
      - AUTOMATED_MODE=true
      - SYNC_INTERVAL=8
      - TRAKT_SPECIAL_LISTS=trending:shows,popular:shows
      - LETTERBOXD_LISTS=${TV_LETTERBOXD_LISTS}
    volumes:
      - ./data-tv:/usr/src/app/data
    restart: unless-stopped
```

### Scenario 2: Geographic Distribution

Deploy across multiple regions with different content preferences:

```yaml
# docker-compose-regions.yml
version: "3.8"

services:
  listsync-us:
    image: ghcr.io/woahai321/list-sync:main
    environment:
      - OVERSEERR_URL=https://us-overseerr.example.com
      - OVERSEERR_API_KEY=${US_API_KEY}
      - IMDB_LISTS=boxoffice,moviemeter  # US-focused content
      - TRAKT_SPECIAL_LISTS=trending:movies,boxoffice:movies
      - SYNC_INTERVAL=6
    volumes:
      - ./data-us:/usr/src/app/data

  listsync-eu:
    image: ghcr.io/woahai321/list-sync:main
    environment:
      - OVERSEERR_URL=https://eu-overseerr.example.com
      - OVERSEERR_API_KEY=${EU_API_KEY}
      - LETTERBOXD_LISTS=${EU_LETTERBOXD_LISTS}  # EU arthouse content
      - MDBLIST_LISTS=${EU_MDBLIST}
      - SYNC_INTERVAL=12
    volumes:
      - ./data-eu:/usr/src/app/data
```

### Load Balancing

Distribute load across multiple providers:

```yaml
services:
  listsync-imdb:
    image: ghcr.io/woahai321/list-sync:main
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${API_KEY}
      - IMDB_LISTS=${ALL_IMDB_LISTS}
      - SYNC_INTERVAL=24
    volumes:
      - ./data-shared:/usr/src/app/data:ro  # Read-only shared config
      - ./data-imdb:/usr/src/app/data/logs

  listsync-trakt:
    image: ghcr.io/woahai321/list-sync:main
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${API_KEY}
      - TRAKT_LISTS=${ALL_TRAKT_LISTS}
      - TRAKT_SPECIAL_LISTS=${ALL_TRAKT_SPECIAL}
      - SYNC_INTERVAL=12
    volumes:
      - ./data-shared:/usr/src/app/data:ro
      - ./data-trakt:/usr/src/app/data/logs
```

## 🤖 Advanced Automation Patterns

### Time-Based Sync Strategies

#### Peak Hour Optimization
```bash
#!/bin/bash
# sync-scheduler.sh - Run different sync patterns based on time

HOUR=$(date +%H)

if [ $HOUR -ge 2 ] && [ $HOUR -le 6 ]; then
    # Off-peak hours: Full sync with all lists
    export IMDB_LISTS="ls123456789,ur987654321,top,boxoffice,moviemeter"
    export TRAKT_SPECIAL_ITEMS_LIMIT=50
    export SYNC_INTERVAL=0.5  # 30 minutes
else
    # Peak hours: Light sync with essential lists only
    export IMDB_LISTS="top,boxoffice"
    export TRAKT_SPECIAL_ITEMS_LIMIT=20
    export SYNC_INTERVAL=2    # 2 hours
fi

docker-compose up -d listsync
```

#### Weekday vs Weekend Patterns
```yaml
# Use different configs based on schedule
# Managed by cron or systemd timers

# docker-compose.weekday.yml
services:
  listsync:
    environment:
      - SYNC_INTERVAL=12
      - TRAKT_SPECIAL_LISTS=trending:movies,popular:shows

# docker-compose.weekend.yml  
services:
  listsync:
    environment:
      - SYNC_INTERVAL=4
      - TRAKT_SPECIAL_LISTS=trending:movies,trending:shows,popular:movies,popular:shows,anticipated:movies
```

### Event-Driven Sync

#### Webhook-Triggered Sync
```python
# webhook-trigger.py
from flask import Flask, request
import subprocess
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret-key"

@app.route('/sync-trigger', methods=['POST'])
def trigger_sync():
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return 'Unauthorized', 401
    
    # Parse payload
    payload = request.json
    
    if payload.get('action') == 'list_updated':
        list_type = payload.get('list_type')
        list_id = payload.get('list_id')
        
        # Trigger targeted sync
        env = {
            f'{list_type.upper()}_LISTS': list_id,
            'AUTOMATED_MODE': 'false'  # One-time sync
        }
        
        subprocess.run(['docker-compose', 'run', '--rm', 
                       '--env-file', '/dev/stdin'], 
                      input='\n'.join(f'{k}={v}' for k, v in env.items()),
                      text=True)
        
        return 'Sync triggered', 200
    
    return 'No action taken', 200

def verify_signature(payload, signature):
    expected = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### File System Monitoring
```bash
#!/bin/bash
# watch-lists.sh - Monitor list files for changes

inotifywait -m -e modify,create,delete /path/to/list/configs/ |
while read path action file; do
    echo "List config changed: $file"
    
    # Extract list type from filename
    if [[ $file == *"imdb"* ]]; then
        LIST_TYPE="IMDB"
    elif [[ $file == *"trakt"* ]]; then
        LIST_TYPE="TRAKT"
    fi
    
    # Trigger sync for specific provider
    docker run --rm \
        --env-file .env \
        -v "$(pwd)/data:/usr/src/app/data" \
        ghcr.io/woahai321/list-sync:main \
        python -c "
from list_sync.main import run_sync
from list_sync.config import load_env_config
url, key, user, _, _, _ = load_env_config()
from list_sync.api.overseerr import OverseerrClient
client = OverseerrClient(url, key, user)
run_sync(client, automated_mode=False)
"
done
```

## 🔌 Integration Examples

### Home Assistant Integration

```yaml
# configuration.yaml
shell_command:
  trigger_listsync: "docker exec listsync python -m list_sync --sync-now"
  
sensor:
  - platform: command_line
    name: "ListSync Status"
    command: 'docker logs listsync --tail 1 | grep -o "Sync completed\|Error\|Running"'
    scan_interval: 300

automation:
  - alias: "Trigger ListSync on new movie/show interest"
    trigger:
      - platform: state
        entity_id: input_select.movie_interest
    action:
      - service: shell_command.trigger_listsync
      - service: notify.discord
        data:
          message: "Triggered ListSync due to new movie interest"
```

### Plex Integration

```python
# plex-integration.py
from plexapi.server import PlexServer
import requests
import json

def sync_plex_watchlist_to_overseerr():
    """Sync Plex watchlist to Overseerr via ListSync"""
    
    # Connect to Plex
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    
    # Get watchlist
    watchlist = plex.watchlist()
    
    # Format for ListSync custom provider
    media_items = []
    for item in watchlist:
        media_items.append({
            "title": item.title,
            "year": item.year,
            "media_type": "movie" if item.type == "movie" else "tv",
            "imdb_id": item.guid if "imdb://" in item.guid else None
        })
    
    # Save to custom list file
    with open('/data/custom-plex-watchlist.json', 'w') as f:
        json.dump(media_items, f)
    
    # Trigger ListSync with custom provider
    requests.post('http://listsync:5000/api/sync', json={
        'custom_list': '/data/custom-plex-watchlist.json'
    })
```

### Jellyfin Integration

```python
# jellyfin-sync.py
import jellyfin_apiclient_python
from jellyfin_apiclient_python import JellyfinClient

def get_jellyfin_watchlist():
    """Extract watchlist from Jellyfin"""
    
    client = JellyfinClient()
    client.config.app('ListSync', '1.0.0', 'listsync', 'listsync-1.0.0')
    client.config.data['auth.ssl'] = False
    
    client.auth.connect(JELLYFIN_URL)
    client.auth.login(JELLYFIN_USERNAME, JELLYFIN_PASSWORD)
    
    # Get user's favorites/watchlist
    user_id = client.auth.user_id
    items = client.jellyfin.user_items(user_id, {
        'IsFavorite': True,
        'Recursive': True,
        'IncludeItemTypes': 'Movie,Series'
    })
    
    return [item for item in items['Items']]
```

### Sonarr/Radarr Integration

```python
# arr-integration.py
def sync_with_arr_wanted():
    """Sync Sonarr/Radarr wanted lists with ListSync"""
    
    # Get Sonarr wanted episodes
    sonarr_wanted = requests.get(
        f"{SONARR_URL}/api/v3/wanted/missing",
        headers={"X-Api-Key": SONARR_API_KEY},
        params={"pageSize": 100}
    ).json()
    
    # Get Radarr wanted movies
    radarr_wanted = requests.get(
        f"{RADARR_URL}/api/v3/wanted/missing",
        headers={"X-Api-Key": RADARR_API_KEY},
        params={"pageSize": 100}
    ).json()
    
    # Create custom lists for ListSync
    wanted_shows = [
        {
            "title": record["series"]["title"],
            "year": record["series"]["year"],
            "media_type": "tv",
            "imdb_id": record["series"]["imdbId"]
        }
        for record in sonarr_wanted["records"]
    ]
    
    wanted_movies = [
        {
            "title": movie["title"],
            "year": movie["year"],
            "media_type": "movie",
            "imdb_id": movie["imdbId"]
        }
        for movie in radarr_wanted["records"]
    ]
    
    # Export for ListSync custom provider
    return wanted_shows + wanted_movies
```

## 📊 Monitoring and Alerting

### Prometheus Metrics

```python
# metrics-exporter.py
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import sqlite3
import time

# Define metrics
sync_duration = Histogram('listsync_sync_duration_seconds', 'Time spent syncing')
items_processed = Counter('listsync_items_processed_total', 'Items processed', ['status'])
active_lists = Gauge('listsync_active_lists', 'Number of active lists', ['provider'])
last_sync_timestamp = Gauge('listsync_last_sync_timestamp', 'Last sync timestamp')

def collect_metrics():
    """Collect metrics from ListSync database"""
    conn = sqlite3.connect('/data/list_sync.db')
    
    # Get sync statistics
    cursor = conn.execute("""
        SELECT status, COUNT(*) 
        FROM synced_items 
        WHERE last_synced > datetime('now', '-24 hours')
        GROUP BY status
    """)
    
    for status, count in cursor.fetchall():
        items_processed.labels(status=status).inc(count)
    
    # Get active lists by provider
    cursor = conn.execute("""
        SELECT list_type, COUNT(*) 
        FROM lists 
        GROUP BY list_type
    """)
    
    for provider, count in cursor.fetchall():
        active_lists.labels(provider=provider).set(count)
    
    conn.close()

if __name__ == '__main__':
    start_http_server(8000)
    
    while True:
        collect_metrics()
        time.sleep(60)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "ListSync Monitoring",
    "panels": [
      {
        "title": "Sync Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(listsync_items_processed_total{status=\"requested\"}[5m]) / rate(listsync_items_processed_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "Items Processed Over Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(listsync_items_processed_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Active Lists by Provider",
        "type": "piechart",
        "targets": [
          {
            "expr": "listsync_active_lists",
            "legendFormat": "{{provider}}"
          }
        ]
      }
    ]
  }
}
```

### Health Check Endpoint

```python
# health-check.py
from flask import Flask, jsonify
import sqlite3
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Comprehensive health check"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database connectivity
    try:
        conn = sqlite3.connect('/data/list_sync.db')
        conn.execute('SELECT 1').fetchone()
        health_status["checks"]["database"] = "healthy"
        conn.close()
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Overseerr API
    try:
        overseerr_url = os.getenv('OVERSEERR_URL')
        api_key = os.getenv('OVERSEERR_API_KEY')
        
        response = requests.get(
            f"{overseerr_url}/api/v1/status",
            headers={"X-Api-Key": api_key},
            timeout=5
        )
        response.raise_for_status()
        health_status["checks"]["overseerr_api"] = "healthy"
    except Exception as e:
        health_status["checks"]["overseerr_api"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check last sync time
    try:
        conn = sqlite3.connect('/data/list_sync.db')
        cursor = conn.execute("""
            SELECT MAX(last_synced) 
            FROM synced_items
        """)
        last_sync = cursor.fetchone()[0]
        
        if last_sync:
            last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
            time_diff = datetime.utcnow() - last_sync_time
            
            if time_diff > timedelta(hours=48):  # No sync in 48 hours
                health_status["checks"]["last_sync"] = f"stale: {time_diff}"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["last_sync"] = "healthy"
        else:
            health_status["checks"]["last_sync"] = "no_syncs_found"
        
        conn.close()
    except Exception as e:
        health_status["checks"]["last_sync"] = f"error: {str(e)}"
    
    return jsonify(health_status), 200 if health_status["status"] == "healthy" else 503

@app.route('/metrics')
def metrics():
    """Simple metrics endpoint"""
    try:
        conn = sqlite3.connect('/data/list_sync.db')
        
        # Get basic stats
        stats = {}
        
        cursor = conn.execute("SELECT COUNT(*) FROM lists")
        stats["total_lists"] = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM synced_items 
            WHERE last_synced > datetime('now', '-24 hours')
        """)
        stats["items_synced_24h"] = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT status, COUNT(*) 
            FROM synced_items 
            WHERE last_synced > datetime('now', '-24 hours')
            GROUP BY status
        """)
        stats["status_breakdown"] = dict(cursor.fetchall())
        
        conn.close()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## 🚀 Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_synced_items_last_synced ON synced_items(last_synced);
CREATE INDEX IF NOT EXISTS idx_synced_items_status ON synced_items(status);
CREATE INDEX IF NOT EXISTS idx_synced_items_overseerr_id ON synced_items(overseerr_id);
CREATE INDEX IF NOT EXISTS idx_synced_items_imdb_id ON synced_items(imdb_id);

-- Optimize database
VACUUM;
ANALYZE;

-- Configure SQLite for better performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
```

### Caching Layer

```python
# redis-cache.py
import redis
import json
import hashlib
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(ttl=3600):
    """Cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Call function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Apply to provider functions
@cache_result(ttl=1800)  # 30 minutes
def fetch_imdb_list_cached(list_id):
    return fetch_imdb_list(list_id)
```

### Parallel Processing Configuration

```yaml
# docker-compose.performance.yml
version: "3.8"

services:
  listsync:
    image: ghcr.io/woahai321/list-sync:main
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${API_KEY}
      - AUTOMATED_MODE=true
      - SYNC_INTERVAL=12
      
      # Performance tuning
      - MAX_WORKERS=10           # Parallel processing threads
      - SELENIUM_POOL_SIZE=3     # Browser instances
      - HTTP_TIMEOUT=30          # Request timeout
      - RETRY_ATTEMPTS=3         # Retry failed requests
      
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.5'
        reservations:
          memory: 1G
          cpus: '0.5'
    
    volumes:
      - ./data:/usr/src/app/data
      - /tmp:/tmp  # Faster temporary storage
    
    # Use faster networking
    network_mode: host
```

## 🔐 Security Hardening

### Secure Configuration

```yaml
# docker-compose.secure.yml
version: "3.8"

services:
  listsync:
    image: ghcr.io/woahai321/list-sync:main
    
    # Run as non-root user
    user: "1000:1000"
    
    # Security options
    security_opt:
      - no-new-privileges:true
    
    # Read-only root filesystem
    read_only: true
    
    # Minimal capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_CONNECT_IPPROTO_TCP
    
    # Temporary filesystems
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
      - /var/tmp:rw,noexec,nosuid,size=50m
    
    volumes:
      - ./data:/usr/src/app/data:rw
      - ./config:/usr/src/app/config:ro
    
    environment:
      # Use secrets instead of environment variables
      - OVERSEERR_URL_FILE=/run/secrets/overseerr_url
      - OVERSEERR_API_KEY_FILE=/run/secrets/api_key
    
    secrets:
      - overseerr_url
      - api_key
    
    # Network isolation
    networks:
      - listsync_network

secrets:
  overseerr_url:
    file: ./secrets/overseerr_url.txt
  api_key:
    file: ./secrets/api_key.txt

networks:
  listsync_network:
    driver: bridge
    internal: true  # No external access except through defined services
```

### Secrets Management

```bash
#!/bin/bash
# setup-secrets.sh

# Create secrets directory
mkdir -p secrets
chmod 700 secrets

# Generate API key file
echo -n "your-overseerr-api-key" > secrets/api_key.txt
chmod 600 secrets/api_key.txt

# Generate URL file
echo -n "https://overseerr.example.com" > secrets/overseerr_url.txt
chmod 600 secrets/overseerr_url.txt

# Use with Docker Swarm or Kubernetes secrets
```

### Network Security

```yaml
# Network isolation with proxy
version: "3.8"

services:
  nginx-proxy:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    networks:
      - frontend
      - backend

  listsync:
    image: ghcr.io/woahai321/list-sync:main
    networks:
      - backend  # No direct external access
    environment:
      - OVERSEERR_URL=http://nginx-proxy/overseerr  # Through proxy

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## 🔧 Custom Provider Development

### Template for New Provider

```python
# custom_provider.py
import requests
import logging
from typing import List, Dict, Any
from seleniumbase import SB

from list_sync.providers import register_provider

@register_provider("myservice")
def fetch_myservice_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch media items from MyService.
    
    Args:
        list_id: Service-specific list identifier
        
    Returns:
        List of media items with standardized structure
    """
    media_items = []
    
    try:
        # Validate input
        if not list_id or not isinstance(list_id, str):
            raise ValueError("Invalid list ID provided")
        
        # Handle different input formats
        if list_id.startswith('http'):
            items = _fetch_from_url(list_id)
        else:
            items = _fetch_from_id(list_id)
        
        # Process and standardize data
        for item in items:
            media_item = {
                "title": item.get("name", "").strip(),
                "media_type": _normalize_media_type(item.get("type")),
                "year": _extract_year(item.get("release_date")),
                "imdb_id": _extract_imdb_id(item.get("external_ids")),
                "description": item.get("overview", ""),
                "rating": _normalize_rating(item.get("rating")),
            }
            
            # Only add if we have minimum required data
            if media_item["title"] and media_item["media_type"]:
                media_items.append(media_item)
        
        logging.info(f"Successfully fetched {len(media_items)} items from MyService list {list_id}")
        return media_items
        
    except Exception as e:
        logging.error(f"Error fetching MyService list {list_id}: {str(e)}")
        raise

def _fetch_from_url(url: str) -> List[Dict]:
    """Fetch from full URL using Selenium"""
    items = []
    
    with SB(uc=True, headless=True) as sb:
        sb.open(url)
        sb.wait_for_element(".media-item", timeout=10)
        
        # Handle pagination
        while True:
            elements = sb.find_elements(".media-item")
            for element in elements:
                item_data = _extract_item_data(element)
                if item_data:
                    items.append(item_data)
            
            # Check for next page
            try:
                next_button = sb.find_element(".pagination-next")
                if not next_button.is_enabled():
                    break
                sb.click(".pagination-next")
                sb.wait_for_element(".media-item", timeout=10)
            except:
                break
    
    return items

def _fetch_from_id(list_id: str) -> List[Dict]:
    """Fetch from API using list ID"""
    api_url = f"https://api.myservice.com/lists/{list_id}"
    
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data.get("items", [])

def _extract_item_data(element) -> Dict:
    """Extract data from web element"""
    try:
        return {
            "name": element.find_element("css selector", ".title").text,
            "type": element.get_attribute("data-type"),
            "release_date": element.find_element("css selector", ".year").text,
            "rating": element.find_element("css selector", ".rating").text,
        }
    except Exception as e:
        logging.warning(f"Failed to extract item data: {e}")
        return {}

def _normalize_media_type(type_str: str) -> str:
    """Normalize media type to 'movie' or 'tv'"""
    if not type_str:
        return "movie"  # Default
    
    type_str = type_str.lower()
    if type_str in ["tv", "series", "show", "television"]:
        return "tv"
    else:
        return "movie"

def _extract_year(date_str: str) -> int:
    """Extract year from date string"""
    if not date_str:
        return None
    
    import re
    match = re.search(r'(\d{4})', date_str)
    return int(match.group(1)) if match else None

def _extract_imdb_id(external_ids: Dict) -> str:
    """Extract IMDb ID from external IDs"""
    if not external_ids:
        return None
    
    imdb_id = external_ids.get("imdb")
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id}"
    
    return imdb_id

def _normalize_rating(rating_str: str) -> float:
    """Normalize rating to 0.0-10.0 scale"""
    if not rating_str:
        return None
    
    try:
        rating = float(rating_str)
        # Convert different scales to 0-10
        if rating <= 5.0:
            return rating * 2  # 0-5 scale to 0-10
        else:
            return rating  # Assume already 0-10
    except (ValueError, TypeError):
        return None
```

### Provider Testing

```python
# test_custom_provider.py
import pytest
from unittest.mock import patch, MagicMock
from custom_provider import fetch_myservice_list

def test_fetch_valid_list():
    """Test fetching a valid list"""
    with patch('custom_provider._fetch_from_id') as mock_fetch:
        mock_fetch.return_value = [
            {
                "name": "Test Movie",
                "type": "movie",
                "release_date": "2023-01-01",
                "rating": "8.5"
            }
        ]
        
        result = fetch_myservice_list("test123")
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Movie"
        assert result[0]["media_type"] == "movie"
        assert result[0]["year"] == 2023

def test_invalid_list_id():
    """Test handling of invalid list ID"""
    with pytest.raises(ValueError):
        fetch_myservice_list("")

def test_network_error_handling():
    """Test network error handling"""
    with patch('custom_provider._fetch_from_id', side_effect=ConnectionError("Network error")):
        with pytest.raises(ConnectionError):
            fetch_myservice_list("test123")
```

## 💾 Database Management

### Backup and Restore

```bash
#!/bin/bash
# backup-restore.sh

backup_database() {
    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Stop ListSync
    docker-compose stop listsync
    
    # Backup database and config
    cp data/list_sync.db "$backup_dir/"
    cp data/config.enc "$backup_dir/" 2>/dev/null || true
    
    # Backup environment
    cp .env "$backup_dir/" 2>/dev/null || true
    
    # Create archive
    tar -czf "${backup_dir}.tar.gz" -C ./backups "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    # Restart ListSync
    docker-compose start listsync
    
    echo "Backup created: ${backup_dir}.tar.gz"
}

restore_database() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        echo "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Stop ListSync
    docker-compose stop listsync
    
    # Backup current data
    cp data/list_sync.db data/list_sync.db.pre-restore
    
    # Extract and restore
    local temp_dir=$(mktemp -d)
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Find the extracted directory
    local extracted_dir=$(find "$temp_dir" -type d -name "20*" | head -1)
    
    if [[ -d "$extracted_dir" ]]; then
        cp "$extracted_dir/list_sync.db" data/
        cp "$extracted_dir/config.enc" data/ 2>/dev/null || true
        echo "Database restored from $backup_file"
    else
        echo "Invalid backup file format"
        exit 1
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
    
    # Restart ListSync
    docker-compose start listsync
}

# Usage
case "$1" in
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    *)
        echo "Usage: $0 {backup|restore backup_file.tar.gz}"
        exit 1
        ;;
esac
```

### Database Migration

```python
# migrate_database.py
import sqlite3
import os
from typing import Dict, Callable

def get_db_version(conn: sqlite3.Connection) -> int:
    """Get current database version"""
    try:
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.OperationalError:
        return 0

def set_db_version(conn: sqlite3.Connection, version: int):
    """Set database version"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()

# Migration functions
def migrate_to_v1(conn: sqlite3.Connection):
    """Add provider_source column to synced_items"""
    conn.execute("""
        ALTER TABLE synced_items 
        ADD COLUMN provider_source TEXT
    """)

def migrate_to_v2(conn: sqlite3.Connection):
    """Add sync_history table"""
    conn.execute("""
        CREATE TABLE sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_completed TIMESTAMP,
            items_processed INTEGER DEFAULT 0,
            items_requested INTEGER DEFAULT 0,
            items_skipped INTEGER DEFAULT 0,
            items_errored INTEGER DEFAULT 0,
            sync_mode TEXT DEFAULT 'manual'
        )
    """)

def migrate_to_v3(conn: sqlite3.Connection):
    """Add indexes for performance"""
    conn.execute("CREATE INDEX IF NOT EXISTS idx_synced_items_last_synced ON synced_items(last_synced)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_synced_items_status ON synced_items(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_synced_items_overseerr_id ON synced_items(overseerr_id)")

# Migration registry
MIGRATIONS: Dict[int, Callable] = {
    1: migrate_to_v1,
    2: migrate_to_v2,
    3: migrate_to_v3,
}

def migrate_database(db_path: str):
    """Run all pending migrations"""
    conn = sqlite3.connect(db_path)
    
    current_version = get_db_version(conn)
    target_version = max(MIGRATIONS.keys())
    
    print(f"Current database version: {current_version}")
    print(f"Target database version: {target_version}")
    
    if current_version >= target_version:
        print("Database is up to date")
        conn.close()
        return
    
    # Create backup
    backup_path = f"{db_path}.backup.{current_version}"
    os.system(f"cp {db_path} {backup_path}")
    print(f"Created backup: {backup_path}")
    
    try:
        # Run migrations
        for version in range(current_version + 1, target_version + 1):
            if version in MIGRATIONS:
                print(f"Running migration to version {version}...")
                MIGRATIONS[version](conn)
                set_db_version(conn, version)
                print(f"Migration to version {version} completed")
        
        print("All migrations completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        print(f"Restoring from backup: {backup_path}")
        conn.close()
        os.system(f"cp {backup_path} {db_path}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database("data/list_sync.db")
```

This comprehensive documentation now covers all aspects of ListSync's functionality, from basic usage to advanced enterprise deployment patterns, providing users with the detailed technical information they need to effectively use and extend the tool. 