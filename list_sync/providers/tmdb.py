"""
TMDB (The Movie Database) list provider for ListSync.
"""

import logging
import re
import requests
from typing import List, Dict, Any, Optional

from seleniumbase import SB

from . import register_provider


@register_provider("tmdb")
def fetch_tmdb_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch TMDB list using API if available, otherwise fallback to web scraping
    
    Args:
        list_id (str): TMDB list ID or URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid
    """
    # Import here to avoid circular imports
    from ..config import get_tmdb_api_key
    
    # Check if API key is available
    api_key = get_tmdb_api_key()
    
    if api_key:
        logging.info(f"Using TMDB API for list: {list_id}")
        return _fetch_tmdb_list_api(list_id, api_key)
    else:
        logging.info(f"Using web scraping fallback for TMDB list: {list_id}")
        return _fetch_tmdb_list_scraping(list_id)


def _fetch_tmdb_list_api(list_id: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch TMDB list using the official API with pagination support
    
    Args:
        list_id (str): TMDB list ID
        api_key (str): TMDB API key
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # Extract list ID from URL if needed
        if list_id.startswith(('http://', 'https://')):
            # Extract list ID from URL like https://www.themoviedb.org/list/12345
            match = re.search(r'/list/(\d+)', list_id)
            if not match:
                raise ValueError(f"Could not extract list ID from URL: {list_id}")
            list_id = match.group(1)
        
        # TMDB API endpoint for getting list details
        base_url = f"https://api.themoviedb.org/3/list/{list_id}"
        params = {
            'api_key': api_key,
            'language': 'en-US'
        }
        
        logging.info(f"Fetching TMDB list {list_id} from API")
        
        # First, get the list details to understand pagination
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        total_items = data.get('item_count', 0)
        logging.info(f"List contains {total_items} total items")
        
        # Process items from the first page
        for item in data.get('items', []):
            processed_item = _process_tmdb_api_item(item)
            if processed_item:
                media_items.append(processed_item)
        
        # Check if we need to fetch more pages
        # TMDB API returns 20 items per page by default
        items_per_page = 20
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            logging.info(f"Fetching additional pages (2/{total_pages})...")
            
            # Fetch remaining pages
            for page in range(2, total_pages + 1):
                try:
                    page_params = params.copy()
                    page_params['page'] = page
                    
                    logging.info(f"Fetching page {page}/{total_pages}")
                    response = requests.get(base_url, params=page_params, timeout=30)
                    response.raise_for_status()
                    
                    page_data = response.json()
                    
                    # Process items from this page
                    for item in page_data.get('items', []):
                        processed_item = _process_tmdb_api_item(item)
                        if processed_item:
                            media_items.append(processed_item)
                    
                    # Small delay to be respectful to the API
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logging.warning(f"Failed to fetch page {page}: {str(e)}")
                    continue
        
        logging.info(f"Successfully fetched {len(media_items)} items from TMDB API across {total_pages} pages")
        return media_items
        
    except requests.exceptions.RequestException as e:
        logging.error(f"TMDB API request failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error fetching TMDB list via API {list_id}: {str(e)}")
        raise


def _process_tmdb_api_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single item from TMDB API response
    
    Args:
        item (Dict[str, Any]): Item from TMDB API response
        
    Returns:
        Optional[Dict[str, Any]]: Processed item or None if processing failed
    """
    try:
        # Determine media type
        media_type = "movie" if item.get('media_type') == 'movie' else "tv"
        
        # Extract year from release date
        year = None
        release_date = item.get('release_date') or item.get('first_air_date')
        if release_date:
            year_match = re.search(r'(\d{4})', release_date)
            if year_match:
                year = int(year_match.group(1))
        
        processed_item = {
            "title": item.get('title') or item.get('name', ''),
            "media_type": media_type,
            "year": year,
            "tmdb_id": str(item.get('id', ''))
        }
        
        logging.debug(f"Added {media_type}: {processed_item['title']} ({year if year else 'year unknown'})")
        return processed_item
        
    except Exception as e:
        logging.warning(f"Failed to process TMDB API item: {str(e)}")
        return None


def _fetch_tmdb_list_scraping(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch TMDB list using web scraping (original implementation)
    
    Args:
        list_id (str): TMDB list ID or URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    logging.info(f"Fetching TMDB list via web scraping: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')
            else:
                # Construct URL from list ID
                url = f"https://www.themoviedb.org/list/{list_id}"
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Initial wait for page load
            sb.sleep(5)
            
            # Add some human-like scrolling behavior to avoid bot detection
            try:
                sb.execute_script("window.scrollTo(0, 300);")
                sb.sleep(1)
                sb.execute_script("window.scrollTo(0, 600);")
                sb.sleep(1)
                sb.execute_script("window.scrollTo(0, 900);")
                sb.sleep(1)
            except Exception as e:
                logging.warning(f"Could not perform scrolling: {str(e)}")
            
            # Wait for any potential captcha/anti-bot verification to load
            sb.sleep(3)
            
            # Process the list
            media_items.extend(_process_tmdb_list(sb, url))
            
            logging.info(f"Found {len(media_items)} items from TMDB list {list_id}")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching TMDB list {list_id}: {str(e)}")
        raise


def _process_tmdb_list(sb, url) -> List[Dict[str, Any]]:
    """
    Process a TMDB list page using proven selectors from testing.
    
    Args:
        sb: SeleniumBase instance
        url: URL of the list
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # Wait for list content to load
        logging.info("Waiting for list content to load...")
        
        # Use the proven selector that works
        try:
            sb.wait_for_element_present('div[class*="border-[1px]"][class*="rounded-md"]', timeout=10)
            logging.info("Found TMDB list content")
        except Exception as e:
            logging.warning(f"Could not find content with primary selector: {str(e)}")
            # Try fallback
            try:
                sb.wait_for_element_present('div[class*="table-row"]', timeout=5)
                logging.info("Found content with fallback selector")
            except Exception as e2:
                raise ValueError(f"Could not find list content on page: {str(e2)}")
        
        # Additional wait to ensure everything is loaded
        sb.sleep(3)
    
    except Exception as e:
        logging.error(f"Failed to load TMDB list page: {str(e)}")
        raise
    
    # Find all movie items using the proven selector
    items = sb.find_elements("css selector", "div[class*='border-[1px]'][class*='rounded-md']")
    logging.info(f"Found {len(items)} movie items initially")
    
    if not items:
        logging.warning("No movie items found")
        return media_items
    
    # Process all items on the current page
    for i, item in enumerate(items):
        try:
            # Extract title using proven selector
            title = ""
            title_links = item.find_elements("css selector", "a[class*='font-bold'][href*='/movie/']")
            if title_links:
                title = title_links[0].text.strip()
            
            if not title:
                logging.warning(f"Could not find title for item {i+1}, skipping")
                continue
            
            # Extract year using proven selector
            year = None
            date_spans = item.find_elements("css selector", "span[class*='whitespace-nowrap']")
            for span in date_spans:
                text = span.text.strip()
                year = _extract_year_from_text(text)
                if year:
                    break
            
            # Extract unique ID
            unique_id = _extract_unique_id(item)
            
            # Determine media type
            media_type = _determine_media_type(item, title)
            
            media_items.append({
                "title": title.strip(),
                "media_type": media_type,
                "year": year,
                "tmdb_id": unique_id
            })
            logging.info(f"Added {media_type}: {title} ({year if year else 'year unknown'}) (TMDB ID: {unique_id})")
            
        except Exception as e:
            logging.warning(f"Failed to parse TMDB item {i+1}: {str(e)}")
            continue
    
    logging.info(f"Successfully extracted {len(media_items)} items from initial page")
    
    # Handle pagination - both Load More buttons AND scroll-triggered loading
    max_pagination_attempts = 30  # Increased for scroll-based loading
    pagination_attempt = 0
    previous_item_count = len(media_items)
    no_progress_count = 0  # Track consecutive attempts with no progress
    
    logging.info(f"Starting pagination with {previous_item_count} initial items")
    
    while pagination_attempt < max_pagination_attempts and no_progress_count < 5:
        current_items = sb.find_elements("css selector", "div[class*='border-[1px]'][class*='rounded-md']")
        current_item_count = len(current_items)
        
        logging.info(f"Pagination attempt {pagination_attempt + 1}: Currently have {current_item_count} items")
        
        # First, try to scroll to trigger lazy loading
        logging.info("Scrolling to trigger lazy loading...")
        try:
            # Multiple scroll patterns to trigger different types of lazy loading
            # Pattern 1: Scroll to bottom
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sb.sleep(2)
            
            # Pattern 2: Scroll up and down to trigger intersection observers
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight - 1500);")
            sb.sleep(1)
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sb.sleep(2)
            
            # Pattern 3: Gradual scroll to trigger progressive loading
            for scroll_pos in [500, 1000, 1500, 2000, 2500, 3000]:
                sb.execute_script(f"window.scrollTo(0, {scroll_pos});")
                sb.sleep(0.5)
            
            # Pattern 4: Final scroll to bottom
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sb.sleep(2)
            
            # Check if scrolling loaded new items
            new_items = sb.find_elements("css selector", "div[class*='border-[1px]'][class*='rounded-md']")
            new_item_count = len(new_items)
            
            if new_item_count > current_item_count:
                logging.info(f"Scroll loading successful: {new_item_count} items (was {current_item_count})")
                current_item_count = new_item_count
                no_progress_count = 0  # Reset no-progress counter
            else:
                logging.info("Scroll loading didn't add new items")
                
        except Exception as e:
            logging.warning(f"Error during scroll loading: {str(e)}")
        
        # Then, look for and click Load More button if available
        load_more_buttons = sb.find_elements("css selector", "a[data-next-page]")
        
        if load_more_buttons:
            button = load_more_buttons[0]
            if button.is_displayed() and button.is_enabled():
                logging.info("Found Load More button - clicking...")
                try:
                    # Scroll to the button
                    sb.execute_script("arguments[0].scrollIntoView(true);", button)
                    sb.sleep(1)
                    
                    # Click the button
                    button.click()
                    sb.sleep(3)  # Wait for new content
                    
                    # Scroll to bottom again to trigger any additional loading
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(2)
                    
                    # Check final item count
                    final_items = sb.find_elements("css selector", "div[class*='border-[1px]'][class*='rounded-md']")
                    final_item_count = len(final_items)
                    
                    if final_item_count > current_item_count:
                        logging.info(f"Load More successful: {final_item_count} items (was {current_item_count})")
                        current_item_count = final_item_count
                        no_progress_count = 0  # Reset no-progress counter
                    else:
                        logging.info("Load More didn't add new items")
                        no_progress_count += 1
                        
                except Exception as e:
                    logging.warning(f"Error clicking Load More button: {str(e)}")
                    no_progress_count += 1
            else:
                logging.info("Load More button not available")
                no_progress_count += 1
        else:
            logging.info("No Load More button found")
            no_progress_count += 1
        
        # Check if we made progress
        if current_item_count <= previous_item_count:
            no_progress_count += 1
            logging.info(f"No progress made (still {current_item_count} items) - no progress count: {no_progress_count}")
            
            # Additional check: look for end-of-list indicators
            try:
                # Check if we're at the very bottom and no more content is loading
                page_height = sb.execute_script("return document.body.scrollHeight")
                current_scroll = sb.execute_script("return window.pageYOffset")
                
                # If we're at the bottom and no new items loaded, we might be done
                if current_scroll + 1000 >= page_height:
                    logging.info("Reached bottom of page with no new items - might be end of list")
                    
            except Exception as e:
                logging.warning(f"Error checking page position: {str(e)}")
        else:
            no_progress_count = 0  # Reset if we made progress
            logging.info(f"Progress made: {current_item_count} items (was {previous_item_count})")
        
        previous_item_count = current_item_count
        pagination_attempt += 1
    
    if no_progress_count >= 5:
        logging.info("No progress made in 5 consecutive attempts - pagination complete")
    elif pagination_attempt >= max_pagination_attempts:
        logging.warning(f"Reached maximum pagination attempts ({max_pagination_attempts}) - stopping")
    
    # After all pagination is complete, extract all items
    all_items = sb.find_elements("css selector", "div[class*='border-[1px]'][class*='rounded-md']")
    logging.info(f"Final extraction: Found {len(all_items)} total items after all pagination")
    
    # Process all items to get the complete list
    media_items = []  # Reset and re-extract everything
    for i, item in enumerate(all_items):
        try:
            # Extract title
            title = ""
            title_links = item.find_elements("css selector", "a[class*='font-bold'][href*='/movie/']")
            if title_links:
                title = title_links[0].text.strip()
            
            if not title:
                continue
            
            # Extract year
            year = None
            date_spans = item.find_elements("css selector", "span[class*='whitespace-nowrap']")
            for span in date_spans:
                text = span.text.strip()
                year = _extract_year_from_text(text)
                if year:
                    break
            
            # Extract unique ID
            unique_id = _extract_unique_id(item)
            
            # Determine media type
            media_type = _determine_media_type(item, title)
            
            media_items.append({
                "title": title.strip(),
                "media_type": media_type,
                "year": year,
                "tmdb_id": unique_id
            })
            
        except Exception as e:
            logging.warning(f"Failed to parse TMDB item {i+1} after pagination: {str(e)}")
            continue
    
    logging.info(f"Successfully extracted {len(media_items)} total items after all pagination")
    
    return media_items


def _extract_title(item) -> str:
    """Extract title from list item."""
    title_selectors = [
        'a[class*="font-bold"][href*="/movie/"]',  # TMDB specific bold movie links
        'a[href*="/movie/"]',  # Any movie link
        'a[href*="/tv/"]',  # Any TV link
        'a[class*="font-bold"]'  # Any bold link
    ]
    
    for selector in title_selectors:
        try:
            elements = item.find_elements("css selector", selector)
            for elem in elements:
                if elem.text.strip():
                    return elem.text.strip()
        except Exception:
            pass
    
    # Fallback: get first non-empty text
    try:
        text = item.text.strip()
        if text:
            return text.split('\n')[0]
    except Exception:
        pass
    
    return ""


def _extract_year(item) -> int:
    """Extract year from list item."""
    # Look for date elements in TMDB format
    date_selectors = [
        'span[class*="whitespace-nowrap"]',  # Date spans
        'div[class*="date-tile"]',  # Date tiles
        'span[class*="bg-date-tile"]'  # Date tile spans
    ]
    
    for selector in date_selectors:
        try:
            elements = item.find_elements("css selector", selector)
            for elem in elements:
                text = elem.text.strip()
                year = _extract_year_from_text(text)
                if year:
                    return year
        except Exception:
            pass
    
    # Fallback: search in all text
    try:
        text = item.text
        year = _extract_year_from_text(text)
        if year:
            return year
    except Exception:
        pass
    
    return None


def _extract_year_from_text(text: str) -> int:
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


def _extract_unique_id(item) -> str:
    """Extract unique ID from list item."""
    try:
        links = item.find_elements("css selector", "a")
        for link in links:
            href = link.get_attribute("href")
            if href:
                # Look for TMDB patterns
                if '/movie/' in href:
                    # TMDB movie pattern: /movie/19995-avatar -> 19995
                    id_match = re.search(r'/movie/(\d+)(?:-[^/]+)?', href)
                    if id_match:
                        return id_match.group(1)
                elif '/tv/' in href:
                    # TMDB TV pattern: /tv/12345-show -> 12345
                    id_match = re.search(r'/tv/(\d+)(?:-[^/]+)?', href)
                    if id_match:
                        return id_match.group(1)
    except Exception:
        pass
    
    return None


def _determine_media_type(item, title: str) -> str:
    """Determine if item is movie or TV show."""
    # Default to movie
    media_type = "movie"
    
    # Look for TV indicators in title, classes, or other elements
    try:
        text = item.text.lower()
        if any(keyword in text for keyword in ['tv', 'series', 'season', 'episode', 'show']):
            media_type = "tv"
    except Exception:
        pass
    
    return media_type


