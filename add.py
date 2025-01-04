# =============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {list-sync v0.5.3}
# =============================================================================
#  __         _
# (_  _ |   .(_
# __)(_)||_||| \/
#              /
# © 2024
# -----------------------------------------------------------------------------
import base64
import getpass
import json
import logging
import os
import sqlite3
import time
import readline
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import re

import requests
from colorama import Style, init
from cryptography.fernet import Fernet
from halo import Halo
from seleniumbase import SB

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Define paths for config and database
DATA_DIR = "./data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.enc")
DB_FILE = os.path.join(DATA_DIR, "list_sync.db")


def custom_input(prompt):
    readline.set_startup_hook(lambda: readline.insert_text(''))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def ensure_data_directory_exists():
    os.makedirs(DATA_DIR, exist_ok=True)

def setup_logging():
    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # Set up file handler for general logging (DEBUG and above)
    file_handler = logging.FileHandler(os.path.join(DATA_DIR, "list_sync.log"))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Create a custom filter to block non-colored output
    class ColoredOutputFilter(logging.Filter):
        def filter(self, record):
            # Only allow ERROR level messages that are explicitly marked for console
            return False  # Block all logging to console
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ColoredOutputFilter())
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set up separate logger for added items
    added_logger = logging.getLogger("added_items")
    added_logger.setLevel(logging.INFO)
    added_handler = logging.FileHandler(os.path.join(DATA_DIR, "added.log"))
    added_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    added_logger.addHandler(added_handler)
    
    # Prevent added_logger from propagating to root logger
    added_logger.propagate = False
    
    # Disable selenium logging to console
    selenium_logger = logging.getLogger('selenium')
    selenium_logger.setLevel(logging.INFO)
    selenium_logger.propagate = False
    
    # Disable urllib3 logging to console
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.INFO)
    urllib3_logger.propagate = False
    
    return added_logger

def init_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_type TEXT NOT NULL,
                list_id TEXT NOT NULL,
                UNIQUE(list_type, list_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synced_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL,
                imdb_id TEXT,
                overseerr_id INTEGER,
                status TEXT,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_interval (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interval_hours INTEGER NOT NULL
            )
        ''')
        conn.commit()

def color_gradient(text, start_color, end_color):
    def hex_to_rgb(hex_code):
        return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))

    start_rgb = hex_to_rgb(start_color.lstrip("#"))
    end_rgb = hex_to_rgb(end_color.lstrip("#"))

    gradient_text = ""
    steps = len(text)

    for i, char in enumerate(text):
        ratio = i / steps
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        gradient_text += f"\033[38;2;{r};{g};{b}m{char}"

    return gradient_text + Style.RESET_ALL

def display_ascii_art():
    ascii_art = """
  _      _        _     ___                    
 | |    (_)  ___ | |_  / __|  _  _   _ _    __ 
 | |__  | | (_-< |  _| \__ \ | || | | ' \  / _|
 |____| |_| /__/  \__| |___/  \_, | |_||_| \__|
                              |__/             
    """
    art_lines = ascii_art.split("\n")
    for line in art_lines:
        print(color_gradient(line, "#00aaff", "#00ffaa"))
        time.sleep(0.1)
    print(Style.RESET_ALL)

def display_banner():
    banner = """
    ==============================================================
             Soluify - {servarr-tools_list-sync_v0.5.3}
    ==============================================================
    """
    print(color_gradient(banner, "#aa00aa", "#00aa00") + Style.RESET_ALL)

def encrypt_config(data, password):
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode())

def decrypt_config(encrypted_data, password):
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode())

def save_config(overseerr_url, api_key, requester_user_id):
    config = {"overseerr_url": overseerr_url, "api_key": api_key, "requester_user_id": requester_user_id}
    print(color_gradient("🔐  Enter a password to encrypt your API details: ", "#ff0000", "#aa0000"), end="")
    password = getpass.getpass("")
    encrypted_config = encrypt_config(config, password)
    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted_config)
    print(f'\n{color_gradient("✅  Details encrypted. Remember your password!", "#00ff00", "#00aa00")}\n')

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "rb") as f:
            encrypted_config = f.read()
        print()  # Ensure password prompt is on a new line
        password = getpass.getpass(color_gradient("🔑  Enter your password: ", "#ff0000", "#aa0000"))
        try:
            config = decrypt_config(encrypted_config, password)
            return config["overseerr_url"], config["api_key"], config["requester_user_id"]
        except Exception:
            print(f'\n{color_gradient("❌  Incorrect password. Unable to decrypt config.", "#ff0000", "#aa0000")}')
            if custom_input("\n🗑️  Delete this config and start over? (y/n): ").lower() == "y":
                os.remove(CONFIG_FILE)
                print(f'\n{color_gradient("🔄  Config deleted. Rerun the script to set it up again.", "#ffaa00", "#ff5500")}\n')
            return None, None, None
    return None, None, None

def test_overseerr_api(overseerr_url, api_key):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    test_url = f"{overseerr_url}/api/v1/status"
    spinner = Halo(text=color_gradient("🔍  Testing API connection...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    try:
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        spinner.succeed(color_gradient("🎉  API connection successful!", "#00ff00", "#00aa00"))
        logging.info("Overseerr API connection successful!")
    except Exception as e:
        spinner.fail(color_gradient(f"❌  Overseerr API connection failed. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Overseerr API connection failed. Error: {str(e)}")
        raise

def set_requester_user(overseerr_url, api_key):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    users_url = f"{overseerr_url}/api/v1/user"
    try:
        requester_user_id = "1"
        response = requests.get(users_url, headers=headers)
        response.raise_for_status()
        jsonResult = response.json()
        if jsonResult['pageInfo']['results'] > 1:
            print(color_gradient("\n📋 Multiple users detected, you can choose which user will make the requests on ListSync behalf.\n", "#00aaff", "#00ffaa"))
            for result in jsonResult['results']:
                print(color_gradient(f"{result['id']}. {result['displayName']}", "#ffaa00", "#ff5500"))
            requester_user_id = custom_input(color_gradient("\nEnter the number of the list to use as requester user: ", "#ffaa00", "#ff5500"))
            if not next((x for x in jsonResult['results'] if str(x['id']) == requester_user_id), None):
                requester_user_id = "1"
                print(color_gradient("\n❌  Invalid option, using admin as requester user.", "#ff0000", "#aa0000"))

        logging.info("Requester user set!")
        return requester_user_id
    except Exception as e:
        logging.error(f"Overseerr API connection failed. Error: {str(e)}")
        return 1

def fetch_imdb_list(list_id):
    """Fetch IMDb list using Selenium with pagination"""
    media_items = []
    print(color_gradient("📚  Fetching IMDB list...", "#ffaa00", "#ff5500"))
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')  # Use the provided URL directly
                if '/chart/' in url:
                    is_chart = True
                elif '/list/' in url or '/user/' in url:
                    is_chart = False
                else:
                    raise ValueError("Invalid IMDb URL format")
            else:
                # Existing logic for list IDs
                if list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
                    url = f"https://www.imdb.com/chart/{list_id}"
                    is_chart = True
                elif list_id.startswith("ls"):
                    url = f"https://www.imdb.com/list/{list_id}"
                    is_chart = False
                elif list_id.startswith("ur"):
                    url = f"https://www.imdb.com/user/{list_id}/watchlist"
                    is_chart = False
                else:
                    raise ValueError("Invalid IMDb list ID format")
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            if is_chart:
                # Wait for chart content to load
                sb.wait_for_element_present('.ipc-metadata-list.ipc-metadata-list--dividers-between', timeout=20)
                
                # Get total number of items
                try:
                    total_element = sb.find_element('[data-testid="chart-layout-total-items"]')
                    total_text = total_element.text
                    total_items = int(re.search(r'(\d+)\s+Titles?', total_text).group(1))
                    logging.info(f"Total items in chart: {total_items}")
                except Exception as e:
                    logging.warning(f"Could not determine total items: {str(e)}")
                    total_items = None
                
                # Process items in the chart
                items = sb.find_elements(".ipc-metadata-list-summary-item__tc")
                logging.info(f"Found {len(items)} items in chart")
                
                for item in items:
                    try:
                        # Get title element
                        title_element = item.find_element("css selector", ".ipc-title__text")
                        full_title = title_element.text
                        # Remove ranking number if present (e.g., "1. The Shawshank Redemption" -> "The Shawshank Redemption")
                        title = re.sub(r'^\d+\.\s*', '', full_title)
                        
                        # Get year from metadata
                        year = None
                        try:
                            metadata = item.find_element("css selector", ".cli-title-metadata")
                            year_element = metadata.find_element("css selector", ".cli-title-metadata-item")
                            year = int(year_element.text)
                            logging.debug(f"Extracted year for {title}: {year}")
                        except Exception as e:
                            logging.warning(f"Could not extract year for {title}: {str(e)}")
                        
                        # Get IMDB ID from the title link
                        title_link = item.find_element("css selector", "a.ipc-title-link-wrapper")
                        imdb_id = title_link.get_attribute("href").split("/")[4]
                        
                        # For charts, all items are movies unless explicitly marked as TV
                        media_type = "movie"
                        try:
                            if "TV" in metadata.text:
                                media_type = "tv"
                        except Exception:
                            pass
                        
                        media_items.append({
                            "title": title.strip(),
                            "imdb_id": imdb_id,
                            "media_type": media_type,
                            "year": year
                        })
                        logging.info(f"Added {media_type}: {title} ({year}) (IMDB ID: {imdb_id})")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse IMDb chart item: {str(e)}")
                        continue
                
            else:
                # Wait for list content to load
                sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=20)
                
                # Get total number of items
                try:
                    total_element = sb.find_element('[data-testid="list-page-mc-total-items"]')
                    total_text = total_element.text
                    total_items = int(re.search(r'(\d+)\s+titles?', total_text).group(1))
                    logging.info(f"Total items in list: {total_items}")
                    expected_pages = (total_items + 249) // 250  # Round up division by 250
                    logging.info(f"Expected number of pages: {expected_pages}")
                except Exception as e:
                    logging.warning(f"Could not determine total items: {str(e)}")
                    total_items = None
                    expected_pages = None
                
                current_page = 1
                
                # Process items on the page
                while True:
                    items = sb.find_elements(".sc-2bfd043a-3.jpWwpQ")
                    logging.info(f"Processing page {current_page}: Found {len(items)} items")
                    
                    for item in items:
                        try:
                            # Get title element
                            title_element = item.find_element("css selector", ".ipc-title__text")
                            full_title = title_element.text
                            title = full_title.split(". ", 1)[1] if ". " in full_title else full_title
                            
                            # Get year from metadata
                            year = None
                            try:
                                metadata = item.find_element("css selector", ".dli-title-metadata")
                                metadata_text = metadata.text
                                # Extract year from formats like "2008–2013" or "2024"
                                year_match = re.search(r'(\d{4})', metadata_text)
                                if year_match:
                                    year = int(year_match.group(1))
                                logging.debug(f"Extracted year for {title}: {year}")
                            except Exception as e:
                                logging.warning(f"Could not extract year for {title}: {str(e)}")
                            
                            # More robust media type detection
                            media_type = "movie"  # default
                            try:
                                type_element = item.find_element("css selector", ".dli-title-type-data")
                                if "TV Series" in type_element.text or "TV Mini Series" in type_element.text:
                                    media_type = "tv"
                            except Exception:
                                try:
                                    if "eps" in metadata_text or "episodes" in metadata_text.lower():
                                        media_type = "tv"
                                except Exception:
                                    logging.warning(f"Could not determine media type from metadata for {title}")
                            
                            # Get IMDB ID from the title link
                            title_link = item.find_element("css selector", "a.ipc-title-link-wrapper")
                            imdb_id = title_link.get_attribute("href").split("/")[4]
                            
                            media_items.append({
                                "title": title.strip(),
                                "imdb_id": imdb_id,
                                "media_type": media_type,
                                "year": year
                            })
                            logging.info(f"Added {media_type}: {title} ({year}) (IMDB ID: {imdb_id})")
                            
                        except Exception as e:
                            logging.warning(f"Failed to parse IMDb item: {str(e)}")
                            continue
                    
                    # Check if we've processed all expected pages
                    if expected_pages and current_page >= expected_pages:
                        logging.info(f"Reached final page {current_page} of {expected_pages}")
                        break
                    
                    # Try to navigate to next page
                    try:
                        # First try clicking the button using a more specific selector
                        try:
                            next_button = sb.find_element(
                                "css selector", 
                                "button.ipc-responsive-button[aria-label='Next']:not([disabled])"
                            )
                            if next_button:
                                sb.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                sb.sleep(1)  # Give time for scrolling
                                next_button.click()
                                
                                # Wait for loading spinner to disappear and content to load
                                sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                                sb.sleep(3)  # Additional wait for content to fully render
                                
                                # Verify we have items on the page
                                new_items = sb.find_elements(".sc-2bfd043a-3.jpWwpQ")
                                if not new_items:
                                    logging.warning(f"No items found after navigation to page {current_page + 1}, retrying...")
                                    # Fall back to direct URL navigation
                                    next_page = current_page + 1
                                    next_url = f"{url}/?page={next_page}"
                                    sb.open(next_url)
                                    sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                                    sb.sleep(3)
                        except Exception as e:
                            logging.info(f"Could not click next button: {str(e)}")
                            # Fall back to direct URL navigation
                            next_page = current_page + 1
                            next_url = f"{url}/?page={next_page}"
                            logging.info(f"Attempting to navigate directly to page {next_page}: {next_url}")
                            sb.open(next_url)
                            sb.wait_for_element_present('[data-testid="list-page-mc-list-content"]', timeout=10)
                            sb.sleep(3)
                        
                        current_page += 1
                        sb.sleep(2)
                    except Exception as e:
                        logging.info(f"No more pages available: {str(e)}")
                        break
                
                # Validate total items found
                if total_items and len(media_items) < total_items:
                    logging.warning(f"Only found {len(media_items)} items out of {total_items} total")
                
            print(color_gradient(f"✨  Found {len(media_items)} items from IMDB list {list_id}!", "#00ff00", "#00aa00"))
            logging.info(f"IMDB list {list_id} fetched successfully. Found {len(media_items)} items.")
            return media_items
        
    except Exception as e:
        print(color_gradient(f"💥  Failed to fetch IMDB list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching IMDB list {list_id}: {str(e)}")
        raise

def fetch_trakt_list(list_id):
    """Fetch Trakt list using Selenium with pagination"""
    media_items = []
    print(color_gradient("📚  Fetching Trakt list...", "#ffaa00", "#ff5500"))
    
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
            
            print(color_gradient(f"✨  Found {len(media_items)} items from Trakt list {list_id}!", "#00ff00", "#00aa00"))
            logging.info(f"Trakt list {list_id} fetched successfully. Found {len(media_items)} items.")
            return media_items
        
    except Exception as e:
        print(color_gradient(f"💥  Failed to fetch Trakt list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching Trakt list {list_id}: {str(e)}")
        raise

def fetch_letterboxd_list(list_id):
    """Fetch Letterboxd list using Selenium with pagination"""
    media_items = []
    print(color_gradient("📚  Fetching Letterboxd list...", "#ffaa00", "#ff5500"))
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Handle full URLs vs list IDs
            if list_id.startswith(('http://', 'https://')):
                url = list_id.rstrip('/')  # Use the provided URL directly
                if not ('letterboxd.com' in url and ('/list/' in url)):
                    raise ValueError("Invalid Letterboxd URL format")
            else:
                raise ValueError("Letterboxd lists must be provided as full URLs")
            
            logging.info(f"Attempting to load URL: {url}")
            sb.open(url)
            
            # Wait for container to load
            sb.wait_for_element_present(".js-list-entries.poster-list.-p125.-grid.film-list", timeout=20)
            
            while True:
                # Wait for items to load and be visible
                sb.wait_for_element_present("li.poster-container", timeout=20)
                sb.sleep(2)  # Additional wait for all items to render
                
                # Get all items on current page
                items = sb.find_elements("li.poster-container")
                logging.info(f"Found {len(items)} items on current page")
                
                for item in items:
                    try:
                        # Get the frame-title span which contains "Title (Year)"
                        title_span = item.find_element("css selector", "span.frame-title")
                        title_text = title_span.text
                        
                        # Extract title and year from "Title (Year)" format
                        if '(' in title_text and ')' in title_text:
                            title = title_text[:title_text.rindex('(')].strip()
                            year_str = title_text[title_text.rindex('(')+1:title_text.rindex(')')]
                            try:
                                year = int(year_str)
                            except (ValueError, TypeError):
                                year = None
                        else:
                            title = title_text.strip()
                            year = None
                            
                        if title:
                            media_items.append({
                                "title": title,
                                "media_type": "movie",  # Default to movie as we can't reliably distinguish
                                "year": year
                            })
                            logging.info(f"Added movie: {title} ({year})")
                        
                    except Exception as e:
                        logging.warning(f"Failed to parse Letterboxd item: {str(e)}")
                        continue
                
                # Check for next page button
                try:
                    # Look for the next button that's not disabled
                    next_button = sb.find_element(".pagination .next:not(.paginate-disabled)")
                    if not next_button:
                        logging.info("No more pages to process")
                        break
                    
                    # Get the href attribute from the anchor tag
                    next_link = next_button.find_element("css selector", "a")
                    next_url = next_link.get_attribute("href")
                    if not next_url:
                        logging.info("No next page URL found")
                        break
                    
                    # Navigate to next page
                    sb.open(next_url)
                    sb.sleep(3)  # Wait for new page to load
                    
                except Exception as e:
                    logging.info(f"No more pages available: {str(e)}")
                    break
            
            print(color_gradient(f"✨  Found {len(media_items)} items from Letterboxd list {list_id}!", "#00ff00", "#00aa00"))
            logging.info(f"Letterboxd list {list_id} fetched successfully. Found {len(media_items)} items.")
            return media_items
        
    except Exception as e:
        print(color_gradient(f"💥  Failed to fetch Letterboxd list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching Letterboxd list {list_id}: {str(e)}")
        raise

def normalize_title(title: str) -> str:
    """Normalize a title for comparison by removing special characters and converting to lowercase."""
    # Remove special characters and convert to lowercase
    return re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().strip()

def search_media_in_overseerr(overseerr_url, api_key, media_title, media_type, release_year=None):
    headers = {"X-Api-Key": api_key}
    
    # Ensure overseerr_url doesn't end with a slash
    overseerr_url = overseerr_url.rstrip('/')
    search_url = f"{overseerr_url}/api/v1/search"
    
    page = 1
    best_match = None
    closest_year_diff = float('inf')
    search_title_normalized = normalize_title(media_title)
    
    while True:
        try:
            # Properly encode the query parameter
            encoded_query = requests.utils.quote(media_title)
            
            # Build the URL manually to ensure proper encoding
            url = f"{search_url}?query={encoded_query}&page={page}&language=en"
            
            # Log the exact URL being requested (for debugging)
            logging.debug(f"Requesting URL: {url}")
            logging.debug(f"Headers: {headers}")
            
            # Make the request
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            
            # Log the response status and headers (for debugging)
            logging.debug(f"Response status: {response.status_code}")
            logging.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 429:
                logging.warning("Rate limited, waiting 5 seconds...")
                time.sleep(5)
                continue
                
            response.raise_for_status()
            search_results = response.json()
            
            if not search_results.get("results"):
                break
                
            for result in search_results["results"]:
                result_type = result.get("mediaType")
                
                if result_type != media_type:
                    continue
                    
                # Get the title based on media type
                result_title = result.get("title") if media_type == "movie" else result.get("name")
                if not result_title:
                    continue
                    
                result_title_normalized = normalize_title(result_title)
                
                # Check for exact title match
                if search_title_normalized != result_title_normalized:
                    continue
                    
                # Get year based on media type
                result_year = None
                try:
                    if media_type == "movie" and "releaseDate" in result and result["releaseDate"]:
                        result_year = int(result["releaseDate"][:4])
                    elif media_type == "tv" and "firstAirDate" in result and result["firstAirDate"]:
                        result_year = int(result["firstAirDate"][:4])
                except (ValueError, TypeError):
                    pass
                    
                if release_year and result_year:
                    year_diff = abs(result_year - release_year)
                    if year_diff < closest_year_diff:
                        closest_year_diff = year_diff
                        best_match = result
                        logging.debug(f"Found better year match for {media_title}: {result_title} ({result_year})")
                elif best_match is None:
                    best_match = result

            if page >= search_results.get("totalPages", 1):
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            logging.error(f'Error searching page {page} for {media_type} "{media_title}": {str(e)}')
            if "429" in str(e):  # Rate limited
                time.sleep(5)
                continue
            raise

    if best_match:
        result_year = None
        try:
            if media_type == "movie" and "releaseDate" in best_match and best_match["releaseDate"]:
                result_year = best_match["releaseDate"][:4]
            elif media_type == "tv" and "firstAirDate" in best_match and best_match["firstAirDate"]:
                result_year = best_match["firstAirDate"][:4]
        except (ValueError, TypeError):
            pass
            
        result_title = best_match.get("title") if media_type == "movie" else best_match.get("name")
        logging.info(f"Best match for '{media_title}' ({release_year}): '{result_title}' ({result_year})")
        
        return {
            "id": best_match["id"],
            "mediaType": best_match["mediaType"],
        }
    
    logging.warning(f'No matching results found for "{media_title}" ({release_year}) of type "{media_type}"')
    return None

def extract_number_of_seasons(media_data):
    number_of_seasons = media_data.get("numberOfSeasons")
    logging.debug(f"Extracted number of seasons: {number_of_seasons}")
    return number_of_seasons if number_of_seasons is not None else 1

def confirm_media_status(overseerr_url, api_key, media_id, media_type):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    media_url = f"{overseerr_url}/api/v1/{media_type}/{media_id}"
    
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        logging.debug(f"Detailed response for {media_type} ID {media_id}: {json.dumps(media_data)}")

        media_info = media_data.get("mediaInfo", {})
        status = media_info.get("status")
        number_of_seasons = extract_number_of_seasons(media_data)

        logging.debug(f"Status for {media_type} ID {media_id}: {status}")
        logging.debug(f"Number of seasons for {media_type} ID {media_id}: {number_of_seasons}")

        # Status codes:
        # 2: PENDING
        # 3: PROCESSING
        # 4: PARTIALLY_AVAILABLE
        # 5: AVAILABLE
        is_available_to_watch = status in [4, 5]
        is_requested = status in [2, 3]

        return is_available_to_watch, is_requested, number_of_seasons
    except Exception as e:
        logging.error(f"Error confirming status for {media_type} ID {media_id}: {str(e)}")
        raise

def request_media_in_overseerr(overseerr_url, api_key, requester_user_id, media_id, media_type):
    headers = {"X-Api-Key": api_key, "X-Api-User": requester_user_id, "Content-Type": "application/json"}
    request_url = f"{overseerr_url}/api/v1/request"
    payload = {
        "mediaId": media_id,
        "mediaType": media_type,
        "is4k": False
    }
    try:
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.debug(f"Request response for {media_type} ID {media_id}: {json.dumps(response.json())}")
        return "success"
    except Exception as e:
        logging.error(f"Error requesting {media_type} ID {media_id}: {str(e)}")
        return "error"

def request_tv_series_in_overseerr(overseerr_url, api_key, requester_user_id, tv_id, number_of_seasons):
    headers = {"X-Api-Key": api_key, "X-Api-User": requester_user_id, "Content-Type": "application/json"}
    request_url = f"{overseerr_url}/api/v1/request"
    
    seasons_list = [i for i in range(1, number_of_seasons + 1)]
    logging.debug(f"Seasons list for TV series ID {tv_id}: {seasons_list}")
    
    payload = {
        "mediaId": tv_id,
        "mediaType": "tv",
        "is4k": False,
        "seasons": seasons_list
    }
    
    logging.debug(f"Request payload for TV series ID {tv_id}: {json.dumps(payload, indent=4)}")

    try:
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.debug(f"Request response for TV series ID {tv_id}: {response.json()}")
        return "success"
    except Exception as e:
        logging.error(f"Error requesting TV series ID {tv_id}: {str(e)}")
        return "error"

def save_list_id(list_id: str, list_type: str):
    """Save list ID to database, converting URLs to IDs if needed"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # For IMDb URLs, store the full URL
        if list_type == "imdb" and list_id.startswith(('http://', 'https://')):
            # Keep the full URL as is
            id_to_save = list_id.rstrip('/')
        # For IMDb chart names, store as is
        elif list_type == "imdb" and list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
            id_to_save = list_id
        # For Trakt URLs, store the full URL
        elif list_type == "trakt" and list_id.startswith(('http://', 'https://')):
            id_to_save = list_id.rstrip('/')
        else:
            # For traditional IDs (ls, ur, numeric), store as is
            id_to_save = list_id
            
        cursor.execute(
            "INSERT OR REPLACE INTO lists (list_type, list_id) VALUES (?, ?)",
            (list_type, id_to_save)
        )
        conn.commit()

def load_list_ids() -> List[Dict[str, str]]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT list_type, list_id FROM lists")
        return [{"type": row[0], "id": row[1]} for row in cursor.fetchall()]

def display_lists():
    lists = load_list_ids()
    print(color_gradient("\nSaved Lists:", "#00aaff", "#00ffaa"))
    for idx, list_info in enumerate(lists, 1):
        print(color_gradient(f"{idx}. {list_info['type'].upper()}: {list_info['id']}", "#ffaa00", "#ff5500"))

def delete_list():
    lists = load_list_ids()
    display_lists()
    choice = custom_input(color_gradient("\nEnter the number of the list to delete (or 'c' to cancel): ", "#ffaa00", "#ff5500"))
    if choice.lower() == 'c':
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(lists):
            list_to_delete = lists[idx]
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM lists WHERE list_type = ? AND list_id = ?",
                    (list_to_delete['type'], list_to_delete['id'])
                )
                conn.commit()
            print(color_gradient(f"\nList {list_to_delete['type'].upper()}: {list_to_delete['id']} deleted.", "#00ff00", "#00aa00"))
        else:
            print(color_gradient("\nInvalid list number.", "#ff0000", "#aa0000"))
    except ValueError:
        print(color_gradient("\nInvalid input. Please enter a number.", "#ff0000", "#aa0000"))

def edit_lists():
    lists = load_list_ids()
    display_lists()
    print(color_gradient("\nEnter new list IDs (or press Enter to keep the current ID):", "#00aaff", "#00ffaa"))
    updated_lists = []
    for list_info in lists:
        new_id = custom_input(color_gradient(f"{list_info['type'].upper()}: {list_info['id']} -> ", "#ffaa00", "#ff5500"))
        updated_lists.append({
            "type": list_info['type'],
            "id": new_id if new_id else list_info['id']
        })
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        cursor.executemany(
            "INSERT INTO lists (list_type, list_id) VALUES (?, ?)",
            [(list_info['type'], list_info['id']) for list_info in updated_lists]
        )
        conn.commit()
    print(color_gradient("\nLists updated successfully.", "#00ff00", "#00aa00"))

def configure_sync_interval():
    interval = custom_input(color_gradient("\n🕒  How often do you want to sync your lists (in hours)? ", "#ffaa00", "#ff5500"))
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_interval")
        cursor.execute("INSERT INTO sync_interval (interval_hours) VALUES (?)", (int(interval),))
        conn.commit()
    print(f'\n{color_gradient("✅  Sync interval configured.", "#00ff00", "#00aa00")}\n')

def load_sync_interval():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT interval_hours FROM sync_interval")
        result = cursor.fetchone()
        return result[0] if result else 0  # Default to 0 hours if not set

def should_sync_item(overseerr_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT last_synced FROM synced_items
            WHERE overseerr_id = ?
            AND last_synced > datetime('now', '-48 hours')
        ''', (overseerr_id,))
        result = cursor.fetchone()
        return result is None

def save_sync_result(title, media_type, imdb_id, overseerr_id, status):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO synced_items 
            (title, media_type, imdb_id, overseerr_id, status, last_synced)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (title, media_type, imdb_id, overseerr_id, status))
        conn.commit()

def process_media_item(item: Dict[str, Any], overseerr_url: str, api_key: str, requester_user_id: str, dry_run: bool) -> Dict[str, Any]:
    title = item.get('title', 'Unknown Title')
    media_type = item.get('media_type', 'unknown')
    imdb_id = item.get('imdb_id')
    year = item.get('year')  # Make year optional

    if dry_run:
        return {"title": title, "status": "would_be_synced"}

    try:
        search_result = search_media_in_overseerr(
            overseerr_url, 
            api_key, 
            title, 
            media_type,
            year  # Pass year as is - it can be None
        )
        if search_result:
            overseerr_id = search_result["id"]
            if not should_sync_item(overseerr_id):
                return {"title": title, "status": "skipped"}

            is_available, is_requested, number_of_seasons = confirm_media_status(overseerr_url, api_key, overseerr_id, search_result["mediaType"])
            
            if is_available:
                save_sync_result(title, media_type, imdb_id, overseerr_id, "already_available")
                return {"title": title, "status": "already_available"}
            elif is_requested:
                save_sync_result(title, media_type, imdb_id, overseerr_id, "already_requested")
                return {"title": title, "status": "already_requested"}
            else:
                if search_result["mediaType"] == 'tv':
                    request_status = request_tv_series_in_overseerr(overseerr_url, api_key, requester_user_id, overseerr_id, number_of_seasons)
                else:
                    request_status = request_media_in_overseerr(overseerr_url, api_key, requester_user_id, overseerr_id, search_result["mediaType"])
                
                if request_status == "success":
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "requested")
                    return {"title": title, "status": "requested"}
                else:
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "request_failed")
                    return {"title": title, "status": "request_failed"}
        else:
            save_sync_result(title, media_type, imdb_id, None, "not_found")
            return {"title": title, "status": "not_found"}
    except Exception as e:
        logging.error(f'Error processing item {title}: {str(e)}')
        return {"title": title, "status": "error"}

def process_media(media_items: List[Dict[str, Any]], overseerr_url: str, api_key: str, requester_user_id: str, dry_run: bool = False):
    total_items = len(media_items)
    results = {
        "requested": 0,
        "already_requested": 0,
        "already_available": 0,
        "not_found": 0,
        "error": 0,
        "skipped": 0
    }

    print(color_gradient(f"\n🎬  Processing {total_items} media items...", "#00aaff", "#00ffaa") + "\n")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_media_item, item, overseerr_url, api_key, requester_user_id, dry_run): item for item in media_items}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                status = result["status"]
                results[status] = results.get(status, 0) + 1
                
                if dry_run:
                    print(color_gradient("🔍 {}: Would be synced".format(result['title']), "#ffaa00", "#ff5500") + "\n")
                else:
                    status_info = {
                    "requested": ("✅", "Successfully Requested", "#4CAF50", "#45a049"),
                    "already_requested": ("📌", "Already Requested", "#2196F3", "#1E88E5"),
                    "already_available": ("☑️ ", "Already Available", "#00BCD4", "#00ACC1"),
                    "not_found": ("❓", "Not Found", "#FFC107", "#FFA000"),
                    "error": ("❌", "Error", "#F44336", "#E53935"),
                    "skipped": ("⏭️ ", "Skipped", "#9E9E9E", "#757575")
                    }.get(status, ("➖", "Unknown Status", "#607D8B", "#546E7A"))

                    
                    emoji, status_text, start_color, end_color = status_info
                    message = "{}: {}".format(result['title'], status_text)
                    print("{} {}\n".format(emoji,  color_gradient(message, start_color, end_color)))
            except Exception as exc:
                print(color_gradient("❌ {} generated an exception: {}".format(item['title'], exc), "#ff0000", "#aa0000") + "\n")
                results["error"] += 1

    if not dry_run:
        display_summary(total_items, results)

def display_summary(total_items: int, results: Dict[str, int]):
    summary = f"""
==============================================================
                    All done! Here's the Summary!
==============================================================
🔁 Total Items Processed: {total_items}

☑️  Items Already Available: {results["already_available"]}

✅ Items Successfully Requested: {results["requested"]}

📌 Items Already Requested: {results["already_requested"]}

❓ Items Not Found: {results["not_found"]}

⏭️  Items Skipped: {results["skipped"]}

❌ Items Failed: {results["error"]}
==============================================================
"""
    print(color_gradient(summary, "#00aaff", "#00ffaa") + Style.RESET_ALL)

def display_menu():
    menu = """
==============================================================
                    🛠️  Soluify - List Sync Tool 🛠️
==============================================================
1. ➕ Add New Lists ➕
2. 🔄 Start Sync with Saved Lists 🔄
3. 🔍 One-Time List Sync 🔍
4. 📋 Manage Existing Lists 📋
5. ⏰ Configure Sync Interval ⏰
6. 🏃 Run Dry Sync 🏃
7. ❌ Exit ❌
==============================================================
"""
    print(color_gradient(menu, "#00aaff", "#00ffaa") + Style.RESET_ALL)

def start_sync(overseerr_url, api_key, requester_user_id, added_logger, dry_run=False):
    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000") + "\n")
        logging.error(f"Error testing Overseerr API: {e}")
        return

    media_items = []
    for list_info in load_list_ids():
        try:
            if list_info['type'] == "imdb":
                media_items.extend(fetch_imdb_list(list_info['id']))
            elif list_info['type'] == "trakt":
                media_items.extend(fetch_trakt_list(list_info['id']))
            elif list_info['type'] == "letterboxd":
                media_items.extend(fetch_letterboxd_list(list_info['id']))
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error fetching list: {e}")
            continue

    process_media(media_items, overseerr_url, api_key, requester_user_id, dry_run)

def one_time_list_sync(overseerr_url, api_key, requester_user_id, added_logger):
    list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) for one-time sync (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
    list_ids = [id.strip() for id in list_ids.split(',')]
    
    media_items = []
    for list_id in list_ids:
        try:
            # Check for IMDb URLs or chart IDs
            if list_id.startswith(('http://', 'https://')):
                if 'imdb.com' in list_id:
                    items = fetch_imdb_list(list_id)
                    if items:
                        media_items.extend(items)
                elif 'trakt.tv' in list_id:
                    media_items.extend(fetch_trakt_list(list_id))
                elif 'letterboxd.com' in list_id and '/list/' in list_id:
                    media_items.extend(fetch_letterboxd_list(list_id))
                else:
                    print(color_gradient("\n❌  Invalid URL format. Must be IMDb, Trakt, or Letterboxd URL.", "#ff0000", "#aa0000"))
            elif list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
                items = fetch_imdb_list(list_id)
                if items:
                    media_items.extend(items)
            # Check for IMDb list IDs
            elif list_id.startswith(('ls', 'ur')):
                media_items.extend(fetch_imdb_list(list_id))
            # Check for Trakt IDs
            elif list_id.isdigit():
                media_items.extend(fetch_trakt_list(list_id))
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. Skipping this ID.", "#ff0000", "#aa0000"))
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list {list_id}: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error fetching list {list_id}: {e}")
            continue
    
    if media_items:
        process_media(media_items, overseerr_url, api_key, requester_user_id)
    else:
        print(color_gradient("\n❌  No valid lists were processed.", "#ff0000", "#aa0000"))

def add_new_lists():
    add_new_list = True
    while add_new_list:
        list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
        list_ids = [id.strip() for id in list_ids.split(',')]
        
        for list_id in list_ids:
            try:
                # Determine list type and validate
                if list_id.startswith(('http://', 'https://')):
                    if 'imdb.com' in list_id:
                        list_type = "imdb"
                    elif 'trakt.tv' in list_id:
                        list_type = "trakt"
                    elif 'letterboxd.com' in list_id and '/list/' in list_id:
                        list_type = "letterboxd"
                    else:
                        raise ValueError("Invalid URL - must be IMDb, Trakt, or Letterboxd")
                elif list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
                    # Verify the list works before saving
                    test_items = fetch_imdb_list(list_id)  # Add this test
                    if not test_items:  # Add this check
                        raise ValueError("Failed to fetch items from list")
                    list_type = "imdb"
                elif list_id.startswith(('ls', 'ur')):
                    list_type = "imdb"
                elif list_id.isdigit():
                    list_type = "trakt"
                else:
                    raise ValueError("Invalid list ID format")

                confirmation_message = f"Are you sure this {list_type.upper()} list is correct? (ID/URL: {list_id})"
                add_to_sync = custom_input(color_gradient(f"\n🚨  {confirmation_message} (y/n): ", "#ffaa00", "#ff5500")).lower()
                if add_to_sync == "y":
                    save_list_id(list_id, list_type)
            except ValueError as e:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. {str(e)}", "#ff0000", "#aa0000"))
                continue

        more_lists = custom_input(color_gradient("\n🏁  Do you want to import any other lists? (y/n): ", "#ffaa00", "#ff5500")).lower()
        if more_lists != "y":
            add_new_list = False

    # Start sync immediately after adding new lists
    overseerr_url, api_key, requester_user_id = load_config()
    if overseerr_url and api_key:
        start_sync(overseerr_url, api_key, requester_user_id, setup_logging())

def manage_lists():
    while True:
        print(color_gradient("\n📋 Manage Lists:", "#00aaff", "#00ffaa"))
        print(color_gradient("1. View Lists", "#ffaa00", "#ff5500"))
        print(color_gradient("2. Delete a List", "#ffaa00", "#ff5500"))
        print(color_gradient("3. Edit Lists", "#ffaa00", "#ff5500"))
        print(color_gradient("4. Return to Main Menu", "#ffaa00", "#ff5500"))
        
        choice = custom_input(color_gradient("\nEnter your choice: ", "#ffaa00", "#ff5500"))
        
        if choice == "1":
            display_lists()
        elif choice == "2":
            delete_list()
        elif choice == "3":
            edit_lists()
        elif choice == "4":
            break
        else:
            print(color_gradient("\n❌ Invalid choice. Please try again.", "#ff0000", "#aa0000"))

def init_selenium_driver():
    logging.info("Initializing Selenium driver...")
    try:
        chrome_options = [
            "--no-sandbox",
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--remote-debugging-port=9222",
            f"--user-data-dir=/tmp/chrome-data-{os.getpid()}"
        ]
        
        with SB(uc=True, 
               headless=True,
               browser='chrome',
               chromium_arg=" ".join(chrome_options),
               xvfb=True) as sb:
            logging.info("Chrome version: " + sb.execute_script("return navigator.userAgent"))
            sb.get("about:blank")
        logging.info("Successfully initialized Selenium driver")
    except Exception as e:
        logging.error(f"Failed to initialize Selenium driver: {str(e)}")
        logging.error(f"Chrome binary path: {os.environ.get('CHROME_BIN')}")
        logging.error(f"ChromeDriver path: {os.environ.get('CHROME_DRIVER_PATH')}")
        raise

def scrape_imdb_list():
    """Scrape IMDB list using SeleniumBase"""
    all_items = []
    
    try:
        with SB(uc=True, headless=True) as sb:
            # Use sb instead of driver
            items = sb.find_elements("li.ipc-metadata-list-summary-item")
            
            for item in items:
                # Extract title, year, rating etc using sb
                title = sb.find_element("h3.ipc-title__text", by="css selector", element=item).text
                # ... other fields
                all_items.append({"title": title})
            
            # Check if there's more pages
            next_button = sb.find_element("button[aria-label='Next']")
            if "disabled" not in next_button.get_attribute("class"):
                next_button.click()
                sb.sleep(2)  # Wait for page load
                
    except Exception as e:
        logging.error(f"Error scraping IMDB list: {e}")
        
    return all_items

def main():
    ensure_data_directory_exists()
    init_database()
    init_selenium_driver()

    display_banner()
    display_ascii_art()

    print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")

    overseerr_url, api_key, requester_user_id = load_config()
    if not overseerr_url or not api_key or not requester_user_id:
        while True:
            if not overseerr_url or not api_key:
                overseerr_url = custom_input(color_gradient("\n🌐  Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
                api_key = custom_input(color_gradient("\n🔑  Enter your Overseerr API key: ", "#ffaa00", "#ff5500"))
            if not requester_user_id:
                try:
                    test_overseerr_api(overseerr_url, api_key)

                    requester_user_id = set_requester_user(overseerr_url, api_key)

                    save_config(overseerr_url, api_key, requester_user_id)

                    break
                except Exception as e:
                    print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000") + "\n")
                    logging.error(f"Error testing Overseerr API: {e}")
                    return

    # Prompt for sync configuration
    print(color_gradient("\n📋 Configure regular syncing:", "#00aaff", "#00ffaa"))
    print(color_gradient("1. Yes, configure sync interval in hours", "#ffaa00", "#ff5500"))
    print(color_gradient("2. No, run a one-time sync", "#ffaa00", "#ff5500"))
    sync_choice = custom_input(color_gradient("\nEnter your choice: ", "#ffaa00", "#ff5500"))

    if sync_choice == "1":
        configure_sync_interval()
    else:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_interval")
            conn.commit()

    sync_interval = load_sync_interval()

    while True:
        display_menu()
        choice = custom_input(color_gradient("Please select an option: ", "#ffaa00", "#ff5500"))

        if choice == "1":
            # Add New Lists
            add_new_lists()

        elif choice == "2":
            # Start Sync with Saved Lists
            start_sync(overseerr_url, api_key, requester_user_id, setup_logging())

        elif choice == "3":
            # One-Time List Sync
            one_time_list_sync(overseerr_url, api_key, requester_user_id, setup_logging())

        elif choice == "4":
            # Manage Existing Lists
            manage_lists()

        elif choice == "5":
            # Configure Sync Interval
            configure_sync_interval()
            sync_interval = load_sync_interval()

        elif choice == "6":
            # Run Dry Sync
            start_sync(overseerr_url, api_key, requester_user_id, setup_logging(), dry_run=True)

        elif choice == "7":
            # Exit
            print(color_gradient("Exiting the application. Goodbye! 👋", "#00aaff", "#00ffaa"))
            return

        else:
            print(color_gradient("\n❌  Invalid choice. Please select a valid option.", "#ff0000", "#aa0000"))

        if sync_interval:
            print(f'\n{color_gradient(f"😴  Sleeping for {sync_interval} hours. Press Ctrl + C to return to the main menu.", "#00aaff", "#00ffaa")}')
            try:
                for _ in range(sync_interval * 3600):
                    time.sleep(1)
                    if os.path.exists(f"{DATA_DIR}/interrupt.txt"):
                        os.remove(f"{DATA_DIR}/interrupt.txt")
                        raise KeyboardInterrupt()
                # Run sync after sleep
                start_sync(overseerr_url, api_key, requester_user_id, setup_logging())
            except KeyboardInterrupt:
                print(color_gradient("\nReturning to the main menu...", "#00aaff", "#00ffaa"))
                continue

if __name__ == "__main__":
    main()

# =======================================================================================================
# Soluify  |  You actually read it? Nice work, stay safe out there people!  |  {list-sync v0.5.3}
# =======================================================================================================