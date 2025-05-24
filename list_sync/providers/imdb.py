"""
IMDb list provider for ListSync.
"""

import logging
import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from seleniumbase import SB

from . import register_provider


@register_provider("imdb")
def fetch_imdb_list(list_id: str) -> list[dict[str, Any]]:
    """
    Fetch IMDb list using Selenium with pagination

    Args:
        list_id (str): IMDb list ID, chart name, or URL

    Returns:
        list[dict[str, Any]]: List of media items

    Raises:
        ValueError: If list ID format is invalid
    """
    media_items = []
    logging.info("Fetching IMDb list: %s", list_id)

    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(("http://", "https://")):
                url = list_id.rstrip("/")  # Use the provided URL directly
                if "/chart/" in url:
                    is_chart = True
                elif "/list/" in url or "/user/" in url:
                    is_chart = False
                else:
                    msg = "Invalid IMDb URL format"
                    raise ValueError(msg)
            # Existing logic for list IDs
            elif list_id in ["top", "boxoffice", "moviemeter", "tvmeter"]:
                url = f"https://www.imdb.com/chart/{list_id}"
                is_chart = True
            elif list_id.startswith("ls"):
                url = f"https://www.imdb.com/list/{list_id}"
                is_chart = False
            elif list_id.startswith("ur"):
                url = f"https://www.imdb.com/user/{list_id}/watchlist"
                is_chart = False
            else:
                msg = "Invalid IMDb list ID format"
                raise ValueError(msg)

            logging.info("Attempting to load URL: %s", url)
            sb.open(url)

            # Common wait logic for all IMDb pages (both lists and charts)
            logging.info("Attempting to load IMDb page: %s", url)
            sb.open(url)

            # Initial wait for page load
            sb.sleep(5)  # Longer initial wait to ensure page starts loading

            # Add some human-like scrolling behavior to avoid bot detection
            try:
                sb.execute_script("window.scrollTo(0, 300);")
                sb.sleep(1)
                sb.execute_script("window.scrollTo(0, 600);")
                sb.sleep(1)
            except WebDriverException as e:
                logging.warning("Could not perform scrolling: %s", e)

            # Wait for any potential captcha/anti-bot verification to load
            sb.sleep(3)

            if is_chart:
                # Process chart page (IMDb top charts)
                media_items.extend(_process_imdb_chart(sb))
            else:
                # Process regular list page
                media_items.extend(_process_imdb_list(sb, url))

            logging.info("Found %d items from IMDb list %s", len(media_items), list_id)
            return media_items

    except (TimeoutException, NoSuchElementException, WebDriverException):
        logging.exception("Error fetching IMDb list %s", list_id)
        raise


def _process_imdb_chart(sb) -> list[dict[str, Any]]:
    """
    Process an IMDb chart page.

    Args:
        sb: SeleniumBase instance

    Returns:
        list[dict[str, Any]]: List of media items
    """
    media_items = []
    chart_found = False

    # Try different approaches to find chart content
    # First, try direct data-testid selectors
    data_testid_selectors = [
        '[data-testid="chart-layout-parent"]',
        '[data-testid="chart-layout-main-column"]',
        '[data-testid="chart-layout-total-items"]',
    ]

    for selector in data_testid_selectors:
        try:
            logging.info("Trying to find chart with data-testid selector: %s", selector)
            # Use a longer timeout for charts
            sb.wait_for_element_present(selector, timeout=10)
            chart_found = True
            logging.info("Chart parent found with selector: %s", selector)
            # Add extra wait after finding the element to ensure it's fully loaded
            sb.sleep(2)
            break
        except (TimeoutException, NoSuchElementException) as e:
            logging.warning("Could not find chart with data-testid selector %s: %s", selector, e)

    # If not found, try different class-based selectors for the list itself
    if not chart_found:
        class_selectors = [
            "ul.ipc-metadata-list.compact-list-view",
            "ul.ipc-metadata-list.detailed-list-view",
            ".ipc-metadata-list.ipc-metadata-list--dividers-between",
            "ul.ipc-metadata-list",  # Most generic one
        ]

        for selector in class_selectors:
            try:
                logging.info("Trying to find chart with class selector: %s", selector)
                # Use a longer timeout for charts
                sb.wait_for_element_present(selector, timeout=10)
                chart_found = True
                logging.info("Chart found with selector: %s", selector)
                # Add extra wait after finding the element
                sb.sleep(2)
                break
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning("Could not find chart with class selector %s: %s", selector, e)

    if not chart_found:
        # Try a more aggressive approach with longer waits and more scrolling
        logging.warning("Could not find chart with standard selectors, trying more aggressive approach")
        sb.sleep(8)  # Wait longer for full page load

        # Add more extensive human-like behavior
        sb.execute_script("window.scrollTo(0, 300);")
        sb.sleep(2)
        sb.execute_script("window.scrollTo(0, 600);")
        sb.sleep(2)
        sb.execute_script("window.scrollTo(0, 900);")
        sb.sleep(2)
        sb.execute_script("window.scrollTo(0, 1200);")
        sb.sleep(2)
        # Scroll back up a bit to simulate natural browsing
        sb.execute_script("window.scrollTo(0, 800);")
        sb.sleep(3)

        # Try a very generic selector that should match any list with a much longer timeout
        try:
            sb.wait_for_element_present("ul", timeout=15)
            # If we find any ul, let's look for list items inside it
            uls = sb.find_elements("ul")
            for ul in uls:
                try:
                    items = ul.find_elements("css selector", "li")
                    if len(items) > 5:  # If we find a list with several items, it's likely our chart
                        logging.info("Found a ul with %d items, likely our chart", len(items))
                        chart_found = True
                        break
                except (NoSuchElementException, WebDriverException):
                    pass
        except (TimeoutException, NoSuchElementException):
            logging.exception("Could not find any ul elements after scrolling")

    if not chart_found:
        msg = "Could not find chart content on IMDb page after multiple attempts"
        raise ValueError(msg)

    # Get total number of items if possible
    try:
        total_elements = sb.find_elements('[data-testid="chart-layout-total-items"]')
        if total_elements:
            total_text = total_elements[0].text
            total_match = re.search(r"(\d+)\s+Titles?", total_text)
            if total_match:
                total_items = int(total_match.group(1))
                logging.info("Total items in chart: %d", total_items)
        else:
            total_items = None
    except (NoSuchElementException, WebDriverException) as e:
        logging.warning("Could not determine total items: %s", e)
        total_items = None

    # Process items in the chart - try multiple selectors for items
    items = []

    # Try different selectors for the chart items, starting with the most specific
    item_selectors = [
        "li.ipc-metadata-list-summary-item",  # Most specific for compact view
        ".ipc-metadata-list-summary-item",    # Alternative for compact view
        ".cli-parent",                        # From the example
        ".ipc-metadata-list-item",             # For other views
    ]

    for selector in item_selectors:
        try:
            logging.info("Trying to find list items with selector: %s", selector)
            items = sb.find_elements(selector)
            if items and len(items) > 0:
                logging.info("Found %d items using selector: %s", len(items), selector)
                break
        except (NoSuchElementException, WebDriverException) as e:
            logging.warning("Could not find items with selector %s: %s", selector, e)

    if not items or len(items) == 0:
        # Last resort: try to find any list items on the page
        try:
            items = sb.find_elements("li")
            logging.warning("Using generic li selector as fallback, found %d items", len(items))
        except (NoSuchElementException, WebDriverException):
            logging.exception("Could not find any list items on the page")
            msg = "Could not find any list items in the chart"
            raise ValueError(msg)

    logging.info("Found %d items in chart", len(items))

    for item in items:
        try:
            # Get title element - try multiple selectors
            full_title = ""

            title_selectors = [
                ".ipc-title__text",
                "h3.ipc-title__text",
                ".cli-title h3",
                "a.ipc-title-link-wrapper",
            ]

            for selector in title_selectors:
                try:
                    title_elements = item.find_elements("css selector", selector)
                    if title_elements:
                        for element in title_elements:
                            element_text = element.text
                            if element_text and len(element_text) > 0:
                                full_title = element_text
                                logging.info("Found title using selector: %s", selector)
                                break
                        if full_title:
                            break
                except (NoSuchElementException, WebDriverException):
                    pass

            if not full_title:
                # Last resort: try to get any text from the item
                try:
                    item_text = item.text
                    text_lines = item_text.split("\n")
                    for line in text_lines:
                        if line and len(line) > 2 and not line.isdigit() and not re.match(r"^\d+\.$", line):
                            full_title = line
                            logging.warning("Using fallback method for title: %s", full_title)
                            break
                except (NoSuchElementException, WebDriverException):
                    pass

            if not full_title:
                logging.warning("Could not find title for item, skipping")
                continue

            # Remove ranking number if present (e.g., "1. The Shawshank Redemption" -> "The Shawshank Redemption")
            title = re.sub(r"^\d+\.\s*", "", full_title)

            # Get year from metadata with various selectors
            year = None
            metadata_text = ""

            metadata_selectors = [
                ".cli-title-metadata",
                ".cli-title-metadata-item",
                ".sc-44e0e03-6",
                ".sc-44e0e03-7",
            ]

            for selector in metadata_selectors:
                try:
                    metadata_elements = item.find_elements("css selector", selector)
                    if metadata_elements:
                        for element in metadata_elements:
                            element_text = element.text
                            metadata_text += " " + element_text
                            # Try to extract year directly from this element
                            year_match = re.search(r"(\d{4})", element_text)
                            if year_match:
                                year = int(year_match.group(1))
                                break
                        if year:
                            break
                except (NoSuchElementException, WebDriverException):
                    pass

            if not year and metadata_text:
                # Try to extract year from concatenated metadata
                year_match = re.search(r"(\d{4})", metadata_text)
                if year_match:
                    year = int(year_match.group(1))

            # If still no year, try to extract from the item's entire text
            if not year:
                try:
                    item_text = item.text
                    year_match = re.search(r"(\d{4})", item_text)
                    if year_match:
                        year = int(year_match.group(1))
                except (NoSuchElementException, WebDriverException):
                    pass

            # Get IMDB ID from the title link - try different approaches
            imdb_id = None
            link_selectors = [
                "a.ipc-title-link-wrapper",
                "a[href*='/title/']",
                "a",  # Most generic selector
            ]

            for selector in link_selectors:
                try:
                    links = item.find_elements("css selector", selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "/title/" in href:
                            # Extract IMDb ID from URL
                            imdb_match = re.search(r"/title/(tt\d+)", href)
                            if imdb_match:
                                imdb_id = imdb_match.group(1)
                                break
                    if imdb_id:
                        break
                except (NoSuchElementException, WebDriverException):
                    pass

            if not imdb_id:
                logging.warning("Could not find IMDb ID for %s, skipping", title)
                continue

            # For charts, all items are movies unless explicitly marked as TV
            media_type = "movie"
            if metadata_text and ("TV" in metadata_text or "Series" in metadata_text):
                media_type = "tv"

            media_items.append({
                "title": title.strip(),
                "imdb_id": imdb_id,
                "media_type": media_type,
                "year": year,
            })
            logging.info("Added %s: %s (%s) (IMDB ID: %s)", media_type, title, year, imdb_id)

        except (NoSuchElementException, WebDriverException) as e:
            logging.warning("Failed to parse IMDb chart item: %s", e)
            continue

    return media_items


def _process_imdb_list(sb, url) -> list[dict[str, Any]]:
    """
    Process a regular IMDb list page.

    Args:
        sb: SeleniumBase instance
        url: URL of the list

    Returns:
        list[dict[str, Any]]: List of media items
    """
    media_items = []

    try:
        # Wait for list content to load with a more resilient approach
        logging.info("Waiting for list content to load...")

        # Try multiple selector approaches in sequence with longer timeouts
        content_found = False

        # First try the data-testid attribute
        try:
            logging.info("Looking for content by data-testid attribute...")
            sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
            content_found = True
            logging.info("Found content by data-testid attribute")
            # Add extra wait after finding the element
            sb.sleep(2)
        except (TimeoutException, NoSuchElementException) as e:
            logging.warning("Could not find content by data-testid: %s", e)

        # If that fails, try looking for the list element directly
        if not content_found:
            try:
                logging.info("Looking for list element directly...")
                sb.wait_for_element_present("ul.ipc-metadata-list", timeout=10)
                content_found = True
                logging.info("Found list element directly")
                # Add extra wait after finding the element
                sb.sleep(2)
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning("Could not find list element: %s", e)

        # If that also fails, try looking for list items
        if not content_found:
            try:
                logging.info("Looking for list items...")
                sb.wait_for_element_present("li.ipc-metadata-list-summary-item", timeout=10)
                content_found = True
                logging.info("Found list items")
                # Add extra wait after finding the element
                sb.sleep(2)
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning("Could not find list items: %s", e)

        # If everything fails, try a more aggressive approach with longer waits and scrolling
        if not content_found:
            logging.warning("Could not find list content, attempting more aggressive approach...")
            # Scroll more and wait longer
            sb.sleep(8)

            # Add more extensive human-like behavior
            sb.execute_script("window.scrollTo(0, 300);")
            sb.sleep(2)
            sb.execute_script("window.scrollTo(0, 600);")
            sb.sleep(2)
            sb.execute_script("window.scrollTo(0, 900);")
            sb.sleep(2)
            sb.execute_script("window.scrollTo(0, 1200);")
            sb.sleep(2)
            # Scroll back up a bit to simulate natural browsing
            sb.execute_script("window.scrollTo(0, 800);")
            sb.sleep(3)

            # Reload the page to handle potential temporary glitches
            sb.open(url)
            sb.sleep(10)  # Wait longer after reload

            # Try once more with very generic selectors and longer timeouts
            try:
                # Try to find any ul element with items
                sb.wait_for_element_present("ul", timeout=15)
                uls = sb.find_elements("ul")
                for ul in uls:
                    try:
                        items = ul.find_elements("css selector", "li")
                        if len(items) > 5:  # If we find a list with several items, it's likely our list
                            logging.info("Found a ul with %d items, likely our list content", len(items))
                            content_found = True
                            break
                    except (NoSuchElementException, WebDriverException):
                        pass

                if not content_found:
                    msg = "Could not find list content on IMDb page after multiple attempts"
                    raise ValueError(msg)
            except (TimeoutException, NoSuchElementException):
                logging.exception("Could not find any list content after multiple attempts")
                msg = "Could not find list content on IMDb page after multiple attempts"
                raise ValueError(msg)

        # Additional wait to ensure everything is loaded
        sb.sleep(3)

    except (TimeoutException, NoSuchElementException, WebDriverException):
        logging.exception("Failed to load IMDb list page")
        raise

    # Get total number of items
    try:
        # Try to find the container with the total items count using exact classes from HTML
        titles_container = sb.find_element("css selector", ".ipc-inline-list__item.sc-d6269c7a-1")
        if titles_container:
            total_text = titles_container.text
            # Extract the number from text like "500 titles"
            titles_match = re.search(r"(\d+)\s*titles?", total_text, re.IGNORECASE)
            if titles_match:
                total_items = int(titles_match.group(1))
                logging.info("Total items in list: %d", total_items)
                expected_pages = (total_items + 249) // 250  # Round up division by 250
                logging.info("Expected number of pages: %d", expected_pages)
            else:
                # Try another approach - find the text showing range like "1 - 250"
                range_container = sb.find_element("css selector", ".ipc-inline-list__item")
                range_text = range_container.text
                logging.info("Found range text: %s", range_text)
                if " - " in range_text:
                    # This is like "1 - 250"
                    try:
                        _, end = range_text.split(" - ")
                        per_page = int(end)
                        logging.info("Items per page: %d", per_page)
                        # Find total in the next element
                        next_item = sb.find_element("css selector", ".ipc-inline-list__item.sc-d6269c7a-1")
                        if next_item:
                            titles_text = next_item.text
                            titles_match = re.search(r"(\d+)", titles_text)
                            if titles_match:
                                total_items = int(titles_match.group(1))
                                expected_pages = (total_items + per_page - 1) // per_page
                                logging.info("Total items: %d, expected pages: %d", total_items, expected_pages)
                    except (ValueError, AttributeError) as e:
                        logging.warning("Could not parse range: %s", e)
                        total_items = None
                        expected_pages = None
                else:
                    total_items = None
                    expected_pages = None
        else:
            logging.warning("Total items container not found")
            total_items = None
            expected_pages = None
    except (NoSuchElementException, WebDriverException) as e:
        logging.warning("Could not determine total items using new selector: %s", e)
        # Fallback to original selector
        try:
            total_element = sb.find_element('[data-testid="list-page-mc-total-items"]')
            total_text = total_element.text
            total_items = int(re.search(r"(\d+)\s+titles?", total_text).group(1))
            logging.info("Total items in list (fallback): %d", total_items)
            expected_pages = (total_items + 249) // 250  # Round up division by 250
        except (NoSuchElementException, WebDriverException, AttributeError) as e2:
            logging.warning("Could not determine total items with fallback: %s", e2)
            total_items = None
            expected_pages = None

    current_page = 1

    # Process items on the page
    while True:
        # Try multiple approaches to find list items
        items = []

        # First try using the most specific selector
        try:
            items = sb.find_elements("css selector", "li.ipc-metadata-list-summary-item")
            if items:
                logging.info("Found %d items using specific selector", len(items))
        except (NoSuchElementException, WebDriverException) as e:
            logging.warning("Could not find items using specific selector: %s", e)

        # If that fails, try a more generic selector
        if not items:
            try:
                items = sb.find_elements("css selector", ".ipc-metadata-list-summary-item")
                if items:
                    logging.info("Found %d items using generic class selector", len(items))
            except (NoSuchElementException, WebDriverException) as e:
                logging.warning("Could not find items using generic selector: %s", e)

        # If that also fails, try an even more generic approach
        if not items:
            try:
                # Try to find the list first
                list_element = sb.find_element("css selector", "ul.ipc-metadata-list")
                # Then get its children
                items = list_element.find_elements("css selector", "li")
                if items:
                    logging.info("Found %d items via parent list element", len(items))
            except (NoSuchElementException, WebDriverException) as e:
                logging.warning("Could not find items via parent: %s", e)

        logging.info("Processing page %d: Found %d items", current_page, len(items))

        if not items:
            logging.warning("No items found on this page, attempting to continue to next page")
            # We might need to try the next page
            if current_page < (expected_pages or 2):  # Try at least page 2 if we don't know expected pages
                # Try to navigate to next page directly
                next_page = current_page + 1
                next_url = f"{url}/?page={next_page}"
                logging.info("Attempting to navigate directly to page %d: %s", next_page, next_url)
                sb.open(next_url)
                sb.sleep(5)  # Wait longer for page load
                current_page += 1
                continue
            logging.info("No more pages expected, breaking loop")
            break

        for item in items:
            try:
                # Get title element with multiple fallbacks
                title_element = None
                full_title = ""

                # Try different approaches to find the title
                selectors_to_try = [
                    ".ipc-title__text",
                    "h3.ipc-title__text",
                    "a.ipc-title-link-wrapper h3",
                    ".dli-title h3",
                ]

                for selector in selectors_to_try:
                    try:
                        title_element = item.find_element("css selector", selector)
                        if title_element:
                            full_title = title_element.text
                            logging.info("Found title using selector: %s", selector)
                            break
                    except (NoSuchElementException, WebDriverException):
                        pass

                if not full_title:
                    # Last resort: try to get any text from the item
                    full_title = item.text.split("\n")[0]
                    logging.warning("Using fallback method for title: %s", full_title)

                title = re.sub(r"^\d+\.\s*", "", full_title)  # Remove the numbering (e.g., "1. ")

                # Get year from metadata with multiple fallbacks
                year = None
                metadata_text = ""

                # Try different approaches to find the metadata
                metadata_selectors = [
                    ".sc-44e0e03-6.liNdun",
                    ".dli-title-metadata",
                    ".sc-44e0e03-6",
                    "[class*='title-metadata']",
                ]

                for selector in metadata_selectors:
                    try:
                        metadata = item.find_element("css selector", selector)
                        if metadata:
                            metadata_text = metadata.text
                            logging.info("Found metadata using selector: %s", selector)
                            break
                    except (NoSuchElementException, WebDriverException):
                        pass

                # Extract year if we found metadata text
                if metadata_text:
                    # Extract year from formats like "2008–2013" or "2024"
                    year_match = re.search(r"(\d{4})", metadata_text)
                    if year_match:
                        year = int(year_match.group(1))
                    logging.debug("Extracted year for %s: %s", title, year)

                # More robust media type detection
                media_type = "movie"  # default
                if metadata_text:
                    # Look for TV Series indicator in metadata text
                    if "TV Series" in metadata_text or "TV Mini Series" in metadata_text or "eps" in metadata_text.lower() or "episodes" in metadata_text.lower():
                        media_type = "tv"

                # Get IMDB ID from the title link with multiple fallbacks
                imdb_id = None
                link_selectors = [
                    "a.ipc-title-link-wrapper",
                    "a[href*='/title/']",
                    ".dli-title a",
                ]

                for selector in link_selectors:
                    try:
                        title_link = item.find_element("css selector", selector)
                        if title_link:
                            href = title_link.get_attribute("href")
                            if href and "/title/" in href:
                                imdb_id = href.split("/")[4]
                                logging.info("Found IMDb ID using selector: %s", selector)
                                break
                    except (NoSuchElementException, WebDriverException):
                        pass

                if not imdb_id:
                    # Try to extract it from any href in the item
                    try:
                        links = item.find_elements("css selector", "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and "/title/" in href:
                                imdb_id = href.split("/")[4]
                                logging.info("Found IMDb ID from generic link")
                                break
                    except (NoSuchElementException, WebDriverException):
                        pass

                if not imdb_id:
                    logging.warning("Could not find IMDb ID for %s, skipping", title)
                    continue

                media_items.append({
                    "title": title.strip(),
                    "imdb_id": imdb_id,
                    "media_type": media_type,
                    "year": year,
                })
                logging.info("Added %s: %s (%s) (IMDB ID: %s)", media_type, title, year, imdb_id)

            except (NoSuchElementException, WebDriverException) as e:
                logging.warning("Failed to parse IMDb item: %s", e)
                continue

        # Check if we've processed all expected pages
        if expected_pages and current_page >= expected_pages:
            logging.info("Reached final page %d of %d", current_page, expected_pages)
            break

        # Try to navigate to next page
        try:
            # First try clicking the button using a more specific selector
            try:
                # Log the HTML structure to help debugging
                logging.info("Looking for next button...")
                pagination_element = sb.find_element("css selector", "div[data-testid='index-pagination']")
                if pagination_element:
                    logging.info("Pagination element found")

                next_button = sb.find_element(
                    "css selector",
                    "button[data-testid='index-pagination-nxt']",
                )

                # Check if the button is disabled
                if next_button:
                    is_disabled = next_button.get_attribute("disabled")
                    logging.info("Next button found, disabled attribute: %s", is_disabled)
                    if is_disabled:
                        logging.info("Next button is disabled, no more pages")
                        break

                    # Button is enabled, so click it
                    sb.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    sb.sleep(1)  # Give time for scrolling
                    next_button.click()

                    # Wait for loading spinner to disappear and content to load
                    sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                    sb.sleep(3)  # Additional wait for content to fully render

                    # Verify we have items on the page
                    new_items = sb.find_elements("css selector", "li.ipc-metadata-list-summary-item")
                    if not new_items:
                        logging.warning("No items found after navigation to page %d, retrying...", current_page + 1)
                        # Fall back to direct URL navigation
                        next_page = current_page + 1
                        next_url = f"{url}/?page={next_page}"
                        sb.open(next_url)
                        sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                        sb.sleep(3)
            except (TimeoutException, NoSuchElementException, WebDriverException) as e:
                logging.info("Could not click next button: %s", e)
                # Fall back to direct URL navigation
                next_page = current_page + 1
                next_url = f"{url}/?page={next_page}"
                logging.info("Attempting to navigate directly to page %d: %s", next_page, next_url)
                sb.open(next_url)
                sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                sb.sleep(3)

            current_page += 1
            sb.sleep(2)
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            logging.info("No more pages available: %s", e)
            break

    # Validate total items found
    if total_items and len(media_items) < total_items:
        logging.warning("Only found %d items out of %d total", len(media_items), total_items)

    return media_items
