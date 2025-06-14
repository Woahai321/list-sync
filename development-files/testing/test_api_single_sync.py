#!/usr/bin/env python3
"""
Test script to simulate the exact API request for single list sync from the web UI
"""

import json
import requests
import time

def test_api_single_sync():
    """Test the API endpoint with the exact payload the web UI sends"""
    
    # The exact format the web UI sends
    test_payload = {
        "list_type": "imdb",
        "list_id": "top"  # This should be a valid list
    }
    
    print("🧪 Testing single list sync API with web UI format...")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # Test the API endpoint
        response = requests.post(
            "http://localhost:4222/api/sync/trigger",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("✅ API request successful!")
                print(f"🎯 Sync type: {result.get('sync_type')}")
                print(f"🎯 Target list: {result.get('target_list')}")
                print(f"🎯 Method: {result.get('method', 'unknown')}")
                
                # Check if request file was created
                import os
                request_file = "data/single_list_sync_request.json"
                if os.path.exists(request_file):
                    with open(request_file, 'r') as f:
                        file_data = json.load(f)
                    print(f"✅ Request file created: {json.dumps(file_data, indent=2)}")
                else:
                    print("⚠️  Request file not found (may have been processed)")
                
                return True
            else:
                print(f"❌ API request failed: {result}")
                return False
        else:
            print(f"❌ Non-JSON response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Is it running on localhost:4222?")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_alternative_payload_format():
    """Test with the alternative nested format"""
    
    test_payload = {
        "type": "single",
        "list": {
            "list_type": "imdb", 
            "list_id": "top"
        }
    }
    
    print("\n🧪 Testing alternative payload format...")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:4222/api/sync/trigger",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            return result.get("success", False)
        return False
        
    except:
        return False

def main():
    """Run API tests"""
    print("🚀 Testing single list sync API integration...\n")
    
    # Test 1: Web UI format (direct list_type/list_id)
    test1_result = test_api_single_sync()
    
    # Test 2: Alternative nested format  
    test2_result = test_alternative_payload_format()
    
    print(f"\n📊 Test Results:")
    print(f"  Web UI format: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"  Nested format: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    overall = test1_result and test2_result
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
    
    if overall:
        print("\n🎉 Single list sync API is working correctly!")
        print("💡 The web UI should now properly sync individual lists")
    else:
        print("\n🔧 API issues detected. Check if:")
        print("  1. API server is running on localhost:4222")
        print("  2. ListSync core application is running") 
        print("  3. Check the API server logs for errors")
    
    return overall

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 