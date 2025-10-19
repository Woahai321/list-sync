"""
Letterboxd provider for ListSync.
"""

import logging
import re
from typing import List, Dict, Any

from seleniumbase import SB

from . import register_provider


def _determine_media_type(title: str) -> str:
    """
    Determine if a title is a movie or TV show based on common patterns
    
    Args:
        title (str): The title to analyze
        
    Returns:
        str: "movie" or "tv_show"
    """
    title_lower = title.lower()
    
    # TV show indicators
    tv_indicators = [
        ':',  # Colon often indicates episode (e.g., "Euphoria: Trouble Don't Last Always")
        'season', 'episode', 'series',
        'special', 'pilot', 'finale',
        'part i', 'part ii', 'part iii', 'part iv', 'part v',
        'chapter', 'episode'
    ]
    
    # Check for TV show patterns
    for indicator in tv_indicators:
        if indicator in title_lower:
            return "tv_show"
    
    # Check for specific TV show patterns
    if any(pattern in title_lower for pattern in [
        'black mirror:', 'sherlock:', 'euphoria:', 'sense8:',
        'bojack horseman', 'wet hot american summer',
        'conversations with a killer', 'the walking dead:',
        'big little lies', 'sharp objects', 'godless',
        'who is america', 'the young pope', 'war and peace',
        'the vietnam war', 'the civil war', 'cosmos:',
        'roots', 'show me a hero', 'patrick melrose'
    ]):
        return "tv_show"
    
    # Default to movie
    return "movie"


@register_provider("letterboxd")
def fetch_letterboxd_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch Letterboxd list using Selenium with pagination, supporting both regular lists and watchlists
    
    Args:
        list_id (str): Letterboxd list ID (username/list-slug) or full URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    logging.info(f"Fetching Letterboxd list: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                base_url = list_id.rstrip('/')
            else:
                base_url = f"https://letterboxd.com/{list_id}"
            
            # Use detail view for better data extraction
            if not base_url.endswith('/detail/'):
                base_url = f"{base_url}/detail/"
            
            # Determine if this is a watchlist or regular list
            is_watchlist = '/watchlist' in base_url or list_id.endswith('/watchlist')
            
            logging.info(f"Processing Letterboxd {'watchlist' if is_watchlist else 'list'}: {base_url}")
            
            page = 1
            while True:
                # Construct page URL
                current_url = base_url if page == 1 else f"{base_url}page/{page}/"
                logging.info(f"Loading URL: {current_url}")
                sb.open(current_url)
                
                # Wait for the list container to load
                sb.wait_for_element_present("div.list-detailed-entries-list", timeout=20)
                logging.info(f"Processing page {page}")
                
                # Scroll to load all lazy-loaded content
                logging.info("Scrolling to load all content...")
                for i in range(10):  # Multiple scroll attempts to ensure all content loads
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(2)
                    
                    # Also try scrolling to specific elements
                    items = sb.find_elements("div.listitem.js-listitem")
                    if items:
                        sb.execute_script("arguments[0].scrollIntoView(true);", items[-1])
                        sb.sleep(1)
                
                logging.info("Scrolling complete")
                
                # Extract data from data attributes instead of text content
                logging.info("Extracting data from attributes...")
                figures = sb.find_elements("div.react-component.figure[data-item-name]")
                logging.info(f"Found {len(figures)} figures with data-item-name")
                
                # If we find 0 items, we've gone too far - break
                if len(figures) == 0:
                    logging.info(f"No items found on page {page}, ending pagination")
                    break
                
                for figure in figures:
                    try:
                        # Extract title and year from data-item-name
                        item_name = figure.get_attribute("data-item-name")
                        if not item_name:
                            continue
                        
                        # Parse title and year (format: "Title (Year)")
                        year_match = re.search(r'(.+?)\s*\((\d{4})\)', item_name)
                        if year_match:
                            title = year_match.group(1).strip()
                            year = int(year_match.group(2))
                        else:
                            title = item_name
                            year = None
                        
                        # Skip items with empty titles
                        if not title:
                            logging.warning("Skipping item with empty title")
                            continue
                        
                        # Extract film ID and slug for additional metadata
                        film_id = figure.get_attribute("data-film-id")
                        slug = figure.get_attribute("data-item-slug")
                        
                        # Determine media type (all appear to be films)
                        media_type = "movie"
                        
                        media_items.append({
                            "title": title,
                            "media_type": media_type,
                            "year": year,
                            "film_id": film_id,
                            "slug": slug
                        })
                        logging.info(f"Added {media_type}: {title} ({year if year else 'year unknown'})")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse item: {str(e)}")
                        continue
                
                # Check for next page
                try:
                    # Look for pagination links
                    next_buttons = sb.find_elements("a.next")
                    has_next_page = False
                    next_button = None
                    
                    if next_buttons:
                        # Check if there's a valid next page button
                        for btn in next_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                has_next_page = True
                                next_button = btn
                                break
                    
                    if has_next_page and next_button:
                        # Click the next button to navigate
                        try:
                            # Scroll to make the button visible
                            sb.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            sb.sleep(1)  # Wait a moment for scroll to complete
                            
                            # Click the button
                            next_button.click()
                            
                            # Wait for the page to load
                            sb.wait_for_element_present("div.list-detailed-entries-list", timeout=20)
                            sb.sleep(2)  # Additional wait to ensure page loads
                            page += 1
                            logging.info(f"Successfully navigated to page {page}")
                        except Exception as e:
                            logging.warning(f"Error clicking next button: {str(e)}")
                            # Try direct URL navigation as fallback
                            fallback_url = f"{base_url}page/{page + 1}/"
                            logging.info(f"Falling back to direct URL navigation: {fallback_url}")
                            sb.open(fallback_url)
                            sb.wait_for_element_present("div.list-detailed-entries-list", timeout=20)
                            page += 1
                    else:
                        logging.info("No next page button found, must be the last page")
                        break
                except Exception as e:
                    logging.warning(f"Error checking pagination: {str(e)}")
                    # If there's an error checking pagination, assume we're done
                    break
            
            logging.info(f"Letterboxd list fetched successfully. Found {len(media_items)} items across {page} pages.")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching Letterboxd list: {str(e)}")
        raise
