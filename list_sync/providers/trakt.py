"""
Trakt provider for ListSync.
"""

import logging
import re
import os
from typing import List, Dict, Any

from seleniumbase import SB

from . import register_provider

# Get configurable limit for special Trakt lists from environment variable
TRAKT_SPECIAL_ITEMS_LIMIT = int(os.getenv('TRAKT_SPECIAL_ITEMS_LIMIT', '20'))

@register_provider("trakt")
def fetch_trakt_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch Trakt list using Selenium with pagination
    
    Args:
        list_id (str): Trakt list ID (numeric) or full URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid
    """
    media_items = []
    logging.info(f"Fetching Trakt list: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')  # Use the provided URL directly
                if not ('trakt.tv/lists/' in url or 'trakt.tv/users/' in url):
                    raise ValueError("Invalid Trakt URL format")
            else:
                # Existing logic for numeric list IDs
                if not list_id.isdigit():
                    raise ValueError("Invalid Trakt list ID format - must be numeric")
                url = f"https://trakt.tv/lists/{list_id}"
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Wait for container to load
            sb.wait_for_element_present(".container", timeout=10)
            
            while True:
                # Wait for either movies or shows container to load
                sb.wait_for_element_present(".row.posters", timeout=10)
                
                # Get all items on current page (both movies and shows)
                items = sb.find_elements(".grid-item.col-xs-6.col-md-2.col-sm-3")
                logging.info(f"Found {len(items)} items on current page")
                
                for item in items:
                    try:
                        # Get the full title and media type
                        watch_button = item.find_element("css selector", "a.watch")
                        full_title = watch_button.get_attribute("data-full-title")
                        media_type = item.get_attribute("data-type")
                        
                        # Remove year from title if present (movies only typically have years)
                        title = full_title
                        if " (" in full_title and media_type == "movie":
                            title = full_title.split(" (")[0]
                        
                        media_items.append({
                            "title": title.strip(),
                            "media_type": "tv" if media_type == "show" else "movie"
                        })
                        logging.info(f"Added {media_type}: {title}")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse Trakt item: {str(e)}")
                        continue
                
                # Check for next page button
                try:
                    next_button = sb.find_element(".pagination-top .next:not(.disabled)")
                    if not next_button:
                        logging.info("No more pages to process")
                        break
                    
                    next_link = next_button.find_element("css selector", "a")
                    next_link.click()
                    sb.sleep(3)  # Wait for new page to load
                    
                except Exception as e:
                    logging.info(f"No more pages available: {str(e)}")
                    break
            
            logging.info(f"Trakt list {list_id} fetched successfully. Found {len(media_items)} items.")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching Trakt list {list_id}: {str(e)}")
        raise


@register_provider("trakt_special")
def fetch_trakt_special_list(url_or_shortcut: str) -> List[Dict[str, Any]]:
    """
    Fetch special Trakt list (trending, popular, etc.) with configurable item limit
    
    Args:
        url_or_shortcut (str): Trakt special list URL or shortcut format (e.g., "trending:movies")
        
    Returns:
        List[Dict[str, Any]]: List of media items (max: TRAKT_SPECIAL_ITEMS_LIMIT from env var, default 20)
        
    Raises:
        ValueError: If URL format is invalid
    """
    media_items = []
    logging.info(f"Fetching special Trakt list: {url_or_shortcut}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle shortcut format like "trending:movies"
            if ':' in url_or_shortcut and not url_or_shortcut.startswith(('http://', 'https://')):
                parts = url_or_shortcut.split(':')
                if len(parts) == 2:
                    list_type, media_type = parts
                    # Convert shorthand to URL (e.g., "trending:movies" -> "https://trakt.tv/movies/trending")
                    if media_type.lower() in ['movies', 'movie']:
                        url = f"https://trakt.tv/movies/{list_type}"
                    elif media_type.lower() in ['shows', 'show', 'tv']:
                        url = f"https://trakt.tv/shows/{list_type}"
                    else:
                        raise ValueError(f"Invalid media type in special list format: {url_or_shortcut}")
                else:
                    raise ValueError(f"Invalid special list format: {url_or_shortcut}")
            else:
                # Clean the URL
                url = url_or_shortcut.rstrip('/')
            
            # Check if URL is in the correct format
            valid_patterns = [
                # Movies
                'trakt.tv/movies/trending', 'trakt.tv/movies/recommendations', 'trakt.tv/movies/streaming',
                'trakt.tv/movies/anticipated', 'trakt.tv/movies/popular', 'trakt.tv/movies/favorited',
                'trakt.tv/movies/watched', 'trakt.tv/movies/collected', 'trakt.tv/movies/boxoffice',
                # TV Shows
                'trakt.tv/shows/trending', 'trakt.tv/shows/recommendations', 'trakt.tv/shows/streaming',
                'trakt.tv/shows/anticipated', 'trakt.tv/shows/popular', 'trakt.tv/shows/favorited',
                'trakt.tv/shows/watched', 'trakt.tv/shows/collected'
            ]
            
            valid_url = False
            for pattern in valid_patterns:
                if pattern in url:
                    valid_url = True
                    break
            
            if not valid_url:
                raise ValueError(f"Invalid Trakt special list URL: {url}")
                
            logging.info(f"Fetching special Trakt list: {url} (limit: {TRAKT_SPECIAL_ITEMS_LIMIT} items)")
            sb.open(url)
            
            page_number = 1
            total_items_scraped = 0
            
            # Continue scraping pages until we reach the limit or run out of pages
            while total_items_scraped < TRAKT_SPECIAL_ITEMS_LIMIT:
                logging.info(f"Processing page {page_number}...")
                
                # Wait for page to load - looking for multiple possible elements
                try:
                    # First try the row fanarts container
                    sb.wait_for_element_present(".row.fanarts", timeout=15)
                    logging.info("Found .row.fanarts container")
                except Exception:
                    # If that fails, try looking for any grid items directly
                    try:
                        sb.wait_for_element_present("[data-type='movie'], [data-type='show']", timeout=15)
                        logging.info("Found grid items by data-type attribute")
                    except Exception:
                        # Try one more general selector for divs with grid-item class
                        sb.wait_for_element_present(".grid-item", timeout=15)
                        logging.info("Found grid items by .grid-item class")
                
                # Add a small wait to ensure the page is fully loaded
                sb.sleep(3)
                
                # Now try to get all grid items
                # Try multiple selectors since the grid classes seem to vary
                items = []
                selectors_to_try = [
                    ".grid-item",
                    "[data-type='movie'], [data-type='show']",
                    ".row.fanarts > div"
                ]
                
                for selector in selectors_to_try:
                    items = sb.find_elements(selector)
                    if items and len(items) > 0:
                        logging.info(f"Found {len(items)} items on page {page_number} using selector: {selector}")
                        break
                
                if not items or len(items) == 0:
                    logging.warning(f"Could not find any list items on page {page_number}")
                    break
                
                # Process items on current page
                items_processed_this_page = 0
                for item in items:
                    if total_items_scraped >= TRAKT_SPECIAL_ITEMS_LIMIT:
                        break
                        
                    try:
                        # Extract media type
                        media_type = item.get_attribute("data-type")
                        if not media_type:
                            # Try to determine from the URL
                            links = item.find_elements("css selector", "a")
                            for link in links:
                                href = link.get_attribute("href")
                                if href:
                                    if "/movies/" in href:
                                        media_type = "movie"
                                        break
                                    elif "/shows/" in href:
                                        media_type = "show"
                                        break
                        
                        # If still no media type, skip this item
                        if not media_type:
                            continue
                        
                        # Extract title and year - try different selectors
                        title_elem = None
                        title_selectors = [
                            ".titles h3",
                            ".fanart .titles h3"
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_elem = item.find_element("css selector", selector)
                                if title_elem:
                                    break
                            except Exception:
                                continue
                        
                        if not title_elem:
                            logging.warning("Could not find title element, skipping item")
                            continue
                        
                        # Title format is typically "Title <span class="year">Year</span>"
                        full_title = title_elem.text
                        year = None
                        
                        # Try to extract year from span.year
                        try:
                            year_span = title_elem.find_element("css selector", "span.year")
                            if year_span:
                                year_text = year_span.text.strip()
                                if year_text.isdigit():
                                    year = int(year_text)
                                # Remove the year span from the title
                                full_title = full_title.replace(year_span.text, "").strip()
                        except Exception:
                            # If we can't find the year span, try to extract from the full title
                            if " (" in full_title and ")" in full_title:
                                title_parts = full_title.split(" (")
                                full_title = title_parts[0].strip()
                                year_part = title_parts[1].strip(")")
                                if year_part.isdigit():
                                    year = int(year_part)
                        
                        media_items.append({
                            "title": full_title.strip(),
                            "media_type": "tv" if media_type == "show" else "movie",
                            "year": year
                        })
                        
                        total_items_scraped += 1
                        items_processed_this_page += 1
                        logging.info(f"Added {media_type}: {full_title} ({year if year else 'unknown year'}) [{total_items_scraped}/{TRAKT_SPECIAL_ITEMS_LIMIT}]")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse Trakt special list item: {str(e)}")
                        continue
                
                logging.info(f"Processed {items_processed_this_page} items on page {page_number}")
                
                # Check if we've reached our limit
                if total_items_scraped >= TRAKT_SPECIAL_ITEMS_LIMIT:
                    logging.info(f"Reached target limit of {TRAKT_SPECIAL_ITEMS_LIMIT} items")
                    break
                
                # Look for next page button
                try:
                    # Look for the next page button that's not disabled
                    next_button = sb.find_element(".next a")
                    if not next_button:
                        logging.info("No next page button found, reached end of list")
                        break
                    
                    # Check if the next button is actually clickable (not disabled)
                    next_container = sb.find_element(".next")
                    if "no-link" in next_container.get_attribute("class"):
                        logging.info("Next page button is disabled, reached end of list")
                        break
                    
                    logging.info(f"Clicking next page button to go to page {page_number + 1}")
                    next_button.click()
                    
                    # Wait for the new page to load
                    sb.sleep(3)
                    page_number += 1
                    
                except Exception as e:
                    logging.info(f"No more pages available or error clicking next: {str(e)}")
                    break
            
            logging.info(f"Special Trakt list fetched successfully. Got {len(media_items)} items across {page_number} pages (target: {TRAKT_SPECIAL_ITEMS_LIMIT}).")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching special Trakt list: {str(e)}")
        raise
