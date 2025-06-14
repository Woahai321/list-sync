#!/usr/bin/env python3
"""
Test script to verify timezone handling fix for last_synced timestamps.
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone
import zoneinfo

# Add the project root to Python path
sys.path.insert(0, '.')

def test_timezone_conversion():
    """Test the timezone conversion logic"""
    print("🕐 Testing Timezone Conversion for Last Synced Timestamps")
    print("=" * 60)
    
    # Test the same conversion logic used in api_server.py
    def convert_utc_timestamp_to_local(utc_timestamp_str):
        """Convert UTC timestamp string to local timezone ISO string"""
        try:
            from list_sync.utils.timezone_utils import get_timezone_from_env
            
            # Parse UTC timestamp (SQLite CURRENT_TIMESTAMP format)
            utc_dt = datetime.fromisoformat(utc_timestamp_str).replace(tzinfo=timezone.utc)
            
            # Get configured timezone
            local_tz_name = get_timezone_from_env()
            local_tz = zoneinfo.ZoneInfo(local_tz_name)
            
            # Convert to local timezone
            local_dt = utc_dt.astimezone(local_tz)
            
            return local_dt.isoformat(), local_tz_name
        except Exception as e:
            return None, str(e)
    
    # Test current system timezone
    from list_sync.utils.timezone_utils import get_current_timezone_info
    tz_info = get_current_timezone_info()
    print(f"Current system timezone: {tz_info['timezone_name']}")
    print(f"Current time: {tz_info['current_time']}")
    print(f"UTC offset: {tz_info['utc_offset']}")
    print()
    
    # Test conversion with sample timestamps
    test_timestamps = [
        "2024-01-15 14:30:00",  # Sample UTC timestamp
        "2024-01-15 09:15:30",  # Another sample
    ]
    
    print("Testing timestamp conversions:")
    print("-" * 40)
    
    for utc_ts in test_timestamps:
        converted, tz_name = convert_utc_timestamp_to_local(utc_ts)
        if converted:
            print(f"UTC:   {utc_ts}")
            print(f"Local: {converted} ({tz_name})")
            
            # Test how JavaScript would interpret this
            from datetime import datetime
            js_date = datetime.fromisoformat(converted.replace('Z', '+00:00'))
            print(f"JS interpretation: {js_date}")
        else:
            print(f"Error converting {utc_ts}: {tz_name}")
        print()

def test_database_timestamps():
    """Check actual timestamps in the database"""
    print("📊 Checking Database Timestamps")
    print("=" * 60)
    
    try:
        with sqlite3.connect('data/list_sync.db') as conn:
            cursor = conn.cursor()
            
            # Check if lists table has last_synced column
            cursor.execute("PRAGMA table_info(lists)")
            columns = cursor.fetchall()
            
            has_last_synced = any(col[1] == 'last_synced' for col in columns)
            
            if not has_last_synced:
                print("❌ last_synced column not found in lists table")
                return
            
            # Get lists with timestamps
            cursor.execute("SELECT list_type, list_id, last_synced FROM lists WHERE last_synced IS NOT NULL LIMIT 5")
            results = cursor.fetchall()
            
            if not results:
                print("ℹ️  No lists with last_synced timestamps found")
                return
            
            print(f"Found {len(results)} lists with sync timestamps:")
            print("-" * 40)
            
            for list_type, list_id, last_synced in results:
                print(f"List: {list_type}:{list_id}")
                print(f"  Raw timestamp: {last_synced}")
                
                # Convert using our function
                def convert_utc_timestamp_to_local(utc_timestamp_str):
                    try:
                        from list_sync.utils.timezone_utils import get_timezone_from_env
                        
                        utc_dt = datetime.fromisoformat(utc_timestamp_str).replace(tzinfo=timezone.utc)
                        local_tz_name = get_timezone_from_env()
                        local_tz = zoneinfo.ZoneInfo(local_tz_name)
                        local_dt = utc_dt.astimezone(local_tz)
                        
                        return local_dt.isoformat(), local_tz_name
                    except Exception as e:
                        return None, str(e)
                
                converted, tz_name = convert_utc_timestamp_to_local(last_synced)
                if converted:
                    print(f"  Converted:     {converted}")
                    print(f"  Timezone:      {tz_name}")
                else:
                    print(f"  Error:         {tz_name}")
                print()
    
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def test_api_endpoint():
    """Test the API endpoint to see actual response"""
    print("🌐 Testing API Endpoint Response")
    print("=" * 60)
    
    try:
        import requests
        
        # Test the /api/lists endpoint
        response = requests.get('http://localhost:8000/api/lists', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            lists = data.get('lists', [])
            
            print(f"API returned {len(lists)} lists")
            
            for list_item in lists[:3]:  # Show first 3
                print(f"\nList: {list_item.get('list_type')}:{list_item.get('list_id')}")
                last_synced = list_item.get('last_synced')
                if last_synced:
                    print(f"  last_synced: {last_synced}")
                    
                    # Test JavaScript Date parsing
                    try:
                        import dateutil.parser
                        parsed_date = dateutil.parser.isoparse(last_synced)
                        print(f"  Parsed date: {parsed_date}")
                        print(f"  Is timezone aware: {parsed_date.tzinfo is not None}")
                    except Exception as e:
                        print(f"  Parse error: {e}")
                else:
                    print("  last_synced: None")
        else:
            print(f"❌ API error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running (this is expected if testing locally)")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    print("🚀 ListSync Timezone Fix Test")
    print("Testing timezone handling for last_synced timestamps")
    print()
    
    test_timezone_conversion()
    print()
    test_database_timestamps()
    print()
    test_api_endpoint()
    
    print("\n✅ Timezone fix testing completed!")
    print("\nNext steps:")
    print("1. Start the API server: python api_server.py")
    print("2. Open the web UI and check the Lists page")
    print("3. Verify that 'last synced' times show correct relative times") 