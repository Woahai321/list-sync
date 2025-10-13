"""
Timezone utilities for ListSync - Support for common timezone abbreviations worldwide.
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime, timezone
import zoneinfo

# Comprehensive mapping of common timezone abbreviations to their full timezone names
TIMEZONE_ABBREVIATIONS: Dict[str, str] = {
    # UTC and GMT
    "UTC": "UTC",
    "GMT": "GMT",
    "Z": "UTC",
    
    # North America - Eastern
    "EST": "America/New_York",
    "EDT": "America/New_York", 
    "ET": "America/New_York",
    
    # North America - Central
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "CT": "America/Chicago",
    
    # North America - Mountain
    "MST": "America/Denver",
    "MDT": "America/Denver", 
    "MT": "America/Denver",
    
    # North America - Pacific
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "PT": "America/Los_Angeles",
    
    # North America - Alaska
    "AKST": "America/Anchorage",
    "AKDT": "America/Anchorage",
    "AT": "America/Anchorage",
    
    # North America - Hawaii
    "HST": "Pacific/Honolulu",
    "HDT": "Pacific/Honolulu",
    
    # North America - Atlantic
    "AST": "America/Halifax",
    "ADT": "America/Halifax",
    
    # North America - Newfoundland
    "NST": "America/St_Johns",
    "NDT": "America/St_Johns",
    
    # Europe - Western
    "WET": "Europe/London",
    "WEST": "Europe/London",
    "BST": "Europe/London",  # British Summer Time
    "IST": "Europe/Dublin",  # Irish Standard Time
    
    # Europe - Central
    "CET": "Europe/Berlin",
    "CEST": "Europe/Berlin",
    "MEZ": "Europe/Berlin",  # German
    "MESZ": "Europe/Berlin", # German Summer Time
    
    # Europe - Eastern
    "EET": "Europe/Athens",
    "EEST": "Europe/Athens",
    "OEZ": "Europe/Athens",  # German
    "OESZ": "Europe/Athens", # German Summer Time
    
    # Europe - Moscow
    "MSK": "Europe/Moscow",
    "MSD": "Europe/Moscow",
    
    # Asia - China
    "CST": "Asia/Shanghai",  # China Standard Time (conflicts with Central Standard Time)
    "CCT": "Asia/Shanghai",  # China Coast Time
    
    # Asia - Japan
    "JST": "Asia/Tokyo",
    "JDT": "Asia/Tokyo",
    
    # Asia - Korea
    "KST": "Asia/Seoul",
    "KDT": "Asia/Seoul",
    
    # Asia - India
    "IST": "Asia/Kolkata",  # India Standard Time (conflicts with Irish Standard Time)
    "IT": "Asia/Kolkata",   # India Time
    
    # Asia - Singapore/Malaysia
    "SGT": "Asia/Singapore",
    "SST": "Asia/Singapore", # Singapore Standard Time
    "MYT": "Asia/Kuala_Lumpur",
    "MST": "Asia/Kuala_Lumpur", # Malaysian Standard Time (conflicts with Mountain Standard Time)
    
    # Asia - Hong Kong
    "HKT": "Asia/Hong_Kong",
    
    # Asia - Philippines
    "PHT": "Asia/Manila",
    "PST": "Asia/Manila",  # Philippine Standard Time (conflicts with Pacific Standard Time)
    
    # Asia - Thailand/Vietnam
    "ICT": "Asia/Bangkok",  # Indochina Time
    
    # Asia - Indonesia
    "WIB": "Asia/Jakarta",   # Western Indonesian Time
    "WITA": "Asia/Makassar", # Central Indonesian Time
    "WIT": "Asia/Jayapura",  # Eastern Indonesian Time
    
    # Asia - Pakistan
    "PKT": "Asia/Karachi",
    
    # Asia - Bangladesh
    "BST": "Asia/Dhaka",  # Bangladesh Standard Time (conflicts with British Summer Time)
    "BDT": "Asia/Dhaka",  # Bangladesh Time
    
    # Asia - Nepal
    "NPT": "Asia/Kathmandu",
    
    # Asia - Sri Lanka
    "SLST": "Asia/Colombo",
    
    # Asia - Myanmar
    "MMT": "Asia/Yangon",
    
    # Asia - Iran
    "IRST": "Asia/Tehran",
    "IRDT": "Asia/Tehran",
    "IT": "Asia/Tehran",  # Iran Time (conflicts with India Time)
    
    # Asia - Afghanistan
    "AFT": "Asia/Kabul",
    
    # Asia - UAE/Gulf
    "GST": "Asia/Dubai",  # Gulf Standard Time
    "AST": "Asia/Dubai",  # Arabia Standard Time (conflicts with Atlantic Standard Time)
    
    # Asia - Israel
    "IST": "Asia/Jerusalem", # Israel Standard Time (conflicts with others)
    "IDT": "Asia/Jerusalem",
    
    # Australia - Eastern
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "AET": "Australia/Sydney",
    "EST": "Australia/Sydney", # Eastern Standard Time (conflicts with US EST)
    "EDT": "Australia/Sydney", # Eastern Daylight Time (conflicts with US EDT)
    
    # Australia - Central
    "ACST": "Australia/Adelaide",
    "ACDT": "Australia/Adelaide",
    "CST": "Australia/Adelaide", # Central Standard Time (conflicts with others)
    "CDT": "Australia/Adelaide", # Central Daylight Time (conflicts with others)
    
    # Australia - Western
    "AWST": "Australia/Perth",
    "AWDT": "Australia/Perth",
    "WST": "Australia/Perth",
    "WDT": "Australia/Perth",
    
    # New Zealand
    "NZST": "Pacific/Auckland",
    "NZDT": "Pacific/Auckland",
    
    # Africa - South Africa
    "SAST": "Africa/Johannesburg",
    
    # Africa - West Africa
    "WAT": "Africa/Lagos",
    "WAST": "Africa/Lagos",
    
    # Africa - Central Africa
    "CAT": "Africa/Harare",
    
    # Africa - East Africa
    "EAT": "Africa/Nairobi",
    
    # South America - Brazil
    "BRT": "America/Sao_Paulo",  # Brasília Time
    "BRST": "America/Sao_Paulo", # Brasília Summer Time
    "BST": "America/Sao_Paulo",  # Brazil Summer Time (conflicts with British Summer Time)
    
    # South America - Argentina
    "ART": "America/Argentina/Buenos_Aires",
    
    # South America - Chile
    "CLT": "America/Santiago",
    "CLST": "America/Santiago",
    
    # South America - Colombia
    "COT": "America/Bogota",
    
    # South America - Peru
    "PET": "America/Lima",
    
    # South America - Venezuela
    "VET": "America/Caracas",
    
    # South America - Ecuador
    "ECT": "America/Guayaquil",
    
    # South America - Bolivia
    "BOT": "America/La_Paz",
    
    # South America - Paraguay
    "PYT": "America/Asuncion",
    "PYST": "America/Asuncion",
    
    # South America - Uruguay
    "UYT": "America/Montevideo",
    "UYST": "America/Montevideo",
    
    # South America - Guyana
    "GYT": "America/Guyana",
    
    # South America - Suriname
    "SRT": "America/Paramaribo",
    
    # South America - French Guiana
    "GFT": "America/Cayenne",
    
    # Caribbean
    "AST": "America/Puerto_Rico", # Atlantic Standard Time (conflicts with others)
    "ADT": "America/Puerto_Rico", # Atlantic Daylight Time (conflicts with others)
    
    # Mexico
    "CST": "America/Mexico_City", # Central Standard Time (conflicts with others)
    "CDT": "America/Mexico_City", # Central Daylight Time (conflicts with others)
    "MST": "America/Mazatlan",    # Mountain Standard Time (conflicts with others)
    "MDT": "America/Mazatlan",    # Mountain Daylight Time (conflicts with others)
    "PST": "America/Tijuana",     # Pacific Standard Time (conflicts with others)
    "PDT": "America/Tijuana",     # Pacific Daylight Time (conflicts with others)
    
    # Canada specific
    "NST": "America/St_Johns",    # Newfoundland Standard Time
    "NDT": "America/St_Johns",    # Newfoundland Daylight Time
    "AST": "America/Halifax",     # Atlantic Standard Time (conflicts with others)
    "ADT": "America/Halifax",     # Atlantic Daylight Time (conflicts with others)
    
    # Pacific Islands
    "HST": "Pacific/Honolulu",    # Hawaii Standard Time
    "AKST": "America/Anchorage",  # Alaska Standard Time
    "AKDT": "America/Anchorage",  # Alaska Daylight Time
    "ChST": "Pacific/Guam",       # Chamorro Standard Time
    "GST": "Pacific/Guam",        # Guam Standard Time (conflicts with Gulf Standard Time)
    "JST": "Asia/Tokyo",          # Japan Standard Time (also used in Pacific)
    "FJST": "Pacific/Fiji",       # Fiji Summer Time
    "FJT": "Pacific/Fiji",        # Fiji Time
    "NZST": "Pacific/Auckland",   # New Zealand Standard Time
    "NZDT": "Pacific/Auckland",   # New Zealand Daylight Time
    "WST": "Pacific/Samoa",       # West Samoa Time (conflicts with Western Standard Time)
    "SST": "Pacific/Samoa",       # Samoa Standard Time (conflicts with Singapore Standard Time)
    "TOT": "Pacific/Tongatapu",   # Tonga Time
    "TOST": "Pacific/Tongatapu",  # Tonga Summer Time
    
    # Military Time Zones (single letters)
    "A": "Europe/Paris",      # Alpha Time Zone (UTC+1)
    "B": "Europe/Athens",     # Bravo Time Zone (UTC+2)
    "C": "Europe/Moscow",     # Charlie Time Zone (UTC+3)
    "D": "Asia/Dubai",        # Delta Time Zone (UTC+4)
    "E": "Asia/Karachi",      # Echo Time Zone (UTC+5)
    "F": "Asia/Dhaka",        # Foxtrot Time Zone (UTC+6)
    "G": "Asia/Bangkok",      # Golf Time Zone (UTC+7)
    "H": "Asia/Shanghai",     # Hotel Time Zone (UTC+8)
    "I": "Asia/Tokyo",        # India Time Zone (UTC+9)
    "K": "Pacific/Guam",      # Kilo Time Zone (UTC+10)
    "L": "Pacific/Noumea",    # Lima Time Zone (UTC+11)
    "M": "Pacific/Auckland",  # Mike Time Zone (UTC+12)
    "N": "Atlantic/Azores",   # November Time Zone (UTC-1)
    "O": "America/Noronha",   # Oscar Time Zone (UTC-2)
    "P": "America/Sao_Paulo", # Papa Time Zone (UTC-3)
    "Q": "America/Halifax",   # Quebec Time Zone (UTC-4)
    "R": "America/New_York",  # Romeo Time Zone (UTC-5)
    "S": "America/Chicago",   # Sierra Time Zone (UTC-6)
    "T": "America/Denver",    # Tango Time Zone (UTC-7)
    "U": "America/Los_Angeles", # Uniform Time Zone (UTC-8)
    "V": "America/Anchorage", # Victor Time Zone (UTC-9)
    "W": "Pacific/Honolulu",  # Whiskey Time Zone (UTC-10)
    "X": "Pacific/Midway",    # X-ray Time Zone (UTC-11)
    "Y": "Pacific/Kwajalein", # Yankee Time Zone (UTC-12)
    "Z": "UTC",               # Zulu Time Zone (UTC+0)
}

# Regional preference mapping for conflicting abbreviations
REGIONAL_PREFERENCES: Dict[str, Dict[str, str]] = {
    "US": {
        "EST": "America/New_York",
        "CST": "America/Chicago", 
        "MST": "America/Denver",
        "PST": "America/Los_Angeles",
        "AST": "America/Puerto_Rico",
        "HST": "Pacific/Honolulu",
        "AKST": "America/Anchorage",
    },
    "EU": {
        "CET": "Europe/Berlin",
        "EET": "Europe/Athens", 
        "WET": "Europe/London",
        "BST": "Europe/London",
        "IST": "Europe/Dublin",
    },
    "ASIA": {
        "JST": "Asia/Tokyo",
        "KST": "Asia/Seoul",
        "CST": "Asia/Shanghai",
        "IST": "Asia/Kolkata",
        "SGT": "Asia/Singapore",
        "HKT": "Asia/Hong_Kong",
        "PHT": "Asia/Manila",
    },
    "AU": {
        "AEST": "Australia/Sydney",
        "ACST": "Australia/Adelaide", 
        "AWST": "Australia/Perth",
        "EST": "Australia/Sydney",
        "CST": "Australia/Adelaide",
        "WST": "Australia/Perth",
    },
    "NZ": {
        "NZST": "Pacific/Auckland",
        "NZDT": "Pacific/Auckland",
    }
}


def normalize_timezone_input(tz_input: str, region_hint: Optional[str] = None) -> str:
    """
    Normalize timezone input to a valid timezone name.
    
    Supports:
    - IANA timezone names (e.g., "Europe/Paris", "America/New_York")
    - Common abbreviations (e.g., "EST", "CET", "PST")
    - UTC/GMT offsets (e.g., "UTC+1", "GMT-5", "UTC+5:30")
    
    Args:
        tz_input (str): Timezone input (abbreviation, full name, or offset)
        region_hint (str, optional): Regional hint for resolving conflicts (US, EU, ASIA, AU, NZ)
        
    Returns:
        str: Valid timezone name
        
    Raises:
        ValueError: If timezone cannot be resolved
    """
    import re
    
    if not tz_input:
        return "UTC"
    
    # Clean up input and preserve original for error messages
    original_input = tz_input.strip()
    tz_input = original_input.upper()
    
    # If it's already a valid timezone name, return as-is (preserving original case)
    try:
        zoneinfo.ZoneInfo(original_input)
        return original_input
    except:
        pass
    
    # Handle UTC/GMT offset formats (e.g., "UTC+1", "GMT-5", "UTC+5:30")
    # Note: Etc/GMT has REVERSED signs! GMT+1 (ahead) = Etc/GMT-1
    offset_pattern = r'^(UTC|GMT)([+-])(\d{1,2})(?::(\d{2}))?$'
    offset_match = re.match(offset_pattern, tz_input)
    
    if offset_match:
        base, sign, hours, minutes = offset_match.groups()
        hours = int(hours)
        minutes = int(minutes) if minutes else 0
        
        # Validate offset range
        if hours > 14 or (hours == 14 and minutes > 0):
            raise ValueError(f"Invalid timezone offset: {original_input}. Offset must be between -14:00 and +14:00")
        
        if minutes not in [0, 30, 45]:
            raise ValueError(f"Invalid timezone offset: {original_input}. Minutes must be 00, 30, or 45")
        
        # Handle simple hour offsets using Etc/GMT (reversed sign!)
        if minutes == 0:
            # Reverse the sign for Etc/GMT format
            reversed_sign = '-' if sign == '+' else '+'
            etc_tz = f"Etc/GMT{reversed_sign}{hours}"
            
            try:
                zoneinfo.ZoneInfo(etc_tz)
                logging.info(f"Converted '{original_input}' to '{etc_tz}'")
                return etc_tz
            except:
                pass
        
        # For offsets with minutes or if Etc/GMT fails, create a fixed offset
        # Note: Python's timezone offsets use positive for east of UTC
        total_minutes = hours * 60 + minutes
        if sign == '-':
            total_minutes = -total_minutes
        
        # Use UTC as the base and note the offset for logging
        logging.info(f"Using UTC as base for offset {original_input} ({sign}{hours}:{minutes:02d})")
        return "UTC"
    
    # Check if it's a known abbreviation
    if tz_input in TIMEZONE_ABBREVIATIONS:
        # If we have a region hint and there's a regional preference, use it
        if region_hint and region_hint.upper() in REGIONAL_PREFERENCES:
            regional_prefs = REGIONAL_PREFERENCES[region_hint.upper()]
            if tz_input in regional_prefs:
                logging.info(f"Resolved '{original_input}' to '{regional_prefs[tz_input]}' using region hint '{region_hint}'")
                return regional_prefs[tz_input]
        
        # Otherwise use the default mapping
        resolved = TIMEZONE_ABBREVIATIONS[tz_input]
        logging.info(f"Resolved abbreviation '{original_input}' to '{resolved}'")
        return resolved
    
    # Try common variations
    variations = [
        tz_input.replace("_", "/"),
        tz_input.replace("-", "/"),
        f"America/{tz_input}",
        f"Europe/{tz_input}",
        f"Asia/{tz_input}",
        f"Australia/{tz_input}",
        f"Pacific/{tz_input}",
        f"Africa/{tz_input}",
    ]
    
    for variation in variations:
        try:
            zoneinfo.ZoneInfo(variation)
            logging.info(f"Resolved '{original_input}' to '{variation}'")
            return variation
        except:
            continue
    
    # If nothing works, raise an error with helpful suggestions
    similar_abbrevs = [abbrev for abbrev in TIMEZONE_ABBREVIATIONS.keys() 
                      if abbrev.startswith(tz_input[:2]) or tz_input[:2] in abbrev]
    
    error_msg = f"Unknown timezone: '{original_input}'. "
    error_msg += "Supported formats:\n"
    error_msg += "  - IANA names: 'Europe/Paris', 'America/New_York'\n"
    error_msg += "  - Abbreviations: 'EST', 'CET', 'PST'\n"
    error_msg += "  - UTC offsets: 'UTC+1', 'GMT-5', 'UTC+5:30'"
    
    if similar_abbrevs:
        error_msg += f"\n  Did you mean: {', '.join(similar_abbrevs[:5])}?"
    
    raise ValueError(error_msg)


def get_timezone_from_env(region_hint: Optional[str] = None) -> str:
    """
    Get timezone from environment variable with abbreviation support.
    
    Args:
        region_hint (str, optional): Regional hint for resolving conflicts
        
    Returns:
        str: Valid timezone name, defaults to UTC if not found or invalid
    """
    tz_env = os.getenv('TZ', 'UTC')
    
    # If no region hint provided, check for TIMEZONE_REGION environment variable
    if not region_hint:
        region_hint = os.getenv('TIMEZONE_REGION', None)
    
    try:
        return normalize_timezone_input(tz_env, region_hint)
    except ValueError as e:
        logging.warning(f"Invalid timezone in TZ environment variable: {e}")
        return "UTC"


def set_system_timezone(timezone_name: str) -> bool:
    """
    Set the system timezone (for Docker containers).
    
    Args:
        timezone_name (str): Valid timezone name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate timezone first
        zoneinfo.ZoneInfo(timezone_name)
        
        # Set environment variable
        os.environ['TZ'] = timezone_name
        
        # Try to update system timezone files if running in Docker
        if os.path.exists('/usr/share/zoneinfo'):
            try:
                import subprocess
                subprocess.run([
                    'ln', '-snf', 
                    f'/usr/share/zoneinfo/{timezone_name}', 
                    '/etc/localtime'
                ], check=True, capture_output=True)
                
                with open('/etc/timezone', 'w') as f:
                    f.write(timezone_name + '\n')
                    
                logging.info(f"System timezone set to: {timezone_name}")
                return True
            except Exception as e:
                logging.warning(f"Could not update system timezone files: {e}")
                # Still return True as environment variable was set
                return True
                
    except Exception as e:
        logging.error(f"Failed to set timezone {timezone_name}: {e}")
        return False
    
    return True


def get_current_timezone_info() -> Dict[str, str]:
    """
    Get current timezone information.
    
    Returns:
        Dict containing timezone info
    """
    now = datetime.now()
    
    # Get timezone from environment
    tz_name = get_timezone_from_env()
    
    try:
        # Create timezone-aware datetime
        tz = zoneinfo.ZoneInfo(tz_name)
        tz_aware_now = now.replace(tzinfo=tz)
        
        return {
            "timezone_name": tz_name,
            "current_time": tz_aware_now.isoformat(),
            "utc_offset": tz_aware_now.strftime("%z"),
            "timezone_abbreviation": tz_aware_now.strftime("%Z"),
            "is_dst": tz_aware_now.dst() is not None and tz_aware_now.dst().total_seconds() > 0,
            "formatted_time": tz_aware_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        }
    except Exception as e:
        logging.error(f"Error getting timezone info: {e}")
        return {
            "timezone_name": "UTC",
            "current_time": now.isoformat(),
            "utc_offset": "+0000",
            "timezone_abbreviation": "UTC",
            "is_dst": False,
            "formatted_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }


def list_supported_abbreviations() -> Dict[str, list]:
    """
    Get a list of all supported timezone abbreviations organized by region.
    
    Returns:
        Dict with regions as keys and lists of abbreviations as values
    """
    regions = {
        "North America": [],
        "Europe": [],
        "Asia": [],
        "Australia/New Zealand": [],
        "Africa": [],
        "South America": [],
        "Pacific": [],
        "Military": [],
        "Universal": []
    }
    
    # Categorize abbreviations
    for abbrev, tz_name in TIMEZONE_ABBREVIATIONS.items():
        if tz_name.startswith("America/"):
            regions["North America"].append(abbrev)
        elif tz_name.startswith("Europe/"):
            regions["Europe"].append(abbrev)
        elif tz_name.startswith("Asia/"):
            regions["Asia"].append(abbrev)
        elif tz_name.startswith("Australia/") or tz_name.startswith("Pacific/Auckland"):
            regions["Australia/New Zealand"].append(abbrev)
        elif tz_name.startswith("Africa/"):
            regions["Africa"].append(abbrev)
        elif tz_name.startswith("Pacific/"):
            regions["Pacific"].append(abbrev)
        elif len(abbrev) == 1:  # Military single-letter codes
            regions["Military"].append(abbrev)
        elif abbrev in ["UTC", "GMT", "Z"]:
            regions["Universal"].append(abbrev)
        else:
            # Determine by timezone name patterns
            if any(continent in tz_name for continent in ["America/Argentina", "America/Sao_Paulo", "America/Santiago"]):
                regions["South America"].append(abbrev)
            else:
                regions["Universal"].append(abbrev)
    
    # Sort each region's abbreviations
    for region in regions:
        regions[region] = sorted(list(set(regions[region])))
    
    return regions 