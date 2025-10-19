"""
Simkl list provider for ListSync.
"""

import logging
import re
from typing import List, Dict, Any

from seleniumbase import SB

from . import register_provider


@register_provider("simkl")
def fetch_simkl_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch Simkl list using Selenium with infinite scroll
    
    Args:
        list_id (str): Simkl list ID or URL
        
    Returns:
        List[Dict[str, Any]]: List of media items
        
    Raises:
        ValueError: If list ID format is invalid
    """
    media_items = []
    logging.info(f"Fetching Simkl list: {list_id}")
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')
            else:
                # Construct URL from list ID
                url = f"https://simkl.com/5/list/{list_id}"
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Initial wait for page load
            sb.sleep(5)
            
            # Continuous scrolling until pagination appears
            logging.info("Starting continuous scroll to trigger pagination...")
            media_items.extend(_process_simkl_list_with_continuous_scroll(sb, url))
            
            logging.info(f"Found {len(media_items)} items from Simkl list {list_id}")
            return media_items
        
    except Exception as e:
        logging.error(f"Error fetching Simkl list {list_id}: {str(e)}")
        raise


def _process_simkl_list_with_continuous_scroll(sb, url) -> List[Dict[str, Any]]:
    """
    Process a Simkl list with continuous scrolling until pagination appears.
    
    Args:
        sb: SeleniumBase instance
        url: URL of the list
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # Wait for initial content to load
        logging.info("Waiting for initial content to load...")
        
        try:
            # Wait for either movies or TV shows content
            sb.wait_for_element_present('a.SimklItem[class*="type-"]', timeout=10)
            logging.info("Found initial Simkl content")
        except Exception as e:
            logging.warning(f"Could not find initial content: {str(e)}")
            return media_items
        
        # Initial scroll to load more content
        logging.info("Starting initial scroll...")
        for scroll_position in [300, 600, 900, 1200, 1500]:
            sb.execute_script(f"window.scrollTo(0, {scroll_position});")
            sb.sleep(1)
        
        sb.sleep(2)
        
        # Continuous scrolling until pagination appears
        logging.info("Starting continuous scroll to trigger pagination...")
        scroll_position = 1800
        max_scrolls = 20  # Prevent infinite scrolling
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            # Scroll down
            sb.execute_script(f"window.scrollTo(0, {scroll_position});")
            sb.sleep(2)
            
            # Check if pagination elements have appeared
            try:
                # Look for progress element
                progress_elements = sb.find_elements("css selector", "pages-progress")
                if progress_elements:
                    progress_element = progress_elements[0]
                    total_items = progress_element.get_attribute('data-total')
                    if total_items:
                        logging.info(f"Found progress element showing {total_items} total items")
                        break
                
                # Look for show more button
                show_more_elements = sb.find_elements("css selector", "page-more")
                if show_more_elements and show_more_elements[0].is_displayed():
                    logging.info("Found 'Show More' button - pagination is ready")
                    break
                    
            except Exception:
                pass
            
            # Check if we've reached the end (no more content to load)
            current_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
            if len(current_items) > 0:
                # Check if we're at the bottom
                page_height = sb.execute_script("return document.body.scrollHeight")
                current_scroll = sb.execute_script("return window.pageYOffset")
                if current_scroll + 1000 >= page_height:
                    logging.info("Reached bottom of page - no more content to load")
                    break
            
            scroll_position += 500
            scroll_count += 1
            logging.info(f"Scroll attempt {scroll_count}/{max_scrolls}, position: {scroll_position}")
        
        # After continuous scrolling, extract all items
        logging.info("Continuous scrolling complete, extracting all items...")
        media_items.extend(_extract_all_simkl_items(sb))
        
    except Exception as e:
        logging.error(f"Error in continuous scroll process: {str(e)}")
        # Fallback to basic processing
        try:
            media_items.extend(_process_simkl_list(sb, url))
        except Exception as e2:
            logging.error(f"Fallback processing also failed: {str(e2)}")
    
    return media_items


def _extract_all_simkl_items(sb) -> List[Dict[str, Any]]:
    """
    Extract all Simkl items after continuous scrolling, handling pagination.
    
    Args:
        sb: SeleniumBase instance
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    try:
        # Wait for list content to load
        logging.info("Waiting for list content to load...")
        
        try:
            sb.wait_for_element_present('a.SimklItem[class*="type-"]', timeout=10)
            logging.info("Found Simkl list content")
        except Exception as e:
            logging.warning(f"Could not find content with primary selector: {str(e)}")
            return media_items
        
        # Additional wait to ensure everything is loaded
        sb.sleep(3)
        
        # Continuous pagination loop - keep clicking until we get all items
        max_pagination_attempts = 50  # Prevent infinite loops (increased for big lists)
        pagination_attempt = 0
        
        show_more_selectors = [
            "page-more",
            ".pageMore",
            "[class*='pageMore']",
            "button[class*='more']",
            "a[class*='more']",
            "pages-more",
            ".pages-more"
        ]

        while pagination_attempt < max_pagination_attempts:
            # Check current progress
            current_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
            logging.info(f"Current items: {len(current_items)}")
            
            # Check if we have the total number of items
            try:
                progress_element = sb.find_element("css selector", "pages-progress")
                total_items = progress_element.get_attribute('data-total')
                if total_items and len(current_items) >= int(total_items):
                    logging.info(f"Reached total items ({total_items}) - stopping pagination")
                    break
            except Exception:
                pass
            
            # Look for "Show More" button
            show_more_button = None
            for selector in show_more_selectors:
                try:
                    buttons = sb.find_elements("css selector", selector)
                    logging.info(f"Checking selector '{selector}': found {len(buttons)} elements")
                    for i, button in enumerate(buttons):
                        try:
                            is_displayed = button.is_displayed()
                            is_enabled = button.is_enabled()
                            button_text = button.text.strip().lower()
                            button_classes = button.get_attribute('class')
                            
                            logging.info(f"  Button {i+1}: displayed={is_displayed}, enabled={is_enabled}, text='{button_text}', classes='{button_classes}'")
                            
                            if is_enabled:  # Removed displayed requirement - button exists but may not be visible
                                # Check if it's a "show more" type button
                                if any(keyword in button_text for keyword in ['more', 'show', 'load', 'next']) or 'more' in button_classes.lower():
                                    show_more_button = button
                                    logging.info(f"Found 'Show More' button with selector: {selector} (displayed={is_displayed})")
                                    break
                        except Exception as e:
                            logging.warning(f"Error checking button {i+1}: {str(e)}")
                            continue
                    if show_more_button:
                        break
                except Exception as e:
                    logging.warning(f"Error with selector '{selector}': {str(e)}")
                    continue
            
            if not show_more_button:
                logging.info("No more 'Show More' buttons found - pagination complete")
                break
            
            # Click the "Show More" button
            logging.info(f"Clicking 'Show More' button (attempt {pagination_attempt + 1})...")
            # Scroll to make button visible
            sb.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            sb.sleep(1)
            
            # Try JavaScript click first (works even if button not displayed)
            try:
                sb.execute_script("arguments[0].click();", show_more_button)
                logging.info("Successfully clicked button with JavaScript")
            except Exception as e:
                logging.warning(f"JavaScript click failed: {str(e)}, trying regular click")
                try:
                    show_more_button.click()
                    logging.info("Successfully clicked button with regular click")
                except Exception as e2:
                    logging.error(f"Regular click also failed: {str(e2)}")
                    return media_items
            
            # Wait for new content to load
            sb.sleep(3)
            
            # Check if new items were loaded
            new_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
            if len(new_items) <= len(current_items):
                logging.info("No new items loaded - pagination may be complete")
                break
            
            pagination_attempt += 1
            logging.info(f"Pagination attempt {pagination_attempt}/{max_pagination_attempts} complete")
        
        # Final extraction of all items
        all_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
        logging.info(f"Final extraction: Found {len(all_items)} total items")
        
        # Process all items to get the complete list
        for i, item in enumerate(all_items):
            try:
                # Extract title from CSS custom property
                title = _extract_title_from_css(item)
                
                if not title:
                    continue
                
                # Extract year from CSS custom property
                year = _extract_year_from_css(item)
                
                # Skip unreleased movies (no year)
                if not year:
                    logging.info(f"Skipping unreleased movie: {title}")
                    continue
                
                # Extract Simkl ID
                simkl_id = item.get_attribute('data-id')
                
                # Extract IMDB rating from CSS custom property
                imdb_rating = _extract_imdb_rating_from_css(item)
                
                # Determine media type
                media_type = _determine_media_type(item)
                
                media_items.append({
                    "title": title.strip(),
                    "media_type": media_type,
                    "year": year,
                    "simkl_id": simkl_id,
                    "imdb_rating": imdb_rating
                })
                
            except Exception as e:
                logging.warning(f"Failed to parse Simkl item {i+1}: {str(e)}")
                continue
        
        logging.info(f"Successfully extracted {len(media_items)} total items after all pagination")
        
    except Exception as e:
        logging.error(f"Error extracting all Simkl items: {str(e)}")
    
    return media_items


def _process_simkl_list_with_pagination(sb, url) -> List[Dict[str, Any]]:
    """
    Process a Simkl list page with pagination handling.
    
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
            sb.wait_for_element_present('a.SimklItem[class*="type-"]', timeout=10)
            logging.info("Found Simkl list content")
        except Exception as e:
            logging.warning(f"Could not find content with primary selector: {str(e)}")
            # Try fallback
            try:
                sb.wait_for_element_present('a[class*="SimklItem"]', timeout=5)
                logging.info("Found content with fallback selector")
            except Exception as e2:
                raise ValueError(f"Could not find list content on page: {str(e2)}")
        
        # Additional wait to ensure everything is loaded
        sb.sleep(3)
    
    except Exception as e:
        logging.error(f"Failed to load Simkl list page: {str(e)}")
        raise
    
    # Process all items on current page
    items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
    logging.info(f"Found {len(items)} movie items on current page")
    
    if not items:
        logging.warning("No movie items found")
        return media_items
    
    # Process all items
    for i, item in enumerate(items):
        try:
            # Extract title from CSS custom property (most reliable method)
            title = _extract_title_from_css(item)
            
            if not title:
                logging.warning(f"Could not find title for item {i+1}, skipping")
                continue
            
            # Extract year from CSS custom property
            year = _extract_year_from_css(item)
            
            # Extract Simkl ID
            simkl_id = item.get_attribute('data-id')
            
            # Extract IMDB rating from CSS custom property
            imdb_rating = _extract_imdb_rating_from_css(item)
            
            # Determine media type
            media_type = _determine_media_type(item)
            
            media_items.append({
                "title": title.strip(),
                "media_type": media_type,
                "year": year,
                "simkl_id": simkl_id,
                "imdb_rating": imdb_rating
            })
            logging.info(f"Added {media_type}: {title} ({year if year else 'year unknown'}) (Simkl ID: {simkl_id})")
            
        except Exception as e:
            logging.warning(f"Failed to parse Simkl item {i+1}: {str(e)}")
            continue
    
    logging.info(f"Successfully extracted {len(media_items)} items from current page")
    
    # Check for progress information first
    try:
        progress_element = sb.find_element("css selector", "pages-progress")
        if progress_element:
            total_items = progress_element.get_attribute('data-total')
            if total_items:
                logging.info(f"Progress shows {total_items} total items available")
    except Exception:
        pass
    
    # Check for "Show More Results" button and handle pagination
    try:
        show_more_selectors = [
            "page-more",
            ".pageMore",
            "[class*='pageMore']",
            "button[class*='more']",
            "a[class*='more']",
            "pages-more",
            ".pages-more"
        ]
        
        show_more_button = None
        for selector in show_more_selectors:
            try:
                buttons = sb.find_elements("css selector", selector)
                logging.info(f"Checking selector '{selector}': found {len(buttons)} elements")
                for i, button in enumerate(buttons):
                    try:
                        is_displayed = button.is_displayed()
                        is_enabled = button.is_enabled()
                        button_text = button.text.strip().lower()
                        button_classes = button.get_attribute('class')
                        
                        logging.info(f"  Button {i+1}: displayed={is_displayed}, enabled={is_enabled}, text='{button_text}', classes='{button_classes}'")
                        
                        if is_enabled:  # Remove displayed requirement - button exists but may not be visible
                            # Check if it's a "show more" type button
                            if any(keyword in button_text for keyword in ['more', 'show', 'load', 'next']) or 'more' in button_classes.lower():
                                show_more_button = button
                                logging.info(f"Found 'Show More' button with selector: {selector} (displayed={is_displayed})")
                                break
                    except Exception as e:
                        logging.warning(f"Error checking button {i+1}: {str(e)}")
                        continue
                if show_more_button:
                    break
            except Exception as e:
                logging.warning(f"Error with selector '{selector}': {str(e)}")
                continue
        
        # Continuous pagination loop - keep clicking until we get all items
        max_pagination_attempts = 50  # Prevent infinite loops (increased for big lists)
        pagination_attempt = 0
        
        while pagination_attempt < max_pagination_attempts:
            # Check current progress
            current_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
            logging.info(f"Current items: {len(current_items)}")
            
            # Check if we have the total number of items
            try:
                progress_element = sb.find_element("css selector", "pages-progress")
                total_items = progress_element.get_attribute('data-total')
                if total_items and len(current_items) >= int(total_items):
                    logging.info(f"Reached total items ({total_items}) - stopping pagination")
                    break
            except Exception:
                pass
            
            # Look for "Show More" button
            show_more_button = None
            for selector in show_more_selectors:
                try:
                    buttons = sb.find_elements("css selector", selector)
                    for button in buttons:
                        if button.is_enabled() and ('more' in button.get_attribute('class').lower() or 'more' in button.text.lower()):
                            show_more_button = button
                            break
                    if show_more_button:
                        break
                except Exception:
                    continue
            
            if not show_more_button:
                logging.info("No more 'Show More' buttons found - pagination complete")
                break
            
            # Click the "Show More" button
            logging.info(f"Clicking 'Show More' button (attempt {pagination_attempt + 1})...")
            try:
                sb.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
                sb.sleep(1)
                sb.execute_script("arguments[0].click();", show_more_button)
                logging.info("Successfully clicked 'Show More' button")
            except Exception as e:
                logging.warning(f"Failed to click 'Show More' button: {str(e)}")
                break
            
            # Wait for new content to load
            sb.sleep(3)
            
            # Check if new items were loaded
            new_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
            if len(new_items) <= len(current_items):
                logging.info("No new items loaded - pagination may be complete")
                break
            
            pagination_attempt += 1
            logging.info(f"Pagination attempt {pagination_attempt}/{max_pagination_attempts} complete")
        
        # Final extraction of all items
        all_items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
        logging.info(f"Final extraction: Found {len(all_items)} total items")
        
        # Process all items to get the complete list
        media_items = []  # Reset and re-extract everything
        for i, item in enumerate(all_items):
            try:
                # Extract title from CSS custom property
                title = _extract_title_from_css(item)
                
                if not title:
                    continue
                
                # Extract year from CSS custom property
                year = _extract_year_from_css(item)
                
                # Skip unreleased movies (no year)
                if not year:
                    logging.info(f"Skipping unreleased movie: {title}")
                    continue
                
                # Extract Simkl ID
                simkl_id = item.get_attribute('data-id')
                
                # Extract IMDB rating from CSS custom property
                imdb_rating = _extract_imdb_rating_from_css(item)
                
                # Determine media type
                media_type = _determine_media_type(item)
                
                media_items.append({
                    "title": title.strip(),
                    "media_type": media_type,
                    "year": year,
                    "simkl_id": simkl_id,
                    "imdb_rating": imdb_rating
                })
                
            except Exception as e:
                logging.warning(f"Failed to parse Simkl item {i+1}: {str(e)}")
                continue
        
        logging.info(f"Successfully extracted {len(media_items)} total items after all pagination")
    
    except Exception as e:
        logging.warning(f"Error handling pagination: {str(e)}")
        # Continue with current items if pagination fails
    
    return media_items


def _process_simkl_list(sb, url) -> List[Dict[str, Any]]:
    """
    Process a Simkl list page using proven selectors from testing.
    
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
            sb.wait_for_element_present('a.SimklItem[class*="type-"]', timeout=10)
            logging.info("Found Simkl list content")
        except Exception as e:
            logging.warning(f"Could not find content with primary selector: {str(e)}")
            # Try fallback
            try:
                sb.wait_for_element_present('a[class*="SimklItem"]', timeout=5)
                logging.info("Found content with fallback selector")
            except Exception as e2:
                raise ValueError(f"Could not find list content on page: {str(e2)}")
        
        # Additional wait to ensure everything is loaded
        sb.sleep(3)
    
    except Exception as e:
        logging.error(f"Failed to load Simkl list page: {str(e)}")
        raise
    
    # Find all movie items using the proven selector
    items = sb.find_elements("css selector", 'a.SimklItem[class*="type-"]')
    logging.info(f"Found {len(items)} movie items")
    
    if not items:
        logging.warning("No movie items found")
        return media_items
    
    # Process all items
    for i, item in enumerate(items):
        try:
            # Extract title from CSS custom property (most reliable method)
            title = _extract_title_from_css(item)
            
            if not title:
                logging.warning(f"Could not find title for item {i+1}, skipping")
                continue
            
            # Extract year from CSS custom property
            year = _extract_year_from_css(item)
            
            # Extract Simkl ID
            simkl_id = item.get_attribute('data-id')
            
            # Extract IMDB rating from CSS custom property
            imdb_rating = _extract_imdb_rating_from_css(item)
            
            # Determine media type
            media_type = _determine_media_type(item)
            
            media_items.append({
                "title": title.strip(),
                "media_type": media_type,
                "year": year,
                "simkl_id": simkl_id,
                "imdb_rating": imdb_rating
            })
            logging.info(f"Added {media_type}: {title} ({year if year else 'year unknown'}) (Simkl ID: {simkl_id})")
            
        except Exception as e:
            logging.warning(f"Failed to parse Simkl item {i+1}: {str(e)}")
            continue
    
    logging.info(f"Successfully extracted {len(media_items)} items from Simkl list")
    
    return media_items


def _extract_title_from_css(item) -> str:
    """Extract title from CSS custom property."""
    try:
        style = item.get_attribute('style')
        if style and '--title:' in style:
            # More permissive regex to extract everything after --title:
            match = re.search(r'--title:\s*[\'"]?([^;]+)[\'"]?', style)
            if match:
                title = match.group(1).strip()
                # Clean up any backslashes, quotes, and other problematic characters
                title = title.replace('\\', '').replace('"', '').replace("'", '').strip()
                # If title is just "Marvel" or similar, it might be incomplete
                if len(title) < 3 or title in ['Marvel', 'Marvels']:
                    return ""
                return title
    except Exception:
        pass
    
    # Fallback: try <itemtitle> tag
    try:
        title_elements = item.find_elements("css selector", "itemtitle")
        if title_elements:
            return title_elements[0].text.strip()
    except Exception:
        pass
    
    # Fallback: try href attribute
    try:
        href = item.get_attribute('href')
        if href and '/movies/' in href:
            title_match = re.search(r'/movies/\d+/([^/]+)$', href)
            if title_match:
                return title_match.group(1).replace('-', ' ').title()
    except Exception:
        pass
    
    return ""


def _extract_year_from_css(item) -> int:
    """Extract year from CSS custom property."""
    try:
        style = item.get_attribute('style')
        if style and '--year-start:' in style:
            match = re.search(r'--year-start:\s*[\'"]?(\d{4})[\'"]?', style)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2030:
                    return year
    except Exception:
        pass
    
    return None


def _extract_imdb_rating_from_css(item) -> float:
    """Extract IMDB rating from CSS custom property."""
    try:
        style = item.get_attribute('style')
        if style and '--rating-imdb:' in style:
            match = re.search(r'--rating-imdb:\s*[\'"]?([\d.]+)[\'"]?', style)
            if match:
                return float(match.group(1))
    except Exception:
        pass
    
    return None


def _determine_media_type(item) -> str:
    """Determine media type from CSS class or href."""
    try:
        class_attr = item.get_attribute('class')
        if 'type-tv' in class_attr:
            return "tv"
        elif 'type-movie' in class_attr:
            return "movie"
        
        # Fallback: determine from href
        href = item.get_attribute('href')
        if href and '/tv/' in href:
            return "tv"
        elif href and '/movies/' in href:
            return "movie"
    except Exception:
        pass
    
    return "movie"  # Default fallback
