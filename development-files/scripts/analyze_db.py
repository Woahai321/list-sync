import sqlite3
import os

# Connect to database
DB_FILE = os.path.join("data", "list_sync.db")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=== DATABASE SCHEMA ANALYSIS ===\n")

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(f'  {table[0]}')

print("\n=== DETAILED TABLE SCHEMAS ===\n")

# Get schema for main tables
main_tables = ['items', 'processed_items', 'collections', 'synced_items', 'lists', 'app_settings']

for table_name in main_tables:
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        if columns:
            print(f'{table_name.upper()} table schema:')
            for col in columns:
                print(f'  {col[1]} ({col[2]}) - {"NOT NULL" if col[3] else "NULL"} - DEFAULT: {col[4] if col[4] else "None"}')
            print()
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")

print("\n=== SAMPLE DATA ===\n")

# Get sample data from key tables
tables_to_sample = ['synced_items', 'lists']

for table_name in tables_to_sample:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} records")

        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            if rows:
                print(f"Sample {table_name} data:")
                for i, row in enumerate(rows):
                    print(f"  Row {i+1}: {dict(zip([col[1] for col in cursor.description], row))}")
                print()
    except Exception as e:
        print(f"Error sampling {table_name}: {e}")

conn.close()
