"""
MDBList provider for ListSync.
"""

import logging
import re
from typing import List, Dict, Any

from seleniumbase import SB

from . import register_provider


@register_provider("mdblist")
def fetch_mdblist_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch MDBList list using Selenium with infinite scrolling support
    
    Args:
        list_id (str): MDBList list ID in format 'username/listname' or full URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid
    """
    media_items = []
    logging.info(f"Fetching MDBList: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')  # Use the provided URL directly
                if 'mdblist.com/lists/' not in url:
                    raise ValueError("Invalid MDBList URL format")
            else:
                # Assume it's a username/listname format
                parts = list_id.split('/')
                if len(parts) == 2:
                    url = f"https://mdblist.com/lists/{parts[0]}/{parts[1]}"
                else:
                    raise ValueError("Invalid MDBList format - must be 'username/listname' or a full URL")
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Initial wait for the page to start loading
            sb.sleep(3)
            
            # Scroll to load all content (infinite scrolling)
            last_height = sb.execute_script("return document.body.scrollHeight")
            items_count = 0
            max_scroll_attempts = 50  # Prevent infinite loops
            
            logging.info("Starting infinite scroll to load all items")
            for _ in range(max_scroll_attempts):
                # Scroll down to bottom
                sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                sb.sleep(2)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = sb.execute_script("return document.body.scrollHeight")
                
                # Count current number of items
                current_items = len(sb.find_elements(".header.movie-title"))
                
                if new_height == last_height and current_items == items_count:
                    # If heights are the same and no new items, we've reached the end
                    logging.info(f"Scrolling complete - loaded {current_items} items")
                    break
                
                items_count = current_items
                last_height = new_height
                logging.info(f"Scrolled and found {items_count} items so far, continuing...")
            
            # Now extract all items using .card selector (more reliable)
            items = sb.find_elements(".card")
            logging.info(f"Found {len(items)} total card items on the page")
            
            for item in items:
                try:
                    # Check if this card has a movie title (skip non-movie cards)
                    title_elem = item.find_element("css selector", ".header.movie-title")
                    if not title_elem:
                        logging.debug("Skipping card without movie title")
                        continue
                    
                    # Extract media type from link
                    links = item.find_elements("css selector", "a")
                    media_type = "unknown"
                    imdb_id = None
                    
                    for link in links:
                        href = link.get_attribute("href")
                        if href:
                            if "/movie/" in href:
                                media_type = "movie"
                                imdb_match = re.search(r'/movie/(tt\d+)', href)
                                if imdb_match:
                                    imdb_id = imdb_match.group(1)
                                break
                            elif "/show/" in href:
                                media_type = "tv"
                                imdb_match = re.search(r'/show/(tt\d+)', href)
                                if imdb_match:
                                    imdb_id = imdb_match.group(1)
                                break
                    
                    # Extract title and year
                    full_title = title_elem.text.strip()
                    # Parse title and year (format: "Title (Year)")
                    year_match = re.search(r'(.+?)\s*\((\d{4})\)', full_title)
                    if year_match:
                        title = year_match.group(1).strip()
                        year = int(year_match.group(2))
                    else:
                        title = full_title
                        year = None
                    
                    # Skip items with empty titles
                    if not title:
                        logging.warning("Skipping item with empty title")
                        continue
                    
                    media_items.append({
                        "title": title,
                        "imdb_id": imdb_id,
                        "media_type": media_type,
                        "year": year
                    })
                    logging.info(f"Added {media_type}: {title} ({year}) (IMDB ID: {imdb_id})")
                except Exception as e:
                    logging.warning(f"Failed to parse MDBList item: {str(e)}")
                    continue
            
            logging.info(f"MDBList fetched successfully. Found {len(media_items)} items.")
            return media_items
            
    except Exception as e:
        logging.error(f"Error fetching MDBList: {str(e)}")
        raise
