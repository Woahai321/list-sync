#!/usr/bin/env python3 
"""
ListSync Web UI API Server
FastAPI backend that integrates with the existing ListSync codebase
"""

import os
import sqlite3
import psutil
import re
import json
import subprocess
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import time
import requests
import signal
import asyncio
import multiprocessing
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import statistics
import zoneinfo

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import existing ListSync modules
from list_sync.database import (
    configure_sync_interval,
    load_sync_interval,
    save_sync_result,
    get_sync_stats,
    load_list_ids,
    save_list_id,
    delete_list,
    DB_FILE,
    init_database
)
from list_sync.config import load_env_config
# Removed in-memory sync tracker - now using database-based tracking

# Import new timezone utilities
from list_sync.utils.timezone_utils import (
    get_current_timezone_info,
    get_timezone_from_env,
    normalize_timezone_input,
    list_supported_abbreviations
)

# Global variable to track server start time
SERVER_START_TIME = None

# Initialize FastAPI app
app = FastAPI(
    title="ListSync Web UI API",
    description="REST API for ListSync media synchronization dashboard",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Set the server start time when the FastAPI app starts"""
    global SERVER_START_TIME

    # Ensure database schema is up to date (creates new tables/columns if missing)
    try:
        init_database()
        logging.info("Database initialized / schema verified successfully at startup")
    except Exception as e:
        logging.error(f"Failed to initialize database on startup: {e}")
        # Don't stop startup, but raise HTTPException later if DB is unusable

    SERVER_START_TIME = time.time()
    print(f"🚀 API Server started at: {datetime.fromtimestamp(SERVER_START_TIME).isoformat()}")
    print(f"📊 Dashboard available at: http://localhost:3222")

# Add CORS middleware
import os

def get_allowed_origins():
    """Get allowed origins from environment or use defaults"""
    env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    
    if env_origins:
        # If environment variable is set, use it (comma-separated)
        return [origin.strip() for origin in env_origins.split(',')]
    
    # Default origins for development
    default_origins = [
        "http://localhost:3222", 
        "http://localhost:4222",
        "http://0.0.0.0:3222",
        "http://0.0.0.0:4222",
        "http://127.0.0.1:3222",
        "http://127.0.0.1:4222"
    ]
    
    # Add common local network patterns
    for i in range(1, 255):
        default_origins.extend([
            f"http://192.168.1.{i}:3222",
            f"http://192.168.1.{i}:4222"
        ])
    
    return default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class SyncIntervalUpdate(BaseModel):
    interval_hours: float

class ListAdd(BaseModel):
    list_type: str
    list_id: str
    user_id: str = "1"

class ProcessInfo(BaseModel):
    pid: int
    status: str
    created: str
    cmdline: List[str]
    memory_percent: Optional[float] = None
    cpu_percent: Optional[float] = None

class LogInfo(BaseModel):
    last_sync_start: Optional[str] = None
    last_sync_complete: Optional[str] = None
    sync_interval_hours: Optional[float] = None
    next_sync_time: Optional[str] = None
    sync_status: str = 'unknown'
    recent_errors: List[str] = []
    log_file_size: int = 0
    log_last_modified: str = ''

class SystemStatus(BaseModel):
    database: Dict[str, Any]
    process: Dict[str, Any]
    sync: Dict[str, Any]
    logs: LogInfo
    overall_health: str

class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str
    category: str
    message: str
    raw_line: str
    media_info: Optional[Dict[str, Any]] = None

class LogStreamResponse(BaseModel):
    entries: List[LogEntry]
    total_count: int
    has_more: bool
    last_position: int

# Utility functions
def find_listsync_processes() -> List[ProcessInfo]:
    """Find ListSync processes dynamically"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['cmdline']:
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    if ('list_sync' in cmdline_str or 'listsync' in cmdline_str) and 'python' in cmdline_str:
                        # Filter out API server itself
                        if 'api_server.py' not in cmdline_str:
                            processes.append(ProcessInfo(
                                pid=proc.info['pid'],
                                cmdline=proc.info['cmdline'],
                                created=datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                                status=proc.status()
                            ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"Error finding processes: {e}")
    
    return processes

def parse_log_for_sync_info(log_path: str = 'data/list_sync.log', max_lines: int = 200) -> LogInfo:
    """Parse log file for sync timing information"""
    log_info = LogInfo()
    
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        # Try to get last sync from database as fallback
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(last_synced) FROM synced_items")
            result = cursor.fetchone()
            if result and result[0]:
                log_info.last_sync_complete = result[0]
                print(f"Got last sync from database: {result[0]}")
            conn.close()
        except Exception as e:
            print(f"Could not get last sync from database: {e}")
        return log_info
    
    try:
        # Get file stats
        stat = os.stat(log_path)
        log_info.log_file_size = stat.st_size
        log_info.log_last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Check last N lines for recent activity
        recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        
        # Enhanced sync completion patterns
        sync_completion_patterns = [
            r'sync complete',
            r'sync summary',
            r'processing complete',
            r'webhook sent',
            r'discord notification sent',
            r'sync finished',
            r'soluify - list sync summary',
            r'sync operation completed',
            r'all lists processed',
            r'sleeping for.*hours',  # This usually indicates sync completion
            r'automated sync mode.*sleeping'
        ]
        
        print(f"Parsing {len(recent_lines)} lines from log file...")
        
        for line in reversed(recent_lines):  # Start from most recent
            line_lower = line.lower()
            
            # Look for sync completion (most recent first)
            for pattern in sync_completion_patterns:
                if pattern in line_lower:
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match and not log_info.last_sync_complete:
                        log_info.last_sync_complete = timestamp_match.group(1)
                        print(f"Found sync completion pattern '{pattern}' with timestamp: {timestamp_match.group(1)}")
                        break
            
            # Look for sync start
            if 'starting sync' in line_lower or 'sync started' in line_lower:
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match and not log_info.last_sync_start:
                    log_info.last_sync_start = timestamp_match.group(1)
                    print(f"Found sync start: {timestamp_match.group(1)}")
        
        # If no sync completion found in logs, try database fallback
        if not log_info.last_sync_complete:
            print("No sync completion found in logs, checking database...")
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(last_synced) FROM synced_items")
                result = cursor.fetchone()
                if result and result[0]:
                    log_info.last_sync_complete = result[0]
                    print(f"Got last sync from database: {result[0]}")
                conn.close()
            except Exception as e:
                print(f"Could not get last sync from database: {e}")
        
        # Look for sync interval in any line
        for line in recent_lines:
            # Look for sync interval
            if 'sleeping for' in line.lower():
                hours_match = re.search(r'sleeping for (\d+\.?\d*) hours', line.lower())
                if hours_match:
                    log_info.sync_interval_hours = float(hours_match.group(1))
                    print(f"Found sync interval in logs: {hours_match.group(1)} hours")
                    break
            elif 'sync interval' in line.lower():
                hours_match = re.search(r'(\d+\.?\d*) hours?', line.lower())
                if hours_match:
                    log_info.sync_interval_hours = float(hours_match.group(1))
                    print(f"Found sync interval in logs: {hours_match.group(1)} hours")
                    break
        
        # Get sync interval from database if not found in logs
        if not log_info.sync_interval_hours:
            try:
                db_interval = load_sync_interval()
                if db_interval > 0:
                    log_info.sync_interval_hours = db_interval
                    print(f"Got sync interval from database: {db_interval} hours")
            except:
                pass
        
        # Calculate next sync time and status
        if log_info.last_sync_complete and log_info.sync_interval_hours:
            try:
                last_sync = datetime.fromisoformat(log_info.last_sync_complete)
                next_sync = last_sync + timedelta(hours=log_info.sync_interval_hours)
                log_info.next_sync_time = next_sync.isoformat()
                
                print(f"Calculated next sync: {next_sync.isoformat()}")
                
                # Determine if sync is overdue (with 10 minute grace period)
                now = datetime.now()
                grace_period = timedelta(minutes=10)
                if now > (next_sync + grace_period):
                    log_info.sync_status = 'overdue'
                elif now > next_sync:
                    log_info.sync_status = 'due'
                else:
                    log_info.sync_status = 'scheduled'
                    
                print(f"Sync status: {log_info.sync_status}")
            except Exception as e:
                print(f"Error calculating next sync: {e}")
                log_info.sync_status = 'unknown'
        else:
            log_info.sync_status = 'unknown'
            print(f"Cannot calculate next sync - last_sync: {log_info.last_sync_complete}, interval: {log_info.sync_interval_hours}")
        
        # Look for recent errors (last 50 lines only)
        error_lines = recent_lines[-50:] if len(recent_lines) > 50 else recent_lines
        for line in error_lines:
            if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'timeout']):
                # Skip common non-error messages
                if not any(skip in line.lower() for skip in ['no error', 'error: none', 'successfully']):
                    log_info.recent_errors.append(line.strip())
        
        # Limit errors to last 5
        log_info.recent_errors = log_info.recent_errors[-5:]
        
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return log_info

def normalize_list_id(list_type: str, list_id: str) -> str:
    """
    Normalize list_id to match what's stored in item_lists table.
    Extracts the actual ID from URLs if needed.
    
    Args:
        list_type: Type of list (e.g., 'mdblist', 'trakt', 'imdb')
        list_id: List ID (may be a URL or just an ID)
        
    Returns:
        Normalized list_id that matches what's in item_lists table
    """
    if not list_id:
        return list_id
    
    # If it's already not a URL, return as-is
    if not list_id.startswith(('http://', 'https://')):
        return list_id
    
    # Extract ID from URL based on list type
    list_type_lower = list_type.lower()
    
    if list_type_lower == 'mdblist':
        # MDBList URLs: https://mdblist.com/lists/username/listname
        # Extract: username/listname
        match = re.search(r'mdblist\.com/lists/([^/?]+)', list_id)
        if match:
            return match.group(1)
    
    elif list_type_lower in ('trakt', 'trakt_special'):
        # Trakt URLs can be various formats:
        # - https://trakt.tv/users/username/lists/list-slug
        # - https://trakt.tv/lists/123
        # Extract the list identifier
        match = re.search(r'trakt\.tv/(?:users/[^/]+/)?lists/([^/?]+)', list_id)
        if match:
            return match.group(1)
        # For special Trakt lists like trending:movies, they might be in the URL path
        match = re.search(r'trakt\.tv/(?:movies|shows)/([^/?]+)', list_id)
        if match:
            return match.group(1)
    
    elif list_type_lower == 'imdb':
        # IMDb URLs: https://www.imdb.com/list/ls123456789
        # Extract: ls123456789
        match = re.search(r'imdb\.com/list/([^/?]+)', list_id)
        if match:
            return match.group(1)
    
    elif list_type_lower == 'letterboxd':
        # Letterboxd URLs: https://letterboxd.com/username/list/listname/
        # NOTE: Letterboxd stores the full URL in the database, so return as-is
        return list_id
    
    elif list_type_lower == 'tmdb':
        # TMDB URLs: https://www.themoviedb.org/list/12345
        # Extract: 12345
        match = re.search(r'themoviedb\.org/list/([^/?]+)', list_id)
        if match:
            return match.group(1)
    
    # For other types or if extraction fails, try to get the last meaningful segment
    # This is a fallback that should work for most cases
    from urllib.parse import urlparse
    try:
        parsed = urlparse(list_id.rstrip('/'))
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            return path_parts[-1]
    except Exception:
        pass
    
    # If all else fails, return the original (though this might not match)
    logging.warning(f"Could not normalize list_id for {list_type}: {list_id}, using as-is")
    return list_id


def get_deduplicated_items():
    """Get unique items with deduplication logic"""
    if not os.path.exists(DB_FILE):
        return []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all synced items including year and source list info
        cursor.execute("SELECT id, title, media_type, year, imdb_id, overseerr_id, status, last_synced, source_list_type, source_list_id FROM synced_items")
        items = cursor.fetchall()
        
        unique_items = {}
        
        # Define status priority (higher number = higher priority)
        status_priority = {
            'requested': 100,
            'already_requested': 90,
            'already_available': 80,
            'available': 70,
            'not_found': 20,
            'error': 10,
            'skipped': 5  # Lowest priority
        }
        
        for item in items:
            item_id, title, media_type, year, imdb_id, overseerr_id, status, last_synced, source_list_type, source_list_id = item
            
            # Create unique key based on title and media type
            key = f"{title}_{media_type}".lower().strip()
            
            if key not in unique_items:
                unique_items[key] = item
            else:
                existing_item = unique_items[key]
                existing_status = existing_item[6]  # Status is now at index 6
                existing_last_synced = existing_item[7]  # Last synced is now at index 7
                
                # Prefer item with higher status priority
                current_priority = status_priority.get(status, 0)
                existing_priority = status_priority.get(existing_status, 0)
                
                should_replace = False
                
                if current_priority > existing_priority:
                    should_replace = True
                elif current_priority == existing_priority:
                    # Same priority, prefer item with overseerr_id
                    if overseerr_id and not existing_item[5]:  # overseerr_id is now at index 5
                        should_replace = True
                    elif (overseerr_id and existing_item[5]) or (not overseerr_id and not existing_item[5]):
                        # Both have or both don't have overseerr_id, prefer more recent
                        if last_synced > existing_last_synced:
                            should_replace = True
                
                if should_replace:
                    unique_items[key] = item
        
        conn.close()
        
        result = list(unique_items.values())
        print(f"DEBUG - Deduplication: {len(items)} raw items -> {len(result)} unique items")
        
        # Debug: Show status breakdown of unique items
        status_counts = {}
        for item in result:
            status = item[6]  # Status is now at index 6
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"DEBUG - Unique item statuses: {status_counts}")
        
        return result
        
    except Exception as e:
        print(f"Error getting deduplicated items: {e}")
        return []

def analyze_data_quality():
    """Analyze data quality with deduplication stats"""
    if not os.path.exists(DB_FILE):
        return None
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all synced items including year
        cursor.execute("SELECT title, media_type, year, imdb_id, overseerr_id, status, last_synced FROM synced_items")
        items = cursor.fetchall()
        
        # Analyze duplicates
        title_counts = Counter()
        status_counts = Counter()
        unique_items = {}
        
        for item in items:
            title, media_type, year, imdb_id, overseerr_id, status, last_synced = item
            
            # Count titles for duplicate analysis
            title_counts[title] += 1
            status_counts[status] += 1
            
            # Create unique key (prefer items with overseerr_id and more recent sync)
            key = f"{title}_{media_type}".lower()
            if key not in unique_items or \
               (overseerr_id and not unique_items[key][4]) or \
               last_synced > unique_items[key][6]:
                unique_items[key] = item
        
        # Categorize statuses
        success_statuses = ['already_available', 'already_requested', 'available', 'requested']
        failure_statuses = ['not_found', 'error']
        
        unique_success = sum(1 for item in unique_items.values() if item[5] in success_statuses)
        unique_failure = sum(1 for item in unique_items.values() if item[5] in failure_statuses)
        
        analysis = {
            'total_raw_items': len(items),
            'total_unique_items': len(unique_items),
            'duplicates_found': len(items) - len(unique_items),
            'status_breakdown': dict(status_counts),
            'unique_success_count': unique_success,
            'unique_failure_count': unique_failure,
            'success_rate': (unique_success / len(unique_items) * 100) if unique_items else 0,
            'most_duplicated': title_counts.most_common(5)
        }
        
        conn.close()
        return analysis
        
    except Exception as e:
        print(f"Error analyzing data quality: {e}")
        return None

def parse_docker_logs_for_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """Parse ListSync core logs for recent sync activity"""
    try:
        # Try to read from the mounted log file first
        log_file_paths = [
            "/var/log/supervisor/listsync-core.log",  # Docker supervisor log (priority)
            "logs/listsync-core.log",  # Mounted from container
            "/usr/src/app/logs/listsync-core.log",  # Container app logs
            "data/list_sync.log"  # Fallback to data directory
        ]
        
        logs_output = None
        log_file_used = None
        
        for log_path in log_file_paths:
            try:
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read last 500 lines to capture recent sync
                        lines = f.readlines()
                        logs_output = ''.join(lines[-500:]) if len(lines) > 500 else ''.join(lines)
                        log_file_used = log_path
                        break
            except Exception as e:
                print(f"Could not read log file {log_path}: {e}")
                continue
        
        if not logs_output:
            print("Could not retrieve ListSync logs from any source")
            return []
        
        print(f"Successfully retrieved logs from: {log_file_used}")
        
        # Parse logs for sync activity
        activities = []
        lines = logs_output.strip().split('\n')
        
        # Look for the specific patterns from the user's logs:
        # 2024-01-15 10:30:45 ☑️  Guardians of the Galaxy: Already Available (1/78)
        # 2024-01-15 10:30:45 📌 Pixar Remix: WALL·E in 16-Bit: Already Requested (54/78)
        # 2024-01-15 10:30:45 ⏭️  Item Name: Skipped (X/Y)
        # 2024-01-15 10:30:45 ✅ Item Name: Requested (X/Y)
        
        for line in lines:
            # Extract timestamp - now we expect format: "YYYY-MM-DD HH:MM:SS content"
            timestamp_str = None
            log_content = line
            
            # Try our new timestamp format first: 2024-01-15 10:30:45
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.*)$', line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                log_content = timestamp_match.group(2)
            else:
                # Try Docker timestamp format: 2024-01-15T10:30:45.123456789Z
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    log_content = line[len(timestamp_match.group(0)):].strip()
                else:
                    # Fallback: use current time if no timestamp found
                    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Look for the specific status patterns with emojis
            status_patterns = [
                (r'☑️\s+(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', 'already_available', 'available'),
                (r'📌\s+(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', 'already_requested', 'requested'),
                (r'✅\s+(.+?):\s*(?:Successfully )?Requested\s*\((\d+)/(\d+)\)', 'requested', 'requested'),
                (r'⏭️\s+(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', 'skipped', 'skipped'),
                (r'❌\s+(.+?):\s*(?:Error|Not Found)\s*\((\d+)/(\d+)\)', 'error', 'error'),
                # Fallback patterns without emojis
                (r'(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', 'already_available', 'available'),
                (r'(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', 'already_requested', 'requested'),
                (r'(.+?):\s*(?:Successfully )?Requested\s*\((\d+)/(\d+)\)', 'requested', 'requested'),
                (r'(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', 'skipped', 'skipped'),
                (r'(.+?):\s*(?:Error|Not Found)\s*\((\d+)/(\d+)\)', 'error', 'error'),
            ]
            
            for pattern, status, action in status_patterns:
                match = re.search(pattern, log_content)
                if match:
                    title = match.group(1).strip()
                    item_num = int(match.group(2))
                    total_items = int(match.group(3))
                    
                    # Clean up title (remove extra whitespace, special characters)
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    # Determine media type based on title patterns
                    media_type = "movie"  # default
                    
                    # Common TV show indicators
                    tv_indicators = [
                        'game of thrones', 'breaking bad', 'the walking dead', 'big bang theory',
                        'stranger things', 'sherlock', 'how i met your mother', 'dexter', 'friends',
                        'lost', 'rick and morty', 'black mirror', 'house', 'the office', 'arrow',
                        'chernobyl', 'better call saul', 'mr. robot', 'the boys', 'squid game'
                    ]
                    
                    title_lower = title.lower()
                    if any(indicator in title_lower for indicator in tv_indicators):
                        media_type = "tv"
                    
                    # Convert timestamp to ISO format for consistency
                    try:
                        if 'T' in timestamp_str:
                            # Already in ISO format or similar
                            if timestamp_str.endswith('Z'):
                                # UTC timestamp - convert to local time
                                utc_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone()
                                local_timestamp = local_dt.isoformat()
                            else:
                                local_timestamp = timestamp_str
                        else:
                            # Standard format "YYYY-MM-DD HH:MM:SS" - convert to ISO
                            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            local_timestamp = dt.isoformat()
                    except Exception as e:
                        print(f"Error converting timestamp {timestamp_str}: {e}")
                        # Fallback to current time
                        local_timestamp = datetime.now().isoformat()
                    
                    activity = {
                        "id": f"log-{item_num}",
                        "title": title,
                        "media_type": media_type,
                        "status": status,
                        "last_synced": local_timestamp,
                        "action": action,
                        "item_number": item_num,
                        "total_items": total_items
                    }
                    
                    activities.append(activity)
                    break  # Found a match, don't check other patterns
        
        # Sort by item number (most recent processing first - highest numbers first)
        activities.sort(key=lambda x: x.get('item_number', 0), reverse=True)
        
        print(f"DEBUG: Found {len(activities)} total activities")
        if activities:
            print("DEBUG: First 10 activities (sorted by item number):")
            for i, activity in enumerate(activities[:10]):
                print(f"  {i+1}. #{activity['item_number']}: {activity['title']} - {activity['action']} - {activity['last_synced']}")
        
        # No deduplication - return raw stream of recent activity
        print(f"Returning {len(activities[:limit])} raw activities from logs")
        
        return activities[:limit]
        
    except Exception as e:
        print(f"Error parsing logs: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_failures_from_logs():
    """Parse failure items from the log file"""
    log_file_paths = [
        "/var/log/supervisor/listsync-core.log",  # Docker supervisor log (priority)
        "logs/listsync-core.log",  # Mounted from container
        "/usr/src/app/logs/listsync-core.log",  # Container app logs
        "data/list_sync.log"  # Fallback to data directory
    ]
    
    failures_data = {
        "not_found": [],
        "errors": [],
        "total_failures": 0,
        "last_sync_time": None,
        "log_file_exists": False
    }
    
    log_content = None
    for log_path in log_file_paths:
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    failures_data["log_file_exists"] = True
                    break
        except Exception as e:
            print(f"Could not read log file {log_path}: {e}")
            continue
    
    if not log_content:
        return failures_data
    
    lines = log_content.strip().split('\n')
    
    # Look for the "Not Found Items" section at the end of sync
    in_not_found_section = False
    last_error_item = None  # Track last error to attach detail lines
    
    for i, line in enumerate(lines):
        # Extract timestamp
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        timestamp_str = timestamp_match.group(1) if timestamp_match else None
        
        # Update last sync time
        if timestamp_str and not failures_data["last_sync_time"]:
            failures_data["last_sync_time"] = timestamp_str
        
        # Look for "Not Found Items" section header
        if "Not Found Items" in line and "(" in line:
            in_not_found_section = True
            continue
        
        # If we're in the not found section, parse items
        if in_not_found_section:
            # Look for items like: "• Untitled Disney (2027) (Not Found)"
            not_found_match = re.search(r'•\s+(.+?)\s+\(Not Found\)', line)
            if not_found_match:
                item_name = not_found_match.group(1).strip()
                failures_data["not_found"].append({
                    "name": item_name,
                    "timestamp": timestamp_str,
                    "item_number": None,
                    "total_items": None,
                    "sync_session": None,
                    "error_details": "Item not found in Overseerr database"
                })
                continue
            
            # Look for HTTP errors like: "• Star Wars: Andor (2022) (Error: 404 Not Found)"
            # Capture everything after "Error:" to get full error message with nested parentheses
            error_match = re.search(r'•\s+(.+?)\s+\(Error:\s+(.+)$', line)
            if error_match:
                item_name = error_match.group(1).strip()
                error_details = error_match.group(2).strip()
                
                # Remove trailing closing parenthesis that's part of the log format
                if error_details.endswith(')'):
                    # Count parentheses to remove only the outer log format one
                    open_count = error_details.count('(')
                    close_count = error_details.count(')')
                    if close_count > open_count:
                        error_details = error_details[:-1]
                
                failures_data["errors"].append({
                    "name": item_name,
                    "timestamp": timestamp_str,
                    "item_number": None,
                    "total_items": None,
                    "sync_session": None,
                    "error_details": error_details
                })
                continue
            
            # If we hit an empty line or new section, exit not found section
            if line.strip() == "" or "─" in line or "=" in line:
                in_not_found_section = False
        
        # Also look for real-time failures during processing
        # Pattern: "❓ Item Name: Not Found (X/Y)"
        not_found_realtime = re.search(r'❓\s+(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', line)
        if not_found_realtime:
            item_name = not_found_realtime.group(1).strip()
            item_num = int(not_found_realtime.group(2))
            total_items = int(not_found_realtime.group(3))
            
            # Check if we already have this item (avoid duplicates)
            if not any(item["name"] == item_name for item in failures_data["not_found"]):
                new_item = {
                    "name": item_name,
                    "timestamp": timestamp_str,
                    "item_number": item_num,
                    "total_items": total_items,
                    "sync_session": None,
                    "error_details": "Item not found during sync processing"
                }
                failures_data["not_found"].append(new_item)
                last_error_item = new_item
        
        # Pattern: "❌ Item Name: Error (X/Y)"
        error_realtime = re.search(r'❌\s+(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', line)
        if error_realtime:
            item_name = error_realtime.group(1).strip()
            item_num = int(error_realtime.group(2))
            total_items = int(error_realtime.group(3))
            
            # Check if we already have this item (avoid duplicates)
            if not any(item["name"] == item_name for item in failures_data["errors"]):
                new_item = {
                    "name": item_name,
                    "timestamp": timestamp_str,
                    "item_number": item_num,
                    "total_items": total_items,
                    "sync_session": None,
                    "error_details": "Processing error during sync"
                }
                failures_data["errors"].append(new_item)
                last_error_item = new_item
        
        # Look for error detail lines that follow error items (format: "    └─ error message")
        if last_error_item and re.match(r'\s+└─\s+(.+)', line):
            error_detail_match = re.match(r'\s+└─\s+(.+)', line)
            if error_detail_match:
                error_detail = error_detail_match.group(1).strip()
                # Update the last error item with this detail
                last_error_item["error_details"] = error_detail
                last_error_item = None  # Reset after attaching details
    
    # Calculate total failures
    failures_data["total_failures"] = len(failures_data["not_found"]) + len(failures_data["errors"])
    
    # Sort by item number if available, otherwise by timestamp
    def sort_key(item):
        if item.get("item_number"):
            return item["item_number"]
        elif item.get("timestamp"):
            try:
                return datetime.fromisoformat(item["timestamp"]).timestamp()
            except:
                return 0
        return 0
    
    failures_data["not_found"].sort(key=sort_key, reverse=True)
    failures_data["errors"].sort(key=sort_key, reverse=True)
    
    return failures_data

def parse_historic_items_from_logs():
    """Parse all items from the entire log file for historic data"""
    log_file_paths = [
        "/var/log/supervisor/listsync-core.log",  # Docker supervisor log (priority)
        "logs/listsync-core.log",  # Mounted from container
        "/usr/src/app/logs/listsync-core.log",  # Container app logs
        "data/list_sync.log"  # Fallback to data directory
    ]
    
    historic_data = {
        "total_processed": [],
        "successful_items": [],
        "requested_items": [],
        "sync_sessions": [],
        "log_file_exists": False,
        "total_unique_processed": 0,
        "total_unique_successful": 0,
        "total_unique_requested": 0
    }
    
    log_content = None
    for log_path in log_file_paths:
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    historic_data["log_file_exists"] = True
                    break
        except Exception as e:
            print(f"Could not read log file {log_path}: {e}")
            continue
    
    if not log_content:
        return historic_data
    
    lines = log_content.strip().split('\n')
    
    # Track sync sessions and items
    current_sync_session = None
    all_items = {}  # For deduplication: key = "title_mediatype", value = latest item data
    
    # Status patterns with emojis and their categories
    status_patterns = [
        # Successful patterns
        (r'☑️\s+(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', 'already_available', 'successful'),
        (r'📌\s+(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', 'already_requested', 'successful'),
        (r'✅\s+(.+?):\s*(?:Successfully )?Requested\s*\((\d+)/(\d+)\)', 'requested', 'successful'),
        (r'⏭️\s+(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', 'skipped', 'successful'),
        # Failure patterns
        (r'❓\s+(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', 'not_found', 'failed'),
        (r'❌\s+(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', 'error', 'failed'),
        # Fallback patterns without emojis
        (r'(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', 'already_available', 'successful'),
        (r'(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', 'already_requested', 'successful'),
        (r'(.+?):\s*(?:Successfully )?Requested\s*\((\d+)/(\d+)\)', 'requested', 'successful'),
        (r'(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', 'skipped', 'successful'),
        (r'(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', 'not_found', 'failed'),
        (r'(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', 'error', 'failed'),
    ]
    
    for line in lines:
        # Extract timestamp
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        timestamp_str = timestamp_match.group(1) if timestamp_match else None
        
        # Detect new sync session
        if "Total unique media items ready for sync:" in line:
            total_match = re.search(r'Total unique media items ready for sync:\s*(\d+)', line)
            if total_match:
                current_sync_session = {
                    "timestamp": timestamp_str,
                    "total_items": int(total_match.group(1)),
                    "session_id": f"sync_{timestamp_str}_{total_match.group(1)}" if timestamp_str else f"sync_unknown_{len(historic_data['sync_sessions'])}"
                }
                historic_data["sync_sessions"].append(current_sync_session)
        
        # Parse individual item processing
        for pattern, status, category in status_patterns:
            match = re.search(pattern, line)
            if match:
                title = match.group(1).strip()
                item_num = int(match.group(2))
                total_items = int(match.group(3))
                
                # Clean up title
                title = re.sub(r'\s+', ' ', title).strip()
                
                # Extract year from title (look for patterns like "Movie Name (2023)" or "Movie Name 2023")
                year = None
                year_patterns = [
                    r'\((\d{4})\)',  # (2023)
                    r'\s(\d{4})\s',  # 2023 with spaces
                    r'\s(\d{4})$',   # 2023 at end
                ]
                
                for pattern in year_patterns:
                    year_match = re.search(pattern, title)
                    if year_match:
                        year = int(year_match.group(1))
                        # Remove year from title for cleaner display
                        title = re.sub(pattern, '', title).strip()
                        # Clean up any double spaces or trailing punctuation
                        title = re.sub(r'\s+', ' ', title).strip()
                        title = re.sub(r'\s*,\s*$', '', title)  # Remove trailing comma
                        break
                
                # Determine media type
                media_type = "movie"  # default
                tv_indicators = [
                    'game of thrones', 'breaking bad', 'the walking dead', 'big bang theory',
                    'stranger things', 'sherlock', 'how i met your mother', 'dexter', 'friends',
                    'lost', 'rick and morty', 'black mirror', 'house', 'the office', 'arrow',
                    'chernobyl', 'better call saul', 'mr. robot', 'the boys', 'squid game'
                ]
                
                if any(indicator in title.lower() for indicator in tv_indicators):
                    media_type = "tv"
                
                # Create unique key for deduplication
                unique_key = f"{title.lower()}_{media_type}"
                
                # Convert timestamp to ISO format
                try:
                    if timestamp_str:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        iso_timestamp = dt.isoformat()
                    else:
                        iso_timestamp = datetime.now().isoformat()
                except:
                    iso_timestamp = datetime.now().isoformat()
                
                item_data = {
                    "id": f"historic-{item_num}-{timestamp_str or 'unknown'}",
                    "title": title,
                    "year": year,
                    "media_type": media_type,
                    "status": status,
                    "category": category,
                    "timestamp": iso_timestamp,
                    "item_number": item_num,
                    "total_items": total_items,
                    "sync_session": current_sync_session["session_id"] if current_sync_session else "unknown",
                    "action": status.replace('_', ' ').title()
                }
                
                # For deduplication, prefer most recent timestamp and higher priority statuses
                status_priority = {
                    'requested': 100,
                    'already_requested': 90,
                    'already_available': 80,
                    'skipped': 70,
                    'not_found': 20,
                    'error': 10
                }
                
                if unique_key not in all_items:
                    all_items[unique_key] = item_data
                else:
                    existing = all_items[unique_key]
                    current_priority = status_priority.get(status, 0)
                    existing_priority = status_priority.get(existing['status'], 0)
                    
                    # Replace if higher priority or same priority but more recent
                    if (current_priority > existing_priority or 
                        (current_priority == existing_priority and iso_timestamp > existing['timestamp'])):
                        all_items[unique_key] = item_data
                
                break  # Found a match, don't check other patterns
    
    # Categorize deduplicated items
    for item in all_items.values():
        # Add to total processed
        historic_data["total_processed"].append(item)
        
        # Add to successful if it's a successful status
        if item["category"] == "successful":
            historic_data["successful_items"].append(item)
            
            # Add to requested if it's specifically a requested item
            if item["status"] in ["requested", "already_requested"]:
                historic_data["requested_items"].append(item)
    
    # Calculate totals
    historic_data["total_unique_processed"] = len(all_items)
    historic_data["total_unique_successful"] = len(historic_data["successful_items"])
    historic_data["total_unique_requested"] = len(historic_data["requested_items"])
    
    # Sort items by timestamp (most recent first)
    for key in ["total_processed", "successful_items", "requested_items"]:
        historic_data[key].sort(key=lambda x: x["timestamp"], reverse=True)
    
    print(f"DEBUG - Historic parsing complete:")
    print(f"  Total unique processed: {historic_data['total_unique_processed']}")
    print(f"  Total unique successful: {historic_data['total_unique_successful']}")
    print(f"  Total unique requested: {historic_data['total_unique_requested']}")
    print(f"  Sync sessions found: {len(historic_data['sync_sessions'])}")
    
    return historic_data

def get_duplicates_from_current_sync():
    """Calculate actual duplicates (same name appearing multiple times) within the most recent sync session from logs"""
    log_file_paths = [
        "/var/log/supervisor/listsync-core.log",  # Docker supervisor log (priority)
        "logs/listsync-core.log",  # Mounted from container
        "/usr/src/app/logs/listsync-core.log",  # Container app logs
        "data/list_sync.log"  # Fallback to data directory
    ]
    
    for log_path in log_file_paths:
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                
                lines = log_content.strip().split('\n')
                
                # Find the most recent sync session boundaries
                sync_start_index = -1
                sync_end_index = -1
                
                # Find the most recent sync start marker
                for i in range(len(lines) - 1, -1, -1):
                    if "📊  Total unique media items ready for sync:" in lines[i]:
                        sync_start_index = i
                        break
                
                if sync_start_index == -1:
                    print("DEBUG - No sync start marker found")
                    return 0
                
                # Find the sync end marker (summary section)
                for i in range(sync_start_index + 1, len(lines)):
                    if "Soluify - List Sync Summary" in lines[i] or "──────────────" in lines[i]:
                        sync_end_index = i
                        break
                
                # If no end marker found, use end of file
                if sync_end_index == -1:
                    sync_end_index = len(lines)
                
                print(f"DEBUG - Analyzing sync session from line {sync_start_index} to {sync_end_index}")
                
                # Parse all items processed in this sync session
                item_names = []
                processing_patterns = [
                    r'☑️\s+(.+?):\s*Already Available\s*\(\d+/\d+\)',
                    r'📌\s+(.+?):\s*Already Requested\s*\(\d+/\d+\)',
                    r'✅\s+(.+?):\s*(?:Successfully )?Requested\s*\(\d+/\d+\)',
                    r'⏭️\s+(.+?):\s*Skipped\s*\(\d+/\d+\)',
                    r'❓\s+(.+?):\s*Not Found\s*\(\d+/\d+\)',
                    r'❌\s+(.+?):\s*(?:Error|Failed)\s*\(\d+/\d+\)',
                ]
                
                # Count occurrences of each item name
                for i in range(sync_start_index + 1, sync_end_index):
                    line = lines[i]
                    
                    for pattern in processing_patterns:
                        match = re.search(pattern, line)
                        if match:
                            item_name = match.group(1).strip()
                            # Normalize the name (remove extra whitespace, convert to lowercase for comparison)
                            normalized_name = re.sub(r'\s+', ' ', item_name).strip().lower()
                            item_names.append(normalized_name)
                            break
                
                # Count duplicates
                from collections import Counter
                name_counts = Counter(item_names)
                duplicates_count = sum(count - 1 for count in name_counts.values() if count > 1)
                
                print(f"DEBUG - Found {len(item_names)} total items processed in sync session")
                print(f"DEBUG - Found {len([count for count in name_counts.values() if count > 1])} items with duplicates")
                print(f"DEBUG - Total duplicate occurrences: {duplicates_count}")
                
                # Debug: Show some duplicate examples
                duplicates = {name: count for name, count in name_counts.items() if count > 1}
                if duplicates:
                    print("DEBUG - Examples of duplicated items:")
                    for name, count in list(duplicates.items())[:5]:  # Show first 5 examples
                        print(f"  '{name}' appeared {count} times")
                
                return duplicates_count
                
        except Exception as e:
            print(f"Error reading log file {log_path}: {e}")
            continue
    
    print("DEBUG - No sync session found in logs")
    return 0

def categorize_log_entry(message: str, level: str) -> str:
    """Categorize log entries based on comprehensive regex patterns"""
    message_lower = message.lower()
    
    # Pattern-based categorization with priority order
    
    # Sync operations (patterns 14, 21, 29)
    if any(keyword in message_lower for keyword in [
        'starting automated sync', 'starting in automated mode', 'sync operation completed',
        'full sync', 'sync complete'
    ]):
        return 'sync'
    
    # Web scraping operations - IMDb, Letterboxd, MDBList, Trakt (patterns 6, 7, 8, 9, 16, 18, 23, 24, 25, 26, 27, 28)
    elif any(keyword in message_lower for keyword in [
        'fetching imdb list', 'fetching letterboxd', 'fetching mdblist', 
        'attempting to load url', 'list fetched successfully',
        'found', 'items using selector', 'processing page', 'trying to find chart',
        'chart parent found', 'clicking next page', 'total items in chart',
        'beautifulsoup', 'selenium', 'scraping'
    ]):
        return 'web_scraping'
    
    # API Calls - Overseerr, TMDb, Trakt API (pattern 13, 19)
    elif any(keyword in message_lower for keyword in [
        'overseerr api', 'api connection', 'tmdb', 'detailed response for movie id',
        'fetching trakt', 'trakt api', 'api request', 'api call',
        '"id":', 'response for'
    ]) or ('{' in message and ('"id"' in message or 'tmdbId' in message or 'imdbId' in message)):
        return 'api_calls'
    
    # Database operations - Title matching, searching (patterns 10, 11, 12, 20)
    elif any(keyword in message_lower for keyword in [
        'searching for', 'match candidate', 'final match for', 'score:', 
        'database', 'exact year match', 'close year match'
    ]):
        return 'database'
    
    # Item processing operations (patterns 3, 4, 5)
    elif any(keyword in message_lower for keyword in [
        'added tv:', 'added movie:', 'processing item', 'requesting'
    ]):
        return 'item_processing'
    
    # Webhook and notification operations (patterns 15, 30)
    elif any(keyword in message_lower for keyword in [
        'discord webhook', 'webhook notification', 'webhook integration'
    ]):
        return 'webhook'
    
    # Pagination operations (pattern 17)
    elif any(keyword in message_lower for keyword in [
        'no more pages available', 'pagination'
    ]):
        return 'pagination'
    
    # Process management (pattern 22)
    elif any(keyword in message_lower for keyword in [
        'process pid', 'sigusr1'
    ]):
        return 'process'
    
    # Default category
    else:
        return 'general'

def extract_media_info(message: str) -> Optional[Dict[str, Any]]:
    """Extract comprehensive media information from log messages using all 30 patterns"""
    import re
    
    # Pattern 3: Added TV/Movie with IMDB
    pattern_3 = r'Added (tv|movie): (.+?) \((\d{4})\) \(IMDB ID: (tt\d+)\)'
    match = re.search(pattern_3, message)
    if match:
        return {
            'pattern': 3,
            'type': 'item_added_imdb',
            'media_type': match.group(1),
            'title': match.group(2).strip(),
            'year': int(match.group(3)),
            'imdb_id': match.group(4),
            'source': 'imdb'
        }
    
    # Pattern 4: Added Movie (Simple)
    pattern_4 = r'Added movie: (.+)$'
    match = re.search(pattern_4, message)
    if match and 'IMDB ID:' not in message and '[' not in message:
        return {
            'pattern': 4,
            'type': 'item_added_simple',
            'media_type': 'movie',
            'title': match.group(1).strip(),
            'source': 'trakt'
        }
    
    # Pattern 5: Added Movie with Position
    pattern_5 = r'Added movie: (.+?) \((\d{4})\) \[(\d+)/(\d+)\]'
    match = re.search(pattern_5, message)
    if match:
        return {
            'pattern': 5,
            'type': 'item_added_position',
            'media_type': 'movie',
            'title': match.group(1).strip(),
            'year': int(match.group(2)),
            'position': int(match.group(3)),
            'total': int(match.group(4)),
            'source': 'trakt_special'
        }
    
    # Pattern 6: Fetching List
    pattern_6 = r'Fetching (IMDB|TRAKT|TRAKT_SPECIAL) list: (.+)'
    match = re.search(pattern_6, message)
    if match:
        return {
            'pattern': 6,
            'type': 'list_fetch_start',
            'list_type': match.group(1).lower(),
            'list_id': match.group(2).strip(),
            'source': match.group(1).lower()
        }
    
    # Pattern 7: Attempting to Load URL
    pattern_7 = r'Attempting to load URL: (.+)'
    match = re.search(pattern_7, message)
    if match:
        return {
            'pattern': 7,
            'type': 'url_load',
            'url': match.group(1).strip()
        }
    
    # Pattern 8: Found Items
    pattern_8 = r'Found (\d+) items (?:using selector: (.+)|on (?:current page|page (\d+)))'
    match = re.search(pattern_8, message)
    if match:
        return {
            'pattern': 8,
            'type': 'items_found',
            'count': int(match.group(1)),
            'selector': match.group(2) if match.group(2) else None,
            'page': int(match.group(3)) if match.group(3) else None
        }
    
    # Pattern 9: Found Title Using Selector
    pattern_9 = r'Found title using selector: (.+)'
    match = re.search(pattern_9, message)
    if match:
        return {
            'pattern': 9,
            'type': 'title_found',
            'selector': match.group(1).strip()
        }
    
    # Pattern 10: Searching for Title
    pattern_10 = r"Searching for '(.+?)' \(Year: (\d{4}|None)\)"
    match = re.search(pattern_10, message)
    if match:
        year = None if match.group(2) == 'None' else int(match.group(2))
        return {
            'pattern': 10,
            'type': 'title_search',
            'title': match.group(1),
            'year': year
        }
    
    # Pattern 11: Match Candidate
    pattern_11 = r"Match candidate: '(.+?)' \((None|\d{4})\) - Score: (\d*\.\d+)"
    match = re.search(pattern_11, message)
    if match:
        year = None if match.group(2) == 'None' else int(match.group(2))
        return {
            'pattern': 11,
            'type': 'match_candidate',
            'title': match.group(1),
            'year': year,
            'score': float(match.group(3))
        }
    
    # Pattern 12: Final Match
    pattern_12 = r"Final match for '(.+?)' \((None|\d{4})\): '(.+?)' \((None|\d{4})\) - Score: (\d*\.\d+)"
    match = re.search(pattern_12, message)
    if match:
        original_year = None if match.group(2) == 'None' else int(match.group(2))
        matched_year = None if match.group(4) == 'None' else int(match.group(4))
        return {
            'pattern': 12,
            'type': 'final_match',
            'original_title': match.group(1),
            'original_year': original_year,
            'matched_title': match.group(3),
            'matched_year': matched_year,
            'score': float(match.group(5))
        }
    
    # Pattern 13: API Connection
    pattern_13 = r'Overseerr API connection successful!'
    if re.search(pattern_13, message):
        return {
            'pattern': 13,
            'type': 'api_connection',
            'service': 'overseerr',
            'status': 'success'
        }
    
    # Pattern 14: Sync Operation
    pattern_14 = r'Starting automated sync with (\d+\.\d+) hour interval'
    match = re.search(pattern_14, message)
    if match:
        return {
            'pattern': 14,
            'type': 'sync_start',
            'interval_hours': float(match.group(1))
        }
    
    # Pattern 15: Webhook Notification
    pattern_15 = r'Discord webhook notification sent successfully'
    if re.search(pattern_15, message):
        return {
            'pattern': 15,
            'type': 'webhook_sent',
            'service': 'discord',
            'status': 'success'
        }
    
    # Pattern 16: Processing Page
    pattern_16 = r'Processing page (\d+)\.\.\.'
    match = re.search(pattern_16, message)
    if match:
        return {
            'pattern': 16,
            'type': 'page_processing',
            'page': int(match.group(1))
        }
    
    # Pattern 17: No More Pages
    pattern_17 = r'No more pages available: Message: (.+)'
    match = re.search(pattern_17, message)
    if match:
        return {
            'pattern': 17,
            'type': 'pagination_end',
            'error_message': match.group(1).strip()
        }
    
    # Pattern 18: List Fetched Successfully
    pattern_18 = r'(IMDB|Trakt) list (.+?) fetched successfully. Found (\d+) items.'
    match = re.search(pattern_18, message)
    if match:
        return {
            'pattern': 18,
            'type': 'list_fetch_complete',
            'service': match.group(1).lower(),
            'list_id': match.group(2).strip(),
            'item_count': int(match.group(3))
        }
    
    # Pattern 19: Detailed Response for Movie ID
    pattern_19 = r'Detailed response for movie ID (\d+): ({.+)'
    match = re.search(pattern_19, message)
    if match:
        return {
            'pattern': 19,
            'type': 'movie_metadata',
            'movie_id': int(match.group(1)),
            'metadata_json': match.group(2)
        }
    
    # Pattern 20: Truncated Log Entries
    pattern_20 = r'\.\.\.truncated (\d+) characters\)\.\.\.:'
    match = re.search(pattern_20, message)
    if match:
        return {
            'pattern': 20,
            'type': 'truncated_log',
            'truncated_chars': int(match.group(1))
        }
    
    # Pattern 21: Mode of Operation
    pattern_21 = r'Starting in automated mode'
    if re.search(pattern_21, message):
        return {
            'pattern': 21,
            'type': 'mode_start',
            'mode': 'automated'
        }
    
    # Pattern 22: Process PID
    pattern_22 = r'Process PID: (\d+) - Send SIGUSR1 to trigger immediate sync'
    match = re.search(pattern_22, message)
    if match:
        return {
            'pattern': 22,
            'type': 'process_info',
            'pid': int(match.group(1)),
            'trigger_signal': 'SIGUSR1'
        }
    
    # Pattern 23: Web Scraping Attempts
    pattern_23 = r'Trying to find chart with data-testid selector: \[data-testid="(.+?)"\]'
    match = re.search(pattern_23, message)
    if match:
        return {
            'pattern': 23,
            'type': 'chart_search',
            'selector': match.group(1)
        }
    
    # Pattern 24: Chart Found
    pattern_24 = r'Chart parent found with selector: \[data-testid="(.+?)"\]'
    match = re.search(pattern_24, message)
    if match:
        return {
            'pattern': 24,
            'type': 'chart_found',
            'selector': match.group(1)
        }
    
    # Pattern 25: Pagination Action
    pattern_25 = r'Clicking next page button to go to page (\d+)'
    match = re.search(pattern_25, message)
    if match:
        return {
            'pattern': 25,
            'type': 'page_navigation',
            'target_page': int(match.group(1))
        }
    
    # Pattern 26: Processed Items
    pattern_26 = r'Processed (\d+) items on page (\d+)'
    match = re.search(pattern_26, message)
    if match:
        return {
            'pattern': 26,
            'type': 'page_processed',
            'item_count': int(match.group(1)),
            'page': int(match.group(2))
        }
    
    # Pattern 27: Total Items in Chart
    pattern_27 = r'Total items in chart: (\d+)'
    match = re.search(pattern_27, message)
    if match:
        return {
            'pattern': 27,
            'type': 'chart_total',
            'total_items': int(match.group(1))
        }
    
    # Pattern 28: Detailed Fetch for Special Trakt List
    pattern_28 = r'Fetching special Trakt list: (.+) \(limit: (\d+) items\)'
    match = re.search(pattern_28, message)
    if match:
        return {
            'pattern': 28,
            'type': 'special_list_fetch',
            'url': match.group(1).strip(),
            'limit': int(match.group(2))
        }
    
    # Pattern 29: Sync Completion
    pattern_29 = r'Sync operation completed successfully'
    if re.search(pattern_29, message):
        return {
            'pattern': 29,
            'type': 'sync_complete',
            'status': 'success'
        }
    
    # Pattern 30: Webhook Enabled
    pattern_30 = r'Discord webhook integration enabled'
    if re.search(pattern_30, message):
        return {
            'pattern': 30,
            'type': 'webhook_enabled',
            'service': 'discord'
        }
    
    return None

def parse_log_line(line: str, line_number: int) -> Optional[LogEntry]:
    """Parse a single log line into a LogEntry"""
    # Pattern: "YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE"
    log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (DEBUG|INFO|ERROR|WARNING) - (.+)$'
    match = re.match(log_pattern, line.strip())
    
    if not match:
        return None
    
    timestamp_str, level, message = match.groups()
    
    # Convert timestamp to ISO format
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        iso_timestamp = dt.isoformat()
    except:
        iso_timestamp = timestamp_str
    
    category = categorize_log_entry(message, level)
    media_info = extract_media_info(message)
    
    return LogEntry(
        id=f"log-{line_number}",
        timestamp=iso_timestamp,
        level=level,
        category=category,
        message=message,
        raw_line=line.strip(),
        media_info=media_info
    )

def get_line_number(entry):
    """Extract line number from log entry ID for secondary sorting"""
    try:
        # ID format is "log-{line_number}"
        return int(entry.id.split('-')[1])
    except (IndexError, ValueError):
        return 0

def get_log_entries(
    log_path: str = 'data/list_sync.log',
    limit: int = 50,
    offset: int = 0,
    level_filter: Optional[str] = None,
    category_filters: Optional[List[str]] = None,
    search: Optional[str] = None,
    sort_order: str = 'desc'
) -> LogStreamResponse:
    """Get log entries with filtering and pagination"""
    
    if not os.path.exists(log_path):
        return LogStreamResponse(entries=[], total_count=0, has_more=False, last_position=0)
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Parse all lines into log entries
        all_entries = []
        for i, line in enumerate(lines):
            entry = parse_log_line(line, i + 1)
            if entry:
                all_entries.append(entry)
        
        # Apply filters
        filtered_entries = all_entries
        
        if level_filter:
            filtered_entries = [e for e in filtered_entries if e.level == level_filter]
        
        if category_filters and len(category_filters) > 0:
            filtered_entries = [e for e in filtered_entries if e.category in category_filters]
        
        if search:
            search_lower = search.lower()
            filtered_entries = [
                e for e in filtered_entries 
                if search_lower in e.message.lower() or 
                   (e.media_info and e.media_info.get('title', '').lower().find(search_lower) != -1)
            ]
        
        # Sort by timestamp and line number to maintain original file order for same timestamps
        if sort_order == 'desc':
            filtered_entries.sort(key=lambda x: (x.timestamp, get_line_number(x)), reverse=True)
        else:
            filtered_entries.sort(key=lambda x: (x.timestamp, get_line_number(x)), reverse=False)
        
        # Apply pagination
        total_count = len(filtered_entries)
        start = offset
        end = offset + limit
        paginated_entries = filtered_entries[start:end]
        
        has_more = end < total_count
        last_position = len(lines)  # Position in original file
        
        return LogStreamResponse(
            entries=paginated_entries,
            total_count=total_count,
            has_more=has_more,
            last_position=last_position
        )
        
    except Exception as e:
        print(f"Error reading log file: {e}")
        return LogStreamResponse(entries=[], total_count=0, has_more=False, last_position=0)

async def stream_log_updates(
    log_path: str = 'data/list_sync.log',
    last_position: int = 0,
    level_filter: Optional[str] = None,
    category_filters: Optional[List[str]] = None,
    search: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """Stream new log entries as they are added to the file"""
    
    if not os.path.exists(log_path):
        yield f"data: {json.dumps({'error': 'Log file not found'})}\n\n"
        return
    
    current_position = last_position
    
    while True:
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last known position
                f.seek(0, 2)  # Go to end of file
                file_size = f.tell()
                
                if file_size > current_position:
                    f.seek(current_position)
                    new_lines = f.readlines()
                    
                    new_entries = []
                    for i, line in enumerate(new_lines):
                        entry = parse_log_line(line, current_position + i + 1)
                        if entry:
                            # Apply filters
                            if level_filter and entry.level != level_filter:
                                continue
                            if category_filters and len(category_filters) > 0 and entry.category not in category_filters:
                                continue
                            if search and search.lower() not in entry.message.lower():
                                if not (entry.media_info and entry.media_info.get('title', '').lower().find(search.lower()) != -1):
                                    continue
                            
                            new_entries.append(entry)
                    
                    if new_entries:
                        # Send new entries
                        for entry in new_entries:
                            yield f"data: {json.dumps(entry.dict())}\n\n"
                    
                    current_position = file_size
                
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        await asyncio.sleep(1)  # Check for updates every second

# API Endpoints

@app.get("/api/system/status")
async def get_system_status():
    """Comprehensive system health check"""
    
    # Database status
    database_status = {
        "connected": False,
        "file_exists": os.path.exists(DB_FILE),
        "file_size": 0,
        "last_modified": "",
        "error": None
    }
    
    if database_status["file_exists"]:
        try:
            stat = os.stat(DB_FILE)
            database_status["file_size"] = stat.st_size
            database_status["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Test connection
            conn = sqlite3.connect(DB_FILE)
            conn.execute("SELECT 1")
            conn.close()
            database_status["connected"] = True
        except Exception as e:
            database_status["error"] = str(e)
    
    # Process status
    processes = find_listsync_processes()
    process_status = {
        "running": len(processes) > 0,
        "processes": [p.dict() for p in processes],
        "error": None
    }
    
    # Log analysis
    logs = parse_log_for_sync_info()
    
    # Sync status
    sync_status = {
        "status": logs.sync_status,
        "last_sync": logs.last_sync_complete,
        "next_sync": logs.next_sync_time,
        "interval_hours": logs.sync_interval_hours,
        "error": None
    }
    
    # Overall health
    overall_health = "healthy"
    if not database_status["connected"] or not process_status["running"]:
        overall_health = "error"
    elif logs.sync_status == "overdue" or logs.recent_errors:
        overall_health = "warning"
    
    return SystemStatus(
        database=database_status,
        process=process_status,
        sync=sync_status,
        logs=logs,
        overall_health=overall_health
    )

@app.get("/api/system/processes")
async def get_processes():
    """Get ListSync process information"""
    return find_listsync_processes()

@app.get("/api/system/logs")
async def get_log_info():
    """Get log file analysis"""
    return parse_log_for_sync_info()

@app.get("/api/system/database/test")
async def test_database():
    """Test database connectivity"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("SELECT 1")
        conn.close()
        return {"connected": True}
    except Exception as e:
        return {"connected": False, "error": str(e)}

@app.get("/api/system/health")
async def get_health_check():
    """Simple health check endpoint"""
    try:
        # Check database
        db_result = await test_database()
        db_connected = db_result["connected"]
        
        # Check if ListSync process is running
        processes = find_listsync_processes()
        process_running = len(processes) > 0
        
        # Parse logs for sync status
        log_info = parse_log_for_sync_info()
        
        return {
            "database": db_connected,
            "process": process_running,
            "sync_status": log_info.sync_status,
            "last_sync": log_info.last_sync_complete,
            "next_sync": log_info.next_sync_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Setup Wizard Endpoints - First-Run Configuration
# ============================================================================

@app.get("/api/setup/status")
async def get_setup_status():
    """
    Check setup status and determine if wizard should be shown.
    
    Returns:
        - is_complete: Whether setup wizard has been completed
        - has_env: Whether .env file exists with basic config
        - needs_migration: Whether .env should be auto-migrated to database
        - settings_count: Number of settings in database
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        
        # Check if setup is marked complete in database
        is_complete = config.is_setup_complete()
        
        # Check if .env exists with configuration
        has_env = config.has_env_config()
        
        # Check how many settings are in database
        settings_count = config.database.count_settings()
        
        # Needs migration if: has .env, not complete, and no/few settings in DB
        needs_migration = has_env and not is_complete and settings_count < 5
        
        return {
            "is_complete": is_complete,
            "has_env": has_env,
            "needs_migration": needs_migration,
            "settings_count": settings_count
        }
    except Exception as e:
        logging.error(f"Error checking setup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup/migrate-from-env")
async def migrate_from_env():
    """
    Migrate settings from .env file to database.
    Auto-runs on startup if .env exists and database is empty.
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        
        # Perform migration
        migrated_count = config.migrate_env_to_database()
        
        # Mark setup as complete after successful migration
        if migrated_count > 0:
            config.mark_setup_complete()
        
        logging.info(f"Environment migration complete: {migrated_count} settings migrated")
        
        return {
            "success": True,
            "settings_migrated": migrated_count,
            "message": f"Successfully migrated {migrated_count} settings from .env to database"
        }
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup/test/overseerr")
async def test_overseerr_connection(data: dict):
    """
    Test Overseerr connection with provided URL and API key.
    
    Expected data:
        - overseerr_url: str
        - overseerr_api_key: str
        - overseerr_user_id: str (optional, defaults to "1")
    """
    try:
        overseerr_url = data.get('overseerr_url', '').strip().rstrip('/')
        overseerr_api_key = data.get('overseerr_api_key', '').strip()
        overseerr_user_id = data.get('overseerr_user_id', '1').strip()
        
        # Basic validation
        if not overseerr_url:
            return {
                "valid": False,
                "error": "Overseerr URL is required"
            }
        
        if not overseerr_api_key:
            return {
                "valid": False,
                "error": "Overseerr API Key is required"
            }
        
        if not overseerr_url.startswith(('http://', 'https://')):
            return {
                "valid": False,
                "error": "URL must start with http:// or https://"
            }
        
        # Test connection by fetching user list and finding the default user
        try:
            headers = {"X-Api-Key": overseerr_api_key}
            
            logging.info(f"Testing Overseerr API key validation with endpoint: {overseerr_url}/api/v1/user")
            
            # Fetch all users to validate API key and get user info
            user_response = requests.get(f"{overseerr_url}/api/v1/user", headers=headers, timeout=10, params={"take": 100})
            
            logging.info(f"Overseerr API key test response status: {user_response.status_code}")
            
            # If we get 401, the API key is invalid
            if user_response.status_code == 401:
                return {
                    "valid": False,
                    "error": "Invalid API key. Please check your Overseerr API key."
                }
            
            # If we get 403, the API key doesn't have permission
            if user_response.status_code == 403:
                return {
                    "valid": False,
                    "error": "API key does not have required permissions. Please check your API key."
                }
            
            # Raise for other HTTP errors
            user_response.raise_for_status()
            
            # Parse response to get user info
            user_data = user_response.json()
            users = user_data.get('results', [])
            
            # Save all users to database for future use
            if users:
                try:
                    from list_sync.database import save_overseerr_users
                    formatted_users = []
                    for user in users:
                        formatted_users.append({
                            'id': str(user.get('id')),
                            'display_name': user.get('displayName', user.get('username', 'Unknown')),
                            'email': user.get('email', ''),
                            'avatar': user.get('avatar', '')
                        })
                    save_overseerr_users(formatted_users)
                    logging.info(f"Pre-populated {len(formatted_users)} Overseerr users to database during setup")
                except Exception as e:
                    # Don't fail the test if user save fails
                    logging.warning(f"Failed to save users to database during setup: {e}")
            
            # Find the specified user (default is user ID 1)
            default_user = None
            for user in users:
                if str(user.get('id')) == str(overseerr_user_id):
                    default_user = user
                    break
            
            if not default_user and users:
                # If specified user not found, return error
                logging.warning(f"User ID {overseerr_user_id} not found in Overseerr")
                return {
                    "valid": False,
                    "error": f"User ID {overseerr_user_id} not found. Please check the User ID."
                }
            elif not users:
                # No users found at all
                logging.warning("No users found in Overseerr")
                return {
                    "valid": False,
                    "error": "No users found in Overseerr. Please check your instance."
                }
            
            # Also test /api/v1/status to get version info
            try:
                status_response = requests.get(f"{overseerr_url}/api/v1/status", headers=headers, timeout=5)
                status_data = status_response.json() if status_response.status_code == 200 else {}
            except:
                status_data = {}
            
            logging.info(f"Overseerr connection test successful - API key validated, found user: {default_user.get('displayName') or default_user.get('username')}")
            
            # Prepare user info for response
            user_info = {
                "id": default_user.get('id'),
                "email": default_user.get('email', ''),
                "username": default_user.get('username', ''),
                "displayName": default_user.get('displayName', ''),
                "plexUsername": default_user.get('plexUsername', ''),
                "avatar": default_user.get('avatar', ''),
                "requestCount": default_user.get('requestCount', 0),
            }
            
            return {
                "valid": True,
                "message": "Overseerr connection successful",
                "version": status_data.get("version", "Unknown"),
                "updateAvailable": status_data.get("updateAvailable", False),
                "user": user_info
            }
        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "error": "Connection timeout. Check your Overseerr URL."
            }
        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "error": "Could not connect to Overseerr. Check your URL and network."
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return {
                    "valid": False,
                    "error": "Invalid API key. Please check your Overseerr API key."
                }
            return {
                "valid": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:100]}"
            }
        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": f"Connection test failed: {str(e)}"
            }
    except Exception as e:
        logging.error(f"Error testing Overseerr connection: {e}")
        return {
            "valid": False,
            "error": f"Unexpected error: {str(e)}"
        }


@app.get("/api/overseerr/users")
async def get_overseerr_users_endpoint():
    """Get all Overseerr users from database"""
    try:
        from list_sync.database import get_overseerr_users
        
        users = get_overseerr_users()
        
        return {
            "success": True,
            "users": users,
            "count": len(users)
        }
    except Exception as e:
        logging.error(f"Error fetching Overseerr users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/overseerr/users/sync")
async def sync_overseerr_users_endpoint():
    """Sync Overseerr users from Overseerr API to database"""
    try:
        from list_sync.config import ConfigManager
        from list_sync.database import save_overseerr_users
        from urllib.parse import quote
        
        # Get Overseerr credentials from config
        config = ConfigManager()
        overseerr_url = config.get_setting('overseerr_url')
        overseerr_api_key = config.get_setting('overseerr_api_key')
        
        if not overseerr_url or not overseerr_api_key:
            raise HTTPException(
                status_code=400,
                detail="Overseerr URL and API key must be configured"
            )
        
        # Fetch users from Overseerr API
        headers = {"X-Api-Key": overseerr_api_key}
        
        # Get all users (paginated)
        all_users = []
        page = 1
        take = 100  # Max per page
        
        while True:
            response = requests.get(
                f"{overseerr_url.rstrip('/')}/api/v1/user",
                headers=headers,
                params={"take": take, "skip": (page - 1) * take},
                timeout=10
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Overseerr API key")
            
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail="Overseerr API key lacks permissions")
            
            response.raise_for_status()
            data = response.json()
            
            users = data.get('results', [])
            if not users:
                break
            
            all_users.extend(users)
            
            # Check if there are more pages
            page_info = data.get('pageInfo', {})
            if page_info.get('pages', 1) <= page:
                break
            
            page += 1
        
        # Transform users to our format
        formatted_users = []
        for user in all_users:
            avatar = user.get('avatar', '')
            full_avatar = avatar
            if avatar and overseerr_url and avatar.startswith('/'):
                full_avatar = f"{overseerr_url.rstrip('/')}{avatar}"
            
            # Use proxy endpoint to enable caching on first use
            proxied_avatar = None
            if full_avatar and full_avatar.startswith(('http://', 'https://')):
                proxied_avatar = f"/api/images/proxy?url={quote(full_avatar, safe='')}"
            
            formatted_users.append({
                'id': str(user.get('id')),
                'display_name': user.get('displayName', user.get('username', 'Unknown')),
                'email': user.get('email', ''),
                'avatar': proxied_avatar or full_avatar or ''
            })
        
        # Save to database
        save_overseerr_users(formatted_users)
        
        logging.info(f"Synced {len(formatted_users)} Overseerr users to database")
        
        return {
            "success": True,
            "message": f"Successfully synced {len(formatted_users)} users",
            "users": formatted_users,
            "count": len(formatted_users)
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error syncing Overseerr users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup/test/trakt")
async def test_trakt_client_id(data: dict):
    """
    Test Trakt Client ID validity.
    
    Expected data:
        - trakt_client_id: str
    """
    try:
        trakt_client_id = data.get('trakt_client_id', '').strip()
        
        # Basic validation
        if not trakt_client_id:
            return {
                "valid": False,
                "error": "Trakt Client ID is required"
            }
        
        # Validate Trakt Client ID format first
        # Trakt Client IDs are typically hex strings (alphanumeric lowercase)
        # They can vary in length but should be at least 16 characters
        import re
        
        # Check length (Trakt Client IDs should be reasonable length)
        if len(trakt_client_id) < 16:
            return {
                "valid": False,
                "error": "Invalid Trakt Client ID format. Client ID is too short (minimum 16 characters)."
            }
        
        # Check if it contains only valid hex characters (0-9, a-f)
        # Trakt Client IDs are typically lowercase hex strings
        if not re.match(r'^[a-f0-9]+$', trakt_client_id.lower()):
            return {
                "valid": False,
                "error": "Invalid Trakt Client ID format. Client ID should contain only hexadecimal characters (0-9, a-f)."
            }
        
        # Test Trakt API with an endpoint that validates the Client ID
        # Use a public endpoint that will reject invalid Client IDs
        try:
            headers = {
                "Content-Type": "application/json",
                "trakt-api-version": "2",
                "trakt-api-key": trakt_client_id
            }
            
            # Try to access a simple public endpoint
            # This endpoint should work with a valid Client ID even without OAuth
            # An invalid Client ID should return 401
            response = requests.get(
                "https://api.trakt.tv/calendars/all/movies/2024-01-01/1",
                headers=headers,
                timeout=10
            )
            
            # Check response status
            # Trakt API returns 401 for unauthorized/invalid Client IDs
            if response.status_code == 401:
                # 401 means unauthorized - this indicates an invalid Client ID
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', '').lower()
                    # Check for specific error messages
                    if 'invalid' in error_message or 'unauthorized' in error_message or 'forbidden' in error_message:
                        return {
                            "valid": False,
                            "error": "Invalid Trakt Client ID. Please verify your Client ID is correct."
                        }
                except:
                    pass
                # Default to invalid if we get 401
                return {
                    "valid": False,
                    "error": "Invalid Trakt Client ID. The API returned unauthorized. Please check your Client ID."
                }
            
            # If we get 400, it's likely an invalid request format or Client ID
            if response.status_code == 400:
                return {
                    "valid": False,
                    "error": "Invalid Trakt Client ID format. Please check your Client ID."
                }
            
            # Check response headers for Client ID validation
            # Trakt API might include validation info in headers
            api_key_header = response.headers.get('X-API-Key-Status', '').lower()
            if 'invalid' in api_key_header or 'rejected' in api_key_header:
                return {
                    "valid": False,
                    "error": "Invalid Trakt Client ID. The API rejected the Client ID."
                }
            
            # 200 or 404 means the request was accepted (Client ID appears valid)
            # 404 is acceptable for calendar endpoints if the date doesn't exist
            if response.status_code in [200, 404]:
                logging.info("Trakt Client ID validation successful")
                return {
                    "valid": True,
                    "message": "Trakt Client ID is valid"
                }
            
            # For any other status, be more cautious
            logging.warning(f"Trakt Client ID validation returned unexpected status: {response.status_code}")
            # If we get an unexpected status, assume invalid for safety
            return {
                "valid": False,
                "error": f"Unexpected response from Trakt API (status {response.status_code}). Please check your Client ID."
            }
        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "error": "Connection timeout. Check your network connection."
            }
        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "error": "Could not connect to Trakt API. Check your network."
            }
        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    except Exception as e:
        logging.error(f"Error testing Trakt Client ID: {e}")
        return {
            "valid": False,
            "error": f"Unexpected error: {str(e)}"
        }


@app.post("/api/setup/step1/essential")
async def save_step1_essential(data: dict):
    """
    Save and validate Step 1: Essential configuration (Overseerr).
    
    Expected data:
        - overseerr_url: str
        - overseerr_api_key: str
        - overseerr_user_id: str
        - overseerr_4k: bool
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        errors = {}
        
        # Validate Overseerr URL
        overseerr_url = data.get('overseerr_url', '').strip().rstrip('/')
        if not overseerr_url:
            errors['overseerr_url'] = 'Overseerr URL is required'
        elif not overseerr_url.startswith(('http://', 'https://')):
            errors['overseerr_url'] = 'URL must start with http:// or https://'
        
        # Validate Overseerr API Key
        overseerr_api_key = data.get('overseerr_api_key', '').strip()
        if not overseerr_api_key:
            errors['overseerr_api_key'] = 'Overseerr API Key is required'
        
        # Test Overseerr connection if no errors so far
        # Use /api/v1/user endpoint which REQUIRES authentication to properly validate API key
        if not errors and overseerr_url and overseerr_api_key:
            try:
                headers = {"X-Api-Key": overseerr_api_key}
                overseerr_user_id = data.get('overseerr_user_id', '1').strip()
                
                # Test with /api/v1/user to validate API key and get user info
                response = requests.get(f"{overseerr_url}/api/v1/user", headers=headers, timeout=10, params={"take": 100})
                
                # If we get 401, the API key is invalid
                if response.status_code == 401:
                    errors['overseerr_api_key'] = 'Invalid API key. Please check your Overseerr API key.'
                    logging.error("Overseerr API key validation failed: 401 Unauthorized")
                # If we get 403, the API key doesn't have permission
                elif response.status_code == 403:
                    errors['overseerr_api_key'] = 'API key does not have required permissions. Please check your API key.'
                    logging.error("Overseerr API key validation failed: 403 Forbidden")
                else:
                    # Raise for other HTTP errors
                    response.raise_for_status()
                    
                    # Verify the specified user exists
                    user_data = response.json()
                    users = user_data.get('results', [])
                    user_found = any(str(user.get('id')) == str(overseerr_user_id) for user in users)
                    
                    if not user_found and users:
                        errors['overseerr_user_id'] = f'User ID {overseerr_user_id} not found in Overseerr.'
                        logging.error(f"Overseerr user validation failed: User ID {overseerr_user_id} not found")
                    else:
                        logging.info("Overseerr connection test successful - API key validated")
            except requests.exceptions.Timeout:
                errors['overseerr_url'] = 'Connection timeout. Check your Overseerr URL.'
            except requests.exceptions.ConnectionError:
                errors['overseerr_url'] = 'Could not connect to Overseerr. Check your URL and network.'
            except requests.exceptions.HTTPError as e:
                # Handle other HTTP errors
                if e.response.status_code == 401:
                    errors['overseerr_api_key'] = 'Invalid API key. Please check your Overseerr API key.'
                elif e.response.status_code == 403:
                    errors['overseerr_api_key'] = 'API key does not have required permissions. Please check your API key.'
                else:
                    errors['overseerr_url'] = f'HTTP {e.response.status_code}: Connection test failed'
            except requests.exceptions.RequestException as e:
                errors['overseerr_url'] = f'Connection test failed: {str(e)}'
                logging.error(f"Overseerr connection test failed: {e}")
        
        # If validation failed, return errors
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        # Save settings to database
        config.save_setting('overseerr_url', overseerr_url)
        config.save_setting('overseerr_api_key', overseerr_api_key)
        config.save_setting('overseerr_user_id', data.get('overseerr_user_id', '1'))
        config.save_setting('overseerr_4k', data.get('overseerr_4k', False))
        
        logging.info("Step 1 (Essential) configuration saved")
        
        return {
            "valid": True,
            "message": "Essential configuration saved successfully"
        }
    except Exception as e:
        logging.error(f"Error in step 1: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        # Return error in same format as validation errors
        return {
            "valid": False,
            "errors": {
                "_general": f"An unexpected error occurred: {str(e)}"
            }
        }


@app.post("/api/setup/step2/configuration")
async def save_step2_configuration(data: dict):
    """
    Save and validate Step 2: Configuration (Trakt + Sync settings + Notifications).
    
    Expected data:
        - trakt_client_id: str
        - sync_interval: int
        - auto_sync: bool
        - timezone: str
        - discord_webhook: str (optional)
        - discord_enabled: bool
    """
    try:
        from list_sync.config import ConfigManager
        from list_sync.utils.timezone_utils import normalize_timezone_input
        
        config = ConfigManager()
        errors = {}
        
        # Validate Trakt Client ID
        trakt_client_id = data.get('trakt_client_id', '').strip()
        if not trakt_client_id:
            errors['trakt_client_id'] = 'Trakt Client ID is required'
        
        # Test Trakt Client ID if no errors so far
        if not errors and trakt_client_id:
            # Validate format first - check for valid hex string
            import re
            if len(trakt_client_id) < 16:
                errors['trakt_client_id'] = 'Invalid Trakt Client ID format. Client ID is too short (minimum 16 characters).'
                logging.error("Trakt Client ID validation failed: Too short")
            elif not re.match(r'^[a-f0-9]+$', trakt_client_id.lower()):
                errors['trakt_client_id'] = 'Invalid Trakt Client ID format. Client ID should contain only hexadecimal characters (0-9, a-f).'
                logging.error("Trakt Client ID validation failed: Invalid format")
            else:
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "trakt-api-version": "2",
                        "trakt-api-key": trakt_client_id
                    }
                    # Use a public endpoint that validates Client ID
                    response = requests.get(
                        "https://api.trakt.tv/calendars/all/movies/2024-01-01/1",
                        headers=headers,
                        timeout=10
                    )
                    
                    # Check response status
                    # Trakt API returns 401 for unauthorized/invalid Client IDs
                    if response.status_code == 401:
                        # 401 means unauthorized - this indicates an invalid Client ID
                        try:
                            error_data = response.json()
                            error_message = error_data.get('error', '').lower()
                            if 'invalid' in error_message or 'unauthorized' in error_message or 'forbidden' in error_message:
                                errors['trakt_client_id'] = 'Invalid Trakt Client ID. Please verify your Client ID is correct.'
                                logging.error("Trakt Client ID validation failed: Invalid Client ID")
                            else:
                                errors['trakt_client_id'] = 'Invalid Trakt Client ID. The API returned unauthorized. Please check your Client ID.'
                                logging.error("Trakt Client ID validation failed: Unauthorized")
                        except:
                            # Can't parse error, assume invalid Client ID
                            errors['trakt_client_id'] = 'Invalid Trakt Client ID. The API returned unauthorized. Please check your Client ID.'
                            logging.error("Trakt Client ID validation failed: Unauthorized")
                    elif response.status_code == 400:
                        errors['trakt_client_id'] = 'Invalid Trakt Client ID format. Please check your Client ID.'
                        logging.error("Trakt Client ID validation failed: Bad request")
                    else:
                        # Check response headers for Client ID validation
                        api_key_header = response.headers.get('X-API-Key-Status', '').lower()
                        if 'invalid' in api_key_header or 'rejected' in api_key_header:
                            errors['trakt_client_id'] = 'Invalid Trakt Client ID. The API rejected the Client ID.'
                            logging.error("Trakt Client ID validation failed: Rejected by API")
                        elif response.status_code in [200, 404]:
                            # 200 or 404 means the request was accepted (Client ID appears valid)
                            logging.info("Trakt Client ID validation successful")
                        else:
                            # Unexpected status - be more cautious
                            logging.warning(f"Trakt Client ID validation returned unexpected status: {response.status_code}")
                            errors['trakt_client_id'] = f'Unexpected response from Trakt API (status {response.status_code}). Please check your Client ID.'
                            logging.error(f"Trakt Client ID validation failed: Unexpected status {response.status_code}")
                except requests.exceptions.Timeout:
                    errors['trakt_client_id'] = 'Connection timeout. Check your network connection.'
                except requests.exceptions.ConnectionError:
                    errors['trakt_client_id'] = 'Could not connect to Trakt API. Check your network.'
                except requests.exceptions.RequestException as e:
                    errors['trakt_client_id'] = f'Validation failed: {str(e)}'
                    logging.error(f"Trakt Client ID validation failed: {e}")
        
        # Validate sync interval
        sync_interval = data.get('sync_interval', 24)
        try:
            sync_interval = int(sync_interval)
            if sync_interval < 1 or sync_interval > 168:
                errors['sync_interval'] = 'Sync interval must be between 1 and 168 hours'
        except (ValueError, TypeError):
            errors['sync_interval'] = 'Sync interval must be a number'
        
        # Validate timezone
        timezone = data.get('timezone', 'UTC').strip()
        try:
            normalized_tz = normalize_timezone_input(timezone)
            if not normalized_tz:
                errors['timezone'] = 'Invalid timezone'
        except Exception as e:
            errors['timezone'] = f'Invalid timezone: {str(e)}'
        
        # Validate Discord webhook if provided
        discord_webhook = data.get('discord_webhook', '').strip()
        discord_enabled = data.get('discord_enabled', False)
        
        if discord_enabled and discord_webhook:
            if not discord_webhook.startswith('https://discord.com/api/webhooks/'):
                errors['discord_webhook'] = 'Invalid Discord webhook URL format'
            # Note: Webhook is tested by the frontend before submission, so we don't need to test again here
        
        # If validation failed, return errors
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        # Save settings to database
        config.save_setting('trakt_client_id', trakt_client_id)
        config.save_setting('sync_interval', sync_interval)
        config.save_setting('auto_sync', data.get('auto_sync', True))
        config.save_setting('timezone', timezone)
        
        if discord_webhook:
            config.save_setting('discord_webhook', discord_webhook)
            config.save_setting('discord_enabled', discord_enabled)
        
        # Also save to sync_interval table (for compatibility)
        configure_sync_interval(sync_interval)
        
        logging.info("Step 2 (Configuration) saved")
        
        return {
            "valid": True,
            "message": "Configuration saved successfully"
        }
    except Exception as e:
        logging.error(f"Error in step 2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup/step3/content-sources")
async def save_step3_content_sources(data: dict):
    """
    Save and validate Step 3: Content Sources (at least one required).
    
    Expected data:
        - imdb_lists: str
        - trakt_lists: str
        - trakt_special_lists: str
        - trakt_special_items_limit: int
        - letterboxd_lists: str
        - anilist_lists: str
        - mdblist_lists: str
        - stevenlu_lists: str
        - tmdb_key: str (optional)
        - tmdb_lists: str
        - tvdb_lists: str
        - simkl_lists: str
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        errors = {}
        validated_sources = []
        
        # Check if at least one list source is provided
        list_fields = [
            'imdb_lists', 'trakt_lists', 'trakt_special_lists', 'letterboxd_lists',
            'anilist_lists', 'mdblist_lists', 'stevenlu_lists', 'tmdb_lists',
            'tvdb_lists', 'simkl_lists'
        ]
        
        has_any_list = any(data.get(field, '').strip() for field in list_fields)
        
        if not has_any_list:
            errors['general'] = 'At least one content source is required'
            return {
                "valid": False,
                "errors": errors
            }
        
        # Validate and collect sources
        for field in list_fields:
            value = data.get(field, '').strip()
            if value:
                provider = field.replace('_lists', '').replace('_', ' ').title()
                validated_sources.append(provider)
        
        # Save all settings
        for field in list_fields:
            config.save_setting(field, data.get(field, ''))
        
        # Save TMDB API key if provided
        if tmdb_key := data.get('tmdb_key', '').strip():
            config.save_setting('tmdb_key', tmdb_key)
        
        # Save special items limit
        trakt_limit = data.get('trakt_special_items_limit', 20)
        try:
            trakt_limit = int(trakt_limit)
        except:
            trakt_limit = 20
        config.save_setting('trakt_special_items_limit', trakt_limit)
        
        logging.info(f"Step 3 (Content Sources) saved: {', '.join(validated_sources)}")
        
        return {
            "valid": True,
            "message": "Content sources saved successfully",
            "validated_sources": validated_sources
        }
    except Exception as e:
        logging.error(f"Error in step 3: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/setup/complete")
async def complete_setup():
    """
    Mark setup wizard as completed and trigger initial sync.
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        
        # Mark setup as complete
        config.mark_setup_complete()
        
        # Load lists from config into database
        from list_sync.config import load_env_lists
        load_env_lists()
        
        logging.info("Setup wizard completed successfully")
        
        return {
            "success": True,
            "message": "Setup completed successfully. ListSync is ready to sync!"
        }
    except Exception as e:
        logging.error(f"Error completing setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sync-interval")
async def get_sync_interval():
    """Get current sync interval with source tracking"""
    try:
        # Always check database first
        db_interval = load_sync_interval()
        if db_interval > 0:
            return {
                "interval_hours": db_interval,
                "source": "database",
                "last_updated": None  # Could add timestamp tracking
            }
        
        # If no database interval, check environment and initialize database
        try:
            _, _, _, env_interval, _, _ = load_env_config()
            if env_interval > 0:
                # Save environment interval to database for future use
                configure_sync_interval(env_interval)
                return {
                    "interval_hours": env_interval,
                    "source": "environment_initialized",
                    "last_updated": None,
                    "message": "Environment interval saved to database"
                }
        except:
            pass
        
        # Default
        return {
            "interval_hours": 12.0,
            "source": "default",
            "last_updated": None,
            "message": "No interval configured, using default"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sync-interval")
async def update_sync_interval(update: SyncIntervalUpdate):
    """Update sync interval in database"""
    try:
        configure_sync_interval(update.interval_hours)
        return {
            "success": True,
            "message": f"Sync interval updated to {update.interval_hours} hours",
            "interval_hours": update.interval_hours,
            "source": "database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-interval/sync-from-env")
async def sync_interval_from_env():
    """Populate database from environment variable (force initialization)"""
    try:
        _, _, _, env_interval, _, _ = load_env_config()
        if env_interval > 0:
            configure_sync_interval(env_interval)
            return {
                "success": True,
                "message": f"Sync interval populated from environment: {env_interval} hours",
                "interval_hours": env_interval,
                "source": "environment"
            }
        else:
            return {
                "success": False,
                "message": "No sync interval found in environment",
                "interval_hours": 0,
                "source": "none"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/sync")
async def get_sync_stats():
    """Get deduplicated sync statistics"""
    try:
        unique_items = get_deduplicated_items()
        
        # Categorize statuses based on user requirements
        newly_requested_statuses = ['requested']  # Actually requested during this sync
        already_requested_statuses = ['already_requested']  # Were already in Overseerr
        available_statuses = ['already_available', 'available']
        skipped_statuses = ['skipped']
        error_statuses = ['not_found', 'error']
        
        newly_requested_count = sum(1 for item in unique_items if item[6] in newly_requested_statuses)
        already_requested_count = sum(1 for item in unique_items if item[6] in already_requested_statuses)
        available_count = sum(1 for item in unique_items if item[6] in available_statuses)
        skipped_count = sum(1 for item in unique_items if item[6] in skipped_statuses)
        error_count = sum(1 for item in unique_items if item[6] in error_statuses)
        
        # Get duplicates from the most recent sync session in logs
        duplicates_in_current_sync = get_duplicates_from_current_sync()
        
        # Get actual failures from the failures endpoint (same source as /failures page)
        try:
            failures = parse_failures_from_logs()
            log_based_errors = failures["total_failures"]
            print(f"DEBUG - Found {log_based_errors} failures from logs (same as /failures page)")
        except Exception as e:
            print(f"DEBUG - Could not parse failures from logs: {e}")
            log_based_errors = error_count
        
        # Calculate simplified metrics
        total_processed = len(unique_items)
        successful_items = newly_requested_count + already_requested_count + available_count + skipped_count  # All non-error items
        total_requested = newly_requested_count  # Only items actually requested during this sync
        total_errors = log_based_errors  # Use same count as /failures page for consistency
        
        # Success rate based on non-error items
        success_rate = (successful_items / total_processed * 100) if total_processed > 0 else 0
        
        # Debug: Print status breakdown
        print(f"DEBUG - Simplified Stats:")
        print(f"  Total Processed: {total_processed}")
        print(f"  Successful: {successful_items} (newly requested: {newly_requested_count}, already requested: {already_requested_count}, available: {available_count}, skipped: {skipped_count})")
        print(f"  Total Requested (NEW): {total_requested}")
        print(f"  Already Requested: {already_requested_count}")
        print(f"  Errors: {total_errors} (from logs, same as /failures page)")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Duplicates in current sync: {duplicates_in_current_sync}")
        
        # Get actual last sync time from logs
        log_info = parse_log_for_sync_info()
        last_updated = log_info.last_sync_complete or log_info.log_last_modified
        
        return {
            "total_processed": total_processed,
            "successful_items": successful_items,
            "total_requested": total_requested,  # Only newly requested items
            "total_errors": total_errors,
            "success_rate": success_rate,
            "duplicates_in_current_sync": duplicates_in_current_sync,  # New field for current sync duplicates
            "last_updated": last_updated,
            # Keep detailed breakdown for other endpoints that might need it
            "breakdown": {
                "newly_requested": newly_requested_count,
                "already_requested": already_requested_count,
                "available": available_count,
                "skipped": skipped_count,
                "errors": log_based_errors  # Use log-based errors for consistency with /failures
            }
        }
    except Exception as e:
        print(f"ERROR in get_sync_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/data-quality")
async def get_data_quality():
    """Get data quality analysis"""
    try:
        analysis = analyze_data_quality()
        if analysis is None:
            raise HTTPException(status_code=500, detail="Could not analyze data quality")
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/status-breakdown")
async def get_status_breakdown():
    """Get success/failure categorization"""
    try:
        unique_items = get_deduplicated_items()
        
        success_statuses = ['already_available', 'already_requested', 'available', 'requested']
        failure_statuses = ['not_found', 'error']
        
        successful_items = [item for item in unique_items if item[6] in success_statuses]
        failed_items = [item for item in unique_items if item[6] in failure_statuses]
        other_items = [item for item in unique_items if item[6] not in success_statuses + failure_statuses]
        
        return {
            "successful": {
                "count": len(successful_items),
                "statuses": success_statuses
            },
            "failed": {
                "count": len(failed_items),
                "statuses": failure_statuses
            },
            "other": {
                "count": len(other_items),
                "statuses": list(set(item[6] for item in other_items))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity/recent")
async def get_recent_activity(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(5, ge=1, le=20, description="Items per page (max 20)")
):
    """Get recent sync activity from listsync-core.log with pagination"""
    try:
        # Try multiple log file paths in order of preference
        log_file_paths = [
            "/var/log/supervisor/listsync-core.log",  # Docker supervisor log
            "logs/listsync-core.log",  # Mounted log directory
            "/usr/src/app/logs/listsync-core.log",  # Container app logs
            "data/list_sync.log"  # Fallback to data directory
        ]
        
        log_content = None
        log_file_used = None
        
        for log_path in log_file_paths:
            try:
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as file:
                        log_content = file.read()
                        log_file_used = log_path
                        break
            except Exception as e:
                print(f"Could not read log file {log_path}: {e}")
                continue
        
        if not log_content:
            return {
                "items": [],
                "total_items": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "error": "No log file found in any of the expected locations"
            }
        
        print(f"Successfully reading recent activity from: {log_file_used}")
        
        recent_items = []
        lines = log_content.strip().split('\n')
        
        # Parse lines in reverse order to get most recent first
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
                
            # Look for sync item patterns with emojis
            if '☑️' in line and 'Already Available' in line:
                # Extract: "☑️  Poker Face: Already Available (10/10)"
                match = re.search(r'☑️\s+(.+?):\s+Already Available\s+\((\d+)/(\d+)\)', line)
                if match:
                    title = match.group(1).strip()
                    position = match.group(2)
                    total = match.group(3)
                    
                    # Extract timestamp from beginning of line
                    timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    recent_items.append({
                        "title": title,
                        "status": "available",
                        "status_text": "Already Available",
                        "timestamp": timestamp,
                        "position": int(position),
                        "total": int(total)
                    })
                    
            elif '❓' in line and 'Not Found' in line:
                # Extract: "❓ Star Wars: Andor: Not Found (5/10)"
                match = re.search(r'❓\s+(.+?):\s+Not Found\s+\((\d+)/(\d+)\)', line)
                if match:
                    title = match.group(1).strip()
                    position = match.group(2)
                    total = match.group(3)
                    
                    timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    recent_items.append({
                        "title": title,
                        "status": "not_found",
                        "status_text": "Not Found",
                        "timestamp": timestamp,
                        "position": int(position),
                        "total": int(total)
                    })
                    
            elif '✅' in line and 'Requested' in line:
                # Extract: "✅  Title: Requested (1/10)"
                match = re.search(r'✅\s+(.+?):\s+Requested\s+\((\d+)/(\d+)\)', line)
                if match:
                    title = match.group(1).strip()
                    position = match.group(2)
                    total = match.group(3)
                    
                    timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    recent_items.append({
                        "title": title,
                        "status": "requested",
                        "status_text": "Requested",
                        "timestamp": timestamp,
                        "position": int(position),
                        "total": int(total)
                    })
                    
            elif '⏭️' in line and 'Skipped' in line:
                # Extract: "⏭️  Title: Skipped (1/10)"
                match = re.search(r'⏭️\s+(.+?):\s+Skipped\s+\((\d+)/(\d+)\)', line)
                if match:
                    title = match.group(1).strip()
                    position = match.group(2)
                    total = match.group(3)
                    
                    timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    recent_items.append({
                        "title": title,
                        "status": "skipped",
                        "status_text": "Skipped",
                        "timestamp": timestamp,
                        "position": int(position),
                        "total": int(total)
                    })
        
        # Sort by timestamp (most recent first) and position
        recent_items.sort(key=lambda x: (x['timestamp'] or '', x['position']), reverse=True)
        
        # Calculate pagination
        total_items = len(recent_items)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        # Get paginated items
        paginated_items = recent_items[start_index:end_index]
        
        return {
            "items": paginated_items,
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "log_file_used": log_file_used
        }
        
    except Exception as e:
        return {
            "items": [],
            "total_items": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False,
            "error": f"Failed to parse log file: {str(e)}"
        }

@app.get("/api/activity/recent/docker")
async def get_recent_activity_from_docker(limit: int = Query(10, ge=1, le=100)):
    """Get recent sync activity specifically from Docker logs"""
    try:
        activities = parse_docker_logs_for_activity(limit)
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists")
async def get_lists():
    """Get all configured lists"""
    try:
        lists = load_list_ids()
        
        # Add display names and include item counts, last_synced, and user_id with proper timezone conversion
        formatted_lists = []
        for i, list_item in enumerate(lists):
            # Extract clean display name from list ID (URL)
            list_id = list_item['id']
            list_type = list_item['type']
            
            # Extract just the meaningful part of the URL/ID for display
            if list_id.startswith(('http://', 'https://')):
                # Parse URL to get the last meaningful segment
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(list_id.rstrip('/'))
                    path_parts = [p for p in parsed.path.split('/') if p]
                    
                    # For Trakt URLs like /users/{user}/lists/{name}
                    if 'trakt' in list_type and len(path_parts) >= 4 and 'lists' in path_parts:
                        list_name = path_parts[-1]  # Get the last segment
                    # For other URLs, just get the last segment
                    else:
                        list_name = path_parts[-1] if path_parts else list_id
                    
                    display_name = list_name
                except Exception:
                    display_name = list_id
            else:
                # Not a URL, use as-is
                display_name = list_id
            
            # Convert last_synced timestamp from UTC to local timezone
            last_synced = list_item.get('last_synced')
            if last_synced:
                try:
                    # SQLite CURRENT_TIMESTAMP returns UTC time without timezone info
                    # Parse it as UTC and convert to local timezone
                    from datetime import datetime
                    import zoneinfo
                    from list_sync.utils.timezone_utils import get_timezone_from_env
                    
                    # Parse UTC timestamp
                    utc_dt = datetime.fromisoformat(last_synced).replace(tzinfo=timezone.utc)
                    
                    # Get configured timezone
                    local_tz_name = get_timezone_from_env()
                    local_tz = zoneinfo.ZoneInfo(local_tz_name)
                    
                    # Convert to local timezone
                    local_dt = utc_dt.astimezone(local_tz)
                    
                    # Return as ISO string with timezone info
                    last_synced = local_dt.isoformat()
                except Exception as e:
                    print(f"Error converting timestamp {last_synced}: {e}")
                    # Keep original timestamp as fallback
                    pass
            
            formatted_lists.append({
                "id": i + 1,
                "list_type": list_item['type'],
                "list_id": list_item['id'],
                "list_url": list_item.get('url'),  # Include the stored URL
                "display_name": display_name,
                "item_count": list_item.get('item_count', 0),  # Include item count from database
                "last_synced": last_synced,  # Include converted last_synced timestamp
                "user_id": list_item.get('user_id', '1')  # Include user_id for per-list user assignment
            })
        
        return {"lists": formatted_lists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/debug")
async def get_lists_debug():
    """Get all configured lists with debug information"""
    try:
        lists = load_list_ids()
        # Also get raw database data for debugging
        import sqlite3
        from list_sync.database import DB_FILE
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT list_type, list_id, list_url, item_count, last_synced FROM lists")
            raw_data = cursor.fetchall()
        
        return {
            "lists": lists,
            "total_count": len(lists),
            "raw_database_data": [
                {
                    "list_type": row[0],
                    "list_id": row[1], 
                    "list_url": row[2],
                    "item_count": row[3],
                    "last_synced": row[4]
                }
                for row in raw_data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists")
async def add_list(list_add: ListAdd):
    """Add new list with URL generation and auto-detection of special Trakt lists"""
    try:
        # Import the construct_list_url function
        from list_sync.utils.helpers import construct_list_url
        
        list_type = list_add.list_type
        list_id = list_add.list_id
        user_id = list_add.user_id
        
        # Auto-detect special Trakt lists (trending:movies, popular:shows, etc.)
        if list_type == "trakt" and ':' in list_id:
            parts = list_id.split(':')
            if len(parts) == 2:
                category, media_type = parts
                if media_type.lower() in ['movies', 'movie', 'shows', 'show', 'tv']:
                    list_type = "trakt_special"
                    logging.info(f"Auto-detected special Trakt list: {list_id}")
        
        # Generate the URL for the list
        list_url = construct_list_url(list_type, list_id)
        
        # Save with the generated URL, default item count of 0, and user_id
        save_list_id(list_id, list_type, list_url, item_count=0, user_id=user_id)
        
        return {
            "success": True,
            "message": f"Added {list_type} list: {list_id}",
            "list_url": list_url,
            "item_count": 0,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/{list_type}/{list_id:path}/items")
async def get_list_items_endpoint(list_type: str, list_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get items from a specific list with enriched metadata"""
    try:
        from list_sync.database import get_list_items, DB_FILE
        import sqlite3
        
        items = get_list_items(list_type, list_id)
        
        # Get poster URLs from database
        item_ids = [item['id'] for item in items[:limit]]
        poster_url_map = {}
        
        if item_ids:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    placeholders = ','.join('?' * len(item_ids))
                    cursor.execute(f"SELECT id, poster_url FROM synced_items WHERE id IN ({placeholders})", item_ids)
                    for row in cursor.fetchall():
                        poster_url_map[row[0]] = row[1]
            except Exception as e:
                logging.warning(f"Failed to fetch poster URLs: {e}")
        
        # Enrich items with poster URLs
        limited_items = []
        for item in items[:limit]:
            enriched_item = {
                **item,
                "poster_url": poster_url_map.get(item['id'])
            }
            limited_items.append(enriched_item)
        
        return {
            "items": limited_items,
            "total": len(items),
            "limit": limit,
            "has_more": len(items) > limit
        }
    except Exception as e:
        logging.error(f"Error fetching list items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lists/{list_type}/{list_id:path}")
async def delete_list_endpoint(list_type: str, list_id: str):
    """Delete list - uses :path to capture full URLs with forward slashes"""
    try:
        # FastAPI automatically URL-decodes path parameters, so list_id is already decoded
        # The :path type allows capturing the full path including forward slashes
        # Log the parameters for debugging
        logging.info(f"Delete request - list_type: {list_type}, list_id: {list_id}")
        
        # Try to delete the list
        success = delete_list(list_type, list_id)
        
        if success:
            logging.info(f"Successfully deleted list: {list_type}/{list_id}")
            return {
                "success": True,
                "message": f"Deleted {list_type} list: {list_id}"
            }
        else:
            # List not found - provide helpful error message
            existing_lists = load_list_ids()
            available_lists = [f"{item['type']}: {item['id']}" for item in existing_lists if item['type'] == list_type]
            error_msg = f"List not found: {list_type}/{list_id}"
            if available_lists:
                error_msg += f". Available {list_type} lists: {', '.join(available_lists[:3])}"  # Limit to 3 examples
            logging.warning(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
            
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logging.error(f"Error deleting list {list_type}/{list_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/items")
async def get_items(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100)):
    """Get all synced items (deduplicated)"""
    try:
        unique_items = get_deduplicated_items()
        
        # Calculate pagination
        total = len(unique_items)
        total_pages = (total + limit - 1) // limit
        start = (page - 1) * limit
        end = start + limit
        
        # Sort by last_synced descending
        sorted_items = sorted(unique_items, key=lambda x: x[6], reverse=True)
        page_items = sorted_items[start:end]
        
        items = []
        for item in page_items:
            item_id, title, media_type, year, imdb_id, overseerr_id, status, last_synced, source_list_type, source_list_id = item
            
            # Build list_sources from source columns
            list_sources = []
            if source_list_type and source_list_id:
                list_sources.append({
                    'list_type': source_list_type,
                    'list_id': source_list_id,
                    'display_name': None
                })
            
            items.append({
                "id": item_id,
                "title": title,
                "media_type": media_type,
                "year": year,
                "imdb_id": imdb_id,
                "overseerr_id": overseerr_id,
                "status": status,
                "last_synced": last_synced,
                "list_sources": list_sources
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple in-memory cache for metadata (expires after 1 hour)
_metadata_cache = {}
_cache_ttl = 3600  # 1 hour in seconds

@app.post("/api/items/enriched/clear-cache")
async def clear_enriched_cache():
    """Clear the metadata cache (useful after fixing data issues)"""
    global _metadata_cache
    cache_size = len(_metadata_cache)
    _metadata_cache = {}
    logging.info(f"Cleared metadata cache ({cache_size} entries)")
    return {"message": f"Cleared {cache_size} cached entries", "success": True}

@app.get("/api/items/enriched")
async def get_enriched_items(
    page: int = Query(1, ge=1), 
    limit: int = Query(50, ge=1, le=100),
    list_source: str = Query("", description="Filter by list source in format 'list_type:list_id'")
):
    """Get synced items enriched with Trakt metadata (poster, rating, etc.)"""
    try:
        from list_sync.providers.trakt import get_trakt_metadata
        from list_sync.database import DB_FILE
        import time
        
        # Debug: Check item_lists table
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM item_lists")
                item_lists_count = cursor.fetchone()[0]
                logging.info(f"📊 item_lists table has {item_lists_count} entries")
        except Exception as e:
            logging.warning(f"Could not check item_lists table: {e}")
        
        # Get base items (deduplicated)
        unique_items = get_deduplicated_items()
        
        # Filter by list source if specified (before pagination)
        # Filter directly using source_list_type and source_list_id columns from synced_items
        if list_source and list_source.strip():
            try:
                filter_list_type, filter_list_id = list_source.split(':', 1)
                
                # Normalize the list_id to match what's stored in database
                normalized_list_id = normalize_list_id(filter_list_type, filter_list_id)
                
                logging.info(f"📋 Filtering by list {filter_list_type}:{filter_list_id} (normalized: {normalized_list_id})")
                
                # Filter items where source_list_type and source_list_id match
                # Item tuple: (id, title, media_type, year, imdb_id, overseerr_id, status, last_synced, source_list_type, source_list_id)
                before_count = len(unique_items)
                unique_items = [
                    item for item in unique_items 
                    if (item[8] == filter_list_type and 
                        (item[9] == normalized_list_id or item[9] == filter_list_id))
                ]
                
                logging.info(f"📋 Filtered {before_count} items → {len(unique_items)} items match list {filter_list_type}:{filter_list_id}")
            except ValueError:
                # Invalid list_source format, ignore filter
                logging.warning(f"Invalid list_source format: {list_source}, ignoring filter")
        
        # Calculate pagination on filtered items
        total = len(unique_items)
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        start = (page - 1) * limit
        end = start + limit
        
        # Sort by last_synced descending (most recently synced first)
        # Handle None values by putting them at the end
        sorted_items = sorted(
            unique_items, 
            key=lambda x: x[7] if x[7] is not None else '', 
            reverse=True
        )
        page_items = sorted_items[start:end]
        
        # Get overseerr URL for constructing links
        config_tuple = load_env_config()
        overseerr_url = config_tuple[0] if config_tuple else None
        
        # Batch fetch tmdb_ids, poster URLs, and list sources from database (more efficient)
        item_ids = [item[0] for item in page_items]
        tmdb_id_map = {}
        poster_url_map = {}
        item_lists_map = {}  # Map item_id to list of lists it belongs to

        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(item_ids))
                
                # Fetch tmdb_ids and poster URLs
                cursor.execute(f"SELECT id, tmdb_id, poster_url FROM synced_items WHERE id IN ({placeholders})", item_ids)
                for row in cursor.fetchall():
                    item_db_id, tmdb_id, poster_url = row
                    if tmdb_id:
                        try:
                            # Handle both string and int tmdb_ids
                            tmdb_id_map[item_db_id] = int(tmdb_id) if isinstance(tmdb_id, str) else tmdb_id
                        except (ValueError, TypeError):
                            logging.warning(f"Invalid tmdb_id format for item {item_db_id}: {tmdb_id}")
                    poster_url_map[item_db_id] = poster_url
                
                # Batch fetch list sources for all items
                # Check if display_name column exists in lists table
                cursor.execute("PRAGMA table_info(lists)")
                list_columns = [col[1] for col in cursor.fetchall()]
                has_display_name = 'display_name' in list_columns
                
                if has_display_name:
                    cursor.execute(f'''
                        SELECT il.item_id, il.list_type, il.list_id, l.display_name
                        FROM item_lists il
                        LEFT JOIN lists l ON il.list_type = l.list_type AND il.list_id = l.list_id
                        WHERE il.item_id IN ({placeholders})
                        ORDER BY il.synced_at DESC
                    ''', item_ids)
                else:
                    # Fallback: Don't join lists table, just get list_type and list_id
                    cursor.execute(f'''
                        SELECT il.item_id, il.list_type, il.list_id, NULL as display_name
                        FROM item_lists il
                        WHERE il.item_id IN ({placeholders})
                        ORDER BY il.synced_at DESC
                    ''', item_ids)
                
                for row in cursor.fetchall():
                    item_db_id, list_type, list_id, display_name = row
                    if item_db_id not in item_lists_map:
                        item_lists_map[item_db_id] = []
                    item_lists_map[item_db_id].append({
                        'list_type': list_type,
                        'list_id': list_id,
                        'display_name': display_name
                    })
                
                # Debug: Log how many items have list sources
                items_with_sources = len([k for k, v in item_lists_map.items() if v])
                logging.info(f"📦 Fetched list_sources for {items_with_sources}/{len(item_ids)} items")
                if items_with_sources > 0:
                    sample_item = next((k for k, v in item_lists_map.items() if v), None)
                    if sample_item:
                        logging.info(f"📋 Sample: Item {sample_item} has {len(item_lists_map[sample_item])} list(s): {item_lists_map[sample_item]}")
        except Exception as e:
            logging.warning(f"Failed to batch fetch tmdb_ids, poster URLs, and list sources: {e}")
        
        enriched_items = []
        current_time = time.time()
        
        for item in page_items:
            item_id, title, media_type, year, imdb_id, overseerr_id, status, last_synced, source_list_type, source_list_id = item
            
            # Get tmdb_id and poster_url from batch fetch
            tmdb_id = tmdb_id_map.get(item_id)
            cached_poster_url = poster_url_map.get(item_id)

            # Get list sources for this item (from item_lists join table for multi-list support)
            list_sources = item_lists_map.get(item_id, [])
            
            # If no list sources from item_lists, use the source_list columns as fallback
            if not list_sources and source_list_type and source_list_id:
                list_sources = [{
                    'list_type': source_list_type,
                    'list_id': source_list_id,
                    'display_name': None
                }]
            
            # Create base enriched item
            enriched_item = {
                "id": item_id,
                "title": title,
                "media_type": media_type,
                "year": year,
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id,
                "overseerr_id": overseerr_id,
                "status": status,
                "last_synced": last_synced,
                "poster_url": cached_poster_url,  # Use cached poster URL if available
                "rating": None,
                "overview": None,
                "genres": [],
                "overseerr_url": None,
                "list_sources": list_sources  # Add list sources
            }
            
            # Construct Overseerr URL if available
            if overseerr_id and overseerr_url:
                media_type_path = "tv" if media_type == "tv" else "movie"
                enriched_item["overseerr_url"] = f"{overseerr_url.rstrip('/')}/{media_type_path}/{overseerr_id}"
            
            # Skip enrichment if no IDs available
            if not tmdb_id and not imdb_id:
                enriched_items.append(enriched_item)
                continue
            
            # Try to enrich with metadata from cache or API
            cache_key = f"{media_type}_{tmdb_id or imdb_id}"
            
            # Check if we have a cached poster URL from database
            if cached_poster_url:
                # We already have the poster URL, no need to fetch metadata
                enriched_items.append(enriched_item)
                continue

            # Check metadata cache
            if cache_key in _metadata_cache:
                cached_data, cache_time = _metadata_cache[cache_key]
                if current_time - cache_time < _cache_ttl:
                    # Use cached data
                    poster_url = cached_data.get("poster_url")
                    if poster_url:
                        from list_sync.database import update_item_poster_url
                        update_item_poster_url(item_id, poster_url)

                    enriched_item.update({
                        "poster_url": poster_url,
                        "rating": cached_data.get("rating"),
                        "overview": cached_data.get("overview"),
                        "genres": cached_data.get("genres", [])
                    })
                    enriched_items.append(enriched_item)
                    continue
            
            # Fetch from API if not in cache or cache expired
            try:
                metadata = get_trakt_metadata(
                    tmdb_id=tmdb_id,
                    imdb_id=imdb_id,
                    media_type=media_type
                )
                
                if metadata:
                    # Cache the metadata (even if some fields are None)
                    _metadata_cache[cache_key] = (metadata, current_time)

                    # Store poster URL in database for this item
                    poster_url = metadata.get("poster_url")
                    if poster_url:
                        from list_sync.database import update_item_poster_url
                        update_item_poster_url(item_id, poster_url)

                    # Enrich item
                    enriched_item.update({
                        "poster_url": poster_url,
                        "rating": metadata.get("rating"),
                        "overview": metadata.get("overview"),
                        "genres": metadata.get("genres", [])
                    })
                else:
                    # Cache negative result to avoid repeated failed lookups
                    _metadata_cache[cache_key] = ({}, current_time)
            except Exception as e:
                logging.warning(f"Failed to enrich item '{title}' (ID: {item_id}): {e}")
                # Cache the error to avoid repeated attempts
                _metadata_cache[cache_key] = ({}, current_time)
            
            enriched_items.append(enriched_item)
        
        return {
            "items": enriched_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logging.error(f"Error in enriched items endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/overseerr/status")
async def get_overseerr_status():
    """Check Overseerr connection status"""
    try:
        # Load environment configuration - returns a tuple
        config_tuple = load_env_config()
        overseerr_url, overseerr_api_key, user_id, sync_interval, automated_mode, is_4k = config_tuple
        
        if not overseerr_url or not overseerr_api_key:
            return {
                "isConnected": False,
                "error": "Overseerr URL or API key not configured",
                "lastChecked": datetime.now().isoformat()
            }
        
        # Make request to Overseerr status endpoint
        headers = {
            'X-Api-Key': overseerr_api_key,
            'Content-Type': 'application/json'
        }
        
        # Clean URL and add status endpoint
        base_url = overseerr_url.rstrip('/')
        status_url = f"{base_url}/api/v1/status"
        
        response = requests.get(status_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            return {
                "isConnected": True,
                "version": status_data.get("version", "Unknown"),
                "updateAvailable": status_data.get("updateAvailable", False),
                "commitsBehind": status_data.get("commitsBehind", 0),
                "restartRequired": status_data.get("restartRequired", False),
                "lastChecked": datetime.now().isoformat()
            }
        else:
            return {
                "isConnected": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "lastChecked": datetime.now().isoformat()
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "isConnected": False,
            "error": f"Connection error: {str(e)}",
            "lastChecked": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "isConnected": False,
            "error": f"Unexpected error: {str(e)}",
            "lastChecked": datetime.now().isoformat()
        }

@app.get("/api/system/time")
async def get_current_time():
    """Get current server time with enhanced timezone support"""
    try:
        # Get comprehensive timezone info using our utilities
        tz_info = get_current_timezone_info()
        
        # Parse the timezone-aware datetime
        current_time = datetime.fromisoformat(tz_info["current_time"])
        
        return {
            "current_time": tz_info["current_time"],
            "timestamp": current_time.timestamp(),
            "timezone": {
                "name": tz_info["timezone_name"],
                "abbreviation": tz_info["timezone_abbreviation"],
                "utc_offset": tz_info["utc_offset"],
                "is_dst": tz_info["is_dst"]
            },
            "formatted": {
                "date": current_time.strftime("%a, %b %d"),
                "time": current_time.strftime("%I:%M %p"),
                "full": tz_info["formatted_time"],
                "iso": tz_info["current_time"]
            }
        }
    except Exception as e:
        # Fallback to basic datetime if timezone utilities fail
        now = datetime.now()
        return {
            "current_time": now.isoformat(),
            "timestamp": now.timestamp(),
            "timezone": {
                "name": "UTC",
                "abbreviation": "UTC", 
                "utc_offset": "+0000",
                "is_dst": False
            },
            "formatted": {
                "date": now.strftime("%a, %b %d"),
                "time": now.strftime("%I:%M %p"),
                "full": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "iso": now.isoformat()
            },
            "error": str(e)
        }

@app.post("/api/sync/trigger")
async def trigger_manual_sync(sync_request: dict = None):
    """Trigger a manual sync by sending SIGUSR1 signal to ListSync process"""
    try:
        from list_sync.utils.sync_status import clear_pause_until
        # Parse request body if provided
        sync_type = "all"  # default
        target_list = None
        
        if sync_request:
            # CRITICAL: Check for direct list_type/list_id FIRST (from our web UI)
            # This ensures single list sync requests are detected correctly
            if sync_request.get("list_type") and sync_request.get("list_id"):
                target_list = {
                    "list_type": sync_request["list_type"],
                    "list_id": sync_request["list_id"]
                }
                sync_type = "single"
                print(f"DEBUG - Detected single list sync request: {target_list}")
            else:
                # Check for explicit type field or nested list object
                sync_type = sync_request.get("type", "all")  # "all", "single"
                target_list = sync_request.get("list", None)  # {list_type: "imdb", list_id: "top"}
                
                # If type is "single" but target_list is not set, try to extract from list object
                if sync_type == "single" and target_list:
                    if isinstance(target_list, dict) and "list_type" in target_list and "list_id" in target_list:
                        # Already in correct format
                        pass
                    else:
                        print(f"WARNING - Single sync type specified but target_list format is invalid: {target_list}")
        
        # Validation: If we have target_list but sync_type is not "single", correct it
        if target_list and sync_type != "single":
            print(f"WARNING - target_list detected but sync_type is '{sync_type}', correcting to 'single'")
            sync_type = "single"
        
        print(f"DEBUG - Sync request parsed: type={sync_type}, target={target_list}, raw_request={sync_request}")
        
        # Find ListSync processes
        processes = find_listsync_processes()
        
        if not processes:
            raise HTTPException(
                status_code=404, 
                detail="No ListSync process found. Please ensure ListSync is running in automated mode."
            )
        
        # For single list sync, create a request file
        if sync_type == "single" and target_list:
            import os
            import json
            import uuid
            
            print(f"DEBUG - Creating single list sync request file for: {target_list}")
            
            # Create the request data
            request_data = {
                "list_type": target_list["list_type"],
                "list_id": target_list["list_id"],
                "timestamp": datetime.now().isoformat(),
                "requested_by": "web_ui"
            }
            
            # Ensure data directory exists
            os.makedirs("data/sync_requests", exist_ok=True)
            
            # Use a unique filename with timestamp and UUID to prevent overwrites
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            request_file = f"data/sync_requests/single_sync_{timestamp_str}_{unique_id}.json"
            
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2)
            
            print(f"DEBUG - Single list sync request file created: {request_file}")
            
            # Also maintain the legacy single file for backwards compatibility
            legacy_file = "data/single_list_sync_request.json"
            with open(legacy_file, 'w') as f:
                json.dump(request_data, f, indent=2)
            
            # Also set environment variables as fallback (though these may not persist across processes)
            os.environ["SINGLE_LIST_SYNC"] = "true"
            os.environ["SINGLE_LIST_TYPE"] = target_list["list_type"]
            os.environ["SINGLE_LIST_ID"] = target_list["list_id"]
            
            print(f"DEBUG - Environment variables set as fallback: SINGLE_LIST_SYNC=true, SINGLE_LIST_TYPE={target_list['list_type']}, SINGLE_LIST_ID={target_list['list_id']}")
        else:
            # Clear any existing single list request file for full sync
            import os
            request_file = "data/single_list_sync_request.json"
            if os.path.exists(request_file):
                os.remove(request_file)
                print(f"DEBUG - Removed existing single list sync request file")
            
            # Clear single list environment variables for full sync
            os.environ.pop("SINGLE_LIST_SYNC", None)
            os.environ.pop("SINGLE_LIST_TYPE", None)
            os.environ.pop("SINGLE_LIST_ID", None)
            print(f"DEBUG - Cleared single list environment variables for full sync")
        
        # Clear any pause (e.g., set after cancellation) so manual trigger runs immediately
        try:
            clear_pause_until()
        except Exception as e:
            print(f"WARNING - Could not clear pause before manual sync: {e}")
        
        # Send SIGUSR1 signal to trigger sync (works for both single and full)
        signals_sent = []
        errors = []
        
        for process in processes:
            try:
                # Send SIGUSR1 signal to trigger immediate sync
                os.kill(process.pid, signal.SIGUSR1)
                signals_sent.append({
                    "pid": process.pid,
                    "cmdline": process.cmdline,
                    "status": "signal_sent"
                })
                print(f"Sent SIGUSR1 signal to ListSync process PID {process.pid}")
                
            except ProcessLookupError:
                errors.append({
                    "pid": process.pid,
                    "error": "Process not found (may have exited)"
                })
            except PermissionError:
                errors.append({
                    "pid": process.pid,
                    "error": "Permission denied (insufficient privileges)"
                })
            except Exception as e:
                errors.append({
                    "pid": process.pid,
                    "error": str(e)
                })
        
        if not signals_sent and errors:
            # All signals failed
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send signals to any ListSync process: {errors}"
            )
        
        return {
            "success": True,
            "sync_type": sync_type,
            "target_list": target_list if sync_type == "single" else None,
            "message": f"Manual {sync_type} sync triggered successfully for {len(signals_sent)} process(es)",
            "signals_sent": signals_sent,
            "errors": errors if errors else None,
            "note": "Sync should start immediately if ListSync is running in automated mode",
            "method": "file_based" if sync_type == "single" else "signal_only",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error triggering manual sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _run_sync_in_subprocess(list_type: str, list_id: str, overseerr_url: str, 
                            overseerr_api_key: str, is_4k: bool, result_queue: multiprocessing.Queue):
    """
    Worker function to run sync in a subprocess.
    This function is called by multiprocessing.Process.
    """
    try:
        # Import inside subprocess to avoid issues
        from list_sync.main import sync_single_list
        from list_sync.utils.sync_status import get_sync_tracker
        
        # Set the subprocess PID in the tracker
        sync_tracker = get_sync_tracker()
        sync_tracker.set_subprocess_pid(os.getpid())
        
        result = sync_single_list(
            list_type,
            list_id,
            overseerr_url,
            overseerr_api_key,
            None,  # Let sync_single_list fetch user_id from list's database record
            is_4k
        )
        result_queue.put({"success": True, "result": result})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})


async def trigger_single_list_sync(target_list: dict, processes: list):
    """Trigger sync for a single specific list using a terminable subprocess"""
    try:
        import tempfile
        
        list_type = target_list.get("list_type")
        list_id = target_list.get("list_id")
        
        if not list_type or not list_id:
            raise HTTPException(
                status_code=400,
                detail="Both list_type and list_id are required for single list sync"
            )
        
        print(f"DEBUG - Starting single list sync for {list_type}:{list_id}")
        
        # Create a temporary configuration for single list sync
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_config = {
                "single_list_sync": True,
                "target_list": {
                    "type": list_type,
                    "id": list_id
                },
                "timestamp": datetime.now().isoformat()
            }
            json.dump(temp_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            print(f"DEBUG - Attempting to import sync functions...")
            
            # Import the config loader
            from list_sync.config import load_env_config
            from list_sync.utils.sync_status import get_sync_tracker
            
            print(f"DEBUG - Import successful, loading environment config...")
            
            # Load environment configuration
            overseerr_url, overseerr_api_key, _, sync_interval, automated_mode, is_4k = load_env_config()
            
            print(f"DEBUG - Environment loaded. URL: {overseerr_url[:20] if overseerr_url else 'None'}...")
            print(f"DEBUG - Starting sync in subprocess for immediate termination support...")
            
            # Create a queue to receive results from subprocess
            result_queue = multiprocessing.Queue()
            
            # Create and start subprocess
            sync_process = multiprocessing.Process(
                target=_run_sync_in_subprocess,
                args=(list_type, list_id, overseerr_url, overseerr_api_key, is_4k, result_queue)
            )
            sync_process.start()
            subprocess_pid = sync_process.pid
            
            print(f"DEBUG - Sync subprocess started with PID {subprocess_pid}")
            
            # Register the subprocess PID in the tracker for immediate cancellation
            sync_tracker = get_sync_tracker()
            sync_tracker.set_subprocess_pid(subprocess_pid)
            
            # Wait for the subprocess with polling to allow for cancellation
            timeout_seconds = 3600  # 1 hour timeout for long syncs
            poll_interval = 0.5  # Check every 0.5 seconds
            elapsed = 0
            
            while sync_process.is_alive() and elapsed < timeout_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                # Check if cancellation was requested
                if sync_tracker.is_cancellation_requested():
                    print(f"DEBUG - Cancellation requested, terminating subprocess {subprocess_pid}")
                    sync_process.terminate()
                    sync_process.join(timeout=2)
                    if sync_process.is_alive():
                        sync_process.kill()
                    sync_tracker.end_sync()
                    return {
                        "success": False,
                        "sync_type": "single",
                        "target_list": target_list,
                        "message": f"Sync cancelled by user for {list_type}:{list_id}",
                        "cancelled": True,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Check if process timed out
            if sync_process.is_alive():
                print(f"ERROR - Sync timed out after {timeout_seconds} seconds, terminating...")
                sync_process.terminate()
                sync_process.join(timeout=2)
                if sync_process.is_alive():
                    sync_process.kill()
                sync_tracker.end_sync()
                return {
                    "success": False,
                    "sync_type": "single",
                    "target_list": target_list,
                    "message": f"Single list sync timed out for {list_type}:{list_id}",
                    "error": f"Sync operation timed out after {timeout_seconds} seconds",
                    "fallback_suggestion": "Try using 'Sync All Lists' or check if the list URL is accessible",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process completed, get result
            try:
                result_data = result_queue.get_nowait()
                if result_data.get("success"):
                    print(f"DEBUG - Sync completed successfully: {result_data.get('result')}")
                    return {
                        "success": True,
                        "sync_type": "single",
                        "target_list": target_list,
                        "message": f"Single list sync completed for {list_type}:{list_id}",
                        "result": result_data.get("result"),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    print(f"ERROR - Sync failed: {result_data.get('error')}")
                    return {
                        "success": False,
                        "sync_type": "single",
                        "target_list": target_list,
                        "message": f"Single list sync failed for {list_type}:{list_id}",
                        "error": result_data.get("error"),
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as queue_error:
                print(f"ERROR - Could not get result from queue: {queue_error}")
                # Process exited but no result - check exit code
                exit_code = sync_process.exitcode
                if exit_code == 0:
                    return {
                        "success": True,
                        "sync_type": "single",
                        "target_list": target_list,
                        "message": f"Single list sync completed for {list_type}:{list_id}",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "sync_type": "single",
                        "target_list": target_list,
                        "message": f"Single list sync failed for {list_type}:{list_id}",
                        "error": f"Process exited with code {exit_code}",
                        "timestamp": datetime.now().isoformat()
                    }
            
        except ImportError as e:
            print(f"ERROR - Import failed: {e}")
            # Fallback: If direct import fails, use signal with temp file approach
            print("Direct sync import failed, falling back to signal method")
            
            # Try to trigger full sync instead
            try:
                for process in processes:
                    os.kill(process.pid, signal.SIGUSR1)
                    print(f"Sent SIGUSR1 signal to process {process.pid} as fallback")
                
                return {
                    "success": True,
                    "sync_type": "fallback_full_sync",
                    "target_list": target_list,
                    "message": "Single list sync not available, triggered full sync instead",
                    "note": "The single list feature isn't fully implemented. A full sync has been triggered.",
                    "fallback_action": "triggered_full_sync",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as signal_error:
                print(f"ERROR - Signal fallback also failed: {signal_error}")
                return {
                    "success": False,
                    "sync_type": "single",
                    "target_list": target_list,
                    "message": "Single list sync not yet implemented in core application",
                    "note": "Both direct sync and signal fallback failed. Please use 'Sync All Lists' instead.",
                    "error": str(signal_error),
                    "timestamp": datetime.now().isoformat()
                }
            
        except Exception as sync_error:
            print(f"ERROR - Sync execution failed: {sync_error}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "sync_type": "single",
                "target_list": target_list,
                "message": f"Single list sync failed for {list_type}:{list_id}",
                "error": str(sync_error),
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"CRITICAL ERROR in single list sync: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Single list sync failed: {str(e)}")

@app.post("/api/sync/single")
async def trigger_single_list_sync_endpoint(sync_request: dict):
    """Endpoint for single list sync requests - redirects to main trigger endpoint"""
    # Redirect to the main trigger endpoint with the same payload
    return await trigger_manual_sync(sync_request)

@app.get("/api/sync/status")
async def get_sync_status():
    """Get current sync status and process information"""
    try:
        # Find ListSync processes
        processes = find_listsync_processes()
        
        process_info = []
        for process in processes:
            try:
                # Get additional process info
                proc = psutil.Process(process.pid)
                process_info.append({
                    "pid": process.pid,
                    "status": process.status,
                    "created": process.created,
                    "cmdline": process.cmdline,
                    "memory_percent": proc.memory_percent(),
                    "cpu_percent": proc.cpu_percent(),
                    "can_signal": True  # Assume we can signal unless we find otherwise
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                process_info.append({
                    "pid": process.pid,
                    "status": "unknown",
                    "created": process.created,
                    "cmdline": process.cmdline,
                    "error": str(e),
                    "can_signal": False
                })
        
        return {
            "processes_found": len(processes),
            "processes": process_info,
            "can_trigger_sync": len(processes) > 0,
            "sync_method": "signal" if len(processes) > 0 else "none",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync/{job_id}/cancel")
async def cancel_sync(job_id: str):
    """Cancel a running sync - first gracefully via cancellation flag, then forcefully if needed"""
    try:
        from list_sync.utils.sync_status import (
            get_sync_tracker,
            set_cancel_request,
            clear_cancel_request,
            set_pause_until
        )
        from list_sync.database import DB_FILE, get_current_sync_status, end_sync_in_db, load_sync_interval
        import asyncio
        import psutil
        import signal
        from datetime import datetime, timedelta
        
        sync_tracker = get_sync_tracker()
        
        # Get current sync state from DATABASE (same source as /api/sync/status/live)
        # This ensures cancel endpoint uses the same logic as the live status endpoint
        db_sync_status = get_current_sync_status()
        is_running = db_sync_status and db_sync_status.get('in_progress') == 1
        
        if not is_running:
            return {
                "success": False,
                "message": "No sync is currently running",
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract sync info from database
        session_id = db_sync_status.get('session_id')
        
        # Prefer subprocess PID (actual worker); avoid killing parent to prevent restarts
        tracker_state = sync_tracker.get_state()
        target_pid = tracker_state.get("sync_subprocess_pid")
        if not target_pid:
            # Fallback to DB pid only if tracker not set
            target_pid = db_sync_status.get('pid')
        
        termination_method = None
        terminated = False
        
        # Set cross-process cancel flag
        if session_id:
            set_cancel_request(session_id)
        
        # Resolve target PID; fallback to detected worker processes if needed
        if not target_pid or not psutil.pid_exists(target_pid):
            processes = find_listsync_processes()
            for proc in processes:
                if psutil.pid_exists(proc.pid):
                    target_pid = proc.pid
                    break
        
        # Always try to send SIGTERM immediately to the running sync process (different process than API)
        if target_pid:
            try:
                import os
                import signal as sig
                os.kill(target_pid, sig.SIGTERM)
                termination_method = "SIGTERM"
                logging.info(f"Sent SIGTERM to sync process PID {target_pid}")
            except Exception as e:
                logging.error(f"Failed to send SIGTERM to PID {target_pid}: {e}")
        
            # Poll for exit, escalate if needed
            for i in range(10):  # up to ~5s
                await asyncio.sleep(0.5)
                if not psutil.pid_exists(target_pid):
                    terminated = True
                    break
            if not terminated and hasattr(signal, "SIGKILL"):
                try:
                    os.kill(target_pid, signal.SIGKILL)
                    termination_method = "SIGKILL"
                    logging.warning(f"Sent SIGKILL to sync process PID {target_pid}")
                except Exception as e:
                    logging.error(f"Failed to send SIGKILL to PID {target_pid}: {e}")
                # Final short wait
                for i in range(6):
                    await asyncio.sleep(0.5)
                    if not psutil.pid_exists(target_pid):
                        terminated = True
                        break
            elif not terminated:
                termination_method = termination_method or "SIGTERM"
        else:
            logging.error("No valid target PID found for cancellation")
        
        # Mark cancellation in DB only if we have session_id
        if session_id:
            try:
                end_sync_in_db(
                    session_id=session_id,
                    status='cancelled',
                    total_items=db_sync_status.get('total_items', 0) or 0,
                    items_requested=db_sync_status.get('items_requested', 0) or 0,
                    items_skipped=db_sync_status.get('items_skipped', 0) or 0,
                    items_errors=db_sync_status.get('items_errors', 0) or 0,
                    error_message="Cancelled via /cancel endpoint"
                )
                clear_cancel_request(session_id)
                logging.info(f"Marked sync session {session_id} as cancelled in database")
            except Exception as e:
                logging.error(f"Error updating database for cancelled sync: {e}")
            
            # Set pause-until based on current interval to avoid immediate restart
            pause_until = None
            try:
                interval_hours = load_sync_interval()
                if interval_hours <= 0:
                    interval_hours = 1  # safe minimum
                pause_until = datetime.utcnow() + timedelta(hours=interval_hours)
                set_pause_until(pause_until.isoformat())
                logging.info(f"⏸️  Pausing automated syncs until {pause_until.isoformat()} after cancellation")
            except Exception as e:
                logging.warning(f"Could not set pause after cancellation: {e}")
        
        # Clear tracker state locally
        sync_tracker.end_sync()
        
        return {
            "success": terminated,
            "message": "Sync cancelled" if terminated else "Cancellation requested; process may still be shutting down",
            "job_id": job_id,
            "terminated": terminated,
            "termination_method": termination_method,
            "target_pid": target_pid,
            "session_id": session_id,
            "pause_until": pause_until.isoformat() if session_id and 'pause_until' in locals() and pause_until else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error canceling sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel sync: {str(e)}")

@app.get("/api/failures")
async def get_failures(
    page: int = Query(1, ge=1), 
    limit: int = Query(50, ge=1, le=100),
    search: str = Query("", description="Search term to filter items by title"),
    failure_type_filter: str = Query("", description="Filter by failure type (not_found/error)"),
    media_type_filter: str = Query("", description="Filter by media type (movie/tv)")
):
    """Get all failures from historic log data with search/filter and pagination"""
    try:
        failures = parse_failures_from_logs()
        
        # Combine all failures with type indicator
        all_failures = []
        
        # Add not_found items
        for item in failures["not_found"]:
            item_with_type = item.copy()
            item_with_type["failure_type"] = "not_found"
            # Map 'name' to 'title' for frontend compatibility
            if "name" in item_with_type and "title" not in item_with_type:
                item_with_type["title"] = item_with_type["name"]
            # Add missing fields for frontend
            item_with_type["media_type"] = item_with_type.get("media_type", "movie")
            item_with_type["year"] = item_with_type.get("year")
            item_with_type["error_type"] = "not_found"
            item_with_type["error_message"] = item_with_type.get("error_details", "Not found in database")
            item_with_type["retryable"] = False
            item_with_type["failed_at"] = item_with_type.get("timestamp", "")
            all_failures.append(item_with_type)
        
        # Add error items
        for item in failures["errors"]:
            item_with_type = item.copy()
            item_with_type["failure_type"] = "error"
            # Map 'name' to 'title' for frontend compatibility
            if "name" in item_with_type and "title" not in item_with_type:
                item_with_type["title"] = item_with_type["name"]
            # Add missing fields for frontend
            item_with_type["media_type"] = item_with_type.get("media_type", "movie")
            item_with_type["year"] = item_with_type.get("year")
            item_with_type["error_type"] = "error"
            item_with_type["error_message"] = item_with_type.get("error_details", "Processing error")
            item_with_type["retryable"] = True
            item_with_type["failed_at"] = item_with_type.get("timestamp", "")
            all_failures.append(item_with_type)
        
        # Apply filters BEFORE pagination
        filtered_failures = all_failures
        
        # Search filter (case-insensitive title search)
        if search.strip():
            search_term = search.strip().lower()
            filtered_failures = [
                item for item in filtered_failures 
                if search_term in item.get("title", item.get("name", "")).lower()
            ]
        
        # Failure type filter
        if failure_type_filter.strip():
            filtered_failures = [
                item for item in filtered_failures 
                if item["failure_type"] == failure_type_filter
            ]
        
        # Media type filter
        if media_type_filter.strip():
            filtered_failures = [
                item for item in filtered_failures 
                if item["media_type"] == media_type_filter
            ]
        
        # Sort by timestamp (most recent first)
        def sort_key(item):
            try:
                if item.get("timestamp"):
                    return datetime.fromisoformat(item["timestamp"].replace('Z', '+00:00')).timestamp()
                else:
                    return 0
            except:
                return 0
        
        filtered_failures.sort(key=sort_key, reverse=True)
        
        # Calculate pagination on filtered results
        total_items = len(filtered_failures)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start = (page - 1) * limit
        end = start + limit
        
        # Get paginated items from filtered results
        paginated_failures = filtered_failures[start:end]
        
        # Separate back into categories for response
        paginated_not_found = [item for item in paginated_failures if item["failure_type"] == "not_found"]
        paginated_errors = [item for item in paginated_failures if item["failure_type"] == "error"]
        
        # Remove the failure_type field from response items
        for item in paginated_not_found:
            item.pop("failure_type", None)
        for item in paginated_errors:
            item.pop("failure_type", None)
        
        return {
            "not_found": paginated_not_found,
            "errors": paginated_errors,
            "total_failures": failures["total_failures"],
            "filtered_count": total_items,  # Count after filtering
            "last_sync_time": failures["last_sync_time"],
            "log_file_exists": failures["log_file_exists"],
            "filters": {
                "search": search,
                "failure_type_filter": failure_type_filter,
                "media_type_filter": media_type_filter
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_items,  # Use filtered count for pagination
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        print(f"Error parsing failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processed")
async def get_processed_items(
    page: int = Query(1, ge=1), 
    limit: int = Query(50, ge=1, le=100),
    search: str = Query("", description="Search term to filter items by title"),
    status_filter: str = Query("", description="Filter by status"),
    media_type_filter: str = Query("", description="Filter by media type (movie/tv)"),
    list_source: str = Query("", description="Filter by list source in format 'list_type:list_id'")
):
    """Get all processed items from historic log data with search/filter and pagination"""
    try:
        historic_data = parse_historic_items_from_logs()
        all_items = historic_data["total_processed"]
        
        # Enrich with database information for Overseerr/IMDb links
        all_items = enrich_historic_data_with_database(all_items)
        
        # Get Overseerr base URL for generating item links
        try:
            overseerr_base_url, _, _, _, _, _ = load_env_config()
            overseerr_base_url = overseerr_base_url.rstrip('/') if overseerr_base_url else None
        except:
            overseerr_base_url = None
        
        # Batch fetch list sources for all items (before filtering)
        item_ids = [item.get('id') for item in all_items if item.get('id')]
        item_lists_map = {}  # Map item_id to list of lists it belongs to
        
        if item_ids:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    placeholders = ','.join('?' * len(item_ids))
                    
                    # Batch fetch list sources for all items
                    # Check if display_name column exists in lists table
                    cursor.execute("PRAGMA table_info(lists)")
                    list_columns = [col[1] for col in cursor.fetchall()]
                    has_display_name = 'display_name' in list_columns
                    
                    if has_display_name:
                        cursor.execute(f'''
                            SELECT il.item_id, il.list_type, il.list_id, l.display_name
                            FROM item_lists il
                            LEFT JOIN lists l ON il.list_type = l.list_type AND il.list_id = l.list_id
                            WHERE il.item_id IN ({placeholders})
                            ORDER BY il.synced_at DESC
                        ''', item_ids)
                    else:
                        # Fallback: Don't join lists table, just get list_type and list_id
                        cursor.execute(f'''
                            SELECT il.item_id, il.list_type, il.list_id, NULL as display_name
                            FROM item_lists il
                            WHERE il.item_id IN ({placeholders})
                            ORDER BY il.synced_at DESC
                        ''', item_ids)
                    
                    for row in cursor.fetchall():
                        item_db_id, list_type, list_id, display_name = row
                        if item_db_id not in item_lists_map:
                            item_lists_map[item_db_id] = []
                        item_lists_map[item_db_id].append({
                            'list_type': list_type,
                            'list_id': list_id,
                            'display_name': display_name
                        })
            except Exception as e:
                logging.warning(f"Failed to batch fetch list sources: {e}")
        
        # Add overseerr_url and list_sources to items
        for item in all_items:
            if overseerr_base_url and item.get('overseerr_id'):
                item['overseerr_url'] = f"{overseerr_base_url}/{item['media_type']}/{item['overseerr_id']}"
            else:
                item['overseerr_url'] = None
            
            # Add list sources from item_lists table
            item_id = item.get('id')
            item['list_sources'] = item_lists_map.get(item_id, [])
            
            # If no list sources from item_lists, use the source_list columns as fallback
            if not item['list_sources'] and item.get('source_list_type') and item.get('source_list_id'):
                item['list_sources'] = [{
                    'list_type': item['source_list_type'],
                    'list_id': item['source_list_id'],
                    'display_name': None
                }]
        
        # Apply filters BEFORE pagination
        filtered_items = all_items
        
        # Search filter (case-insensitive title search)
        if search.strip():
            search_term = search.strip().lower()
            filtered_items = [
                item for item in filtered_items 
                if search_term in item["title"].lower()
            ]
        
        # Status filter
        if status_filter.strip():
            filtered_items = [
                item for item in filtered_items 
                if item["status"] == status_filter
            ]
        
        # Media type filter
        if media_type_filter.strip():
            filtered_items = [
                item for item in filtered_items 
                if item["media_type"] == media_type_filter
            ]
        
        # List source filter
        if list_source and list_source.strip():
            try:
                filter_list_type, filter_list_id = list_source.split(':', 1)
                
                # Normalize the list_id to match what's stored in item_lists table
                normalized_list_id = normalize_list_id(filter_list_type, filter_list_id)
                
                logging.info(f"📋 Filtering processed items by list {filter_list_type}:{filter_list_id} (normalized: {normalized_list_id})")
                
                # Filter items that have this list in their list_sources
                filtered_items = [
                    item for item in filtered_items
                    if any(
                        source['list_type'] == filter_list_type and 
                        (source['list_id'] == normalized_list_id or source['list_id'] == filter_list_id)
                        for source in item.get('list_sources', [])
                    )
                ]
                
                logging.info(f"📊 After list filtering: {len(filtered_items)} items match")
            except ValueError:
                logging.warning(f"Invalid list_source format: {list_source}, expected 'list_type:list_id'")
        
        # Calculate pagination on filtered results
        total_items = len(filtered_items)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start = (page - 1) * limit
        end = start + limit
        
        # Get paginated items from filtered results
        paginated_items = filtered_items[start:end]
        
        return {
            "items": paginated_items,
            "total_count": historic_data["total_unique_processed"],
            "filtered_count": total_items,  # Count after filtering
            "sync_sessions": historic_data["sync_sessions"],
            "log_file_exists": historic_data["log_file_exists"],
            "filters": {
                "search": search,
                "status_filter": status_filter,
                "media_type_filter": media_type_filter,
                "list_source": list_source
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_items,  # Use filtered count for pagination
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        print(f"Error parsing processed items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/successful")
async def get_successful_items(
    page: int = Query(1, ge=1), 
    limit: int = Query(50, ge=1, le=100),
    search: str = Query("", description="Search term to filter items by title"),
    status_filter: str = Query("", description="Filter by status"),
    media_type_filter: str = Query("", description="Filter by media type (movie/tv)")
):
    """Get all successful items from historic log data with search/filter and pagination"""
    try:
        historic_data = parse_historic_items_from_logs()
        all_items = historic_data["successful_items"]
        
        # Enrich with database information for Overseerr/IMDb links
        all_items = enrich_historic_data_with_database(all_items)
        
        # Get Overseerr base URL for generating item links
        try:
            overseerr_base_url, _, _, _, _, _ = load_env_config()
            overseerr_base_url = overseerr_base_url.rstrip('/') if overseerr_base_url else None
        except:
            overseerr_base_url = None
        
        # Add overseerr_url to items
        for item in all_items:
            if overseerr_base_url and item.get('overseerr_id'):
                item['overseerr_url'] = f"{overseerr_base_url}/{item['media_type']}/{item['overseerr_id']}"
            else:
                item['overseerr_url'] = None
        
        # Apply filters BEFORE pagination
        filtered_items = all_items
        
        # Search filter (case-insensitive title search)
        if search.strip():
            search_term = search.strip().lower()
            filtered_items = [
                item for item in filtered_items 
                if search_term in item["title"].lower()
            ]
        
        # Status filter
        if status_filter.strip():
            filtered_items = [
                item for item in filtered_items 
                if item["status"] == status_filter
            ]
        
        # Media type filter
        if media_type_filter.strip():
            filtered_items = [
                item for item in filtered_items 
                if item["media_type"] == media_type_filter
            ]
        
        # Calculate pagination on filtered results
        total_items = len(filtered_items)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start = (page - 1) * limit
        end = start + limit
        
        # Get paginated items from filtered results
        paginated_items = filtered_items[start:end]
        
        # Calculate media type counts from ALL filtered items (not just current page)
        movie_count = sum(1 for item in filtered_items if item.get("media_type") == "movie")
        tv_count = sum(1 for item in filtered_items if item.get("media_type") == "tv")
        
        return {
            "items": paginated_items,
            "total_count": historic_data["total_unique_successful"],
            "filtered_count": total_items,  # Count after filtering
            "movie_count": movie_count,  # Total movies in filtered results
            "tv_count": tv_count,  # Total TV shows in filtered results
            "sync_sessions": historic_data["sync_sessions"],
            "log_file_exists": historic_data["log_file_exists"],
            "filters": {
                "search": search,
                "status_filter": status_filter,
                "media_type_filter": media_type_filter
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_items,  # Use filtered count for pagination
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        print(f"Error parsing successful items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requested")
async def get_requested_items(
    page: int = Query(1, ge=1), 
    limit: int = Query(50, ge=1, le=100),
    search: str = Query("", description="Search term to filter items by title"),
    status_filter: str = Query("", description="Filter by status"),
    media_type_filter: str = Query("", description="Filter by media type (movie/tv)")
):
    """Get all requested items from database (historic data) with search/filter and pagination"""
    try:
        if not os.path.exists(DB_FILE):
            return {
                "items": [],
                "total_count": 0,
                "filtered_count": 0,
                "database_exists": False,
                "filters": {
                    "search": search,
                    "status_filter": status_filter,
                    "media_type_filter": media_type_filter
                },
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_items": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Build WHERE clause for filters - ONLY include 'requested' status, not 'already_requested'
        where_conditions = ["status = 'requested'"]
        params = []
        
        if search.strip():
            where_conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{search.strip().lower()}%")
        
        if status_filter.strip():
            where_conditions.append("status = ?")
            params.append(status_filter)
        
        if media_type_filter.strip():
            where_conditions.append("media_type = ?")
            params.append(media_type_filter)
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count with filters
        cursor.execute(f"SELECT COUNT(*) FROM synced_items WHERE {where_clause}", params)
        total_items = cursor.fetchone()[0]
        
        # Calculate pagination
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        offset = (page - 1) * limit
        
        # Get paginated items with filters
        cursor.execute(f"""
            SELECT id, title, media_type, imdb_id, overseerr_id, status, last_synced 
            FROM synced_items 
            WHERE {where_clause}
            ORDER BY last_synced DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        items = cursor.fetchall()
        
        # Get total count without filters for reference - ONLY 'requested' items
        cursor.execute("SELECT COUNT(*) FROM synced_items WHERE status = 'requested'")
        total_count_unfiltered = cursor.fetchone()[0]
        
        conn.close()
        
        # Get Overseerr base URL for generating item links
        try:
            overseerr_base_url, _, _, _, _, _ = load_env_config()
            overseerr_base_url = overseerr_base_url.rstrip('/') if overseerr_base_url else None
        except:
            overseerr_base_url = None
        
        formatted_items = []
        for item in items:
            item_id, title, media_type, imdb_id, overseerr_id, status, last_synced = item
            
            # Generate Overseerr URL if we have the base URL and overseerr_id
            overseerr_url = None
            if overseerr_base_url and overseerr_id:
                overseerr_url = f"{overseerr_base_url}/{media_type}/{overseerr_id}"
            
            formatted_items.append({
                "id": item_id,
                "title": title,
                "media_type": media_type,
                "imdb_id": imdb_id,
                "overseerr_id": overseerr_id,
                "status": status,
                "timestamp": last_synced,
                "action": "Requested",  # Since we only show 'requested' status now
                "overseerr_url": overseerr_url
            })
        
        return {
            "items": formatted_items,
            "total_count": total_count_unfiltered,
            "filtered_count": total_items,  # Count after filtering
            "database_exists": True,
            "filters": {
                "search": search,
                "status_filter": status_filter,
                "media_type_filter": media_type_filter
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_items,  # Use filtered count for pagination
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        print(f"Error getting requested items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Collections API endpoints
@app.get("/api/collections")
async def get_collections(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query("", description="Search collections by franchise name"),
    sort: str = Query("total_votes", regex="^(popularity|rating|movie_count|name|total_votes)$", description="Sort by popularity, rating, movie_count, name, or total_votes")
):
    """Get all collections with pagination, search, and sorting"""
    try:
        from list_sync.providers.collections import get_all_collections
        from list_sync.database import load_list_ids
        
        collections = get_all_collections()
        
        # Get synced collections info
        all_lists = load_list_ids()
        synced_info = {}
        for list_item in all_lists:
            if list_item.get("type") == "collections":
                franchise_name = list_item.get("id")
                synced_info[franchise_name] = {
                    "last_synced": list_item.get("last_synced"),
                    "item_count": list_item.get("item_count", 0)
                }
        
        # Apply search filter
        if search.strip():
            search_lower = search.strip().lower()
            collections = [
                c for c in collections
                if search_lower in c.get("franchise", "").lower()
            ]
        
        # Apply sorting (default: total_votes for quality content first)
        if sort == "total_votes":
            collections.sort(key=lambda x: x.get("totalVotes", 0), reverse=True)
        elif sort == "popularity":
            collections.sort(key=lambda x: x.get("popularityScore", 0), reverse=True)
        elif sort == "rating":
            collections.sort(key=lambda x: x.get("averageRating", 0), reverse=True)
        elif sort == "movie_count":
            collections.sort(key=lambda x: x.get("totalMovies", 0), reverse=True)
        elif sort == "name":
            collections.sort(key=lambda x: x.get("franchise", "").lower())
        
        # Calculate pagination
        total = len(collections)
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        start = (page - 1) * limit
        end = start + limit
        page_collections = collections[start:end]
        
        # Add synced info to each collection
        for collection in page_collections:
            franchise = collection.get("franchise")
            if franchise in synced_info:
                collection["_synced_info"] = synced_info[franchise]
            else:
                collection["_synced_info"] = None
        
        return {
            "collections": page_collections,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "limit": limit
        }
    except Exception as e:
        logging.error(f"Error getting collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/random")
async def get_random_collections(count: int = Query(5, ge=1, le=20, description="Number of random collections to return")):
    """Get random collections from the full database (only collections with 3+ movies) - cached for performance"""
    try:
        import random
        from list_sync.providers.collections import get_all_collections
        
        # Use cached collections data (already cached in collections.py)
        collections = get_all_collections()
        
        # Filter to only collections with 3 or more movies (do this once, cache the result)
        if not hasattr(get_random_collections, '_filtered_cache'):
            get_random_collections._filtered_cache = [
                c for c in collections 
                if c and c.get("franchise") and c.get("totalMovies", 0) >= 3
            ]
            logging.info(f"Cached {len(get_random_collections._filtered_cache)} collections with 3+ movies for random selection")
        
        filtered_collections = get_random_collections._filtered_cache
        
        if len(filtered_collections) == 0:
            logging.warning("No collections with 3+ movies available for random selection")
            return {"collections": []}
        
        # Get random sample from filtered collections
        if len(filtered_collections) <= count:
            random_collections = filtered_collections
        else:
            random_collections = random.sample(filtered_collections, count)
        
        # Ensure all collections have required fields
        validated_collections = []
        for collection in random_collections:
            if collection and collection.get("franchise"):
                # Ensure all expected fields exist
                validated_collection = {
                    "franchise": collection.get("franchise"),
                    "totalMovies": collection.get("totalMovies", 0),
                    "totalVotes": collection.get("totalVotes", 0),
                    "averageRating": collection.get("averageRating", 0),
                    "popularityScore": collection.get("popularityScore", 0),
                    "poster_url": None,  # Will be fetched separately
                }
                validated_collections.append(validated_collection)
        
        return {"collections": validated_collections}
    except Exception as e:
        logging.error(f"Error getting random collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/popular")
async def get_popular_collections():
    """Get top 20 collections by total votes (quality content first)"""
    try:
        from list_sync.providers.collections import get_all_collections
        from list_sync.database import load_list_ids
        
        collections = get_all_collections()
        
        # Sort by total votes (quality content first) and take top 20
        collections.sort(key=lambda x: x.get("totalVotes", 0), reverse=True)
        top_20 = collections[:20]
        
        # Get synced collections info
        all_lists = load_list_ids()
        synced_info = {}
        for list_item in all_lists:
            if list_item.get("type") == "collections":
                franchise_name = list_item.get("id")
                synced_info[franchise_name] = {
                    "last_synced": list_item.get("last_synced"),
                    "item_count": list_item.get("item_count", 0)
                }
        
        # Add synced info to each collection
        for collection in top_20:
            franchise = collection.get("franchise")
            if franchise in synced_info:
                collection["_synced_info"] = synced_info[franchise]
            else:
                collection["_synced_info"] = None
        
        return {
            "collections": top_20
        }
    except Exception as e:
        logging.error(f"Error getting popular collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/synced")
async def get_synced_collections_info():
    """Get information about synced collections (franchise name and last_synced timestamp)"""
    try:
        from list_sync.database import load_list_ids
        
        all_lists = load_list_ids()
        synced_collections = {}
        
        for list_item in all_lists:
            if list_item.get("type") == "collections":
                franchise_name = list_item.get("id")
                synced_collections[franchise_name] = {
                    "last_synced": list_item.get("last_synced"),
                    "item_count": list_item.get("item_count", 0)
                }
        
        return {
            "synced_collections": synced_collections
        }
    except Exception as e:
        logging.error(f"Error getting synced collections info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/{franchise_name}")
async def get_collection_details(franchise_name: str):
    """Get specific collection details by franchise name"""
    try:
        from urllib.parse import unquote
        from list_sync.providers.collections import get_collection_by_name
        
        # URL decode the franchise name
        decoded_name = unquote(franchise_name)
        
        collection = get_collection_by_name(decoded_name)
        
        if not collection:
            raise HTTPException(status_code=404, detail=f"Collection not found: {decoded_name}")
        
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting collection details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/{franchise_name}/movies")
async def get_collection_movies(franchise_name: str):
    """Get movies in a collection with full details"""
    try:
        from urllib.parse import unquote
        from list_sync.providers.collections import get_collection_by_name
        
        # URL decode the franchise name
        decoded_name = unquote(franchise_name)
        
        collection = get_collection_by_name(decoded_name)
        
        if not collection:
            raise HTTPException(status_code=404, detail=f"Collection not found: {decoded_name}")
        
        # Return full movieRatings data if available, otherwise fallback to basic format
        movies = collection.get("movieRatings", [])
        
        # If no movieRatings, create basic format from movieIds
        if not movies:
            from list_sync.providers.collections import fetch_collection
            movies = fetch_collection(decoded_name)
        
        return {
            "franchise": decoded_name,
            "movies": movies,
            "total": len(movies)
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting collection movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/{franchise_name}/poster")
async def get_collection_poster(franchise_name: str):
    """Get poster URL for collection (uses most voted movie's poster from Trakt)"""
    try:
        from urllib.parse import unquote
        from list_sync.providers.collections import get_collection_by_name, get_oldest_movie_id
        from list_sync.providers.trakt import get_trakt_metadata
        
        # URL decode the franchise name
        decoded_name = unquote(franchise_name)
        
        collection = get_collection_by_name(decoded_name)
        
        if not collection:
            raise HTTPException(status_code=404, detail=f"Collection not found: {decoded_name}")
        
        # Get most voted movie ID (function name kept for compatibility but logic changed)
        oldest_movie_id = get_oldest_movie_id(collection)
        
        if not oldest_movie_id:
            return {"poster_url": None}
        
        # Fetch poster from Trakt
        metadata = get_trakt_metadata(tmdb_id=oldest_movie_id, media_type="movie")
        
        poster_url = metadata.get("poster_url") if metadata else None
        
        return {
            "poster_url": poster_url,
            "movie_id": oldest_movie_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting collection poster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collections/posters/batch")
async def get_collection_posters_batch(request: Request):
    """Get poster URLs for multiple collections in parallel (faster than individual requests)"""
    try:
        import asyncio
        from urllib.parse import unquote
        from list_sync.providers.collections import get_collection_by_name, get_oldest_movie_id
        from list_sync.providers.trakt import get_trakt_metadata
        
        body = await request.json()
        franchise_names = body.get("franchise_names", [])
        
        if not franchise_names or not isinstance(franchise_names, list):
            raise HTTPException(status_code=400, detail="franchise_names must be a non-empty list")
        
        if len(franchise_names) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 franchise names per batch")
        
        async def fetch_poster(franchise_name: str):
            """Fetch poster for a single collection"""
            try:
                decoded_name = unquote(franchise_name) if "%" in franchise_name else franchise_name
                collection = get_collection_by_name(decoded_name)
                
                if not collection:
                    return {
                        "franchise": franchise_name,
                        "poster_url": None,
                        "error": "Collection not found"
                    }
                
                oldest_movie_id = get_oldest_movie_id(collection)
                
                if not oldest_movie_id:
                    return {
                        "franchise": franchise_name,
                        "poster_url": None,
                        "movie_id": None
                    }
                
                # Fetch poster from Trakt (run in thread pool to avoid blocking)
                loop = asyncio.get_event_loop()
                metadata = await loop.run_in_executor(
                    None,
                    lambda: get_trakt_metadata(tmdb_id=oldest_movie_id, media_type="movie")
                )
                
                poster_url = metadata.get("poster_url") if metadata else None
                
                return {
                    "franchise": franchise_name,
                    "poster_url": poster_url,
                    "movie_id": oldest_movie_id
                }
            except Exception as e:
                logging.warning(f"Error fetching poster for {franchise_name}: {e}")
                return {
                    "franchise": franchise_name,
                    "poster_url": None,
                    "error": str(e)
                }
        
        # Fetch all posters in parallel
        results = await asyncio.gather(*[fetch_poster(name) for name in franchise_names])
        
        return {
            "posters": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting batch collection posters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/media/request")
async def request_single_media(request: Request):
    """Request a single media item to Overseerr (one-time sync, not a list)"""
    try:
        from list_sync.config import load_env_config
        from list_sync.api.overseerr import OverseerrClient
        
        body = await request.json()
        tmdb_id = body.get("tmdb_id")
        media_type = body.get("media_type", "movie")
        is_4k = body.get("is_4k", False)
        
        if not tmdb_id:
            raise HTTPException(status_code=400, detail="tmdb_id is required")
        
        if media_type not in ["movie", "tv"]:
            raise HTTPException(status_code=400, detail="media_type must be 'movie' or 'tv'")
        
        # Ensure tmdb_id is an integer
        try:
            tmdb_id = int(tmdb_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="tmdb_id must be a valid integer")
        
        # Get environment configuration
        config_tuple = load_env_config()
        if not config_tuple or not config_tuple[0] or not config_tuple[1]:
            raise HTTPException(status_code=400, detail="Overseerr not configured")
        
        overseerr_url, api_key, requester_user_id = config_tuple[0], config_tuple[1], config_tuple[2] or "1"
        is_4k_config = config_tuple[5] if len(config_tuple) > 5 else False
        
        # Use config 4K setting if not explicitly provided
        if is_4k is None:
            is_4k = is_4k_config
        
        # Create Overseerr client
        overseerr_client = OverseerrClient(overseerr_url, api_key, requester_user_id)
        
        # Get media by TMDB ID to get Overseerr ID
        media_data = overseerr_client.get_media_by_tmdb_id(tmdb_id, media_type)
        
        if not media_data:
            return {
                "success": False,
                "status": "not_found",
                "message": f"Media with TMDB ID {tmdb_id} not found in Overseerr"
            }
        
        overseerr_id = media_data.get("id")
        if not overseerr_id:
            return {
                "success": False,
                "status": "error",
                "message": "Could not determine Overseerr ID"
            }
        
        # Check current status
        is_available, is_requested, _ = overseerr_client.get_media_status(overseerr_id, media_type)
        
        if is_requested:
            return {
                "success": True,
                "status": "already_requested",
                "message": "Media is already requested in Overseerr",
                "overseerr_id": overseerr_id
            }
        
        if is_available:
            return {
                "success": True,
                "status": "already_available",
                "message": "Media is already available in Overseerr",
                "overseerr_id": overseerr_id
            }
        
        # Request the media
        request_status = overseerr_client.request_media(overseerr_id, media_type, is_4k, requester_user_id=None)
        
        if request_status == "success":
            return {
                "success": True,
                "status": "requested",
                "message": "Media successfully requested in Overseerr",
                "overseerr_id": overseerr_id
            }
        elif request_status == "already_requested":
            return {
                "success": True,
                "status": "already_requested",
                "message": "Media is already requested in Overseerr",
                "overseerr_id": overseerr_id
            }
        else:
            return {
                "success": False,
                "status": "error",
                "message": f"Failed to request media: {request_status}",
                "overseerr_id": overseerr_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error requesting single media: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _run_collection_sync_in_subprocess(list_type: str, list_id: str, overseerr_url: str, 
                                       overseerr_api_key: str, user_id: str, is_4k: bool, 
                                       result_queue: multiprocessing.Queue):
    """
    Worker function to run collection sync in a subprocess.
    This function is called by multiprocessing.Process.
    """
    try:
        # Import inside subprocess to avoid issues
        from list_sync.main import sync_single_list
        from list_sync.utils.sync_status import get_sync_tracker
        
        # Set the subprocess PID in the tracker
        sync_tracker = get_sync_tracker()
        sync_tracker.set_subprocess_pid(os.getpid())
        
        result = sync_single_list(
            list_type,
            list_id,
            overseerr_url,
            overseerr_api_key,
            user_id,
            is_4k,
            False  # dry_run
        )
        result_queue.put({"success": True, "result": result})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})


@app.post("/api/collections/{franchise_name}/sync")
async def sync_collection(franchise_name: str):
    """Sync a collection to Overseerr using a terminable subprocess"""
    try:
        from urllib.parse import unquote
        from list_sync.config import load_env_config
        from list_sync.utils.sync_status import get_sync_tracker
        
        # URL decode the franchise name
        decoded_name = unquote(franchise_name)
        
        # Get environment configuration
        config_tuple = load_env_config()
        if not config_tuple or not config_tuple[0] or not config_tuple[1]:
            raise HTTPException(status_code=400, detail="Overseerr not configured")
        
        overseerr_url, api_key, requester_user_id = config_tuple[0], config_tuple[1], config_tuple[2] or "1"
        is_4k = config_tuple[5] if len(config_tuple) > 5 else False
        
        # Create a queue to receive results from subprocess
        result_queue = multiprocessing.Queue()
        
        # Create and start subprocess for immediate termination support
        sync_process = multiprocessing.Process(
            target=_run_collection_sync_in_subprocess,
            args=("collections", decoded_name, overseerr_url, api_key, requester_user_id, is_4k, result_queue)
        )
        sync_process.start()
        subprocess_pid = sync_process.pid
        
        logging.info(f"Collection sync subprocess started with PID {subprocess_pid}")
        
        # Register the subprocess PID in the tracker for immediate cancellation
        sync_tracker = get_sync_tracker()
        sync_tracker.set_subprocess_pid(subprocess_pid)
        
        # Wait for the subprocess with polling to allow for cancellation
        timeout_seconds = 3600  # 1 hour timeout
        poll_interval = 0.5
        elapsed = 0
        
        while sync_process.is_alive() and elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            # Check if cancellation was requested
            if sync_tracker.is_cancellation_requested():
                logging.info(f"Cancellation requested, terminating collection sync subprocess {subprocess_pid}")
                sync_process.terminate()
                sync_process.join(timeout=2)
                if sync_process.is_alive():
                    sync_process.kill()
                sync_tracker.end_sync()
                return {
                    "success": False,
                    "franchise": decoded_name,
                    "message": "Collection sync cancelled by user",
                    "cancelled": True
                }
        
        # Check if process timed out
        if sync_process.is_alive():
            logging.error(f"Collection sync timed out after {timeout_seconds} seconds")
            sync_process.terminate()
            sync_process.join(timeout=2)
            if sync_process.is_alive():
                sync_process.kill()
            sync_tracker.end_sync()
            raise HTTPException(status_code=500, detail="Collection sync timed out")
        
        # Get result from queue
        try:
            result_data = result_queue.get_nowait()
            if result_data.get("success"):
                result = result_data.get("result", {})
                if result.get("success", False):
                    return {
                        "success": True,
                        "franchise": decoded_name,
                        "items_processed": result.get("items_processed", 0),
                        "items_requested": result.get("items_requested", 0),
                        "items_already_available": result.get("items_already_available", 0),
                        "items_already_requested": result.get("items_already_requested", 0),
                        "items_skipped": result.get("items_skipped", 0),
                        "items_not_found": result.get("items_not_found", 0),
                        "errors": result.get("errors", 0),
                        "message": result.get("message", "Collection synced successfully")
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=result.get("message", "Collection sync failed")
                    )
            else:
                raise HTTPException(status_code=500, detail=result_data.get("error", "Collection sync failed"))
        except HTTPException:
            raise
        except Exception as queue_error:
            logging.warning(f"Could not get result from queue: {queue_error}")
            exit_code = sync_process.exitcode
            if exit_code == 0:
                return {
                    "success": True,
                    "franchise": decoded_name,
                    "message": "Collection synced"
                }
            else:
                raise HTTPException(status_code=500, detail=f"Collection sync process exited with code {exit_code}")
                
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error syncing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timezone/supported")
async def get_supported_timezones():
    """Get list of all supported timezone abbreviations organized by region"""
    try:
        abbreviations = list_supported_abbreviations()
        return {
            "success": True,
            "regions": abbreviations,
            "total_abbreviations": sum(len(abbrevs) for abbrevs in abbreviations.values()),
            "note": "Use these abbreviations in the TZ environment variable"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timezone/current")
async def get_current_timezone():
    """Get detailed information about the current timezone"""
    try:
        tz_info = get_current_timezone_info()
        return {
            "success": True,
            "timezone": tz_info,
            "environment_tz": os.getenv('TZ', 'Not set'),
            "system_supports_abbreviations": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/timezone/validate")
async def validate_timezone(timezone_input: dict):
    """Validate a timezone input and return the normalized timezone name"""
    try:
        tz_input = timezone_input.get("timezone", "")
        region_hint = timezone_input.get("region_hint", None)
        
        if not tz_input:
            raise HTTPException(status_code=400, detail="Timezone input is required")
        
        try:
            normalized_tz = normalize_timezone_input(tz_input, region_hint)
            return {
                "success": True,
                "input": tz_input,
                "normalized": normalized_tz,
                "region_hint": region_hint,
                "valid": True
            }
        except ValueError as e:
            return {
                "success": False,
                "input": tz_input,
                "normalized": None,
                "region_hint": region_hint,
                "valid": False,
                "error": str(e)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add these new API endpoints before the main execution block

@app.get("/api/logs/entries")
async def get_log_entries_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR)$"),
    category: Optional[List[str]] = Query(None, description="Filter by categories (can specify multiple)"),
    search: Optional[str] = Query(None, description="Search in log messages and media titles"),
    sort_order: str = Query('desc', regex="^(asc|desc)$", description="Sort order by timestamp")
):
    """Get paginated log entries with filtering"""
    try:
        offset = (page - 1) * limit
        response = get_log_entries(
            limit=limit,
            offset=offset,
            level_filter=level,
            category_filters=category,
            search=search,
            sort_order=sort_order
        )
        
        # Add pagination metadata
        total_pages = (response.total_count + limit - 1) // limit if response.total_count > 0 else 0
        
        return {
            "entries": response.entries,
            "total_count": response.total_count,
            "has_more": response.has_more,
            "last_position": response.last_position,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": response.total_count,
                "total_pages": total_pages,
                "has_next": response.has_more,
                "has_prev": page > 1
            },
            "filters": {
                "level": level,
                "categories": category,
                "search": search,
                "sort_order": sort_order
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/stream")
async def stream_logs(
    last_position: int = Query(0, ge=0),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR)$"),
    category: Optional[List[str]] = Query(None, description="Filter by categories (can specify multiple)"),
    search: Optional[str] = Query(None, description="Search in log messages and media titles")
):
    """Stream live log updates using Server-Sent Events"""
    try:
        return StreamingResponse(
            stream_log_updates(
                last_position=last_position,
                level_filter=level,
                category_filters=category,
                search=search
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/categories")
async def get_log_categories():
    """Get available log categories and their counts"""
    try:
        response = get_log_entries(limit=10000)  # Get a large sample
        
        category_counts = {}
        level_counts = {}
        
        for entry in response.entries:
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
            level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
        
        return {
            "categories": [
                {"name": "sync", "label": "Sync Operations", "count": category_counts.get("sync", 0)},
                {"name": "fetching", "label": "List Fetching", "count": category_counts.get("fetching", 0)},
                {"name": "items", "label": "Item Addition", "count": category_counts.get("items", 0)},
                {"name": "scraping", "label": "Web Scraping", "count": category_counts.get("scraping", 0)},
                {"name": "matching", "label": "Title Matching", "count": category_counts.get("matching", 0)},
                {"name": "api", "label": "API Connections", "count": category_counts.get("api", 0)},
                {"name": "webhook", "label": "Webhooks", "count": category_counts.get("webhook", 0)},
                {"name": "pagination", "label": "Pagination", "count": category_counts.get("pagination", 0)},
                {"name": "process", "label": "Process Management", "count": category_counts.get("process", 0)},
                {"name": "metadata", "label": "Metadata", "count": category_counts.get("metadata", 0)},
                {"name": "general", "label": "General", "count": category_counts.get("general", 0)}
            ],
            "levels": [
                {"name": "INFO", "label": "Info", "count": level_counts.get("INFO", 0)},
                {"name": "DEBUG", "label": "Debug", "count": level_counts.get("DEBUG", 0)},
                {"name": "WARNING", "label": "Warning", "count": level_counts.get("WARNING", 0)},
                {"name": "ERROR", "label": "Error", "count": level_counts.get("ERROR", 0)}
            ],
            "total_entries": response.total_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/stats")
async def get_log_stats():
    """Get log file statistics and recent activity summary"""
    try:
        log_path = 'data/list_sync.log'
        
        if not os.path.exists(log_path):
            return {
                "total_entries": 0,
                "level_counts": {},
                "category_counts": {},
                "recent_activity": 0,
                "file_exists": False,
                "error": "Log file not found"
            }
        
        # Get file stats
        stat = os.stat(log_path)
        file_size = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Use a more efficient approach - sample recent entries for stats
        # This balances accuracy with performance
        level_counts = {}
        category_counts = {}
        recent_activity = 0
        total_entries = 0
        
        # Calculate time for recent activity (last hour)
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        try:
            # Read file in chunks to avoid memory issues with very large files
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Count total lines first (fast)
                f.seek(0)
                total_entries = sum(1 for _ in f)
                
                # Reset and read last 10000 lines for stats (more representative sample)
                f.seek(0)
                lines = f.readlines()
                
                # Take a sample of lines for stats - last 10000 lines should be representative
                sample_lines = lines[-10000:] if len(lines) > 10000 else lines
                
                # Parse sample lines for level/category counts
                for i, line in enumerate(sample_lines):
                    entry = parse_log_line(line, i + 1)
                    if entry:
                        # Count levels and categories
                        level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
                        category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
                        
                        # Count recent activity
                        try:
                            entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                            if entry_time >= one_hour_ago:
                                recent_activity += 1
                        except:
                            # If timestamp parsing fails, skip this entry for recent activity count
                            pass
                            
        except Exception as e:
            print(f"Error reading log file for stats: {e}")
            # Fallback to using get_log_entries with reasonable limit
            response = get_log_entries(limit=1000)
            total_entries = response.total_count
            
            if response.entries:
                for entry in response.entries:
                    level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
                    category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
                    
                    try:
                        entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                        if entry_time >= one_hour_ago:
                            recent_activity += 1
                    except:
                        pass
        
        return {
            "total_entries": total_entries,
            "level_counts": level_counts,
            "category_counts": category_counts,
            "recent_activity": recent_activity,
            "file_exists": True,
            "file_size": file_size,
            "last_modified": last_modified
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Pydantic models
class AnalyticsOverview(BaseModel):
    total_items: int
    success_rate: float
    avg_processing_time: float
    active_sync: bool
    total_sync_operations: int
    total_errors: int
    last_sync_time: str

class MediaAdditionData(BaseModel):
    timestamp: str
    count: int
    type: str  # 'movie' or 'tv'
    source: str

class ListFetchData(BaseModel):
    timestamp: str
    success_rate: float
    total_attempts: int
    successful_fetches: int
    failed_fetches: int
    source: str

class LowConfidenceMatch(BaseModel):
    title: str
    year: Optional[int] = None
    score: float
    original_title: Optional[str] = None
    source: str
    timestamp: str
    needs_review: bool

class MatchingData(BaseModel):
    perfect_matches: int
    partial_matches: int
    failed_matches: int
    average_score: float
    low_confidence_matches: List[LowConfidenceMatch]

class SearchFailureData(BaseModel):
    title: str
    search_count: int
    last_attempt: str
    sources: List[str]
    type: str  # 'movie' or 'tv'

class ScrapingPerformanceData(BaseModel):
    timestamp: str
    items_per_minute: float
    source: str
    total_items: int
    processing_time: float

class SourceDistributionData(BaseModel):
    source: str
    items_found: int
    average_items_per_page: float
    total_pages: int
    success_rate: float

class SelectorPerformanceData(BaseModel):
    website: str
    selector: str
    success_rate: float
    total_attempts: int
    last_used: str
    status: str  # 'working', 'failing', 'deprecated'

class GenreDistributionData(BaseModel):
    genre: str
    count: int
    percentage: float

class YearDistributionData(BaseModel):
    year: int
    count: int
    type: str  # 'movie' or 'tv'

class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    media_additions: List[MediaAdditionData]
    list_fetches: List[ListFetchData]
    matching: MatchingData
    search_failures: List[SearchFailureData]
    scraping_performance: List[ScrapingPerformanceData]
    source_distribution: List[SourceDistributionData]
    selector_performance: List[SelectorPerformanceData]
    genre_distribution: List[GenreDistributionData]
    year_distribution: List[YearDistributionData]

# Analytics processing functions
def process_analytics_data(time_range: str = '24h', category: str = 'all') -> AnalyticsResponse:
    """Process log data to generate comprehensive analytics"""
    try:
        # Calculate time filter
        now = datetime.now()
        if time_range == '1h':
            start_time = now - timedelta(hours=1)
        elif time_range == '24h':
            start_time = now - timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        elif time_range == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)  # Default to 24h
        
        # Get log entries for analysis
        category_filters_list = [category] if category != 'all' else None
        log_response = get_log_entries(limit=5000, category_filters=category_filters_list)
        entries = log_response.entries
        
        # Filter by time range
        filtered_entries = []
        for entry in entries:
            try:
                entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                if entry_time >= start_time:
                    filtered_entries.append(entry)
            except:
                # If timestamp parsing fails, include the entry
                filtered_entries.append(entry)
        
        # Process overview data
        overview = process_overview_analytics(filtered_entries)
        
        # Process specific analytics
        media_additions = process_media_additions(filtered_entries)
        list_fetches = process_list_fetches(filtered_entries)
        matching = process_matching_analytics(filtered_entries)
        search_failures = process_search_failures(filtered_entries)
        scraping_performance = process_scraping_performance(filtered_entries)
        source_distribution = process_source_distribution(filtered_entries)
        selector_performance = process_selector_performance(filtered_entries)
        genre_distribution = process_genre_distribution(filtered_entries)
        year_distribution = process_year_distribution(filtered_entries)
        
        return AnalyticsResponse(
            overview=overview,
            media_additions=media_additions,
            list_fetches=list_fetches,
            matching=matching,
            search_failures=search_failures,
            scraping_performance=scraping_performance,
            source_distribution=source_distribution,
            selector_performance=selector_performance,
            genre_distribution=genre_distribution,
            year_distribution=year_distribution
        )
        
    except Exception as e:
        print(f"Error processing analytics data: {e}")
        # Return empty analytics data on error
        return AnalyticsResponse(
            overview=AnalyticsOverview(
                total_items=0,
                success_rate=0.0,
                avg_processing_time=0.0,
                active_sync=False,
                total_sync_operations=0,
                total_errors=0,
                last_sync_time=""
            ),
            media_additions=[],
            list_fetches=[],
            matching=MatchingData(
                perfect_matches=0,
                partial_matches=0,
                failed_matches=0,
                average_score=0.0,
                low_confidence_matches=[]
            ),
            search_failures=[],
            scraping_performance=[],
            source_distribution=[],
            selector_performance=[],
            genre_distribution=[],
            year_distribution=[]
        )

def process_overview_analytics(entries: List[LogEntry]) -> AnalyticsOverview:
    """Process overview analytics from log entries"""
    total_items = 0
    success_count = 0
    error_count = 0
    sync_operations = 0
    processing_times = []
    last_sync_time = ""
    active_sync = False
    
    for entry in entries:
        if entry.category == 'items':
            total_items += 1
            if 'added' in entry.message.lower() or 'success' in entry.message.lower():
                success_count += 1
        
        if entry.level == 'ERROR':
            error_count += 1
        
        if entry.category == 'sync':
            sync_operations += 1
            if not last_sync_time:
                last_sync_time = entry.timestamp
            if 'starting' in entry.message.lower():
                active_sync = True
        
        # Extract processing times if available
        if entry.media_info and 'processing_time' in entry.media_info:
            processing_times.append(entry.media_info['processing_time'])
    
    success_rate = (success_count / total_items * 100) if total_items > 0 else 0
    avg_processing_time = statistics.mean(processing_times) if processing_times else 0
    
    return AnalyticsOverview(
        total_items=total_items,
        success_rate=round(success_rate, 1),
        avg_processing_time=round(avg_processing_time, 2),
        active_sync=active_sync,
        total_sync_operations=sync_operations,
        total_errors=error_count,
        last_sync_time=last_sync_time
    )

def process_media_additions(entries: List[LogEntry]) -> List[MediaAdditionData]:
    """Process media addition analytics"""
    additions_by_source = defaultdict(lambda: defaultdict(int))
    
    for entry in entries:
        if entry.category == 'items' and entry.media_info:
            source = entry.media_info.get('source', 'unknown')
            media_type = 'movie'  # Default, could be enhanced with better detection
            timestamp = entry.timestamp[:16]  # Group by hour
            additions_by_source[timestamp][source] += 1
    
    result = []
    for timestamp, sources in additions_by_source.items():
        for source, count in sources.items():
            result.append(MediaAdditionData(
                timestamp=timestamp,
                count=count,
                type='movie',
                source=source
            ))
    
    return sorted(result, key=lambda x: x.timestamp, reverse=True)[:20]

def process_list_fetches(entries: List[LogEntry]) -> List[ListFetchData]:
    """Process list fetch analytics"""
    fetches_by_time = defaultdict(lambda: {'success': 0, 'failed': 0, 'sources': set()})
    
    for entry in entries:
        if entry.category == 'fetching':
            timestamp = entry.timestamp[:16]  # Group by hour
            source = entry.media_info.get('source', 'unknown') if entry.media_info else 'unknown'
            
            fetches_by_time[timestamp]['sources'].add(source)
            
            if 'success' in entry.message.lower() or 'fetched' in entry.message.lower():
                fetches_by_time[timestamp]['success'] += 1
            elif 'error' in entry.message.lower() or 'failed' in entry.message.lower():
                fetches_by_time[timestamp]['failed'] += 1
    
    result = []
    for timestamp, data in fetches_by_time.items():
        total = data['success'] + data['failed']
        success_rate = (data['success'] / total * 100) if total > 0 else 0
        
        for source in data['sources']:
            result.append(ListFetchData(
                timestamp=timestamp,
                success_rate=round(success_rate, 1),
                total_attempts=total,
                successful_fetches=data['success'],
                failed_fetches=data['failed'],
                source=source
            ))
    
    return sorted(result, key=lambda x: x.timestamp, reverse=True)[:20]

def process_matching_analytics(entries: List[LogEntry]) -> MatchingData:
    """Process matching accuracy analytics"""
    perfect_matches = 0
    partial_matches = 0
    failed_matches = 0
    scores = []
    low_confidence = []
    
    for entry in entries:
        if entry.category == 'matching' and entry.media_info:
            score = entry.media_info.get('score', 0)
            if isinstance(score, (int, float)):
                scores.append(score)
                
                if score >= 1.0:
                    perfect_matches += 1
                elif score >= 0.7:
                    partial_matches += 1
                else:
                    failed_matches += 1
                
                # Low confidence matches (score < 0.7)
                if score < 0.7:
                    low_confidence.append(LowConfidenceMatch(
                        title=entry.media_info.get('title', 'Unknown'),
                        year=entry.media_info.get('year'),
                        score=score,
                        source=entry.media_info.get('source', 'unknown'),
                        timestamp=entry.timestamp,
                        needs_review=True
                    ))
    
    avg_score = statistics.mean(scores) if scores else 0
    
    return MatchingData(
        perfect_matches=perfect_matches,
        partial_matches=partial_matches,
        failed_matches=failed_matches,
        average_score=round(avg_score, 3),
        low_confidence_matches=sorted(low_confidence, key=lambda x: x.score)[:10]
    )

def process_search_failures(entries: List[LogEntry]) -> List[SearchFailureData]:
    """Process search failure analytics"""
    failures = defaultdict(lambda: {'count': 0, 'last_attempt': '', 'sources': set()})
    
    for entry in entries:
        if 'search' in entry.message.lower() and 'failed' in entry.message.lower():
            title = entry.media_info.get('title', 'Unknown') if entry.media_info else 'Unknown'
            source = entry.media_info.get('source', 'unknown') if entry.media_info else 'unknown'
            
            failures[title]['count'] += 1
            failures[title]['last_attempt'] = entry.timestamp
            failures[title]['sources'].add(source)
    
    result = []
    for title, data in failures.items():
        result.append(SearchFailureData(
            title=title,
            search_count=data['count'],
            last_attempt=data['last_attempt'],
            sources=list(data['sources']),
            type='movie'  # Default
        ))
    
    return sorted(result, key=lambda x: x.search_count, reverse=True)[:10]

def process_scraping_performance(entries: List[LogEntry]) -> List[ScrapingPerformanceData]:
    """Process scraping performance analytics"""
    performance_by_time = defaultdict(lambda: {'items': 0, 'time': 0, 'sources': set()})
    
    for entry in entries:
        if entry.category == 'scraping':
            timestamp = entry.timestamp[:16]  # Group by hour
            source = entry.media_info.get('source', 'unknown') if entry.media_info else 'unknown'
            
            performance_by_time[timestamp]['items'] += 1
            performance_by_time[timestamp]['sources'].add(source)
            
            # Estimate processing time (simplified)
            performance_by_time[timestamp]['time'] += 1  # 1 second per item estimate
    
    result = []
    for timestamp, data in performance_by_time.items():
        items_per_minute = (data['items'] / max(data['time'], 1)) * 60
        
        for source in data['sources']:
            result.append(ScrapingPerformanceData(
                timestamp=timestamp,
                items_per_minute=round(items_per_minute, 1),
                source=source,
                total_items=data['items'],
                processing_time=data['time']
            ))
    
    return sorted(result, key=lambda x: x.timestamp, reverse=True)[:20]

def process_source_distribution(entries: List[LogEntry]) -> List[SourceDistributionData]:
    """Process source distribution analytics"""
    sources = defaultdict(lambda: {'items': 0, 'pages': set(), 'success': 0, 'total': 0})
    
    for entry in entries:
        if entry.media_info and 'source' in entry.media_info:
            source = entry.media_info['source']
            sources[source]['items'] += 1
            sources[source]['total'] += 1
            
            if 'page' in entry.media_info:
                sources[source]['pages'].add(entry.media_info['page'])
            
            if 'success' in entry.message.lower():
                sources[source]['success'] += 1
    
    result = []
    for source, data in sources.items():
        total_pages = len(data['pages']) if data['pages'] else 1
        avg_items_per_page = data['items'] / total_pages
        success_rate = (data['success'] / data['total'] * 100) if data['total'] > 0 else 0
        
        result.append(SourceDistributionData(
            source=source,
            items_found=data['items'],
            average_items_per_page=round(avg_items_per_page, 1),
            total_pages=total_pages,
            success_rate=round(success_rate, 1)
        ))
    
    return sorted(result, key=lambda x: x.items_found, reverse=True)[:10]

def process_selector_performance(entries: List[LogEntry]) -> List[SelectorPerformanceData]:
    """Process selector performance analytics"""
    selectors = defaultdict(lambda: {'success': 0, 'total': 0, 'last_used': ''})
    
    # Mock selector data since we don't have detailed selector info in logs
    mock_selectors = [
        {'website': 'trakt.tv', 'selector': '.list-item', 'success_rate': 95, 'attempts': 150, 'status': 'working'},
        {'website': 'imdb.com', 'selector': '.titleColumn', 'success_rate': 88, 'attempts': 120, 'status': 'working'},
        {'website': 'letterboxd.com', 'selector': '.film-poster', 'success_rate': 92, 'attempts': 80, 'status': 'working'},
        {'website': 'mubi.com', 'selector': '.film-title', 'success_rate': 45, 'attempts': 30, 'status': 'failing'},
        {'website': 'criterion.com', 'selector': '.spine-title', 'success_rate': 78, 'attempts': 60, 'status': 'working'},
        {'website': 'rottentomatoes.com', 'selector': '.movie-title', 'success_rate': 15, 'attempts': 25, 'status': 'deprecated'},
    ]
    
    result = []
    for selector in mock_selectors:
        result.append(SelectorPerformanceData(
            website=selector['website'],
            selector=selector['selector'],
            success_rate=selector['success_rate'],
            total_attempts=selector['attempts'],
            last_used=datetime.now().isoformat(),
            status=selector['status']
        ))
    
    return result

def process_genre_distribution(entries: List[LogEntry]) -> List[GenreDistributionData]:
    """Process genre distribution analytics"""
    # Mock genre data since we don't extract genres from logs
    mock_genres = [
        {'genre': 'Drama', 'count': 45},
        {'genre': 'Comedy', 'count': 38},
        {'genre': 'Action', 'count': 32},
        {'genre': 'Thriller', 'count': 28},
        {'genre': 'Horror', 'count': 22},
        {'genre': 'Romance', 'count': 18},
        {'genre': 'Sci-Fi', 'count': 15},
        {'genre': 'Documentary', 'count': 12},
    ]
    
    total = sum(g['count'] for g in mock_genres)
    
    result = []
    for genre in mock_genres:
        percentage = (genre['count'] / total * 100) if total > 0 else 0
        result.append(GenreDistributionData(
            genre=genre['genre'],
            count=genre['count'],
            percentage=round(percentage, 1)
        ))
    
    return result

def process_year_distribution(entries: List[LogEntry]) -> List[YearDistributionData]:
    """Process year distribution analytics"""
    years = defaultdict(int)
    
    for entry in entries:
        if entry.media_info and 'year' in entry.media_info:
            year = entry.media_info['year']
            if isinstance(year, int) and 1900 <= year <= 2024:
                years[year] += 1
    
    # Add some mock data if no years found
    if not years:
        current_year = datetime.now().year
        for i in range(5):
            years[current_year - i] = 10 - i * 2
    
    result = []
    for year, count in years.items():
        result.append(YearDistributionData(
            year=year,
            count=count,
            type='movie'  # Default
        ))
    
    return sorted(result, key=lambda x: x.year, reverse=True)[:10]

@app.get("/api/analytics")
async def get_analytics(
    time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$"),
    category: str = Query('all', regex="^(all|sync|fetching|matching|scraping)$")
):
    """Get comprehensive analytics data"""
    try:
        analytics_data = process_analytics_data(time_range, category)
        return analytics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@app.get("/api/analytics/overview")
async def get_analytics_overview(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get analytics overview data"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating overview: {str(e)}")

@app.get("/api/analytics/media-additions")
async def get_media_additions(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get media addition analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.media_additions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating media additions: {str(e)}")

@app.get("/api/analytics/list-fetches")
async def get_list_fetches(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get list fetch analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.list_fetches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating list fetches: {str(e)}")

@app.get("/api/analytics/matching")
async def get_matching_analytics(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get matching accuracy analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.matching
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating matching analytics: {str(e)}")

@app.get("/api/analytics/search-failures")
async def get_search_failures(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get search failure analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.search_failures
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating search failures: {str(e)}")

@app.get("/api/analytics/scraping-performance")
async def get_scraping_performance(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get scraping performance analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.scraping_performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating scraping performance: {str(e)}")

@app.get("/api/analytics/source-distribution")
async def get_source_distribution(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get source distribution analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.source_distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating source distribution: {str(e)}")

@app.get("/api/analytics/selector-performance")
async def get_selector_performance(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get selector performance analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.selector_performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating selector performance: {str(e)}")

@app.get("/api/analytics/genre-distribution")
async def get_genre_distribution(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get genre distribution analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.genre_distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating genre distribution: {str(e)}")

@app.get("/api/analytics/year-distribution")
async def get_year_distribution(time_range: str = Query('24h', regex="^(1h|24h|7d|30d)$")):
    """Get year distribution analytics"""
    try:
        analytics_data = process_analytics_data(time_range)
        return analytics_data.year_distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating year distribution: {str(e)}")

def parse_recent_activity_from_structured_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Parse recent sync activity from the structured log file (data/list_sync.log)"""
    try:
        log_path = 'data/list_sync.log'
        
        if not os.path.exists(log_path):
            print(f"Structured log file not found: {log_path}")
            return []
        
        # Get recent log entries using the existing function
        log_response = get_log_entries(
            log_path=log_path,
            limit=1000,  # Get more entries to find sync activity
            offset=0,
            sort_order='desc'  # Most recent first
        )
        
        recent_items = []
        
        # Look for sync-related entries in the structured log
        for entry in log_response.entries:
            # Skip if no media info
            if not entry.media_info:
                continue
            
            # Look for item addition patterns (Pattern 3, 4, 5)
            if entry.media_info.get('type') in ['item_added_imdb', 'item_added_simple', 'item_added_position']:
                title = entry.media_info.get('title', 'Unknown')
                media_type = entry.media_info.get('media_type', 'movie')
                source = entry.media_info.get('source', 'unknown')
                
                # Determine status based on the log message
                status = "requested"
                status_text = "Added"
                
                if 'already' in entry.message.lower():
                    status = "available"
                    status_text = "Already Available"
                elif 'skipped' in entry.message.lower():
                    status = "skipped"
                    status_text = "Skipped"
                elif 'error' in entry.message.lower() or 'failed' in entry.message.lower():
                    status = "not_found"
                    status_text = "Error"
                
                # Extract position info if available
                position = entry.media_info.get('position', 0)
                total = entry.media_info.get('total', 0)
                
                recent_items.append({
                    "title": title,
                    "status": status,
                    "status_text": status_text,
                    "timestamp": entry.timestamp,
                    "position": position,
                    "total": total,
                    "media_type": media_type,
                    "source": source,
                    "log_entry_id": entry.id
                })
            
            # Look for search results and matching patterns
            elif entry.media_info.get('type') == 'final_match':
                title = entry.media_info.get('original_title', 'Unknown')
                matched_title = entry.media_info.get('matched_title', title)
                score = entry.media_info.get('score', 0)
                
                # Determine status based on match score
                if score >= 1.0:
                    status = "available"
                    status_text = "Found Match"
                elif score >= 0.7:
                    status = "requested"
                    status_text = "Partial Match"
                else:
                    status = "not_found"
                    status_text = "Poor Match"
                
                recent_items.append({
                    "title": title,
                    "status": status,
                    "status_text": f"{status_text} ({score:.2f})",
                    "timestamp": entry.timestamp,
                    "position": 0,
                    "total": 0,
                    "media_type": "unknown",
                    "source": "matching",
                    "log_entry_id": entry.id,
                    "matched_title": matched_title,
                    "match_score": score
                })
            
            # Look for list fetch completion
            elif entry.media_info.get('type') == 'list_fetch_complete':
                service = entry.media_info.get('service', 'unknown')
                list_id = entry.media_info.get('list_id', 'unknown')
                item_count = entry.media_info.get('item_count', 0)
                
                recent_items.append({
                    "title": f"{service.upper()}: {list_id}",
                    "status": "available",
                    "status_text": f"Fetched {item_count} items",
                    "timestamp": entry.timestamp,
                    "position": 0,
                    "total": item_count,
                    "media_type": "list",
                    "source": service,
                    "log_entry_id": entry.id
                })
            
            # Look for sync operations
            elif entry.media_info.get('type') in ['sync_start', 'sync_complete']:
                sync_type = entry.media_info.get('type')
                
                if sync_type == 'sync_start':
                    interval = entry.media_info.get('interval_hours', 0)
                    recent_items.append({
                        "title": "Sync Operation",
                        "status": "requested",
                        "status_text": f"Started (every {interval}h)",
                        "timestamp": entry.timestamp,
                        "position": 0,
                        "total": 0,
                        "media_type": "system",
                        "source": "sync",
                        "log_entry_id": entry.id
                    })
                else:  # sync_complete
                    recent_items.append({
                        "title": "Sync Operation",
                        "status": "available",
                        "status_text": "Completed",
                        "timestamp": entry.timestamp,
                        "position": 0,
                        "total": 0,
                        "media_type": "system",
                        "source": "sync",
                        "log_entry_id": entry.id
                    })
        
        # Sort by timestamp (most recent first)
        recent_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit results
        return recent_items[:limit]
        
    except Exception as e:
        print(f"Error parsing recent activity from structured log: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/api/recent-activity")
async def get_recent_activity(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(5, ge=1, le=20, description="Items per page (max 20)"),
    media_only: bool = Query(False, description="Filter to only show media items with position/total info")
):
    """Get recent sync activity from log files with pagination"""
    try:
        # Use the direct log parsing method that reads from logs/listsync-core.log
        all_items = parse_docker_logs_for_activity(limit=100)  # Get more items for pagination
        
        # Convert the format to match what the frontend expects
        formatted_items = []
        for item in all_items:
            # Map the status from parse_docker_logs_for_activity to our expected format
            status_mapping = {
                "already_available": "available",
                "already_requested": "requested", 
                "requested": "requested",
                "skipped": "skipped",
                "error": "not_found"
            }
            
            status_text_mapping = {
                "already_available": "Already Available",
                "already_requested": "Already Requested",
                "requested": "Requested", 
                "skipped": "Skipped",
                "error": "Not Found"
            }
            
            mapped_status = status_mapping.get(item["status"], item["status"])
            mapped_status_text = status_text_mapping.get(item["status"], item.get("action", "Unknown"))
            
            formatted_items.append({
                "title": item["title"],
                "status": mapped_status,
                "status_text": mapped_status_text,
                "timestamp": item["last_synced"],
                "position": item.get("item_number", 0),
                "total": item.get("total_items", 0)
            })
        
        # Filter to only media items if requested (items with position/total info)
        if media_only:
            formatted_items = [
                item for item in formatted_items 
                if item.get('position', 0) > 0 and item.get('total', 0) > 0
            ]
        
        if not formatted_items:
            return {
                "items": [],
                "total_items": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "log_file_used": "logs/listsync-core.log",
                "error": "No recent activity found in log files"
            }
        
        # Calculate pagination
        total_items = len(formatted_items)
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 0
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        # Get paginated items
        paginated_items = formatted_items[start_index:end_index]
        
        return {
            "items": paginated_items,
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "log_file_used": "logs/listsync-core.log"
        }
        
    except Exception as e:
        return {
            "items": [],
            "total_items": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False,
            "error": f"Failed to parse log files: {str(e)}"
        }

@app.get("/api/sync/status/live")
async def get_live_sync_status():
    """Get real-time sync status by checking database"""
    try:
        # Import database function
        from list_sync.database import get_current_sync_status, end_sync_in_db
        import psutil
        from list_sync.utils.sync_status import get_sync_tracker
        
        # Get current sync status from database
        sync_status = get_current_sync_status()
        
        if sync_status and sync_status.get('in_progress') == 1:
            # Sync is currently running
            sync_type = sync_status.get('sync_type', 'unknown')
            status = f"running_{sync_type}" if sync_type != 'unknown' else "running"
            session_id = sync_status.get('session_id')
            pid = sync_status.get('pid')

            # Detect stale "in progress" records (no running process and tracker says idle)
            tracker_running = False
            try:
                tracker_running = get_sync_tracker().is_sync_running()
            except Exception:
                tracker_running = False

            pid_running = False
            if pid:
                try:
                    pid_running = psutil.pid_exists(pid)
                except Exception:
                    pid_running = False

            if not pid_running and not tracker_running:
                # Auto-clear stale state so UI doesn't remain stuck
                try:
                    end_sync_in_db(
                        session_id=session_id,
                        status='completed',
                        total_items=sync_status.get('total_items', 0) or 0,
                        items_requested=sync_status.get('items_requested', 0) or 0,
                        items_skipped=sync_status.get('items_skipped', 0) or 0,
                        items_errors=sync_status.get('items_errors', 0) or 0,
                        error_message="Auto-cleared stale in_progress flag (no running process detected)"
                    )
                except Exception as e:
                    logging.warning(f"Failed to auto-clear stale sync state for {session_id}: {e}")

                return {
                    "is_running": False,
                    "status": "idle",
                    "sync_type": None,
                    "session_id": None,
                    "start_time": None,
                    "duration_seconds": None,
                    "list_type": None,
                    "list_id": None,
                    "pid": None,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate duration if start time is available
            duration = None
            start_time_str = sync_status.get('start_time')
            if start_time_str:
                try:
                    # Parse SQLite timestamp format
                    if isinstance(start_time_str, str):
                        # Handle different timestamp formats
                        if 'T' in start_time_str:
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        else:
                            # SQLite format: YYYY-MM-DD HH:MM:SS
                            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                        duration_seconds = (datetime.now() - start_time).total_seconds()
                        duration = int(duration_seconds)
                except Exception as e:
                    logging.warning(f"Error parsing start_time: {e}")
                    pass
            
            return {
                "is_running": True,
                "status": status,
                "sync_type": sync_type,
                "session_id": sync_status.get('session_id'),
                "start_time": start_time_str,
                "duration_seconds": duration,
                "list_type": sync_status.get('list_type'),
                "list_id": sync_status.get('list_id'),
                "pid": sync_status.get('pid'),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Sync is idle (no sync in progress)
            return {
                "is_running": False,
                "status": "idle",
                "sync_type": None,
                "session_id": None,
                "start_time": None,
                "duration_seconds": None,
                "list_type": None,
                "list_id": None,
                "pid": None,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        print(f"Error getting live sync status: {e}")
        import traceback
        traceback.print_exc()
        return {
            "is_running": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/overseerr/config")
async def get_overseerr_config():
    """Get Overseerr configuration for frontend use"""
    try:
        # Load environment configuration - returns a tuple
        config_tuple = load_env_config()
        overseerr_url, overseerr_api_key, user_id, sync_interval, automated_mode, is_4k = config_tuple
        
        if not overseerr_url:
            return {
                "configured": False,
                "base_url": None,
                "error": "Overseerr URL not configured"
            }
        
        # Clean URL and return base URL for frontend
        base_url = overseerr_url.rstrip('/')
        
        return {
            "configured": True,
            "base_url": base_url,
            "user_id": user_id
        }
    except Exception as e:
        return {
            "configured": False,
            "base_url": None,
            "error": f"Configuration error: {str(e)}"
        }

@app.get("/api/settings/config")
async def get_settings():
    """Get all application settings for the settings page (reads from database or .env)"""
    try:
        from list_sync.config import ConfigManager
        from list_sync import encryption
        
        config = ConfigManager()
        
        # Helper to get and optionally mask sensitive values
        def get_setting_safe(key, default='', mask=False):
            value = config.get_setting(key, default)
            if mask and value:
                return encryption.mask_sensitive_value(str(value))
            return value
        
        # Get all settings (database or env fallback)
        overseerr_url = get_setting_safe('overseerr_url', '')
        overseerr_api_key = get_setting_safe('overseerr_api_key', '', mask=True)
        user_id = get_setting_safe('overseerr_user_id', '1')
        is_4k = get_setting_safe('overseerr_4k', False)
        
        trakt_client_id = get_setting_safe('trakt_client_id', '', mask=True)
        
        sync_interval = get_setting_safe('sync_interval', 24)
        try:
            sync_interval = int(sync_interval)
        except:
            sync_interval = 24
            
        automated_mode = get_setting_safe('auto_sync', True)
        if isinstance(automated_mode, str):
            automated_mode = automated_mode.lower() in ('true', '1', 'yes')
            
        timezone = get_setting_safe('timezone', 'UTC')
        
        discord_webhook = get_setting_safe('discord_webhook', '', mask=True)
        discord_enabled = get_setting_safe('discord_enabled', False)
        if isinstance(discord_enabled, str):
            discord_enabled = discord_enabled.lower() in ('true', '1', 'yes')
        
        frontend_domain = get_setting_safe('frontend_domain', 'http://localhost:3222')
        backend_domain = get_setting_safe('backend_domain', 'http://localhost:4222')
        nuxt_public_api_url = get_setting_safe('nuxt_public_api_url', 'http://localhost:4222')
        
        imdb_lists = get_setting_safe('imdb_lists', '')
        trakt_lists = get_setting_safe('trakt_lists', '')
        trakt_special_lists = get_setting_safe('trakt_special_lists', '')
        
        trakt_special_items_limit = get_setting_safe('trakt_special_items_limit', 20)
        try:
            trakt_special_items_limit = int(trakt_special_items_limit)
        except:
            trakt_special_items_limit = 20
            
        letterboxd_lists = get_setting_safe('letterboxd_lists', '')
        anilist_lists = get_setting_safe('anilist_lists', '')
        mdblist_lists = get_setting_safe('mdblist_lists', '')
        stevenlu_lists = get_setting_safe('stevenlu_lists', '')
        tmdb_key = get_setting_safe('tmdb_key', '', mask=True)
        tmdb_lists = get_setting_safe('tmdb_lists', '')
        tvdb_lists = get_setting_safe('tvdb_lists', '')
        simkl_lists = get_setting_safe('simkl_lists', '')
        
        return {
            # Overseerr Configuration
            "overseerr_url": overseerr_url or '',
            "overseerr_api_key": overseerr_api_key or '',
            "overseerr_user_id": user_id or '1',
            "overseerr_4k": is_4k,
            
            # Sync Settings
            "sync_interval": sync_interval,
            "auto_sync": automated_mode,
            "timezone": timezone,
            
            # Notifications
            "discord_webhook": discord_webhook,
            "discord_enabled": bool(discord_webhook),
            
            # Trakt API
            "trakt_client_id": trakt_client_id,
            
            # Service Endpoints
            "frontend_domain": frontend_domain,
            "backend_domain": backend_domain,
            "nuxt_public_api_url": nuxt_public_api_url,
            
            # Content Sources
            "imdb_lists": imdb_lists,
            "trakt_lists": trakt_lists,
            "trakt_special_lists": trakt_special_lists,
            "trakt_special_items_limit": trakt_special_items_limit,
            "letterboxd_lists": letterboxd_lists,
            "anilist_lists": anilist_lists,
            "mdblist_lists": mdblist_lists,
            "stevenlu_lists": stevenlu_lists,
            "tmdb_key": tmdb_key,
            "tmdb_lists": tmdb_lists,
            "tvdb_lists": tvdb_lists,
            "simkl_lists": simkl_lists,
        }
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        return {
            # Overseerr Configuration
            "overseerr_url": '',
            "overseerr_api_key": '',
            "overseerr_user_id": '1',
            "overseerr_4k": False,
            
            # Sync Settings
            "sync_interval": 24,
            "auto_sync": True,
            "timezone": 'UTC',
            
            # Notifications
            "discord_webhook": '',
            "discord_enabled": False,
            
            # Trakt API
            "trakt_client_id": '',
            
            # Service Endpoints
            "frontend_domain": 'http://localhost:3222',
            "backend_domain": 'http://localhost:4222',
            "nuxt_public_api_url": 'http://localhost:4222',
            
            # Content Sources
            "imdb_lists": '',
            "trakt_lists": '',
            "trakt_special_lists": '',
            "trakt_special_items_limit": 20,
            "letterboxd_lists": '',
            "anilist_lists": '',
            "mdblist_lists": '',
            "stevenlu_lists": '',
            "tmdb_key": '',
            "tmdb_lists": '',
            "tvdb_lists": '',
            "simkl_lists": '',
        }

@app.post("/api/settings/config")
async def update_settings(settings: dict):
    """
    Update application settings - saves to database with encryption for sensitive fields.
    Changes take effect immediately (no restart required).
    
    Note: Masked values (****...) from sensitive fields are automatically detected
    and skipped to preserve existing encrypted values in the database.
    """
    try:
        from list_sync.config import ConfigManager
        
        config = ConfigManager()
        
        logging.info(f"Saving {len(settings)} settings to database")
        
        # Save all settings to database
        # The save_setting method will automatically skip masked placeholders
        # for sensitive fields to prevent overwriting real API keys
        for key, value in settings.items():
            config.save_setting(key, value)
        
        # Also update sync_interval table for compatibility
        if 'sync_interval' in settings:
            try:
                interval = int(settings['sync_interval'])
                configure_sync_interval(interval)
            except:
                pass
        
        logging.info(f"Settings update complete: {len(settings)} fields processed")
        
        return {
            "success": True,
            "message": "Settings saved successfully to database. Changes are active immediately!",
            "settings_updated": len(settings)
        }
    except Exception as e:
        logging.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notifications/test")
async def test_discord_notification(payload: dict = None):
    """Send a test Discord notification to verify webhook configuration"""
    try:
        # Get Discord webhook URL from request body or environment
        webhook_url = None
        if payload and 'webhook_url' in payload:
            webhook_url = payload['webhook_url']
        
        if not webhook_url:
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
        
        if not webhook_url:
            raise HTTPException(
                status_code=400, 
                detail="Discord webhook URL is required. Please provide a webhook URL or set DISCORD_WEBHOOK_URL in your environment variables."
            )
        
        # Try to use the discord-webhook library if available
        try:
            from discord_webhook import DiscordWebhook, DiscordEmbed
            from datetime import datetime
            
            # Create webhook instance - explicitly set content to None to avoid duplicate messages
            webhook = DiscordWebhook(url=webhook_url, username="ListSync Test", content=None)
            
            # Create embed with test message
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed = DiscordEmbed(
                title="🧪 Discord Integration Test",
                description="If you see this message, Discord notifications are working correctly! ✅",
                color=10181046  # Purple color
            )
            
            embed.add_embed_field(
                name="Test Time",
                value=current_time,
                inline=True
            )
            
            embed.add_embed_field(
                name="Status",
                value="✅ Connected",
                inline=True
            )
            
            embed.set_footer(text="ListSync Notification System")
            embed.set_timestamp()
            
            # Add embed to webhook (only embed, no content)
            webhook.add_embed(embed)
            
            # Send webhook
            response = webhook.execute()
            
            return {
                "success": True,
                "message": "Test notification sent successfully! Check your Discord channel.",
                "timestamp": current_time
            }
            
        except ImportError:
            # Fallback to using requests directly
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Only send embed, no content to avoid duplicate messages
            payload = {
                "embeds": [{
                    "title": "🧪 Discord Integration Test",
                    "description": "If you see this message, Discord notifications are working correctly! ✅",
                    "color": 10181046,
                    "fields": [
                        {
                            "name": "Test Time",
                            "value": current_time,
                            "inline": True
                        },
                        {
                            "name": "Status",
                            "value": "✅ Connected",
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "ListSync Notification System"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": "Test notification sent successfully! Check your Discord channel.",
                "timestamp": current_time
            }
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Discord webhook request timed out")
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to send Discord notification: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" (Status: {e.response.status_code})"
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        import traceback
        error_detail = f"Failed to send test notification: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_detail)
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

def enrich_historic_data_with_database(historic_items):
    """Enrich historic log data with database fields (overseerr_id, imdb_id, year, media_type)"""
    if not os.path.exists(DB_FILE):
        return historic_items
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all database items with their IDs, year, and source list info
        try:
            cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status, year, source_list_type, source_list_id FROM synced_items")
            db_items = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If year or source list columns don't exist, try without them
            print(f"Warning: Could not fetch all columns from database: {e}")
            try:
                cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status, year FROM synced_items")
                db_items_without_source = cursor.fetchall()
                # Convert to format with source_list_type and source_list_id as None
                db_items = [(title, media_type, imdb_id, overseerr_id, status, year, None, None) 
                           for title, media_type, imdb_id, overseerr_id, status, year in db_items_without_source]
            except sqlite3.OperationalError:
                # If year column also doesn't exist
                cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status FROM synced_items")
                db_items_minimal = cursor.fetchall()
                # Convert to format with year, source_list_type and source_list_id as None
                db_items = [(title, media_type, imdb_id, overseerr_id, status, None, None, None) 
                           for title, media_type, imdb_id, overseerr_id, status in db_items_minimal]
        
        conn.close()
        
        # Create lookup dictionaries for database items
        # Try both possible media types since log parsing might be wrong
        db_lookup = {}
        db_lookup_by_title = {}  # Fallback lookup by title only
        
        for title, media_type, imdb_id, overseerr_id, status, year, source_list_type, source_list_id in db_items:
            key = f"{title.lower().strip()}_{media_type}"
            title_key = title.lower().strip()
            
            if key not in db_lookup:
                db_lookup[key] = {
                    "media_type": media_type,
                    "imdb_id": imdb_id,
                    "overseerr_id": overseerr_id,
                    "db_status": status,
                    "year": year,
                    "source_list_type": source_list_type,
                    "source_list_id": source_list_id
                }
            
            # Store by title only as fallback (prefer more recent entries)
            if title_key not in db_lookup_by_title:
                db_lookup_by_title[title_key] = {
                    "media_type": media_type,
                    "imdb_id": imdb_id,
                    "overseerr_id": overseerr_id,
                    "db_status": status,
                    "year": year,
                    "source_list_type": source_list_type,
                    "source_list_id": source_list_id
                }
        
        print(f"DEBUG: Loaded {len(db_lookup)} items from database, sample years: {[v['year'] for v in list(db_lookup.values())[:5]]}")
        
        # Enrich historic items with database information
        for item in historic_items:
            lookup_key = f"{item['title'].lower().strip()}_{item['media_type']}"
            title_only_key = item['title'].lower().strip()
            
            db_data = None
            
            # First try exact match (title + media_type)
            if lookup_key in db_lookup:
                db_data = db_lookup[lookup_key]
            # Fallback to title-only match (media_type might be wrong from log parsing)
            elif title_only_key in db_lookup_by_title:
                db_data = db_lookup_by_title[title_only_key]
                print(f"DEBUG: Using title-only match for '{item['title']}': log={item['media_type']}, db={db_data['media_type']}")
            
            if db_data:
                # Use database media_type as the authoritative source
                item['media_type'] = db_data['media_type']
                item['imdb_id'] = db_data['imdb_id']
                item['overseerr_id'] = db_data['overseerr_id']
                item['db_status'] = db_data['db_status']
                item['source_list_type'] = db_data.get('source_list_type')
                item['source_list_id'] = db_data.get('source_list_id')
                # Use database year if available (it's more reliable than log parsing)
                if db_data['year']:
                    item['year'] = db_data['year']
            else:
                item['imdb_id'] = None
                item['overseerr_id'] = None
                item['db_status'] = None
                item['source_list_type'] = None
                item['source_list_id'] = None
                # Keep the media_type and year from log parsing if no database match
        
        return historic_items
        
    except Exception as e:
        print(f"Error enriching historic data with database: {e}")
        import traceback
        traceback.print_exc()
        # Return original data if enrichment fails
        for item in historic_items:
            if not item.get('imdb_id'):
                item['imdb_id'] = None
            if not item.get('overseerr_id'):
                item['overseerr_id'] = None
            if not item.get('db_status'):
                item['db_status'] = None
            if not item.get('source_list_type'):
                item['source_list_type'] = None
            if not item.get('source_list_id'):
                item['source_list_id'] = None
        return historic_items


# ==========================================
# SYNC HISTORY - Log Parser
# ==========================================

from dataclasses import dataclass, field, asdict
from enum import Enum

class SyncType(Enum):
    FULL = "full"
    SINGLE = "single"

class ItemStatus(Enum):
    REQUESTED = "requested"
    ALREADY_AVAILABLE = "already_available"
    ALREADY_REQUESTED = "already_requested"
    SKIPPED = "skipped"
    NOT_FOUND = "not_found"
    ERROR = "error"

@dataclass
class SyncList:
    """Represents a list that was synced."""
    type: str
    id: str
    url: Optional[str] = None
    item_count: int = 0

@dataclass
class SyncItem:
    """Represents an individual item processed during sync."""
    title: str
    status: str
    progress_number: int
    progress_total: int
    timestamp: str
    year: Optional[int] = None
    media_type: str = "movie"
    error_details: Optional[str] = None

@dataclass
class SyncResults:
    """Results summary for a sync session."""
    requested: int = 0
    already_available: int = 0
    already_requested: int = 0
    skipped: int = 0
    not_found: int = 0
    error: int = 0

@dataclass
class SyncSession:
    """Complete sync session data."""
    id: str
    type: SyncType
    start_timestamp: str
    end_timestamp: Optional[str] = None
    duration: Optional[float] = None
    version: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    lists: List[SyncList] = field(default_factory=list)
    results: SyncResults = field(default_factory=SyncResults)
    items: List[SyncItem] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    not_found_items: List[str] = field(default_factory=list)
    average_time_ms: Optional[float] = None
    total_time_seconds: Optional[float] = None
    status: str = "in_progress"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['type'] = self.type.value
        return data

class SyncLogParser:
    """Parser for sync log files."""
    
    # Patterns for detecting log elements
    TIMESTAMP_PATTERN = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)'
    
    # Session markers
    FULL_SYNC_START = r'📊\s+Total unique media items ready for sync:\s*(\d+)'
    SINGLE_SYNC_START = r'🎯\s+Single List Sync:\s*(.+)'
    # Alternative patterns for different log formats
    SINGLE_SYNC_START_ALT = r'Starting single list sync for\s+(.+)'
    SYNC_SUMMARY_START = r'(Soluify - List Sync Summary|={50,})'
    SYNC_SUMMARY_DASHES = r'^[-─═]{50,}$'
    # Sync complete markers (new format)
    SYNC_COMPLETE_PATTERN = r'==========\s+SYNC COMPLETE\s+\[(FULL|SINGLE)\]\s+- Session:\s+([^\s]+)\s+(?:- List:\s+[^\s]+\s+)?- Status:\s+(\w+)\s+=========='
    # Pattern to detect "Not Found Items" section header (optional - only if there are failures)
    NOT_FOUND_SECTION = r'Not Found Items \((\d+)\)'
    
    # List fetching
    # Updated to handle the new message format with "(check backend logs...)" suffix
    LIST_FETCH_START = r'🔍\s+Fetching items from (\w+) list:\s+(.+?)(?:\.\.\.|\.\.\.?\s+\(check backend logs|$)'
    LIST_FETCH_SUCCESS = r'✅\s+Found (\d+) items in (\w+) list:\s+(.+?)$'
    
    # Processing
    PROCESSING_START = r'🎬\s+Processing (\d+) media items'
    
    # Item status patterns with emojis
    ITEM_PATTERNS = [
        (r'✅\s+(.+?):\s*(?:Successfully\s+)?Requested\s*\((\d+)/(\d+)\)', ItemStatus.REQUESTED.value),
        (r'☑️\s+(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_AVAILABLE.value),
        (r'📌\s+(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_REQUESTED.value),
        (r'⏭️\s+(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', ItemStatus.SKIPPED.value),
        (r'❓\s+(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', ItemStatus.NOT_FOUND.value),
        (r'❌\s+(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', ItemStatus.ERROR.value),
    ]
    
    # Alternative item status patterns for different log formats (after timestamp stripping)
    ITEM_PATTERNS_ALT = [
        (r'-\s+\w+\s+-\s+(.+?):\s*(?:Successfully\s+)?Requested\s*\((\d+)/(\d+)\)', ItemStatus.REQUESTED.value),
        (r'-\s+\w+\s+-\s+(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_AVAILABLE.value),
        (r'-\s+\w+\s+-\s+(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_REQUESTED.value),
        (r'-\s+\w+\s+-\s+(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', ItemStatus.SKIPPED.value),
        (r'-\s+\w+\s+-\s+(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', ItemStatus.NOT_FOUND.value),
        (r'-\s+\w+\s+-\s+(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', ItemStatus.ERROR.value),
    ]
    
    # Summary patterns
    TOTAL_TIME_PATTERN = r'Total Time:\s*(\d+)m\s*(\d+)s'
    AVG_TIME_PATTERN = r'Avg Time:\s*([\d.]+)ms/item'
    RESULT_PATTERN = r'[✅☑️📌⏭️❌]\s*(\w+(?:\s+\w+)?):\s*(\d+)'
    MEDIA_TYPE_PATTERN = r'(Movies|TV Shows):\s*(\d+)\s*\(([\d.]+)%\)'
    SYNCED_LIST_PATTERN = r'📋\s+(\w+):\s+(https?://\S+)'
    NOT_FOUND_ITEM_PATTERN = r'•\s+(.+?)\s*\((Error:|Not Found)'
    
    # Version
    VERSION_PATTERN = r'Soluify\s*-\s*\{(.+?)\}'
    
    def __init__(self):
        self.sessions: List[SyncSession] = []
    
    def extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        match = re.match(self.TIMESTAMP_PATTERN, line)
        if match:
            try:
                # Handle both formats: with and without milliseconds
                timestamp_str = match.group(1)
                if ',' in timestamp_str:
                    # Format: YYYY-MM-DD HH:MM:SS,mmm
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                else:
                    # Format: YYYY-MM-DD HH:MM:SS
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                return dt.isoformat()
            except:
                return None
        return None
    
    def detect_session_start(self, line: str) -> Optional[tuple]:
        """Detect if line marks start of a sync session."""
        full_match = re.search(self.FULL_SYNC_START, line)
        if full_match:
            return (SyncType.FULL, {'total_items': int(full_match.group(1))})
        
        # Try emoji-based pattern first
        single_match = re.search(self.SINGLE_SYNC_START, line)
        if single_match:
            # Capture everything after "Single List Sync:"
            list_info = single_match.group(1).strip()
            
            # Try to parse as TYPE:ID format, but accept any format
            if ':' in list_info:
                parts = list_info.split(':', 1)
                list_type = parts[0].strip()
                list_id = parts[1].strip()
            else:
                # If no colon, use the whole string as list_id
                list_type = 'UNKNOWN'
                list_id = list_info
            
            return (SyncType.SINGLE, {'list_type': list_type, 'list_id': list_id})
        
        # Try alternative pattern for different log formats
        single_match_alt = re.search(self.SINGLE_SYNC_START_ALT, line)
        if single_match_alt:
            # Capture everything after "Starting single list sync for"
            list_info = single_match_alt.group(1).strip()
            
            # Try to parse as TYPE:ID format, but accept any format
            if ':' in list_info:
                parts = list_info.split(':', 1)
                list_type = parts[0].strip()
                list_id = parts[1].strip()
            else:
                # If no colon, use the whole string as list_id
                list_type = 'UNKNOWN'
                list_id = list_info
            
            return (SyncType.SINGLE, {'list_type': list_type, 'list_id': list_id})
        
        return None
    
    def detect_session_end(self, line: str, session_type: SyncType) -> bool:
        """Detect if line marks end of a sync session."""
        # Check for new SYNC COMPLETE marker first (most reliable)
        if re.search(self.SYNC_COMPLETE_PATTERN, line):
            return True
        # Fallback to old patterns: "Soluify - List Sync Summary" or the dashed line separator
        return bool(re.search(self.SYNC_SUMMARY_START, line) or 
                   re.search(self.SYNC_SUMMARY_DASHES, line))
    
    def parse_list_fetch(self, line: str) -> Optional[tuple]:
        """Parse list fetching line."""
        # Try the updated pattern first (handles new message format)
        fetch_match = re.search(self.LIST_FETCH_START, line)
        if fetch_match:
            list_type = fetch_match.group(1)
            list_id = fetch_match.group(2).strip()
            # Clean up list_id - remove trailing dots and any parenthetical text
            list_id = re.sub(r'\.\.\.+.*$', '', list_id).strip()
            list_id = re.sub(r'\s*\(.*$', '', list_id).strip()
            return (list_type, list_id, None)
        
        success_match = re.search(self.LIST_FETCH_SUCCESS, line)
        if success_match:
            return (success_match.group(2), success_match.group(3), int(success_match.group(1)))
        
        return None
    
    
    def parse_item_status(self, line: str, timestamp: str) -> Optional[SyncItem]:
        """Parse an item processing line."""
        # Try emoji-based patterns first
        for pattern, status in self.ITEM_PATTERNS:
            match = re.search(pattern, line)
            if match:
                title = match.group(1).strip()
                progress_num = int(match.group(2))
                progress_total = int(match.group(3))
                
                # Extract year from title
                year = None
                year_match = re.search(r'\((\d{4})\)|\s(\d{4})$', title)
                if year_match:
                    year = int(year_match.group(1) or year_match.group(2))
                    title = re.sub(r'\s*\(?\d{4}\)?$', '', title).strip()
                
                # Extract error details for error status
                error_details = None
                if status == ItemStatus.ERROR.value:
                    error_match = re.search(r'Error:\s*(.+)$', line)
                    if error_match:
                        error_details = error_match.group(1).strip()
                
                return SyncItem(
                    title=title,
                    status=status,
                    progress_number=progress_num,
                    progress_total=progress_total,
                    timestamp=timestamp,
                    year=year,
                    error_details=error_details
                )
        
        # Try alternative patterns for different log formats
        for pattern, status in self.ITEM_PATTERNS_ALT:
            match = re.search(pattern, line)
            if match:
                title = match.group(1).strip()  # Group 1 is the title in alternative patterns
                progress_num = int(match.group(2))  # Group 2 is progress number
                progress_total = int(match.group(3))  # Group 3 is progress total
                
                # Extract year from title
                year = None
                year_match = re.search(r'\((\d{4})\)|\s(\d{4})$', title)
                if year_match:
                    year = int(year_match.group(1) or year_match.group(2))
                    title = re.sub(r'\s*\(?\d{4}\)?$', '', title).strip()
                
                # Extract error details for error status
                error_details = None
                if status == ItemStatus.ERROR.value:
                    error_match = re.search(r'Error:\s*(.+)$', line)
                    if error_match:
                        error_details = error_match.group(1).strip()
                
                return SyncItem(
                    title=title,
                    status=status,
                    progress_number=progress_num,
                    progress_total=progress_total,
                    timestamp=timestamp,
                    year=year,
                    error_details=error_details
                )
        
        return None
    
    def parse_log_file(self, log_path: str) -> List[SyncSession]:
        """Parse entire log file and extract all sync sessions."""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []
        
        sessions = []
        current_session: Optional[SyncSession] = None
        current_lists: Dict[str, SyncList] = {}
        summary_lines: List[str] = []
        in_summary = False
        last_timestamp_in_session: Optional[str] = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            timestamp = self.extract_timestamp(line)
            
            # Strip timestamp from line content for pattern matching
            line_content = line
            if timestamp:
                # Remove the timestamp prefix (format: "YYYY-MM-DD HH:MM:SS ")
                line_content = re.sub(self.TIMESTAMP_PATTERN, '', line).strip()
            
            # Track last timestamp for current session (but don't set as end yet)
            if current_session and timestamp:
                last_timestamp_in_session = timestamp
            
            # Detect session start
            session_start = self.detect_session_start(line_content)
            if session_start:
                # Save previous session if exists
                if current_session:
                    # Calculate duration before saving
                    if current_session.start_timestamp and current_session.end_timestamp:
                        try:
                            start = datetime.fromisoformat(current_session.start_timestamp)
                            end = datetime.fromisoformat(current_session.end_timestamp)
                            current_session.duration = (end - start).total_seconds()
                        except:
                            pass
                    
                    current_session.status = "completed"
                    current_session.processed_items = len(current_session.items)
                    sessions.append(current_session)
                
                # Start new session
                session_type, metadata = session_start
                session_id = f"sync_{timestamp}_{session_type.value}"
                
                current_session = SyncSession(
                    id=session_id,
                    type=session_type,
                    start_timestamp=timestamp or datetime.now().isoformat(),
                    total_items=metadata.get('total_items', 0)
                )
                
                current_lists = {}
                in_summary = False
                summary_lines = []
                last_timestamp_in_session = timestamp
                continue
            
            if not current_session:
                continue
            
            # Extract version
            if not current_session.version:
                version_match = re.search(self.VERSION_PATTERN, line_content)
                if version_match:
                    current_session.version = version_match.group(1)
            
            # Parse processing start to get total items for single syncs
            processing_match = re.search(self.PROCESSING_START, line_content)
            if processing_match and current_session.type == SyncType.SINGLE:
                total_items = int(processing_match.group(1))
                current_session.total_items = total_items
                print(f"DEBUG - Single sync total items: {total_items}")
            
            # Parse list fetching
            list_info = self.parse_list_fetch(line_content)
            if list_info:
                list_type, list_id, item_count = list_info
                
                list_key = f"{list_type}:{list_id}"
                if list_key not in current_lists:
                    current_lists[list_key] = SyncList(
                        type=list_type,
                        id=list_id,
                        item_count=0
                    )
                
                if item_count is not None:
                    current_lists[list_key].item_count = item_count
                    if current_lists[list_key] not in current_session.lists:
                        current_session.lists.append(current_lists[list_key])
            
            # Parse item status
            item = self.parse_item_status(line_content, timestamp or datetime.now().isoformat())
            if item:
                current_session.items.append(item)
                # Debug output removed for production
                
                # Update results
                if item.status == ItemStatus.REQUESTED.value:
                    current_session.results.requested += 1
                elif item.status == ItemStatus.ALREADY_AVAILABLE.value:
                    current_session.results.already_available += 1
                elif item.status == ItemStatus.ALREADY_REQUESTED.value:
                    current_session.results.already_requested += 1
                elif item.status == ItemStatus.SKIPPED.value:
                    current_session.results.skipped += 1
                elif item.status == ItemStatus.NOT_FOUND.value:
                    current_session.results.not_found += 1
                elif item.status == ItemStatus.ERROR.value:
                    current_session.results.error += 1
                    current_session.errors.append({
                        'title': item.title,
                        'error': item.error_details or 'Unknown error',
                        'timestamp': item.timestamp
                    })
            # Item parsing completed
            
            # Detect summary section start
            if re.search(self.SYNC_SUMMARY_START, line_content) or re.search(self.SYNC_SUMMARY_DASHES, line_content):
                in_summary = True
                summary_lines = []
                continue
            
            if in_summary:
                summary_lines.append(line_content)
            
            
            # Detect session end
            if self.detect_session_end(line_content, current_session.type):
                # Session end detected
                # Set end timestamp to the current line's timestamp (preferred) or last seen
                # The SYNC COMPLETE marker should have a timestamp, so use it if available
                if timestamp:
                    current_session.end_timestamp = timestamp
                elif last_timestamp_in_session:
                    current_session.end_timestamp = last_timestamp_in_session
                else:
                    # Fallback to current time if no timestamp found
                    current_session.end_timestamp = datetime.now().isoformat()
                
                # Calculate duration if both timestamps exist
                if current_session.start_timestamp and current_session.end_timestamp:
                    try:
                        start = datetime.fromisoformat(current_session.start_timestamp)
                        end = datetime.fromisoformat(current_session.end_timestamp)
                        current_session.duration = (end - start).total_seconds()
                    except Exception as e:
                        logging.warning(f"Failed to calculate duration: {e}")
                        pass
                
                current_session.status = "completed"
                current_session.processed_items = len(current_session.items)
                sessions.append(current_session)
                current_session = None
                in_summary = False
                last_timestamp_in_session = None
        
        # Handle unclosed session
        if current_session:
            # Calculate duration if both timestamps exist
            if current_session.start_timestamp and current_session.end_timestamp:
                try:
                    start = datetime.fromisoformat(current_session.start_timestamp)
                    end = datetime.fromisoformat(current_session.end_timestamp)
                    current_session.duration = (end - start).total_seconds()
                    
                    # If session has an end timestamp and it's been more than 2 minutes since then,
                    # and we have processed items, consider it completed
                    time_since_end = (datetime.now() - end).total_seconds()
                    if time_since_end > 120 and len(current_session.items) > 0:
                        current_session.status = "completed"
                    else:
                        current_session.status = "in_progress"
                except:
                    current_session.status = "in_progress"
            else:
                # No end timestamp - check if session looks complete
                # If we have processed items and the session started more than 5 minutes ago,
                # and there's a summary section, consider it completed
                if len(current_session.items) > 0 and current_session.start_timestamp:
                    try:
                        start = datetime.fromisoformat(current_session.start_timestamp)
                        time_since_start = (datetime.now() - start).total_seconds()
                        
                        # If session has results tallied (indicating summary was parsed)
                        # OR it's been more than 10 minutes and we have items processed
                        # consider it completed
                        has_results = (current_session.results.requested > 0 or 
                                     current_session.results.already_available > 0 or
                                     current_session.results.skipped > 0 or
                                     current_session.results.not_found > 0)
                        
                        if has_results or time_since_start > 600:
                            current_session.status = "completed"
                        else:
                            current_session.status = "in_progress"
                    except:
                        current_session.status = "in_progress"
                else:
                    current_session.status = "in_progress"
            
            current_session.processed_items = len(current_session.items)
            # Session completed
            sessions.append(current_session)
        
        return sessions


# ==========================================
# SYNC HISTORY - API Endpoints
# ==========================================

@app.get("/api/sync-history")
async def get_sync_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, regex="^(full|single)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get list of sync sessions with filtering and pagination.
    
    Parameters:
    - limit: Maximum number of sessions to return (1-100, default 50)
    - offset: Pagination offset (default 0)
    - type: Filter by sync type ('full' or 'single')
    - start_date: Filter sessions after this date (ISO format)
    - end_date: Filter sessions before this date (ISO format)
    """
    parser = SyncLogParser()
    
    # Try different log locations (check most recent first)
    log_paths = [
        "/var/log/supervisor/listsync-core.log",
        "logs/listsync-core.log",
        "/usr/src/app/logs/listsync-core.log",
        "data/list_sync.log"
    ]
    
    sessions = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                # Force fresh read by checking file modification time
                # This ensures we get the latest sync data
                sessions = parser.parse_log_file(log_path)
                break
            except Exception as e:
                logging.error(f"Error parsing log file {log_path}: {e}")
                continue
    
    # Filter by type
    if type:
        sessions = [s for s in sessions if s.type.value == type]
    
    # Filter by date range
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            sessions = [s for s in sessions if datetime.fromisoformat(s.start_timestamp) >= start_dt]
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            sessions = [s for s in sessions if datetime.fromisoformat(s.start_timestamp) <= end_dt]
        except:
            pass
    
    # Don't filter out sessions - show all syncs even if lists weren't parsed correctly
    # The stats endpoint counts all sessions, so we should too for consistency
    # If a session doesn't have lists but has items/results, it's still a valid sync
    # Only filter out completely empty sessions (no items, no results, no lists)
    def is_valid_session(session):
        # Session is valid if it has lists, items, or results
        has_lists = session.lists and len(session.lists) > 0
        has_items = len(session.items) > 0
        has_results = (session.results.requested > 0 or 
                      session.results.already_available > 0 or
                      session.results.already_requested > 0 or
                      session.results.skipped > 0 or
                      session.results.not_found > 0 or
                      session.results.error > 0)
        return has_lists or has_items or has_results
    
    sessions = [s for s in sessions if is_valid_session(s)]
    
    # Sort by most recent first
    sessions.sort(key=lambda x: x.start_timestamp, reverse=True)
    
    # Pagination
    total = len(sessions)
    sessions = sessions[offset:offset + limit]
    
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/sync-history/stats")
async def get_sync_history_stats():
    """Get aggregate statistics about sync history."""
    parser = SyncLogParser()
    
    log_paths = [
        "/var/log/supervisor/listsync-core.log",
        "logs/listsync-core.log",
        "/usr/src/app/logs/listsync-core.log",
        "data/list_sync.log"
    ]
    
    sessions = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                sessions = parser.parse_log_file(log_path)
                break
            except Exception as e:
                logging.error(f"Error parsing log file {log_path} for stats: {e}")
                continue
    
    if not sessions:
        return {"error": "No sync sessions found"}
    
    # Apply same filtering as main endpoint for consistency
    def is_valid_session(session):
        has_lists = session.lists and len(session.lists) > 0
        has_items = len(session.items) > 0
        has_results = (session.results.requested > 0 or 
                      session.results.already_available > 0 or
                      session.results.already_requested > 0 or
                      session.results.skipped > 0 or
                      session.results.not_found > 0 or
                      session.results.error > 0)
        return has_lists or has_items or has_results
    
    sessions = [s for s in sessions if is_valid_session(s)]
    
    if not sessions:
        return {"error": "No valid sync sessions found"}
    
    # Calculate statistics
    total_sessions = len(sessions)
    full_syncs = len([s for s in sessions if s.type.value == "full"])
    single_syncs = len([s for s in sessions if s.type.value == "single"])
    
    total_items = sum(s.processed_items for s in sessions)
    total_requested = sum(s.results.requested for s in sessions)
    total_errors = sum(s.results.error for s in sessions)
    
    # Success rate
    success_rate = ((total_items - total_errors) / total_items * 100) if total_items > 0 else 0
    
    # Average per sync
    avg_items = total_items / total_sessions if total_sessions > 0 else 0
    
    # Recent syncs (last 24h, 7d, 30d) - use timedelta for accurate time comparison
    from datetime import timedelta
    now = datetime.now()
    last_24h = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)) < timedelta(days=1)]
    last_7d = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)) < timedelta(days=7)]
    last_30d = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)) < timedelta(days=30)]
    
    # Most synced lists
    list_counts = {}
    for session in sessions:
        if session.lists:  # Only iterate if lists exist
            for lst in session.lists:
                key = f"{lst.type}:{lst.id}"
                list_counts[key] = list_counts.get(key, 0) + 1
    
    most_synced = sorted(list_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Average duration - try to calculate for sessions that don't have it
    for session in sessions:
        if session.duration is None and session.start_timestamp and session.end_timestamp:
            try:
                start = datetime.fromisoformat(session.start_timestamp)
                end = datetime.fromisoformat(session.end_timestamp)
                session.duration = (end - start).total_seconds()
            except:
                pass
    
    # Filter valid durations
    durations = [s.duration for s in sessions if s.duration is not None and s.duration > 0]
    avg_duration = sum(durations) / len(durations) if durations else None
    
    return {
        "total_sessions": total_sessions,
        "full_syncs": full_syncs,
        "single_syncs": single_syncs,
        "total_items_processed": total_items,
        "total_requested": total_requested,
        "total_errors": total_errors,
        "success_rate": round(success_rate, 2),
        "avg_items_per_sync": round(avg_items, 2),
        "avg_duration_seconds": round(avg_duration, 2) if avg_duration is not None else None,
        "recent_stats": {
            "last_24h": len(last_24h),
            "last_7d": len(last_7d),
            "last_30d": len(last_30d)
        },
        "most_synced_lists": [
            {"list": lst, "count": count} for lst, count in most_synced
        ]
    }


@app.get("/api/sync-history/{session_id}")
async def get_sync_session(session_id: str):
    """Get detailed information about a specific sync session."""
    parser = SyncLogParser()
    
    log_paths = [
        "/var/log/supervisor/listsync-core.log",
        "logs/listsync-core.log",
        "/usr/src/app/logs/listsync-core.log",
        "data/list_sync.log"
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            sessions = parser.parse_log_file(log_path)
            session = next((s for s in sessions if s.id == session_id), None)
            
            if session:
                return session.to_dict()
            break
    
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/logs/live")
async def get_live_logs(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(200, ge=1, le=500, description="Lines per page (max 500)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc")
):
    """Get live log content from the core log file with pagination."""
    try:
        # Try different log locations
        log_paths = [
            "/var/log/supervisor/listsync-core.log",
            "logs/listsync-core.log",
            "/usr/src/app/logs/listsync-core.log",
            "data/list_sync.log"
        ]
        
        log_content = ""
        log_file_used = None
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    log_file_used = log_path
                    break
                except Exception as e:
                    print(f"Error reading log file {log_path}: {e}")
                    continue
        
        if not log_content:
            return {
                "success": False,
                "error": "No log file found",
                "lines": [],
                "total_lines": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        
        # Split into lines
        all_lines = log_content.strip().split('\n')
        total_lines = len(all_lines)
        
        # Calculate pagination
        total_pages = (total_lines + limit - 1) // limit  # Ceiling division
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Get the requested page of lines
        if sort_order == "desc":
            # Reverse order (newest first)
            lines = all_lines[::-1][start_idx:end_idx]
        else:
            # Normal order (oldest first)
            lines = all_lines[start_idx:end_idx]
        
        return {
            "success": True,
            "lines": lines,
            "total_lines": total_lines,
            "file_size": len(log_content),
            "file_path": log_file_used,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "sort_order": sort_order
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "lines": [],
            "total_lines": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }


@app.get("/api/logs/backend")
async def get_backend_logs(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(200, ge=1, le=500, description="Lines per page (max 500)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc")
):
    """Get backend log content from the data/list_sync.log file with pagination."""
    try:
        # Backend log file path
        log_path = "data/list_sync.log"
        
        if not os.path.exists(log_path):
            return {
                "success": False,
                "error": "Backend log file not found",
                "lines": [],
                "total_lines": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        
        # Read the log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        # Split into lines
        all_lines = log_content.strip().split('\n')
        total_lines = len(all_lines)
        
        # Calculate pagination
        total_pages = (total_lines + limit - 1) // limit  # Ceiling division
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Get the requested page of lines
        if sort_order == "desc":
            # Reverse order (newest first)
            lines = all_lines[::-1][start_idx:end_idx]
        else:
            # Normal order (oldest first)
            lines = all_lines[start_idx:end_idx]
        
        return {
            "success": True,
            "lines": lines,
            "total_lines": total_lines,
            "file_size": len(log_content),
            "file_path": log_path,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "sort_order": sort_order
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "lines": [],
            "total_lines": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }


@app.get("/api/logs/rotation-info")
async def get_log_rotation_info():
    """Get information about log rotation status."""
    try:
        from list_sync.utils.log_rotation import get_log_rotator
        
        rotator = get_log_rotator()
        info = rotator.get_log_file_info()
        
        return {
            "success": True,
            "rotation_info": info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rotation_info": None
        }


@app.get("/api/logs/rotate")
async def rotate_logs():
    """Manually trigger log rotation."""
    try:
        from list_sync.utils.log_rotation import check_and_rotate_logs
        
        success = check_and_rotate_logs()
        
        return {
            "success": success,
            "message": "Log rotation completed" if success else "No rotation needed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Log rotation failed"
        }


@app.get("/api/sync-history/{session_id}/raw-logs")
async def get_sync_session_raw_logs(session_id: str):
    """Get raw log lines for a specific sync session."""
    parser = SyncLogParser()
    
    log_paths = [
        "/var/log/supervisor/listsync-core.log",
        "logs/listsync-core.log",
        "/usr/src/app/logs/listsync-core.log",
        "data/list_sync.log"
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Parse to find the session
                sessions = parser.parse_log_file(log_path)
                session = next((s for s in sessions if s.id == session_id), None)
                
                if not session:
                    continue
                
                # Find log lines that belong to this session by timestamp range
                session_lines = []
                in_session = False
                start_time = datetime.fromisoformat(session.start_timestamp) if session.start_timestamp else None
                end_time = datetime.fromisoformat(session.end_timestamp) if session.end_timestamp else None
                
                for line in lines:
                    timestamp_match = re.match(parser.TIMESTAMP_PATTERN, line.strip())
                    if timestamp_match:
                        line_time = datetime.fromisoformat(timestamp_match.group(1))
                        
                        if start_time and line_time >= start_time:
                            in_session = True
                        
                        if end_time and line_time > end_time:
                            in_session = False
                            break
                    
                    if in_session:
                        session_lines.append(line.rstrip('\n'))
                
                return {
                    "session_id": session_id,
                    "lines": session_lines,
                    "line_count": len(session_lines),
                    "start_timestamp": session.start_timestamp,
                    "end_timestamp": session.end_timestamp
                }
            
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")
    
    raise HTTPException(status_code=404, detail="Session or log file not found")


# ============================================================================
# Image Caching and Proxy Endpoints - Trakt API Compliance
# ============================================================================

@app.get("/api/images/proxy")
async def proxy_image(url: str = Query(..., description="Image URL to proxy/cache")):
    """
    Proxy and cache images from external sources (Trakt, TMDB, etc.).
    This ensures compliance with Trakt's image caching requirements.
    Images are stored in data/images/ folder and served from filesystem.
    
    FLOW:
    1. Check if image is cached in database
    2. If cached, verify file exists and serve from filesystem
    3. If not cached or file missing:
       - Download from original URL (Trakt, TMDB, etc.)
       - Save to data/images/ with hash-based filename
       - Store metadata in database
       - Serve from filesystem
    4. All subsequent requests serve from local cache (NO HOTLINKING)

    Args:
        url: The original image URL to proxy

    Returns:
        The cached image file with proper headers
    """
    from list_sync.database import get_cached_image, save_cached_image
    import requests
    import imghdr
    import os

    try:
        # Validate URL
        if not url or not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid image URL")
        
        # Check if we have this image cached
        cached = get_cached_image(url)
        if cached:
            local_path = cached.get('local_path')
            
            # Verify file exists
            if local_path and os.path.exists(local_path):
                # Serve file from filesystem (NO HOTLINKING - Trakt API compliant)
                logging.debug(f"Serving cached image from: {local_path}")
                
                # Generate ETag from file modification time for efficient caching
                try:
                    mtime = os.path.getmtime(local_path)
                    etag = f'W/"{int(mtime)}"'
                    last_modified = datetime.fromtimestamp(mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
                except:
                    etag = None
                    last_modified = None
                
                headers = {
                    'Cache-Control': 'public, max-age=31536000, immutable',  # 1 year - aggressive caching
                    'X-Image-Source': cached.get('source', 'unknown'),
                    'X-Image-Cached': 'true'
                }
                
                if etag:
                    headers['ETag'] = etag
                if last_modified:
                    headers['Last-Modified'] = last_modified
                
                return FileResponse(
                    local_path,
                    media_type=cached.get('mime_type') or 'image/webp',
                    headers=headers
                )
            else:
                # File missing but DB record exists - log and re-download
                logging.warning(f"Cached image file missing, re-downloading: {url}")

        # Download the image from original source (Trakt, TMDB, etc.)
        logging.info(f"Downloading image from source: {url}")
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'ListSync/1.0.0'
        })

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch image: {response.status_code}"
            )

        image_data = response.content
        
        # Validate image data
        if not image_data or len(image_data) == 0:
            raise HTTPException(status_code=500, detail="Empty image data received")
        
        # Enforce reasonable file size limit (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_data) > max_size:
            logging.warning(f"Image too large ({len(image_data)} bytes), skipping cache: {url}")
            # Serve directly without caching
            return Response(
                content=image_data,
                media_type='image/webp',
                headers={'Cache-Control': 'no-cache'}
            )

        # Detect image type from actual data (most reliable method)
        image_type = imghdr.what(None, image_data)
        if not image_type:
            # Fallback: try to detect from URL or Content-Type header
            content_type = response.headers.get('Content-Type', '')
            if 'webp' in content_type:
                image_type = 'webp'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                image_type = 'jpeg'
            elif 'png' in content_type:
                image_type = 'png'
            else:
                image_type = 'webp'  # Default to webp for Trakt images

        mime_type = f"image/{image_type}"

        # Determine source from URL
        if 'trakt.tv' in url or 'walter' in url:
            source = 'trakt'
        elif 'tmdb.org' in url or 'themoviedb.org' in url:
            source = 'tmdb'
        else:
            source = 'unknown'

        # Save to cache (saves to data/images/ filesystem and updates database)
        logging.info(f"Saving {len(image_data)} bytes to cache as {image_type}")
        image_id = save_cached_image(url, image_data, mime_type, source)
        
        # Get the saved image record to get local_path
        cached = get_cached_image(url)
        if cached and cached.get('local_path'):
            local_path = cached['local_path']
            
            # Serve the newly saved file
            # Generate ETag for newly saved file
            try:
                mtime = os.path.getmtime(local_path)
                etag = f'W/"{int(mtime)}"'
                last_modified = datetime.fromtimestamp(mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
            except:
                etag = None
                last_modified = None
            
            headers = {
                'Cache-Control': 'public, max-age=31536000, immutable',  # 1 year - aggressive caching
                'X-Image-Source': source,
                'X-Image-Cached': 'false'  # First time, so newly cached
            }
            
            if etag:
                headers['ETag'] = etag
            if last_modified:
                headers['Last-Modified'] = last_modified
            
            return FileResponse(
                local_path,
                media_type=mime_type,
                headers=headers
            )
        else:
            # Fallback: serve from memory if file save failed
            logging.warning(f"Failed to get local_path after save, serving from memory: {url}")
            return Response(
                content=image_data,
                media_type=mime_type,
                headers={
                    'Cache-Control': 'public, max-age=86400',
                    'X-Image-Source': source,
                    'X-Image-Cached': 'false'
                }
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching image {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        logging.error(f"Error proxying image {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/cache/stats")
async def get_image_cache_stats():
    """
    Get statistics about cached images.
    
    Returns:
        dict: Statistics including total images, size, breakdown by source
    """
    from list_sync.database import get_cached_image_stats

    try:
        stats = get_cached_image_stats()
        return stats
    except Exception as e:
        logging.error(f"Error getting image cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/images/cache/cleanup")
async def cleanup_image_cache(hours: int = Query(720, description="Remove images not accessed in X hours")):
    """
    Clean up expired cached images.
    Removes both database records and files from filesystem.
    
    Args:
        hours: Remove images not accessed in this many hours (default: 720 = 30 days)
    
    Returns:
        dict: Cleanup results
    """
    from list_sync.database import cleanup_expired_images
    
    try:
        if hours < 24:
            raise HTTPException(status_code=400, detail="Hours must be at least 24")
        
        deleted_count = cleanup_expired_images(hours)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "hours": hours,
            "message": f"Removed {deleted_count} expired images"
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error cleaning up image cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/images/cache/cleanup")
async def cleanup_image_cache(hours: int = Query(24, description="Remove images older than this many hours")):
    """Clean up expired cached images."""
    from list_sync.database import cleanup_expired_images

    try:
        deleted_count = cleanup_expired_images(hours)
        return {
            "message": f"Cleaned up {deleted_count} expired images",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logging.error(f"Error cleaning up image cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/cache/list")
async def list_cached_images(limit: int = Query(50, ge=1, le=1000)):
    """List cached images for debugging."""
    try:
        from list_sync.database import DB_FILE
        import sqlite3

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, image_url, mime_type, file_size, cached_at, last_accessed, source
                FROM cached_images
                ORDER BY last_accessed DESC
                LIMIT ?
            ''', (limit,))
            images = [dict(row) for row in cursor.fetchall()]

        return {"images": images, "total": len(images)}
    except Exception as e:
        logging.error(f"Error listing cached images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting ListSync Web UI API Server...")
    print("📊 Dashboard will be available at: http://localhost:3222")
    print("🔗 API documentation at: http://localhost:4222/docs")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=4222,
        reload=True,
        log_level="info"
    )
