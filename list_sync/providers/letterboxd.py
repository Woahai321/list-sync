"""
Letterboxd provider for ListSync.
"""

import logging
from typing import List, Dict, Any

from seleniumbase import SB

from . import register_provider


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
            
            logging.info(f"Processing Letterboxd {'watchlist' if is_watchlist else 'list'}: {base_url}")
            
            page = 1
            while True:
                # Construct page URL
                current_url = base_url if page == 1 else f"{base_url}/page/{page}"
                logging.info(f"Loading URL: {current_url}")
                sb.open(current_url)
                
                # Wait for the list container to load
                sb.wait_for_element_present("ul.poster-list", timeout=20)
                logging.info(f"Processing page {page}")
                
                # Get all movie items on current page
                items = sb.find_elements("li.poster-container")
                items_count = len(items)
                logging.info(f"Found {items_count} items on page {page}")
                
                # If we find 0 items, we've gone too far - break
                if items_count == 0:
                    logging.info(f"No items found on page {page}, ending pagination")
                    break
                
                for item in items:
                    try:
                        # Get the film details link
                        film_link = item.find_element("css selector", "div.film-poster")
                        
                        # Extract title from data-film-slug
                        film_slug = film_link.get_attribute("data-film-slug")
                        if film_slug:
                            # Convert slug to title (e.g., "the-matrix" -> "The Matrix")
                            title = " ".join(word.capitalize() for word in film_slug.split("-"))
                        else:
                            # Fallback to alt text of poster image
                            title = item.find_element("css selector", "img").get_attribute("alt")
                        
                        # Remove year from title if it exists
                        if '(' in title and ')' in title and title.rstrip()[-1] == ')':
                            title = title[:title.rindex('(')].strip()
                        
                        # Try to get year from data attribute
                        try:
                            year = int(film_link.get_attribute("data-film-release-year"))
                        except (ValueError, TypeError, AttributeError):
                            year = None
                        
                        media_items.append({
                            "title": title.strip(),
                            "media_type": "movie",
                            "year": year
                        })
                        logging.info(f"Added movie: {title} ({year if year else 'year unknown'})")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse movie item: {str(e)}")
                        continue
                
                # Check for next page based on list type
                try:
                    if is_watchlist:
                        # Watchlists use "Older" button with class "next"
                        # For watchlists, we ONLY rely on the "Older" button, not item count
                        next_buttons = sb.find_elements("a.next")
                        has_next_page = False
                        next_button = None
                        
                        if next_buttons:
                            # Verify it's the "Older" button
                            for btn in next_buttons:
                                if 'Older' in btn.text or '/page/' in btn.get_attribute('href'):
                                    logging.info("Found 'Older' button, clicking to go to next page")
                                    has_next_page = True
                                    next_button = btn
                                    page += 1
                                    break
                        
                        if has_next_page and next_button:
                            # Click the "Older" button to navigate
                            try:
                                # Scroll to make the button visible
                                sb.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                sb.sleep(1)  # Wait a moment for scroll to complete
                                
                                # Click the button
                                next_button.click()
                                
                                # Wait for the page to load
                                sb.wait_for_element_present("ul.poster-list", timeout=20)
                                sb.sleep(2)  # Additional wait to ensure page loads
                                logging.info(f"Successfully navigated to watchlist page {page}")
                            except Exception as e:
                                logging.warning(f"Error clicking 'Older' button: {str(e)}")
                                # Try direct URL navigation as fallback
                                fallback_url = f"{base_url}/page/{page}"
                                logging.info(f"Falling back to direct URL navigation: {fallback_url}")
                                sb.open(fallback_url)
                                sb.wait_for_element_present("ul.poster-list", timeout=20)
                        else:
                            logging.info("No 'Older' button found, must be last page of watchlist")
                            break
                            
                    else:
                        # Regular lists use standard pagination
                        # If we found exactly 100 items, there might be more pages
                        if items_count == 100:
                            page += 1
                            logging.info(f"Found exactly 100 items, trying page {page}")
                        else:
                            logging.info(f"Found {items_count} items (< 100), must be the last page")
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
