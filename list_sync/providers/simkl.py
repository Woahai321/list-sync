"""
SIMKL list provider for ListSync.
Uses official SIMKL API for authenticated user watchlists.
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional

import requests
from . import register_provider

# SIMKL API configuration
SIMKL_API_BASE = "https://api.simkl.com"
SIMKL_CLIENT_ID = os.getenv('SIMKL_CLIENT_ID')
SIMKL_USER_TOKEN = os.getenv('SIMKL_USER_TOKEN')


def get_simkl_headers() -> Dict[str, str]:
    """Get headers for SIMKL API requests."""
    if not SIMKL_CLIENT_ID or not SIMKL_USER_TOKEN:
        raise ValueError("SIMKL_CLIENT_ID and SIMKL_USER_TOKEN required. Get credentials at https://simkl.com/settings/developer/")
    
    return {
        "Content-Type": "application/json",
        "simkl-api-key": SIMKL_CLIENT_ID,
        "Authorization": f"Bearer {SIMKL_USER_TOKEN}"
    }


def fetch_simkl_watchlist(media_type: str) -> List[Dict[str, Any]]:
    """
    Fetch user's watchlist from SIMKL API.
    
    Args:
        media_type (str): Type of media to fetch ('movies', 'shows', 'anime')
        
    Returns:
        List[Dict[str, Any]]: List of media items from watchlist
    """
    if not SIMKL_CLIENT_ID or not SIMKL_USER_TOKEN:
        logging.error("SIMKL_CLIENT_ID and SIMKL_USER_TOKEN required. Get credentials at https://simkl.com/settings/developer/")
        return []
    
    url = f"{SIMKL_API_BASE}/sync/all-items/{media_type}"
    params = {"extended": "full"}
    
    logging.info(f"🎯 SIMKL API: Fetching {media_type} watchlist")
    
    try:
        response = requests.get(url, headers=get_simkl_headers(), params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 10))
            logging.warning(f"⚠️  SIMKL API rate limit hit. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            response = requests.get(url, headers=get_simkl_headers(), params=params, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        
        media_items = []
        for item in data:
            # Extract basic information
            title = item.get('title', '')
            year = item.get('year')
            tmdb_id = item.get('ids', {}).get('tmdb')
            imdb_id = item.get('ids', {}).get('imdb')
            tvdb_id = item.get('ids', {}).get('tvdb')
            
            # Map SIMKL status to our format
            status = item.get('status', '')
            if status in ['watching', 'plantowatch', 'completed', 'hold', 'dropped']:
                media_items.append({
                    "title": title,
                    "media_type": "movie" if media_type == "movies" else "show",
                    "year": year,
                    "tmdb_id": tmdb_id,
                    "imdb_id": imdb_id,
                    "tvdb_id": tvdb_id,
                    "status": status
                })
        
        logging.info(f"✅ SIMKL API: Fetched {len(media_items)} {media_type} items")
        return media_items
        
    except requests.exceptions.RequestException as e:
        if "401" in str(e):
            logging.error(f"❌ SIMKL API authentication failed. Please check your SIMKL_USER_TOKEN.")
            logging.error(f"   Get your OAuth access_token at: https://simkl.com/oauth/authorize")
            logging.error(f"   See documentation: https://simkl.com/settings/developer/")
        else:
            logging.error(f"❌ SIMKL API error fetching {media_type}: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"❌ SIMKL API unexpected error fetching {media_type}: {str(e)}")
        return []
    

@register_provider("simkl")
def fetch_simkl_list(list_id: str) -> List[Dict[str, Any]]:
    """
    SIMKL provider is temporarily disabled.
    Waiting for SIMKL API to support custom public lists.
    
    Args:
        list_id (str): List identifier (ignored)
        
    Returns:
        List[Dict[str, Any]]: Empty list with warning message
    """
    logging.warning("⚠️  SIMKL provider is temporarily disabled.")
    logging.warning("   SIMKL API currently only supports authenticated user watchlists.")
    logging.warning("   Custom public lists are not supported by SIMKL API.")
    logging.warning("   Use Trakt, IMDB, or MDBList for public list syncing.")
    
    print("⚠️  SIMKL provider is temporarily disabled.")
    print("   SIMKL API currently only supports authenticated user watchlists.")
    print("   Custom public lists are not supported by SIMKL API.")
    print("   Use Trakt, IMDB, or MDBList for public list syncing.")
    
    return []


def search_simkl_by_title(title: str, year: Optional[int] = None, media_type: str = "movie") -> Optional[Dict[str, Any]]:
    """
    Search SIMKL by title and year to get IDs.
    
    Args:
        title (str): Media title
        year (int, optional): Release year
        media_type (str): Type of media ('movie' or 'show')
        
    Returns:
        Optional[Dict[str, Any]]: Media information with IDs, or None if not found
    """
    if not SIMKL_CLIENT_ID or not SIMKL_USER_TOKEN:
        logging.error("SIMKL_CLIENT_ID and SIMKL_USER_TOKEN required for search")
        return None
    
    url = f"{SIMKL_API_BASE}/search/{media_type}"
    params = {
        "q": title,
        "extended": "full"
    }
    
    if year:
        params["year"] = year
    
    logging.info(f"🔍 SIMKL API: Searching for '{title}' ({year}) [{media_type}]")
    
    try:
        response = requests.get(url, headers=get_simkl_headers(), params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 10))
            logging.warning(f"⚠️  SIMKL API rate limit hit. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            response = requests.get(url, headers=get_simkl_headers(), params=params, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            item = data[0]  # Take first result
            return {
                "title": item.get('title', ''),
                "year": item.get('year'),
                "media_type": media_type,
                "tmdb_id": item.get('ids', {}).get('tmdb'),
                "imdb_id": item.get('ids', {}).get('imdb'),
                "tvdb_id": item.get('ids', {}).get('tvdb')
            }
        
        logging.warning(f"⚠️  SIMKL API: No results found for '{title}' ({year})")
        return None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ SIMKL API search error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"❌ SIMKL API unexpected search error: {str(e)}")
        return None