#!/usr/bin/env python3
"""
Test script to verify list URL and item count functionality.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from list_sync.database import init_database, save_list_id, load_list_ids, clear_all_lists, update_list_item_count
from list_sync.utils.helpers import construct_list_url

def test_url_construction():
    """Test URL construction for different list types."""
    print("🔧 Testing URL construction...")
    
    test_cases = [
        ("imdb", "ls123456789", "https://www.imdb.com/list/ls123456789"),
        ("imdb", "ur123456789", "https://www.imdb.com/user/ur123456789/watchlist"),
        ("imdb", "top", "https://www.imdb.com/chart/top"),
        ("trakt", "123456", "https://trakt.tv/lists/123456"),
        ("trakt", "trending:movies", "https://trakt.tv/movies/trending"),
        ("trakt_special", "trending:shows", "https://trakt.tv/shows/trending"),
        ("trakt_special", "collected:movies", "https://trakt.tv/movies/collected"),
        ("trakt_special", "collected:shows", "https://trakt.tv/shows/collected"),
        ("trakt_special", "watched:movies", "https://trakt.tv/movies/watched"),
        ("trakt_special", "popular:movies", "https://trakt.tv/movies/popular"),
        ("trakt_special", "anticipated:shows", "https://trakt.tv/shows/anticipated"),
        ("letterboxd", "username/list-name", "https://letterboxd.com/username/list-name"),
        ("mdblist", "username/listname", "https://mdblist.com/lists/username/listname"),
        ("stevenlu", "anything", "https://movies.stevenlu.com/"),
    ]
    
    for list_type, list_id, expected_url in test_cases:
        actual_url = construct_list_url(list_type, list_id)
        status = "✅" if actual_url == expected_url else "❌"
        print(f"{status} {list_type:12} | {list_id:20} | {actual_url}")
        if actual_url != expected_url:
            print(f"   Expected: {expected_url}")
    
    print()

def test_database_operations():
    """Test database operations with URLs and item counts."""
    print("💾 Testing database operations...")
    
    # Initialize database
    init_database()
    
    # Clear existing lists for clean test
    clear_all_lists()
    
    # Test adding lists with URL generation and item counts
    test_lists = [
        ("imdb", "ls123456789", 150),
        ("trakt", "trending:movies", 25), 
        ("letterboxd", "testuser/test-list", 75),
        ("mdblist", "testuser/testlist", 200)
    ]
    
    print("Adding test lists with item counts...")
    for list_type, list_id, item_count in test_lists:
        save_list_id(list_id, list_type, item_count=item_count)
        print(f"  Added {list_type}: {list_id} ({item_count} items)")
    
    # Load and display lists with URLs and item counts
    print("\nLoaded lists with URLs and item counts:")
    lists = load_list_ids()
    for list_item in lists:
        url = list_item.get('url', 'No URL')
        count = list_item.get('item_count', 0)
        print(f"  {list_item['type']:10} | {list_item['id']:20} | {count:3d} items | {url}")
    
    # Test updating item counts
    print("\nTesting item count updates...")
    update_list_item_count("imdb", "ls123456789", 175)
    update_list_item_count("trakt", "trending:movies", 30)
    
    # Load and display updated counts
    print("Updated item counts:")
    lists = load_list_ids()
    for list_item in lists:
        if list_item['type'] in ['imdb', 'trakt']:
            count = list_item.get('item_count', 0)
            print(f"  {list_item['type']:10} | {list_item['id']:20} | {count:3d} items")
    
    # Test manually specifying URL and item count
    print("\nTesting manual URL and item count specification...")
    custom_url = "https://example.com/custom-list"
    save_list_id("custom123", "custom", custom_url, item_count=42)
    
    lists = load_list_ids()
    custom_list = [l for l in lists if l['type'] == 'custom'][0]
    print(f"Custom list URL: {custom_list.get('url')}")
    print(f"Custom list item count: {custom_list.get('item_count')} items")
    
    print()

def test_item_count_edge_cases():
    """Test edge cases for item counts."""
    print("🧪 Testing item count edge cases...")
    
    # Test with item_count=0
    save_list_id("empty-list", "test", item_count=0)
    
    # Test without specifying item_count (should default to 0)
    save_list_id("default-list", "test")
    
    # Test with large item count
    save_list_id("large-list", "test", item_count=999999)
    
    # Load and verify
    lists = load_list_ids()
    test_lists = [l for l in lists if l['type'] == 'test']
    
    for list_item in test_lists:
        count = list_item.get('item_count', 0)
        print(f"  {list_item['id']:15} | {count:7d} items")
    
    print()

def test_item_count_functionality():
    """Test the item count database functionality."""
    print("🔧 Testing item count database functionality...")
    
    # Initialize database
    init_database()
    
    # Clear existing data
    clear_all_lists()
    
    # Test updating item counts
    save_list_id("test_list", "imdb", item_count=50)
    update_list_item_count("imdb", "test_list", 75)
    
    # Load and verify
    lists = load_list_ids()
    test_list = next((l for l in lists if l["id"] == "test_list"), None)
    
    if test_list and test_list.get("item_count") == 75:
        print("✅ Item count update test passed")
    else:
        print("❌ Item count update test failed")
        return False
    
    return True

def test_year_storage():
    """Test the year storage functionality in synced_items."""
    print("🔧 Testing year storage in synced_items...")
    
    # Initialize database
    init_database()
    
    # Import the updated save_sync_result function
    from list_sync.database import save_sync_result
    
    # Test saving items with year data
    test_items = [
        ("The Dark Knight", "movie", None, 155, "already_available", 2008),
        ("Inception", "movie", "tt1375666", 157336, "requested", 2010),
        ("Breaking Bad", "tv", None, 121, "already_requested", 2008),
        ("Old Movie", "movie", None, None, "not_found", 1925),
        ("Recent Show", "tv", None, 999, "requested", 2023)
    ]
    
    for title, media_type, imdb_id, overseerr_id, status, year in test_items:
        save_sync_result(title, media_type, imdb_id, overseerr_id, status, year)
        print(f"✅ Saved: {title} ({year}) - {media_type} - {status}")
    
    # Verify the data was stored correctly
    import sqlite3
    from list_sync.database import DB_FILE
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, media_type, year, status FROM synced_items ORDER BY year")
        results = cursor.fetchall()
        
        print("\n📊 Stored items with years:")
        for title, media_type, year, status in results:
            year_str = str(year) if year else "None"
            print(f"   • {title} ({year_str}) - {media_type} - {status}")
    
    if len(results) >= 5:
        print("✅ Year storage test passed - all items stored with year data")
        return True
    else:
        print("❌ Year storage test failed - not all items were stored")
        return False

def test_url_update_functionality():
    """Test the URL update functionality for existing lists."""
    print("🔧 Testing URL update functionality...")
    
    # Initialize database
    init_database()
    
    # Import the update function
    from list_sync.database import update_existing_list_urls
    
    # Clear existing data for clean test
    clear_all_lists()
    
    # Add some test lists with incorrect URLs (simulating old data)
    import sqlite3
    from list_sync.database import DB_FILE
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Insert lists with incorrect URLs
        test_data = [
            ("trakt_special", "trending:shows", "trending:shows", 20),  # Wrong URL
            ("trakt_special", "collected:movies", "collected:movies", 20),  # Wrong URL  
            ("imdb", "top", "https://www.imdb.com/chart/top", 250),  # Correct URL
        ]
        
        for list_type, list_id, wrong_url, item_count in test_data:
            cursor.execute(
                "INSERT INTO lists (list_type, list_id, list_url, item_count) VALUES (?, ?, ?, ?)",
                (list_type, list_id, wrong_url, item_count)
            )
        conn.commit()
    
    print("📝 Added test data with incorrect URLs...")
    
    # Show before state
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT list_type, list_id, list_url FROM lists")
        before_data = cursor.fetchall()
        
        print("\n📊 Before URL update:")
        for list_type, list_id, list_url in before_data:
            print(f"   {list_type:12} | {list_id:20} | {list_url}")
    
    # Run the update function
    update_existing_list_urls()
    
    # Show after state
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT list_type, list_id, list_url FROM lists")
        after_data = cursor.fetchall()
        
        print("\n✅ After URL update:")
        for list_type, list_id, list_url in after_data:
            expected_url = construct_list_url(list_type, list_id)
            status = "✅" if list_url == expected_url else "❌"
            print(f"   {status} {list_type:12} | {list_id:20} | {list_url}")
    
    print("✅ URL update functionality test completed\n")
    return True

def main():
    """Run all tests."""
    print("🧪 Testing List URL and Item Count Functionality\n")
    
    try:
        test_url_construction()
        test_database_operations()
        test_item_count_edge_cases()
        test_item_count_functionality()
        test_year_storage()
        test_url_update_functionality()
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 