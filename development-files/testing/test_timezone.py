#!/usr/bin/env python3
"""
Test script for ListSync timezone utilities.
Demonstrates the new timezone abbreviation support.
"""

import os
import sys
sys.path.insert(0, '.')

from list_sync.utils.timezone_utils import (
    normalize_timezone_input,
    get_current_timezone_info,
    list_supported_abbreviations,
    set_system_timezone
)

def test_timezone_abbreviations():
    """Test various timezone abbreviations"""
    print("🌍 Testing Timezone Abbreviation Support\n")
    
    # Test cases: (input, expected_region, description)
    test_cases = [
        ("EST", "US", "US Eastern Standard Time"),
        ("PST", "US", "US Pacific Standard Time"),
        ("CET", "EU", "Central European Time"),
        ("JST", "ASIA", "Japan Standard Time"),
        ("AEST", "AU", "Australian Eastern Standard Time"),
        ("GMT", None, "Greenwich Mean Time"),
        ("UTC", None, "Coordinated Universal Time"),
        ("Z", None, "Zulu Time (Military)"),
        ("A", None, "Alpha Time Zone (Military)"),
        ("IST", "ASIA", "India Standard Time (with region hint)"),
        ("IST", "EU", "Irish Standard Time (with region hint)"),
        ("America/New_York", None, "Full timezone name"),
    ]
    
    print("Testing timezone abbreviation normalization:")
    print("-" * 60)
    
    for tz_input, region_hint, description in test_cases:
        try:
            normalized = normalize_timezone_input(tz_input, region_hint)
            print(f"✅ {tz_input:8} ({region_hint or 'auto':4}) → {normalized:25} | {description}")
        except ValueError as e:
            print(f"❌ {tz_input:8} ({region_hint or 'auto':4}) → ERROR: {e}")
    
    print("\n" + "=" * 60)

def test_current_timezone():
    """Test current timezone information"""
    print("\n🕐 Current Timezone Information:")
    print("-" * 40)
    
    tz_info = get_current_timezone_info()
    for key, value in tz_info.items():
        print(f"{key:20}: {value}")

def test_supported_abbreviations():
    """Test listing supported abbreviations"""
    print("\n📋 Supported Timezone Abbreviations by Region:")
    print("-" * 50)
    
    regions = list_supported_abbreviations()
    for region, abbreviations in regions.items():
        print(f"\n{region} ({len(abbreviations)} abbreviations):")
        # Show first 10 abbreviations per region
        shown = abbreviations[:10]
        print(f"  {', '.join(shown)}")
        if len(abbreviations) > 10:
            print(f"  ... and {len(abbreviations) - 10} more")

def test_environment_variables():
    """Test environment variable handling"""
    print("\n🔧 Environment Variable Testing:")
    print("-" * 40)
    
    # Save original values
    original_tz = os.environ.get('TZ')
    original_region = os.environ.get('TIMEZONE_REGION')
    
    test_scenarios = [
        ("EST", "US", "US Eastern with region hint"),
        ("EST", "AU", "Australian Eastern with region hint"),
        ("CET", None, "Central European Time"),
        ("INVALID", None, "Invalid timezone (should fallback to UTC)"),
    ]
    
    for tz, region, description in test_scenarios:
        # Set environment variables
        os.environ['TZ'] = tz
        if region:
            os.environ['TIMEZONE_REGION'] = region
        elif 'TIMEZONE_REGION' in os.environ:
            del os.environ['TIMEZONE_REGION']
        
        try:
            from list_sync.utils.timezone_utils import get_timezone_from_env
            result = get_timezone_from_env()
            print(f"✅ TZ={tz}, REGION={region or 'None'} → {result} | {description}")
        except Exception as e:
            print(f"❌ TZ={tz}, REGION={region or 'None'} → ERROR: {e}")
    
    # Restore original values
    if original_tz:
        os.environ['TZ'] = original_tz
    elif 'TZ' in os.environ:
        del os.environ['TZ']
    
    if original_region:
        os.environ['TIMEZONE_REGION'] = original_region
    elif 'TIMEZONE_REGION' in os.environ:
        del os.environ['TIMEZONE_REGION']

def main():
    """Run all timezone tests"""
    print("🚀 ListSync Timezone Utilities Test Suite")
    print("=" * 60)
    
    try:
        test_timezone_abbreviations()
        test_current_timezone()
        test_supported_abbreviations()
        test_environment_variables()
        
        print("\n" + "=" * 60)
        print("✅ All timezone tests completed successfully!")
        print("\n💡 Usage Examples:")
        print("   docker-compose.yml: TZ=EST")
        print("   .env file:          TZ=PST")
        print("   With region hint:   TZ=IST, TIMEZONE_REGION=ASIA")
        print("   API validation:     POST /api/timezone/validate")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 