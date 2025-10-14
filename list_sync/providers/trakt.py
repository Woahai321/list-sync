"""
Trakt provider for ListSync - using Trakt API v2.
"""

import logging
import os
import re
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

from . import register_provider

# Load environment variables
if os.path.exists('.env'):
    load_dotenv()

# Trakt API configuration
TRAKT_CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
TRAKT_BASE_URL = "https://api.trakt.tv"
TRAKT_API_VERSION = "2"

# Get configurable limit for special Trakt lists from environment variable
TRAKT_SPECIAL_ITEMS_LIMIT = int(os.getenv('TRAKT_SPECIAL_ITEMS_LIMIT', '20'))


def get_trakt_headers() -> Dict[str, str]:
    """
    Get headers for Trakt API requests.
    
    Returns:
        Dict[str, str]: Headers including API key
        
    Raises:
        ValueError: If TRAKT_CLIENT_ID is not set
    """
    if not TRAKT_CLIENT_ID:
        raise ValueError(
            "TRAKT_CLIENT_ID environment variable is not set. "
            "Please set it in your .env file or environment variables. "
            "Get your Client ID from: https://trakt.tv/oauth/applications"
        )
    
    return {
        "Content-Type": "application/json",
        "trakt-api-version": TRAKT_API_VERSION,
        "trakt-api-key": TRAKT_CLIENT_ID
    }


def parse_trakt_list_url(list_id: str) -> str:
    """
    Parse Trakt list URL to extract API endpoint path.
    
    Args:
        list_id (str): Trakt list ID (numeric), list slug, or full URL
        
    Returns:
        str: API endpoint path (e.g., '/users/username/lists/list-slug/items' or '/users/username/watchlist')
        
    Raises:
        ValueError: If list ID format is invalid
    """
    # Handle full URLs
    if list_id.startswith(('http://', 'https://')):
        # Remove query parameters if present
        url = list_id.split('?')[0].rstrip('/')
        
        # Pattern 1: /users/{username}/watchlist
        pattern_watchlist = r'trakt\.tv/users/([^/]+)/watchlist'
        match = re.search(pattern_watchlist, url)
        if match:
            username = match.group(1)
            return f"/users/{username}/watchlist"
        
        # Pattern 2: /users/{username}/lists/{list-slug}
        pattern_list = r'trakt\.tv/users/([^/]+)/lists/([^/?]+)'
        match = re.search(pattern_list, url)
        if match:
            username, list_slug = match.groups()
            return f"/users/{username}/lists/{list_slug}/items"
        
        # Pattern 3: /lists/{numeric-id}
        pattern_numeric = r'trakt\.tv/lists/(\d+)'
        match = re.search(pattern_numeric, url)
        if match:
            list_id = match.group(1)
            return f"/lists/{list_id}/items"
        
        raise ValueError(f"Invalid Trakt URL format: {list_id}")
    
    # Handle numeric list IDs (legacy format)
    if list_id.isdigit():
        return f"/lists/{list_id}/items"
    
    raise ValueError(
        f"Invalid Trakt list ID format: {list_id}. "
        "Expected a numeric ID, list URL, or full Trakt URL."
    )


def extract_media_from_list_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract media information from a Trakt list item.
    
    Args:
        item (Dict[str, Any]): Trakt API list item
        
    Returns:
        Optional[Dict[str, Any]]: Normalized media item or None if parsing fails
    """
    try:
        item_type = item.get('type')
        
        # Get the media object (nested under 'movie' or 'show' key)
        if item_type == 'movie':
            media = item.get('movie', {})
        elif item_type == 'show':
            media = item.get('show', {})
        else:
            logging.warning(f"Unknown item type: {item_type}")
            return None
        
        if not media:
            logging.warning(f"No media object found in item: {item}")
            return None
        
        title = media.get('title')
        year = media.get('year')
        ids = media.get('ids', {})
        
        if not title:
            logging.warning(f"No title found in media: {media}")
            return None
        
        return {
            "title": title,
            "year": year,
            "media_type": "tv" if item_type == "show" else "movie",
            "tmdb_id": ids.get('tmdb'),
            "imdb_id": ids.get('imdb')
        }
        
    except Exception as e:
        logging.warning(f"Failed to parse Trakt list item: {str(e)}")
        return None


@register_provider("trakt")
def fetch_trakt_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch Trakt list using Trakt API v2.
    
    Supports:
    - User custom lists: https://trakt.tv/users/{username}/lists/{list-slug}
    - User watchlists: https://trakt.tv/users/{username}/watchlist
    - Public lists: https://trakt.tv/lists/{numeric-id}
    
    Args:
        list_id (str): Trakt list ID (numeric) or full URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid or API credentials not set
        requests.HTTPError: If API request fails
    """
    media_items = []
    logging.info(f"Fetching Trakt list: {list_id}")
    
    try:
        # Parse the list ID to get API endpoint
        endpoint = parse_trakt_list_url(list_id)
        url = f"{TRAKT_BASE_URL}{endpoint}"
        
        logging.info(f"Fetching from API endpoint: {url}")
        
        # Make API request
        response = requests.get(url, headers=get_trakt_headers(), timeout=30)
        response.raise_for_status()
        
        items = response.json()
        
        if not isinstance(items, list):
            raise ValueError(f"Unexpected API response format: expected list, got {type(items)}")
        
        logging.info(f"Found {len(items)} items in list")
        
        # Parse each item
        for item in items:
            media = extract_media_from_list_item(item)
            if media:
                media_items.append({
                    "title": media["title"],
                    "media_type": media["media_type"],
                    "year": media.get("year")
                })
                logging.info(f"Added {media['media_type']}: {media['title']} ({media.get('year', 'unknown year')})")
        
        logging.info(f"Trakt list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.error(f"Trakt list not found: {list_id}")
            raise ValueError(f"Trakt list not found: {list_id}. Please check the list URL or ID.")
        elif e.response.status_code == 401:
            logging.error("Trakt API authentication failed. Please check TRAKT_CLIENT_ID.")
            raise ValueError("Trakt API authentication failed. Please check your TRAKT_CLIENT_ID.")
        else:
            logging.error(f"Trakt API error: {e.response.status_code} - {e.response.text}")
            raise
    except Exception as e:
        logging.error(f"Error fetching Trakt list {list_id}: {str(e)}")
        raise


@register_provider("trakt_special")
def fetch_trakt_special_list(url_or_shortcut: str) -> List[Dict[str, Any]]:
    """
    Fetch special Trakt list (trending, popular, etc.) using Trakt API v2.
    
    Args:
        url_or_shortcut (str): Trakt special list URL or shortcut format (e.g., "trending:movies")
        
    Returns:
        List[Dict[str, Any]]: List of media items (max: TRAKT_SPECIAL_ITEMS_LIMIT from env var, default 20)
        
    Raises:
        ValueError: If URL format is invalid or API credentials not set
        requests.HTTPError: If API request fails
    """
    media_items = []
    logging.info(f"Fetching special Trakt list: {url_or_shortcut}")
    
    try:
        # Parse URL or shortcut to get endpoint
        endpoint = parse_special_list_url(url_or_shortcut)
        
        logging.info(f"Fetching special list from endpoint: {endpoint} (limit: {TRAKT_SPECIAL_ITEMS_LIMIT} items)")
        
        # Fetch items with pagination
        page = 1
        total_items_fetched = 0
        
        while total_items_fetched < TRAKT_SPECIAL_ITEMS_LIMIT:
            # Calculate how many items we need for this page
            items_needed = TRAKT_SPECIAL_ITEMS_LIMIT - total_items_fetched
            page_limit = min(items_needed, 100)  # API max is typically 100 per page
            
            url = f"{TRAKT_BASE_URL}{endpoint}"
            params = {
                "page": page,
                "limit": page_limit
            }
            
            logging.info(f"Fetching page {page} with limit {page_limit}...")
            
            response = requests.get(url, headers=get_trakt_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            items = response.json()
            
            if not isinstance(items, list) or len(items) == 0:
                logging.info(f"No more items available (page {page})")
                break
            
            logging.info(f"Found {len(items)} items on page {page}")
            
            # Parse items from this page
            for item in items:
                if total_items_fetched >= TRAKT_SPECIAL_ITEMS_LIMIT:
                    break
                
                media = extract_media_from_special_list_item(item, endpoint)
                if media:
                    media_items.append({
                        "title": media["title"],
                        "media_type": media["media_type"],
                        "year": media.get("year")
                    })
                    total_items_fetched += 1
                    logging.info(
                        f"Added {media['media_type']}: {media['title']} ({media.get('year', 'unknown year')}) "
                        f"[{total_items_fetched}/{TRAKT_SPECIAL_ITEMS_LIMIT}]"
                    )
            
            # Check if we got fewer items than requested (end of list)
            if len(items) < page_limit:
                logging.info(f"Reached end of list at page {page}")
                break
            
            page += 1
        
        logging.info(
            f"Special Trakt list fetched successfully. Got {len(media_items)} items "
            f"(target: {TRAKT_SPECIAL_ITEMS_LIMIT})."
        )
        return media_items
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.error("Trakt API authentication failed. Please check TRAKT_CLIENT_ID.")
            raise ValueError("Trakt API authentication failed. Please check your TRAKT_CLIENT_ID.")
        else:
            logging.error(f"Trakt API error: {e.response.status_code} - {e.response.text}")
            raise
    except Exception as e:
        logging.error(f"Error fetching special Trakt list: {str(e)}")
        raise


def parse_special_list_url(url_or_shortcut: str) -> str:
    """
    Parse special list URL or shortcut to API endpoint.
    
    Args:
        url_or_shortcut (str): URL or shortcut like "trending:movies"
        
    Returns:
        str: API endpoint path (e.g., '/movies/trending')
        
    Raises:
        ValueError: If format is invalid
    """
    # Handle shortcut format like "trending:movies"
    if ':' in url_or_shortcut and not url_or_shortcut.startswith(('http://', 'https://')):
        parts = url_or_shortcut.split(':')
        if len(parts) == 2:
            list_type, media_type = parts
            
            # Normalize media type
            if media_type.lower() in ['movies', 'movie']:
                return f"/movies/{list_type.lower()}"
            elif media_type.lower() in ['shows', 'show', 'tv']:
                return f"/shows/{list_type.lower()}"
            else:
                raise ValueError(f"Invalid media type in shortcut: {media_type}")
        else:
            raise ValueError(f"Invalid shortcut format: {url_or_shortcut}")
    
    # Handle full URLs
    if url_or_shortcut.startswith(('http://', 'https://')):
        url = url_or_shortcut.rstrip('/')
        
        # Valid patterns for special lists
        valid_patterns = [
            # Movies
            (r'trakt\.tv/movies/(trending|recommendations|streaming|anticipated|popular|favorited|watched|collected|boxoffice)', r'/movies/\1'),
            # Shows
            (r'trakt\.tv/shows/(trending|recommendations|streaming|anticipated|popular|favorited|watched|collected)', r'/shows/\1'),
        ]
        
        for pattern, replacement in valid_patterns:
            match = re.search(pattern, url)
            if match:
                return match.expand(replacement)
        
        raise ValueError(f"Invalid Trakt special list URL: {url_or_shortcut}")
    
    raise ValueError(f"Invalid format: {url_or_shortcut}")


def extract_media_from_special_list_item(item: Dict[str, Any], endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Extract media information from a special list item.
    Special lists can have different formats (trending vs popular, etc.)
    
    Args:
        item (Dict[str, Any]): API response item
        endpoint (str): The API endpoint to help determine format
        
    Returns:
        Optional[Dict[str, Any]]: Normalized media item or None if parsing fails
    """
    try:
        # Determine if this is movies or shows from endpoint
        is_movie = '/movies/' in endpoint
        media_key = 'movie' if is_movie else 'show'
        media_type = 'movie' if is_movie else 'tv'
        
        # Some endpoints (like trending) wrap the media object, others don't
        if media_key in item:
            # Wrapped format (e.g., trending)
            media = item[media_key]
        else:
            # Direct format (e.g., popular)
            media = item
        
        title = media.get('title')
        year = media.get('year')
        ids = media.get('ids', {})
        
        if not title:
            logging.warning(f"No title found in media: {media}")
            return None
        
        return {
            "title": title,
            "year": year,
            "media_type": media_type,
            "tmdb_id": ids.get('tmdb'),
            "imdb_id": ids.get('imdb')
        }
        
    except Exception as e:
        logging.warning(f"Failed to parse special list item: {str(e)}")
        return None
