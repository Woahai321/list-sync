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
            
            # Determine if this is a watchlist or regular list
            is_watchlist = '/watchlist' in base_url or list_id.endswith('/watchlist')
            
            # Use detail view for better data extraction (only for custom lists, not watchlists)
            if not is_watchlist and not base_url.endswith('/detail/'):
                base_url = f"{base_url}/detail/"
            
            logging.info(f"Processing Letterboxd {'watchlist' if is_watchlist else 'list'}: {base_url}")
            
            page = 1
            next_page_url = None  # Track the next page URL
            while True:
                # Construct page URL - handle both first page and subsequent pages
                if page == 1:
                    current_url = base_url
                elif next_page_url:
                    # Use the specific next page URL we found
                    current_url = next_page_url
                else:
                    # Fallback: construct URL manually
                    if is_watchlist:
                        current_url = f"{base_url}/page/{page}/"
                    else:
                        current_url = f"{base_url}page/{page}/"
                
                logging.info(f"Loading URL: {current_url}")
                sb.open(current_url)
                
                # Wait for the list container to load - different selectors for watchlists vs custom lists
                if is_watchlist:
                    try:
                        sb.wait_for_element_present("ul.poster-list", timeout=20)
                    except:
                        logging.warning("Could not find ul.poster-list, attempting to continue")
                else:
                    sb.wait_for_element_present("div.list-detailed-entries-list", timeout=20)
                
                logging.info(f"Processing page {page}")
                
                # Scroll to load all lazy-loaded content
                logging.info("Scrolling to load all content...")
                scroll_attempts = 3 if is_watchlist else 10  # Watchlists load faster
                for i in range(scroll_attempts):
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(1 if is_watchlist else 2)
                    
                    # Also try scrolling to specific elements (for custom lists)
                    if not is_watchlist:
                        items = sb.find_elements("div.listitem.js-listitem")
                        if items:
                            sb.execute_script("arguments[0].scrollIntoView(true);", items[-1])
                            sb.sleep(1)
                
                logging.info("Scrolling complete")
                
                # Extract data - different structure for watchlists vs custom lists
                logging.info("Extracting data from attributes...")
                
                if is_watchlist:
                    # Watchlists use li.griditem structure
                    figures = sb.find_elements("li.griditem")
                    logging.info(f"Found {len(figures)} grid items (watchlist)")
                else:
                    # Custom lists use detail view with figures
                    figures = sb.find_elements("div.react-component.figure[data-item-name]")
                    logging.info(f"Found {len(figures)} figures (custom list)")
                
                # If we find 0 items, we've gone too far - break
                if len(figures) == 0:
                    logging.info(f"No items found on page {page}, ending pagination")
                    break
                
                for figure in figures:
                    try:
                        # Extract data - different attributes for watchlist vs custom list
                        if is_watchlist:
                            # For watchlists, find the react-component div within the grid item
                            try:
                                react_div = figure.find_element("css selector", "div.react-component")
                            except:
                                react_div = figure
                            
                            item_name = react_div.get_attribute("data-item-name")
                            film_id = react_div.get_attribute("data-film-id")
                            slug = react_div.get_attribute("data-item-slug")
                        else:
                            # For custom lists, use the figure element directly
                            item_name = figure.get_attribute("data-item-name")
                            film_id = figure.get_attribute("data-film-id")
                            slug = figure.get_attribute("data-item-slug")
                        
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
                
                # Check for next page - improved logic for Letterboxd pagination
                try:
                    has_next_page = False
                    next_page_url = None
                    
                    # Look for pagination container first
                    pagination_container = sb.find_elements("div.pagination")
                    if pagination_container:
                        # Look for next button within pagination
                        next_buttons = sb.find_elements("div.pagination a.next")
                        if next_buttons and len(next_buttons) > 0:
                            next_href = next_buttons[0].get_attribute("href")
                            if next_href:
                                has_next_page = True
                                # Convert relative URL to absolute URL
                                if next_href.startswith('/'):
                                    next_page_url = f"https://letterboxd.com{next_href}"
                                else:
                                    next_page_url = next_href
                                logging.info(f"Found next page URL: {next_page_url}")
                    
                    # Fallback: also check for numbered pagination
                    if not has_next_page:
                        page_links = sb.find_elements("div.pagination .paginate-pages a")
                        if page_links:
                            # Find the highest page number
                            max_page = page
                            for link in page_links:
                                href = link.get_attribute("href")
                                if href and f"page/{page + 1}/" in href:
                                    has_next_page = True
                                    next_page_url = href if href.startswith('http') else f"https://letterboxd.com{href}"
                                    break
                    
                    if has_next_page and next_page_url:
                        page += 1
                        logging.info(f"Next page available, will load page {page} from URL: {next_page_url}")
                        # Store the next page URL for the next iteration
                        # The next_page_url variable will be used in the next loop iteration
                        # Continue to next iteration of while loop which will load the next page
                    else:
                        logging.info("No next page found, must be the last page")
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
