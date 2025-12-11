#!/usr/bin/env python3
"""
Database Analysis Script - Check if list sources data exists
"""

import sqlite3
import os
from pathlib import Path

# Find database file - check multiple possible locations
possible_paths = [
    os.path.join(os.path.dirname(__file__), 'data', 'list_sync.db'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'list_sync.db'),
    os.path.join(os.getcwd(), 'data', 'list_sync.db'),
]

DB_FILE = None
for path in possible_paths:
    if os.path.exists(path):
        DB_FILE = path
        break

if not DB_FILE:
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    DB_FILE = os.path.join(DATA_DIR, 'list_sync.db')

if not os.path.exists(DB_FILE):
    print(f"❌ Database file not found: {DB_FILE}")
    exit(1)

print("=" * 80)
print("DATABASE ANALYSIS - List Sources Check")
print("=" * 80)
print(f"Database: {DB_FILE}\n")

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row  # Enable column access by name
cursor = conn.cursor()

# Check if item_lists table exists
print("1. CHECKING TABLE STRUCTURE")
print("-" * 80)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item_lists'")
table_exists = cursor.fetchone()
if table_exists:
    print("✅ item_lists table EXISTS")
    
    # Get table schema
    cursor.execute("PRAGMA table_info(item_lists)")
    columns = cursor.fetchall()
    print("   Columns:")
    for col in columns:
        print(f"     - {col[1]} ({col[2]})")
else:
    print("❌ item_lists table DOES NOT EXIST")
    print("   This table is required to track which lists items came from!")

print()

# Check synced_items table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='synced_items'")
if cursor.fetchone():
    cursor.execute("SELECT COUNT(*) FROM synced_items")
    item_count = cursor.fetchone()[0]
    print(f"✅ synced_items table EXISTS with {item_count} items")
else:
    print("❌ synced_items table DOES NOT EXIST")
    item_count = 0

print()

# Check lists table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lists'")
if cursor.fetchone():
    cursor.execute("SELECT COUNT(*) FROM lists")
    list_count = cursor.fetchone()[0]
    print(f"✅ lists table EXISTS with {list_count} lists")
    
    # Show sample lists
    if list_count > 0:
        # Check what columns exist
        cursor.execute("PRAGMA table_info(lists)")
        list_columns = [col[1] for col in cursor.fetchall()]
        if 'display_name' in list_columns:
            cursor.execute("SELECT list_type, list_id, display_name FROM lists LIMIT 5")
            lists = cursor.fetchall()
            print("   Sample lists:")
            for lst in lists:
                print(f"     - {lst['list_type']}:{lst['list_id']} ({lst['display_name'] or 'No display name'})")
        else:
            cursor.execute("SELECT list_type, list_id FROM lists LIMIT 5")
            lists = cursor.fetchall()
            print("   Sample lists:")
            for lst in lists:
                print(f"     - {lst['list_type']}:{lst['list_id']}")
else:
    print("❌ lists table DOES NOT EXIST")
    list_count = 0

print()
print("2. CHECKING LIST RELATIONSHIPS (item_lists table)")
print("-" * 80)

if table_exists:
    cursor.execute("SELECT COUNT(*) FROM item_lists")
    relationship_count = cursor.fetchone()[0]
    print(f"Total relationships in item_lists: {relationship_count}")
    
    if relationship_count > 0:
        print("✅ Relationships exist! Items are linked to lists.")
        
        # Show sample relationships
        # Check if display_name column exists in lists table
        cursor.execute("PRAGMA table_info(lists)")
        list_columns = [col[1] for col in cursor.fetchall()]
        if 'display_name' in list_columns:
            cursor.execute("""
                SELECT 
                    il.item_id,
                    si.title,
                    il.list_type,
                    il.list_id,
                    l.display_name,
                    il.synced_at
                FROM item_lists il
                LEFT JOIN synced_items si ON il.item_id = si.id
                LEFT JOIN lists l ON il.list_type = l.list_type AND il.list_id = l.list_id
                LIMIT 10
            """)
        else:
            cursor.execute("""
                SELECT 
                    il.item_id,
                    si.title,
                    il.list_type,
                    il.list_id,
                    il.synced_at
                FROM item_lists il
                LEFT JOIN synced_items si ON il.item_id = si.id
                LIMIT 10
            """)
        relationships = cursor.fetchall()
        print("\n   Sample relationships:")
        for rel in relationships:
            if 'display_name' in rel.keys():
                print(f"     - Item #{rel['item_id']} ({rel['title']}) ← {rel['list_type']}:{rel['list_id']} ({rel['display_name'] or 'No name'})")
            else:
                print(f"     - Item #{rel['item_id']} ({rel['title']}) ← {rel['list_type']}:{rel['list_id']}")
        
        # Check how many items have relationships
        cursor.execute("SELECT COUNT(DISTINCT item_id) FROM item_lists")
        items_with_lists = cursor.fetchone()[0]
        print(f"\n   Items with list relationships: {items_with_lists} out of {item_count}")
        
        if items_with_lists < item_count:
            missing = item_count - items_with_lists
            print(f"   ⚠️  {missing} items are missing list relationships!")
    else:
        print("❌ NO relationships found in item_lists table!")
        print("   This means items are NOT linked to lists.")
        print("   You need to re-sync your lists to populate this table.")
else:
    print("❌ Cannot check relationships - item_lists table doesn't exist!")

print()
print("3. CHECKING SAMPLE ITEMS")
print("-" * 80)

if item_count > 0:
    # Get sample items with their list relationships
    cursor.execute("""
        SELECT 
            si.id,
            si.title,
            si.media_type,
            si.year,
            si.status,
            GROUP_CONCAT(il.list_type || ':' || il.list_id, ', ') as list_sources
        FROM synced_items si
        LEFT JOIN item_lists il ON si.id = il.item_id
        GROUP BY si.id
        LIMIT 10
    """)
    items = cursor.fetchall()
    
    print("Sample items with their list sources:")
    for item in items:
        sources = item['list_sources'] or "❌ NO LIST SOURCES"
        print(f"   - #{item['id']}: {item['title']} ({item['year']}) - {sources}")
else:
    print("No items in database")

print()
print("4. SUMMARY")
print("-" * 80)

if table_exists:
    cursor.execute("SELECT COUNT(*) FROM item_lists")
    rel_count = cursor.fetchone()[0]
    
    if rel_count == 0:
        print("❌ PROBLEM: item_lists table is EMPTY")
        print("   → Items are not linked to lists")
        print("   → List tags will NOT show on items")
        print("   → Filtering by list will NOT work")
        print("\n   SOLUTION: Re-sync your lists from the Lists page")
    elif rel_count < item_count:
        print(f"⚠️  PARTIAL: Only {rel_count} relationships for {item_count} items")
        print("   → Some items are missing list relationships")
        print("   → Re-sync to fix missing relationships")
    else:
        print(f"✅ GOOD: {rel_count} relationships found")
        print("   → Items should have list tags")
        print("   → Filtering should work")
else:
    print("❌ CRITICAL: item_lists table doesn't exist!")
    print("   → Database schema is incomplete")
    print("   → Run database initialization")

print()
print("=" * 80)

conn.close()

