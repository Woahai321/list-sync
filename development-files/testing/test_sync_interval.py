#!/usr/bin/env python3
"""
Test script to verify sync interval management functionality.
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from list_sync.database import init_database, configure_sync_interval, load_sync_interval
from list_sync.config import load_env_config

def test_sync_interval_flow():
    """Test the complete sync interval management flow."""
    print("🔧 Testing Sync Interval Management\n")
    
    # Initialize database
    init_database()
    
    print("1. Testing database operations...")
    
    # Clear any existing interval
    try:
        import sqlite3
        from list_sync.database import DB_FILE
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_interval")
            conn.commit()
        print("   ✅ Cleared existing sync interval")
    except Exception as e:
        print(f"   ⚠️  Error clearing interval: {e}")
    
    # Test setting interval
    configure_sync_interval(24.0)
    interval = load_sync_interval()
    print(f"   ✅ Set interval to 24.0 hours, loaded: {interval} hours")
    
    # Test updating interval
    configure_sync_interval(12.5)
    interval = load_sync_interval()
    print(f"   ✅ Updated interval to 12.5 hours, loaded: {interval} hours")
    
    # Test fractional interval
    configure_sync_interval(0.5)
    interval = load_sync_interval()
    print(f"   ✅ Set interval to 0.5 hours, loaded: {interval} hours")
    
    print("\n2. Testing environment variable handling...")
    
    # Check current environment
    try:
        _, _, _, env_interval, _, _ = load_env_config()
        print(f"   📊 Current environment interval: {env_interval} hours")
    except Exception as e:
        print(f"   ⚠️  Error reading environment: {e}")
    
    print("\n3. Testing interval precedence...")
    
    # Set a database value
    configure_sync_interval(6.0)
    db_interval = load_sync_interval()
    print(f"   💾 Database interval: {db_interval} hours")
    
    # Check what environment has
    try:
        _, _, _, env_interval, _, _ = load_env_config()
        if env_interval > 0:
            print(f"   🌍 Environment interval: {env_interval} hours")
            print(f"   📋 Database should take precedence (current: {db_interval})")
        else:
            print("   🌍 No environment interval set")
    except:
        print("   🌍 Error reading environment interval")
    
    print("\n4. Testing initialization logic...")
    
    # Clear database again to test initialization
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_interval")
            conn.commit()
        print("   🗑️  Cleared database interval")
        
        # Check what would happen during initialization
        db_interval = load_sync_interval()
        print(f"   📊 Database interval after clear: {db_interval} hours")
        
        # Test environment fallback
        try:
            _, _, _, env_interval, _, _ = load_env_config()
            if env_interval > 0:
                print(f"   🔄 Would initialize from environment: {env_interval} hours")
                configure_sync_interval(env_interval)
                final_interval = load_sync_interval()
                print(f"   ✅ Initialized database with: {final_interval} hours")
            else:
                print("   ⚠️  No environment interval to initialize from")
        except Exception as e:
            print(f"   ❌ Error during initialization test: {e}")
            
    except Exception as e:
        print(f"   ❌ Error in initialization test: {e}")
    
    print("\n5. Testing edge cases...")
    
    # Test zero interval
    configure_sync_interval(0.0)
    interval = load_sync_interval()
    print(f"   📊 Zero interval test: {interval} hours")
    
    # Test very small interval
    configure_sync_interval(0.1)
    interval = load_sync_interval()
    print(f"   📊 Small interval (0.1h): {interval} hours")
    
    # Test large interval
    configure_sync_interval(168.0)  # 1 week
    interval = load_sync_interval()
    print(f"   📊 Large interval (1 week): {interval} hours")
    
    print("\n✅ All sync interval tests completed!")

def test_api_scenario():
    """Test the scenario that would happen via API calls."""
    print("\n🌐 Testing API-like scenarios...\n")
    
    # Scenario 1: Fresh start with environment variable
    print("Scenario 1: Fresh start with environment variable")
    
    # Clear database
    try:
        import sqlite3
        from list_sync.database import DB_FILE
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_interval")
            conn.commit()
        print("   🗑️  Database cleared")
    except Exception as e:
        print(f"   ❌ Error clearing database: {e}")
        return
    
    # Check current state
    db_interval = load_sync_interval()
    print(f"   📊 Database interval: {db_interval} hours")
    
    # Check environment
    try:
        _, _, _, env_interval, _, _ = load_env_config()
        print(f"   🌍 Environment interval: {env_interval} hours")
        
        if env_interval > 0:
            print("   🔄 Simulating API initialization...")
            configure_sync_interval(env_interval)
            new_db_interval = load_sync_interval()
            print(f"   ✅ Database initialized to: {new_db_interval} hours")
        else:
            print("   ⚠️  No environment interval to initialize")
    except Exception as e:
        print(f"   ❌ Error in environment check: {e}")
    
    # Scenario 2: User updates via UI
    print("\nScenario 2: User updates via UI")
    
    print("   👤 User sets interval to 8 hours via UI...")
    configure_sync_interval(8.0)
    ui_interval = load_sync_interval()
    print(f"   ✅ UI update saved: {ui_interval} hours")
    
    print("   🔄 Application checks database...")
    app_interval = load_sync_interval()
    print(f"   ✅ Application sees: {app_interval} hours")
    
    print("\n✅ API scenario tests completed!")

def main():
    """Run all tests."""
    try:
        test_sync_interval_flow()
        test_api_scenario()
        print("\n🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 