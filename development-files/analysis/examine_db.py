import sqlite3
import os

# Connect to the database
db_path = 'data/list_sync.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "="*50)
    
    # Examine each table structure and sample data
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        print("-" * 30)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")
        
        # Get sample data (first 3 rows)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            print("Sample data:")
            for row in rows:
                print(f"  {row}")
    
    conn.close()
else:
    print(f"Database file not found: {db_path}")

# Also check if there are any processes running that might be ListSync
print("\n" + "="*50)
print("Checking for running processes...")

try:
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('listsync' in str(cmd).lower() or 'list_sync' in str(cmd).lower() for cmd in cmdline):
                    print(f"Found ListSync process: PID {proc.info['pid']}")
                    print(f"  Command: {' '.join(cmdline)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
except ImportError:
    print("psutil not available - cannot check running processes")

# Check log file for recent activity
log_path = 'data/list_sync.log'
if os.path.exists(log_path):
    print(f"\nLog file size: {os.path.getsize(log_path)} bytes")
    print("Last 5 lines of log:")
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(f"  {line.strip()}") 