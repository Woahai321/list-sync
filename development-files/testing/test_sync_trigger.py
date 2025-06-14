#!/usr/bin/env python3
"""
Test script to verify the signal-based sync trigger functionality.
This script will test the API endpoints for triggering manual syncs.
"""

import requests
import json
import time

API_BASE = "http://localhost:4222/api"

def test_sync_process_status():
    """Test the sync process status endpoint"""
    print("🔍 Testing sync process status...")
    try:
        response = requests.get(f"{API_BASE}/sync/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync status endpoint working")
            print(f"   Processes found: {data['processes_found']}")
            print(f"   Can trigger sync: {data['can_trigger_sync']}")
            print(f"   Sync method: {data['sync_method']}")
            
            if data['processes']:
                for proc in data['processes']:
                    print(f"   Process PID {proc['pid']}: {proc['status']} (can_signal: {proc['can_signal']})")
            
            return data['can_trigger_sync']
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing status: {e}")
        return False

def test_trigger_sync():
    """Test the sync trigger endpoint"""
    print("\n🚀 Testing sync trigger...")
    try:
        response = requests.post(f"{API_BASE}/sync/trigger")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync trigger successful!")
            print(f"   Message: {data['message']}")
            print(f"   Note: {data['note']}")
            
            if data['signals_sent']:
                for signal_info in data['signals_sent']:
                    print(f"   Signal sent to PID {signal_info['pid']}: {signal_info['status']}")
            
            if data.get('errors'):
                print("   Errors:")
                for error in data['errors']:
                    print(f"     PID {error['pid']}: {error['error']}")
            
            return True
        else:
            error_text = response.text
            print(f"❌ Sync trigger failed: {response.status_code}")
            print(f"   Error: {error_text}")
            return False
    except Exception as e:
        print(f"❌ Error triggering sync: {e}")
        return False

def main():
    print("🧪 Testing ListSync Signal-Based Sync Trigger")
    print("=" * 50)
    
    # Test 1: Check sync process status
    can_trigger = test_sync_process_status()
    
    if not can_trigger:
        print("\n⚠️  No ListSync process found or cannot trigger sync")
        print("   Make sure ListSync is running in automated mode")
        print("   Example: python -m list_sync --automated --interval 12")
        return
    
    # Test 2: Trigger sync
    success = test_trigger_sync()
    
    if success:
        print("\n🎉 All tests passed! Signal-based sync trigger is working.")
        print("   Check the ListSync logs to see if the sync was triggered.")
    else:
        print("\n❌ Tests failed. Check the API server and ListSync process.")

if __name__ == "__main__":
    main() 