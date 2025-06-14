#!/usr/bin/env python3
"""
Test script to verify SyncResults attributes are accessed correctly
"""

import sys

# Add the list_sync module to Python path
sys.path.insert(0, '.')

def test_sync_results_attributes():
    """Test that SyncResults has the expected attributes and structure"""
    from list_sync.ui.display import SyncResults
    
    print("🧪 Testing SyncResults class...")
    
    # Create a SyncResults instance
    sync_results = SyncResults()
    
    # Check that it has the expected attributes
    expected_attributes = [
        'start_time', 'not_found_items', 'error_items', 'media_type_counts',
        'year_distribution', 'total_items', 'synced_lists', 'results'
    ]
    
    print(f"📊 Checking SyncResults attributes...")
    for attr in expected_attributes:
        if hasattr(sync_results, attr):
            print(f"  ✅ {attr}: {type(getattr(sync_results, attr))}")
        else:
            print(f"  ❌ Missing attribute: {attr}")
            return False
    
    # Check that results dict has expected keys
    expected_result_keys = [
        'requested', 'already_requested', 'already_available', 
        'not_found', 'error', 'skipped'
    ]
    
    print(f"\n📊 Checking results dictionary keys...")
    for key in expected_result_keys:
        if key in sync_results.results:
            print(f"  ✅ results['{key}']: {sync_results.results[key]}")
        else:
            print(f"  ❌ Missing results key: {key}")
            return False
    
    # Test that we can access the results the way sync_single_list does
    print(f"\n📊 Testing access patterns used in sync_single_list...")
    try:
        items_requested = sync_results.results["requested"]
        items_available = sync_results.results["already_available"]
        items_already_requested = sync_results.results["already_requested"]
        items_skipped = sync_results.results["skipped"]
        items_not_found = sync_results.results["not_found"]
        errors = sync_results.results["error"]
        
        print(f"  ✅ All result access patterns work correctly")
        print(f"     - requested: {items_requested}")
        print(f"     - already_available: {items_available}")
        print(f"     - already_requested: {items_already_requested}")
        print(f"     - skipped: {items_skipped}")
        print(f"     - not_found: {items_not_found}")
        print(f"     - error: {errors}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error accessing results: {e}")
        return False

def test_single_list_sync_function():
    """Test that the sync_single_list function signature is correct"""
    from list_sync.main import sync_single_list
    
    print(f"\n🧪 Testing sync_single_list function...")
    
    # Check that the function exists and has the expected signature
    import inspect
    sig = inspect.signature(sync_single_list)
    
    expected_params = [
        'list_type', 'list_id', 'overseerr_url', 'overseerr_api_key',
        'user_id', 'is_4k', 'dry_run'
    ]
    
    actual_params = list(sig.parameters.keys())
    print(f"  Function parameters: {actual_params}")
    
    for param in expected_params:
        if param in actual_params:
            print(f"  ✅ Parameter '{param}' present")
        else:
            print(f"  ❌ Missing parameter: {param}")
            return False
    
    print(f"  ✅ sync_single_list function signature is correct")
    return True

def simulate_sync_results():
    """Simulate a sync results object like what would be returned from real sync"""
    from list_sync.ui.display import SyncResults
    
    print(f"\n🧪 Simulating real sync results...")
    
    # Create and populate a SyncResults like a real sync would
    sync_results = SyncResults()
    sync_results.total_items = 45
    sync_results.results["requested"] = 2
    sync_results.results["already_available"] = 3
    sync_results.results["already_requested"] = 0
    sync_results.results["skipped"] = 39
    sync_results.results["not_found"] = 1
    sync_results.results["error"] = 0
    
    # Test the exact code pattern from sync_single_list
    try:
        result = {
            "success": True,
            "message": f"Single list sync completed for test:list",
            "items_processed": sync_results.total_items,
            "items_requested": sync_results.results["requested"],
            "items_already_available": sync_results.results["already_available"],
            "items_already_requested": sync_results.results["already_requested"],
            "items_skipped": sync_results.results["skipped"],
            "items_not_found": sync_results.results["not_found"],
            "errors": sync_results.results["error"],
            "list_info": None,
            "dry_run": False
        }
        
        print(f"  ✅ Successfully created result dict:")
        for key, value in result.items():
            print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error creating result dict: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing SyncResults attribute fix...\n")
    
    tests = {
        "sync_results_attributes": test_sync_results_attributes(),
        "single_list_sync_function": test_single_list_sync_function(),
        "simulate_sync_results": simulate_sync_results()
    }
    
    print(f"\n📊 Test Results:")
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(tests.values())
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 SyncResults fix is working correctly!")
        print("💡 Single list sync should now complete without attribute errors")
    else:
        print("\n🔧 There are still issues with SyncResults access")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 