"""
TVDB (The TV Database) list provider for ListSync.
"""

import logging
import re
import requests
import time
from typing import List, Dict, Any, Optional

from seleniumbase import SB

from . import register_provider


@register_provider("tvdb")
def fetch_tvdb_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch TVDB list using API if available, otherwise fallback to web scraping
    
    Args:
        list_id (str): TVDB list ID, user ID for favorites, or URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid
    """
    # Import here to avoid circular imports
    from ..config import get_tvdb_api_key
    
    # Check if API key is available
    api_key = get_tvdb_api_key()
    
    if api_key:
        logging.info(f"Using TVDB API for list: {list_id}")
        return _fetch_tvdb_list_api(list_id, api_key)
    else:
        logging.info(f"Using web scraping fallback for TVDB list: {list_id}")
        return _fetch_tvdb_list_scraping(list_id)


def _get_tvdb_token(api_key: str) -> Optional[str]:
    """
    Get TVDB API token for authentication.
    
    Args:
        api_key (str): TVDB API key
        
    Returns:
        Optional[str]: JWT token if successful, None otherwise
    """
    try:
        auth_url = "https://api4.thetvdb.com/v4/login"
        auth_data = {
            "apikey": api_key
        }
        
        response = requests.post(auth_url, json=auth_data, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('data', {}).get('token')
        
        if token:
            logging.info("Successfully authenticated with TVDB API")
            return token
        else:
            logging.error("Failed to get token from TVDB API response")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"TVDB API authentication failed: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error during TVDB authentication: {str(e)}")
        return None


def _fetch_tvdb_list_api(list_id: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch TVDB list using web scraping with optional API enhancement
    
    Args:
        list_id (str): TVDB list URL or identifier
        api_key (str): TVDB API key (optional for enhancement)
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # For TVDB, we primarily use web scraping since they don't have public lists like TMDB
        # The API key can be used to enhance the data we get from scraping
        logging.info(f"Using web scraping for TVDB list: {list_id}")
        
        # Use web scraping to get the basic list
        media_items = _fetch_tvdb_list_scraping(list_id)
        
        # If we have an API key, enhance the data with API information
        if api_key and media_items:
            logging.info("Enhancing scraped data with TVDB API information")
            token = _get_tvdb_token(api_key)
            if token:
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                media_items = _enhance_with_tvdb_api(media_items, headers)
        
        logging.info(f"Successfully fetched {len(media_items)} items from TVDB")
        return media_items
        
    except Exception as e:
        logging.error(f"Error fetching TVDB list {list_id}: {str(e)}")
        raise


def _fetch_tvdb_user_favorites(user_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch user favorites from TVDB API.
    
    Args:
        user_id (str): TVDB user ID
        headers (Dict[str, str]): API headers with authentication
        
    Returns:
        List[Dict[str, Any]]: List of favorite series
    """
    media_items = []
    
    try:
        # TVDB API v4 endpoint for user favorites
        favorites_url = f"https://api4.thetvdb.com/v4/user/{user_id}/favorites"
        
        logging.info(f"Fetching TVDB user favorites from: {favorites_url}")
        
        response = requests.get(favorites_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        favorites = data.get('data', [])
        
        logging.info(f"Found {len(favorites)} favorites")
        
        # Process each favorite
        for favorite in favorites:
            try:
                # Get series details for each favorite
                series_id = favorite.get('seriesId')
                if series_id:
                    series_details = _get_tvdb_series_details(series_id, headers)
                    if series_details:
                        processed_item = _process_tvdb_series_item(series_details)
                        if processed_item:
                            media_items.append(processed_item)
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
                
            except Exception as e:
                logging.warning(f"Failed to process favorite {favorite}: {str(e)}")
                continue
        
        return media_items
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch TVDB user favorites: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error processing TVDB user favorites: {str(e)}")
        raise


def _get_tvdb_series_details(series_id: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Get detailed series information from TVDB API.
    
    Args:
        series_id (str): TVDB series ID
        headers (Dict[str, str]): API headers with authentication
        
    Returns:
        Optional[Dict[str, Any]]: Series details or None if failed
    """
    try:
        series_url = f"https://api4.thetvdb.com/v4/series/{series_id}"
        
        response = requests.get(series_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', {})
        
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to get series details for {series_id}: {str(e)}")
        return None
    except Exception as e:
        logging.warning(f"Error getting series details for {series_id}: {str(e)}")
        return None


def _process_tvdb_series_item(series: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single series from TVDB API response
    
    Args:
        series (Dict[str, Any]): Series from TVDB API response
        
    Returns:
        Optional[Dict[str, Any]]: Processed item or None if processing failed
    """
    try:
        # Extract year from first air date
        year = None
        first_air_date = series.get('firstAired')
        if first_air_date:
            year_match = re.search(r'(\d{4})', first_air_date)
            if year_match:
                year = int(year_match.group(1))
        
        processed_item = {
            "title": series.get('name', ''),
            "media_type": "tv",  # TVDB is primarily for TV shows
            "year": year,
            "tvdb_id": str(series.get('id', '')),
            "overview": series.get('overview', ''),
            "status": series.get('status', ''),
            "network": series.get('network', '')
        }
        
        logging.debug(f"Added TV series: {processed_item['title']} ({year if year else 'year unknown'})")
        return processed_item
        
    except Exception as e:
        logging.warning(f"Failed to process TVDB series item: {str(e)}")
        return None


def _fetch_tvdb_list_scraping(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch TVDB list using web scraping (fallback implementation)
    
    Args:
        list_id (str): TVDB list ID or URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    logging.info(f"Fetching TVDB list via web scraping: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')
            else:
                # For TVDB, we'll try to construct a user favorites URL
                # This is a fallback since TVDB doesn't have public lists like TMDB
                url = f"https://www.thetvdb.com/user/{list_id}/favorites"
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Initial wait for page load
            sb.sleep(5)
            
            # Add some human-like scrolling behavior
            try:
                sb.execute_script("window.scrollTo(0, 300);")
                sb.sleep(1)
                sb.execute_script("window.scrollTo(0, 600);")
                sb.sleep(1)
                sb.execute_script("window.scrollTo(0, 900);")
                sb.sleep(1)
            except Exception as e:
                logging.warning(f"Could not perform scrolling: {str(e)}")
            
            # Wait for any potential captcha/anti-bot verification
            sb.sleep(3)
            
            # Process the list
            media_items.extend(_process_tvdb_list(sb, url))
            
            logging.info(f"Found {len(media_items)} items from TVDB list {list_id}")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching TVDB list {list_id}: {str(e)}")
        raise


def _process_tvdb_list(sb, url) -> List[Dict[str, Any]]:
    """
    Process a TVDB list page using web scraping.
    
    Args:
        sb: SeleniumBase instance
        url: URL of the list
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # Wait for list content to load
        logging.info("Waiting for TVDB list content to load...")
        
        # Look for the main list content structure
        try:
            # Wait for the main list structure
            sb.wait_for_element_present('div.row', timeout=10)
            logging.info("Found TVDB list content structure")
        except Exception as e:
            logging.warning(f"Could not find TVDB list content: {str(e)}")
            return media_items
        
        # Additional wait to ensure everything is loaded
        sb.sleep(3)
        
        # Find all list items (each item is in a div.row)
        items = sb.find_elements("css selector", 'div.row')
        logging.info(f"Found {len(items)} potential list items")
        
        if not items:
            logging.warning("No list items found")
            return media_items
        
        # Process all items
        for i, item in enumerate(items):
            try:
                # Look for the title link within this row
                title_links = item.find_elements("css selector", 'h3.mt-0.mb-0 a')
                if not title_links:
                    continue
                
                title_link = title_links[0]
                title = title_link.text.strip()
                if not title:
                    continue
                
                # Extract ID and determine media type from href
                href = title_link.get_attribute("href")
                media_id = None
                media_type = "unknown"
                
                if href:
                    if '/movies/' in href:
                        media_type = "movie"
                        id_match = re.search(r'/movies/([^/]+)', href)
                        if id_match:
                            media_id = id_match.group(1)
                    elif '/series/' in href:
                        media_type = "tv"
                        id_match = re.search(r'/series/(\d+)', href)
                        if id_match:
                            media_id = id_match.group(1)
                
                # Extract year from the same row
                year = None
                try:
                    # Look for the year in the div with fa-film icon
                    year_divs = item.find_elements("css selector", 'div.mb-1')
                    for year_div in year_divs:
                        year_text = year_div.text.strip()
                        year = _extract_year_from_text(year_text)
                        if year:
                            break
                except Exception:
                    pass
                
                # Extract description if available
                description = ""
                try:
                    desc_p = item.find_elements("css selector", 'p')
                    if desc_p:
                        description = desc_p[0].text.strip()
                except Exception:
                    pass
                
                media_items.append({
                    "title": title,
                    "media_type": media_type,
                    "year": year,
                    "tvdb_id": media_id,
                    "description": description
                })
                
                logging.info(f"Added {media_type}: {title} ({year if year else 'year unknown'}) (TVDB ID: {media_id})")
                
            except Exception as e:
                logging.warning(f"Failed to parse TVDB item {i+1}: {str(e)}")
                continue
        
        logging.info(f"Successfully extracted {len(media_items)} items from TVDB list")
        return media_items
        
    except Exception as e:
        logging.error(f"Error processing TVDB list: {str(e)}")
        return media_items


def _enhance_with_tvdb_api(media_items: List[Dict[str, Any]], headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Enhance scraped data with TVDB API information.
    
    Args:
        media_items (List[Dict[str, Any]]): List of scraped media items
        headers (Dict[str, str]): API headers with authentication
        
    Returns:
        List[Dict[str, Any]]: Enhanced media items
    """
    enhanced_items = []
    
    for item in media_items:
        try:
            # Try to get additional details from TVDB API
            if item.get('tvdb_id') and item.get('media_type') == 'tv':
                # For TV series, get series details
                series_details = _get_tvdb_series_details(item['tvdb_id'], headers)
                if series_details:
                    # Enhance with API data
                    item.update({
                        'overview': series_details.get('overview', item.get('description', '')),
                        'status': series_details.get('status', ''),
                        'network': series_details.get('network', ''),
                        'first_aired': series_details.get('firstAired', ''),
                        'runtime': series_details.get('runtime', ''),
                        'rating': series_details.get('rating', ''),
                        'genres': ', '.join(series_details.get('genres', []))
                    })
            
            enhanced_items.append(item)
            
        except Exception as e:
            logging.warning(f"Failed to enhance item {item.get('title', 'Unknown')}: {str(e)}")
            enhanced_items.append(item)  # Add original item if enhancement fails
    
    return enhanced_items


def _extract_year_from_text(text: str) -> Optional[int]:
    """Extract year from various date formats."""
    if not text:
        return None
    
    # Date patterns to try (in order of specificity)
    date_patterns = [
        # Full date formats: "July 19, 2010", "Dec 25, 2023", "January 1, 2000"
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+(\d{4})',
        
        # Month day year: "7/19/2010", "12/25/2023", "1/1/2000"
        r'\d{1,2}/\d{1,2}/(\d{4})',
        
        # Year month day: "2010-07-19", "2023-12-25"
        r'(\d{4})-\d{1,2}-\d{1,2}',
        
        # Just year: "2010", "2023"
        r'(\d{4})',
        
        # Year in parentheses: "(2010)", "(2023)"
        r'\((\d{4})\)',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                year = int(match.group(1))
                # Validate year range
                if 1900 <= year <= 2030:
                    return year
            except (ValueError, IndexError):
                continue
    
    return None
