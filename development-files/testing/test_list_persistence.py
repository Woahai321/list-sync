#!/usr/bin/env python3
"""
Test script to verify list persistence behavior
"""

import json
import os
import sys
import sqlite3

# Add the list_sync module to Python path
sys.path.insert(0, '.')

def setup_test_environment():
    """Set up test environment variables"""
    os.environ['IMDB_LISTS'] = 'top,chart/top-250-movies'
    os.environ['TRAKT_LISTS'] = '123456'
    print("✅ Set test environment variables:")
    print(f"  IMDB_LISTS: {os.environ['IMDB_LISTS']}")
    print(f"  TRAKT_LISTS: {os.environ['TRAKT_LISTS']}")

def clear_test_environment():
    """Clear test environment variables"""
    for key in ['IMDB_LISTS', 'TRAKT_LISTS', 'TRAKT_SPECIAL_LISTS']:
        os.environ.pop(key, None)
    print("✅ Cleared test environment variables")

def add_lists_via_web_ui():
    """Simulate adding lists via web UI (database operations)"""
    from list_sync.database import save_list_id, init_database
    
    # Initialize database
    init_database()
    
    # Add some lists as if they were added via web UI
    web_ui_lists = [
        ("letterboxd", "username/my-favorites"),
        ("mdblist", "my-custom-list"),
        ("imdb", "watchlist")  # This should persist even if not in env
    ]
    
    for list_type, list_id in web_ui_lists:
        save_list_id(list_id, list_type)
        print(f"✅ Added {list_type} list via 'web UI': {list_id}")
    
    return web_ui_lists

def get_current_lists():
    """Get current lists from database"""
    from list_sync.database import load_list_ids
    
    lists = load_list_ids()
    print(f"📊 Current lists in database ({len(lists)} total):")
    for list_info in lists:
        print(f"  - {list_info['type']}: {list_info['id']}")
    return lists

def test_list_persistence():
    """Test that lists persist correctly when environment lists are loaded"""
    print("🧪 Testing list persistence behavior...\n")
    
    # Step 1: Clear environment and add lists via web UI
    clear_test_environment()
    web_ui_lists = add_lists_via_web_ui()
    
    print("\n📊 Step 1 - Lists added via web UI:")
    initial_lists = get_current_lists()
    
    # Step 2: Set environment variables (simulating Docker restart)
    print("\n📊 Step 2 - Setting environment variables (simulating restart):")
    setup_test_environment()
    
    # Step 3: Load environment lists (this should ADD to existing, not replace)
    print("\n📊 Step 3 - Loading environment lists (should be additive):")
    from list_sync.config import load_env_lists
    
    env_lists_added = load_env_lists()
    print(f"Environment lists added: {env_lists_added}")
    
    # Step 4: Check final state
    print("\n📊 Step 4 - Final state after loading environment:")
    final_lists = get_current_lists()
    
    # Verify results
    print("\n🔍 Verification:")
    
    # Check that all original web UI lists are still there
    original_set = {(item['type'], item['id']) for item in initial_lists}
    final_set = {(item['type'], item['id']) for item in final_lists}
    
    preserved_lists = original_set.intersection(final_set)
    lost_lists = original_set - final_set
    new_lists = final_set - original_set
    
    print(f"  Original lists: {len(original_set)}")
    print(f"  Final lists: {len(final_set)}")
    print(f"  Preserved: {len(preserved_lists)}")
    print(f"  Lost: {len(lost_lists)}")
    print(f"  New from env: {len(new_lists)}")
    
    if lost_lists:
        print(f"  ❌ LOST LISTS: {lost_lists}")
        return False
    
    if len(preserved_lists) == len(original_set):
        print(f"  ✅ All original lists preserved!")
    else:
        print(f"  ❌ Some original lists were lost!")
        return False
    
    if new_lists:
        print(f"  ✅ New environment lists added: {new_lists}")
    
    # Test adding the same environment lists again (should not duplicate)
    print("\n📊 Step 5 - Testing duplicate prevention:")
    env_lists_added_again = load_env_lists()
    
    if env_lists_added_again:
        print("  ❌ Environment lists were added again (duplicates created)")
        return False
    else:
        print("  ✅ No duplicates created on second load")
    
    duplicate_check_lists = get_current_lists()
    if len(duplicate_check_lists) == len(final_lists):
        print("  ✅ List count unchanged (no duplicates)")
        return True
    else:
        print(f"  ❌ List count changed: {len(final_lists)} -> {len(duplicate_check_lists)}")
        return False

def test_database_structure():
    """Test that database has the expected structure with new columns"""
    from list_sync.database import DB_FILE
    
    print("\n🧪 Testing database structure...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if lists table has the expected columns
        cursor.execute("PRAGMA table_info(lists)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = ['id', 'list_type', 'list_id', 'list_url', 'item_count']
        
        print(f"  Database columns: {column_names}")
        print(f"  Expected columns: {expected_columns}")
        
        missing_columns = set(expected_columns) - set(column_names)
        if missing_columns:
            print(f"  ❌ Missing columns: {missing_columns}")
            return False
        
        print("  ✅ All expected columns present")
        
        # Check that URL and item_count columns are populated
        cursor.execute("SELECT list_type, list_id, list_url, item_count FROM lists LIMIT 5")
        rows = cursor.fetchall()
        
        for row in rows:
            list_type, list_id, list_url, item_count = row
            print(f"  - {list_type}:{list_id} | URL: {list_url or 'NULL'} | Count: {item_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def main():
    """Run all persistence tests"""
    print("🚀 Starting list persistence tests...\n")
    
    results = {
        "persistence_test": test_list_persistence(),
        "database_structure_test": test_database_structure()
    }
    
    # Cleanup
    clear_test_environment()
    
    print(f"\n📊 Test Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 List persistence is working correctly!")
        print("💡 Lists added via web UI will persist across restarts")
        print("💡 Environment variables will only add new lists, not remove existing ones")
    else:
        print("\n🔧 List persistence issues detected!")
        print("💡 Check the database operations and load_env_lists() function")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 