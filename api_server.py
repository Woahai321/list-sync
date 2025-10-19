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
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import statistics
import zoneinfo

from fastapi import FastAPI, HTTPException, Query
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
    DB_FILE
)
from list_sync.config import load_env_config

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

def get_deduplicated_items():
    """Get unique items with deduplication logic"""
    if not os.path.exists(DB_FILE):
        return []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all synced items including year
        cursor.execute("SELECT id, title, media_type, year, imdb_id, overseerr_id, status, last_synced FROM synced_items")
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
            item_id, title, media_type, year, imdb_id, overseerr_id, status, last_synced = item
            
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
        
        # Add display names and include item counts and last_synced with proper timezone conversion
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
                "last_synced": last_synced  # Include converted last_synced timestamp
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
        
        # Save with the generated URL and default item count of 0
        save_list_id(list_id, list_type, list_url, item_count=0)
        
        return {
            "success": True,
            "message": f"Added {list_type} list: {list_id}",
            "list_url": list_url,
            "item_count": 0
        }
    except Exception as e:
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
            item_id, title, media_type, year, imdb_id, overseerr_id, status, last_synced = item
            items.append({
                "id": item_id,
                "title": title,
                "media_type": media_type,
                "year": year,
                "imdb_id": imdb_id,
                "overseerr_id": overseerr_id,
                "status": status,
                "last_synced": last_synced,
                "list_sources": []  # Could be populated if needed
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
        # Parse request body if provided
        sync_type = "all"  # default
        target_list = None
        
        if sync_request:
            sync_type = sync_request.get("type", "all")  # "all", "single"
            target_list = sync_request.get("list", None)  # {list_type: "imdb", list_id: "top"}
            
            # Also check for direct list_type/list_id (from our web UI)
            if not target_list and sync_request.get("list_type") and sync_request.get("list_id"):
                target_list = {
                    "list_type": sync_request["list_type"],
                    "list_id": sync_request["list_id"]
                }
                sync_type = "single"
        
        print(f"DEBUG - Sync request: type={sync_type}, target={target_list}")
        
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

async def trigger_single_list_sync(target_list: dict, processes: list):
    """Trigger sync for a single specific list"""
    try:
        import tempfile
        import shutil
        
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
            print(f"DEBUG - Attempting to import sync_single_list function...")
            
            # Import the main sync functions
            from list_sync.main import sync_single_list
            from list_sync.config import load_env_config
            
            print(f"DEBUG - Import successful, loading environment config...")
            
            # Load environment configuration
            overseerr_url, overseerr_api_key, user_id, sync_interval, automated_mode, is_4k = load_env_config()
            
            print(f"DEBUG - Environment loaded. URL: {overseerr_url[:20] if overseerr_url else 'None'}...")
            print(f"DEBUG - Starting sync execution with 60 second timeout...")
            
            # Execute single list sync directly with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sync_single_list,
                        list_type,
                        list_id,
                        overseerr_url,
                        overseerr_api_key,
                        user_id,
                        is_4k
                    ),
                    timeout=60.0  # 60 second timeout
                )
                
                print(f"DEBUG - Sync completed successfully: {result}")
                
                return {
                    "success": True,
                    "sync_type": "single",
                    "target_list": target_list,
                    "message": f"Single list sync completed for {list_type}:{list_id}",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
            except asyncio.TimeoutError:
                print(f"ERROR - Sync timed out after 60 seconds")
                return {
                    "success": False,
                    "sync_type": "single",
                    "target_list": target_list,
                    "message": f"Single list sync timed out for {list_type}:{list_id}",
                    "error": "Sync operation timed out after 60 seconds",
                    "fallback_suggestion": "Try using 'Sync All Lists' or check if the list URL is accessible",
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
    media_type_filter: str = Query("", description="Filter by media type (movie/tv)")
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
        
        return {
            "items": paginated_items,
            "total_count": historic_data["total_unique_processed"],
            "filtered_count": total_items,  # Count after filtering
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
    """Get real-time sync status by checking logs/listsync-core.log for sync activity patterns"""
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
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read last 100 lines for recent activity check
                        lines = f.readlines()
                        log_content = ''.join(lines[-100:]) if len(lines) > 100 else ''.join(lines)
                        log_file_used = log_path
                        break
            except Exception as e:
                print(f"Could not read log file {log_path}: {e}")
                continue
        
        if not log_content:
            return {
                "is_running": False,
                "status": "unknown",
                "log_file_found": False,
                "error": "No log file found in any of the expected locations",
                "last_activity": None,
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"Successfully reading sync status from: {log_file_used}")
        
        # Parse recent lines to detect sync activity
        lines = log_content.strip().split('\n')
        recent_lines = lines[-50:]  # Check last 50 lines
        
        # Track sync markers with timestamps
        sync_start_markers = []
        sync_end_markers = []
        current_time = datetime.now()
        
        # Look for sync start and end patterns in recent lines
        for line in recent_lines:
            line_lower = line.lower()
            
            # Extract timestamp from line if possible
            line_timestamp = None
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                try:
                    line_timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            # Check for sync start patterns
            if any(pattern in line_lower for pattern in [
                '🔍  fetching items from trakt_special',
                'fetching items from trakt_special',
                '🔍  fetching items from',
                'processing media items',
                'total unique media items ready for sync'
            ]):
                sync_start_markers.append({
                    'line': line.strip(),
                    'timestamp': line_timestamp or current_time,
                    'pattern': 'start'
                })
            
            # Check for sync end patterns
            if any(pattern in line_lower for pattern in [
                'soluify - list sync summary',
                'sync summary',
                'sync complete',
                'processing complete',
                'webhook sent',
                'discord notification sent'
            ]):
                sync_end_markers.append({
                    'line': line.strip(),
                    'timestamp': line_timestamp or current_time,
                    'pattern': 'end'
                })
        
        # Determine if sync is currently running
        is_running = False
        status = "idle"
        last_activity = None
        
        # Check if we have any markers
        all_markers = sync_start_markers + sync_end_markers
        if all_markers:
            # Sort by timestamp to get chronological order
            all_markers.sort(key=lambda x: x['timestamp'])
            
            # Get the most recent marker
            latest_marker = all_markers[-1]
            last_activity = latest_marker['line']
            
            # If latest marker is a start and it's within the last 10 minutes, sync is probably running
            if latest_marker['pattern'] == 'start':
                time_diff = current_time - latest_marker['timestamp']
                if time_diff.total_seconds() < 600:  # 10 minutes
                    is_running = True
                    status = "running"
                else:
                    status = "idle"
            else:
                # Latest marker is an end, so sync is idle
                status = "idle"
        
        return {
            "is_running": is_running,
            "status": status,
            "log_file_found": True,
            "log_file_used": log_file_used,
            "last_activity": last_activity,
            "sync_start_count": len(sync_start_markers),
            "sync_end_count": len(sync_end_markers),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting live sync status: {e}")
        return {
            "is_running": False,
            "status": "error",
            "log_file_found": False,
            "error": str(e),
            "last_activity": None,
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
    """Get all application settings for the settings page"""
    try:
        # Load environment configuration
        config_tuple = load_env_config()
        overseerr_url, overseerr_api_key, user_id, sync_interval, automated_mode, is_4k = config_tuple
        
        # Get Discord webhook from environment
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL', '')
        
        # Get timezone from environment
        timezone = os.getenv('TZ', 'UTC')
        
        return {
            "overseerr_url": overseerr_url or '',
            "overseerr_api_key": overseerr_api_key or '',
            "overseerr_user_id": user_id or '1',
            "overseerr_4k": is_4k,
            "sync_interval": sync_interval,
            "auto_sync": automated_mode,
            "timezone": timezone,
            "discord_webhook": discord_webhook,
            "discord_enabled": bool(discord_webhook)
        }
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        return {
            "overseerr_url": '',
            "overseerr_api_key": '',
            "overseerr_user_id": '1',
            "overseerr_4k": False,
            "sync_interval": 24,
            "auto_sync": True,
            "timezone": 'UTC',
            "discord_webhook": '',
            "discord_enabled": False
        }

@app.post("/api/settings/config")
async def update_settings(settings: dict):
    """
    Update application settings.
    Note: These are stored in environment variables, so changes require container restart.
    In production, consider database-backed config.
    """
    try:
        # For now, return a message that settings need to be updated in .env
        # In a real production app, you'd store these in a database
        return {
            "success": True,
            "message": "Settings received. Please update your .env file and restart the container for changes to take effect.",
            "note": "Runtime configuration updates require database-backed settings (planned feature)"
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
            
            # Create webhook instance
            webhook = DiscordWebhook(url=webhook_url, username="ListSync Test")
            
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
            
            # Add embed to webhook
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
            
            payload = {
                "content": "🧪 **Test Notification from ListSync**",
                "embeds": [{
                    "title": "Discord Integration Test",
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
        
        # Get all database items with their IDs and year
        try:
            cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status, year FROM synced_items")
            db_items = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If year column doesn't exist, try without it
            print(f"Warning: Could not fetch year from database: {e}")
            cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status FROM synced_items")
            db_items_without_year = cursor.fetchall()
            # Convert to format with year=None
            db_items = [(title, media_type, imdb_id, overseerr_id, status, None) 
                       for title, media_type, imdb_id, overseerr_id, status in db_items_without_year]
        
        conn.close()
        
        # Create lookup dictionaries for database items
        # Try both possible media types since log parsing might be wrong
        db_lookup = {}
        db_lookup_by_title = {}  # Fallback lookup by title only
        
        for title, media_type, imdb_id, overseerr_id, status, year in db_items:
            key = f"{title.lower().strip()}_{media_type}"
            title_key = title.lower().strip()
            
            if key not in db_lookup:
                db_lookup[key] = {
                    "media_type": media_type,
                    "imdb_id": imdb_id,
                    "overseerr_id": overseerr_id,
                    "db_status": status,
                    "year": year
                }
            
            # Store by title only as fallback (prefer more recent entries)
            if title_key not in db_lookup_by_title:
                db_lookup_by_title[title_key] = {
                    "media_type": media_type,
                    "imdb_id": imdb_id,
                    "overseerr_id": overseerr_id,
                    "db_status": status,
                    "year": year
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
                # Use database year if available (it's more reliable than log parsing)
                if db_data['year']:
                    item['year'] = db_data['year']
            else:
                item['imdb_id'] = None
                item['overseerr_id'] = None
                item['db_status'] = None
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
    # Pattern to detect "Not Found Items" section header (optional - only if there are failures)
    NOT_FOUND_SECTION = r'Not Found Items \((\d+)\)'
    
    # List fetching
    LIST_FETCH_START = r'🔍\s+Fetching items from (\w+) list:\s+(.+?)\.\.\.?$'
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
        # Both full and single syncs end with the same summary pattern
        # "Soluify - List Sync Summary" or the dashed line separator
        return bool(re.search(self.SYNC_SUMMARY_START, line) or 
                   re.search(self.SYNC_SUMMARY_DASHES, line))
    
    def parse_list_fetch(self, line: str) -> Optional[tuple]:
        """Parse list fetching line."""
        fetch_match = re.search(self.LIST_FETCH_START, line)
        if fetch_match:
            return (fetch_match.group(1), fetch_match.group(2), None)
        
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
                # Set end timestamp to the current line's timestamp or last seen
                current_session.end_timestamp = timestamp or last_timestamp_in_session or datetime.now().isoformat()
                
                # Calculate duration if both timestamps exist
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
                current_session = None
                in_summary = False
        
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
    
    # Try different log locations
    log_paths = [
        "/var/log/supervisor/listsync-core.log",
        "logs/listsync-core.log",
        "/usr/src/app/logs/listsync-core.log",
        "data/list_sync.log"
    ]
    
    sessions = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            sessions = parser.parse_log_file(log_path)
            break
    
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
            sessions = parser.parse_log_file(log_path)
            break
    
    if not sessions:
        return {"error": "No sync sessions found"}
    
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
    
    # Recent syncs (last 24h, 7d, 30d)
    now = datetime.now()
    last_24h = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)).days < 1]
    last_7d = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)).days < 7]
    last_30d = [s for s in sessions if (now - datetime.fromisoformat(s.start_timestamp)).days < 30]
    
    # Most synced lists
    list_counts = {}
    for session in sessions:
        for lst in session.lists:
            key = f"{lst.type}:{lst.id}"
            list_counts[key] = list_counts.get(key, 0) + 1
    
    most_synced = sorted(list_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Average duration
    durations = [s.duration for s in sessions if s.duration is not None and s.duration > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "total_sessions": total_sessions,
        "full_syncs": full_syncs,
        "single_syncs": single_syncs,
        "total_items_processed": total_items,
        "total_requested": total_requested,
        "total_errors": total_errors,
        "success_rate": round(success_rate, 2),
        "avg_items_per_sync": round(avg_items, 2),
        "avg_duration_seconds": round(avg_duration, 2),
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
async def get_live_logs():
    """Get live log content from the core log file."""
    try:
        # Try different log locations
        log_paths = [
            "/var/log/supervisor/listsync-core.log",
            "logs/listsync-core.log",
            "/usr/src/app/logs/listsync-core.log",
            "data/list_sync.log"
        ]
        
        log_content = ""
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    break
                except Exception as e:
                    print(f"Error reading log file {log_path}: {e}")
                    continue
        
        if not log_content:
            return {
                "success": False,
                "error": "No log file found",
                "lines": []
            }
        
        # Split into lines and return the last 1000 lines
        lines = log_content.strip().split('\n')
        
        return {
            "success": True,
            "lines": lines,
            "total_lines": len(lines),
            "file_size": len(log_content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "lines": []
        }


@app.get("/api/logs/backend")
async def get_backend_logs():
    """Get backend log content from the data/list_sync.log file."""
    try:
        # Backend log file path
        log_path = "data/list_sync.log"
        
        if not os.path.exists(log_path):
            return {
                "success": False,
                "error": "Backend log file not found",
                "lines": []
            }
        
        # Read the log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        # Split into lines and return the last 1000 lines
        lines = log_content.strip().split('\n')
        
        return {
            "success": True,
            "lines": lines,
            "total_lines": len(lines),
            "file_size": len(log_content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "lines": []
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
