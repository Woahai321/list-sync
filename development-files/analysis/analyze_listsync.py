import sqlite3
import os
import psutil
import re
from datetime import datetime, timedelta
from collections import Counter

def find_listsync_process():
    """Find ListSync process dynamically"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['cmdline']:
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    if ('list_sync' in cmdline_str or 'listsync' in cmdline_str) and 'python' in cmdline_str:
                        processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': proc.info['cmdline'],
                            'created': datetime.fromtimestamp(proc.info['create_time']),
                            'status': proc.status()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"Error finding processes: {e}")
    
    return processes

def parse_log_for_sync_info(log_path, max_lines=100):
    """Parse log file for sync timing information"""
    if not os.path.exists(log_path):
        return None
    
    sync_info = {
        'last_sync_start': None,
        'last_sync_complete': None,
        'sync_interval_hours': None,
        'next_sync_time': None,
        'recent_errors': [],
        'sync_status': 'unknown'
    }
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Check last N lines for recent activity 
        recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        
        for line in recent_lines:
            # Look for sync completion
            if 'sync complete' in line.lower():
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    sync_info['last_sync_complete'] = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
            
            # Look for sync interval
            if 'sleeping for' in line.lower():
                hours_match = re.search(r'sleeping for (\d+\.?\d*) hours', line.lower())
                if hours_match:
                    sync_info['sync_interval_hours'] = float(hours_match.group(1))
            
            # Look for errors
            if 'error' in line.lower() or 'exception' in line.lower():
                sync_info['recent_errors'].append(line.strip())
        
        # Calculate next sync time if we have the info
        if sync_info['last_sync_complete'] and sync_info['sync_interval_hours']:
            sync_info['next_sync_time'] = sync_info['last_sync_complete'] + timedelta(hours=sync_info['sync_interval_hours'])
            
            # Determine if sync is overdue
            now = datetime.now()
            if now > sync_info['next_sync_time']:
                sync_info['sync_status'] = 'overdue'
            else:
                sync_info['sync_status'] = 'scheduled'
    
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return sync_info

def analyze_synced_items(db_path):
    """Analyze synced items for deduplication and status mapping"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all synced items
        cursor.execute("SELECT title, media_type, imdb_id, overseerr_id, status, last_synced FROM synced_items")
        items = cursor.fetchall()
        
        # Analyze duplicates
        title_counts = Counter()
        status_counts = Counter()
        unique_items = {}
        
        for item in items:
            title, media_type, imdb_id, overseerr_id, status, last_synced = item
            
            # Count titles for duplicate analysis
            title_counts[title] += 1
            status_counts[status] += 1
            
            # Create unique key (prefer items with overseerr_id and more recent sync)
            key = f"{title}_{media_type}".lower()
            if key not in unique_items or (overseerr_id and not unique_items[key][3]) or last_synced > unique_items[key][5]:
                unique_items[key] = item
        
        # Categorize statuses
        success_statuses = ['already_available', 'already_requested', 'available', 'requested']
        failure_statuses = ['not_found', 'error']
        
        unique_success = sum(1 for item in unique_items.values() if item[4] in success_statuses)
        unique_failure = sum(1 for item in unique_items.values() if item[4] in failure_statuses)
        unique_other = len(unique_items) - unique_success - unique_failure
        
        analysis = {
            'total_raw_items': len(items),
            'total_unique_items': len(unique_items),
            'duplicates_found': len(items) - len(unique_items),
            'status_breakdown': dict(status_counts),
            'unique_success_count': unique_success,
            'unique_failure_count': unique_failure,
            'unique_other_count': unique_other,
            'success_rate': (unique_success / len(unique_items) * 100) if unique_items else 0,
            'most_duplicated': title_counts.most_common(5)
        }
        
        conn.close()
        return analysis
        
    except Exception as e:
        print(f"Error analyzing synced items: {e}")
        return None

def check_sync_interval_in_db(db_path):
    """Check if sync interval is stored in database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sync_interval")
        intervals = cursor.fetchall()
        
        conn.close()
        return intervals
    except Exception as e:
        print(f"Error checking sync interval: {e}")
        return []

# Run comprehensive analysis
print("=== LISTSYNC COMPREHENSIVE ANALYSIS ===\n")

# 1. Process Detection
print("1. PROCESS DETECTION")
print("-" * 30)
processes = find_listsync_process()
if processes:
    for proc in processes:
        # Filter out the current analysis script
        if 'analyze_listsync.py' not in ' '.join(proc['cmdline']):
            print(f"Found ListSync process:")
            print(f"  PID: {proc['pid']}")
            print(f"  Status: {proc['status']}")
            print(f"  Started: {proc['created']}")
            print(f"  Command: {' '.join(proc['cmdline'])}")
else:
    print("No ListSync processes found")

# 2. Log Analysis
print(f"\n2. LOG ANALYSIS")
print("-" * 30)
log_info = parse_log_for_sync_info('data/list_sync.log')
if log_info:
    print(f"Last sync completed: {log_info['last_sync_complete']}")
    print(f"Sync interval: {log_info['sync_interval_hours']} hours")
    print(f"Next sync scheduled: {log_info['next_sync_time']}")
    print(f"Sync status: {log_info['sync_status']}")
    if log_info['recent_errors']:
        print(f"Recent errors: {len(log_info['recent_errors'])}")
        for error in log_info['recent_errors'][-3:]:  # Show last 3 errors
            print(f"  {error}")
else:
    print("Could not parse log file")

# 3. Database Sync Interval
print(f"\n3. DATABASE SYNC INTERVAL")
print("-" * 30)
db_intervals = check_sync_interval_in_db('data/list_sync.db')
if db_intervals:
    print(f"Intervals in database: {db_intervals}")
else:
    print("No sync intervals found in database (table is empty)")

# 4. Data Analysis
print(f"\n4. SYNCED ITEMS ANALYSIS")
print("-" * 30)
item_analysis = analyze_synced_items('data/list_sync.db')
if item_analysis:
    print(f"Total raw items: {item_analysis['total_raw_items']}")
    print(f"Unique items: {item_analysis['total_unique_items']}")
    print(f"Duplicates found: {item_analysis['duplicates_found']}")
    print(f"Success rate: {item_analysis['success_rate']:.1f}%")
    print(f"Successful items: {item_analysis['unique_success_count']}")
    print(f"Failed items: {item_analysis['unique_failure_count']}")
    print(f"Other status items: {item_analysis['unique_other_count']}")
    print(f"Status breakdown: {item_analysis['status_breakdown']}")
    if item_analysis['most_duplicated']:
        print(f"Most duplicated titles:")
        for title, count in item_analysis['most_duplicated']:
            if count > 1:
                print(f"  {title}: {count} times")
else:
    print("Could not analyze synced items")

print(f"\n=== ANALYSIS COMPLETE ===") 