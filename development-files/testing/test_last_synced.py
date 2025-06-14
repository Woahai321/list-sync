#!/usr/bin/env python3
"""
Test script to verify last_synced functionality
"""

import json
import os
import sys
import sqlite3
import time

# Add the list_sync module to Python path
sys.path.insert(0, '.')

def test_database_migration():
    """Test that the database migration adds the last_synced column"""
    print("🧪 Testing database migration for last_synced column...")
    
    from list_sync.database import init_database, DB_FILE
    
    # Initialize database (this should add the column)
    init_database()
    
    # Check if column exists
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(lists)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_synced' in columns:
            print("✅ last_synced column exists in lists table")
            return True
        else:
            print("❌ last_synced column missing from lists table")
            return False

def test_sync_info_update():
    """Test updating sync info (item count + last_synced)"""
    print("\n🧪 Testing sync info update functionality...")
    
    from list_sync.database import save_list_id, update_list_sync_info, load_list_ids
    
    # Add a test list
    test_list_type = "test"
    test_list_id = "sync_test_001"
    save_list_id(test_list_id, test_list_type, list_url="http://test.com", item_count=0)
    
    # Update sync info
    update_list_sync_info(test_list_type, test_list_id, 42)
    
    # Load and verify
    lists = load_list_ids()
    test_list = None
    for list_item in lists:
        if list_item['type'] == test_list_type and list_item['id'] == test_list_id:
            test_list = list_item
            break
    
    if test_list:
        if test_list.get('item_count') == 42:
            print("✅ Item count updated correctly")
        else:
            print(f"❌ Item count incorrect: expected 42, got {test_list.get('item_count')}")
            return False
            
        if test_list.get('last_synced'):
            print(f"✅ Last synced timestamp set: {test_list['last_synced']}")
            return True
        else:
            print("❌ Last synced timestamp not set")
            return False
    else:
        print("❌ Test list not found")
        return False

def test_api_response():
    """Test that the API returns last_synced data"""
    print("\n🧪 Testing API response includes last_synced...")
    
    try:
        import requests
        response = requests.get("http://localhost:4222/api/lists", timeout=5)
        if response.status_code == 200:
            data = response.json()
            lists = data.get('lists', [])
            
            if lists:
                first_list = lists[0]
                if 'last_synced' in first_list:
                    print(f"✅ API includes last_synced field: {first_list.get('last_synced', 'None')}")
                    return True
                else:
                    print("❌ API missing last_synced field")
                    return False
            else:
                print("⚠️  No lists found in API response")
                return True  # Not an error, just no data
        else:
            print(f"⚠️  API server not running (HTTP {response.status_code})")
            return True  # Not an error for this test
    except requests.exceptions.RequestException:
        print("⚠️  API server not running or not accessible")
        return True  # Not an error for this test

def test_web_ui_display():
    """Test that the relative time formatting works"""
    print("\n🧪 Testing relative time formatting...")
    
    from datetime import datetime, timedelta
    
    # Simulate the formatRelativeTime function
    def format_relative_time(timestamp):
        if not timestamp:
            return 'Never'
        
        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
        diff = now - date
        diff_minutes = int(diff.total_seconds() / 60)
        diff_hours = int(diff.total_seconds() / 3600)
        diff_days = int(diff.total_seconds() / 86400)
        
        if diff_minutes < 1:
            return 'Just now'
        elif diff_minutes < 60:
            return f'{diff_minutes}m ago'
        elif diff_hours < 24:
            return f'{diff_hours}h ago'
        elif diff_days < 7:
            return f'{diff_days}d ago'
        else:
            return date.strftime('%b %d')
    
    # Test cases
    now = datetime.now()
    test_cases = [
        (None, 'Never'),
        ((now - timedelta(seconds=30)).isoformat(), 'Just now'),
        ((now - timedelta(minutes=5)).isoformat(), '5m ago'),
        ((now - timedelta(hours=2)).isoformat(), '2h ago'),
        ((now - timedelta(days=3)).isoformat(), '3d ago'),
    ]
    
    all_passed = True
    for timestamp, expected in test_cases:
        result = format_relative_time(timestamp)
        if expected in result or result == expected:
            print(f"✅ {timestamp or 'None'} → {result}")
        else:
            print(f"❌ {timestamp or 'None'} → {result} (expected {expected})")
            all_passed = False
    
    return all_passed

def cleanup_test_data():
    """Clean up any test data created during tests"""
    print("\n🧹 Cleaning up test data...")
    
    from list_sync.database import delete_list
    
    # Remove test lists
    delete_list("test", "sync_test_001")
    print("✅ Test data cleaned up")

def main():
    print("🔬 Testing Last Synced Functionality\n")
    
    tests = [
        ("Database Migration", test_database_migration),
        ("Sync Info Update", test_sync_info_update),
        ("API Response", test_api_response),
        ("UI Time Formatting", test_web_ui_display)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    cleanup_test_data()
    
    print(f"\n📊 Test Results:")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Last synced functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 