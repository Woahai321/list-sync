# =============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {list-sync v0.5.4}
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
import sys

import requests
from colorama import Style, init
from cryptography.fernet import Fernet
from halo import Halo
from seleniumbase import SB
from dotenv import load_dotenv

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Define paths for config and database
DATA_DIR = "./data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.enc")
DB_FILE = os.path.join(DATA_DIR, "list_sync.db")

<<<<<<< Updated upstream
=======
# Load environment variables if .env exists
if os.path.exists('.env'):
    load_dotenv()

>>>>>>> Stashed changes
class SyncResults:
    def __init__(self):
        self.start_time = time.time()
        self.not_found_items = []  # For #1
        self.error_items = []      # For #4
        self.media_type_counts = {"movie": 0, "tv": 0}  # For #5
        self.year_distribution = {
            "pre-1980": 0,
            "1980-1999": 0,
            "2000-2019": 0,
            "2020+": 0
        }  # For #8
        self.total_items = 0
        self.results = {
            "requested": 0,
            "already_requested": 0,
            "already_available": 0,
            "not_found": 0,
            "error": 0,
            "skipped": 0
        }

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
    file_handler = logging.FileHandler(os.path.join(DATA_DIR, "list_sync.log"), encoding='utf-8')
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
    ascii_art = r"""
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
    """Display the banner."""
    banner = """
<<<<<<< Updated upstream
    ==============================================================
             Soluify - {servarr-tools_list-sync_v0.5.4}
    ==============================================================
    """
    print(color_gradient(banner, "#aa00aa", "#00aa00") + Style.RESET_ALL)
=======
==============================================================
Soluify - {servarr-tools_list-sync_v0.5.4}
==============================================================
"""
    print(color_gradient(banner, "#00aaff", "#00ffaa"))
>>>>>>> Stashed changes

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
                base_url = list_id.rstrip('/')
            else:
                base_url = f"https://letterboxd.com/{list_id}"
            
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
                
                # If we found exactly 100 items, there might be more pages
                if items_count == 100:
                    page += 1
                    logging.info(f"Found exactly 100 items, trying page {page}")
                else:
                    logging.info(f"Found {items_count} items (< 100), must be the last page")
                    break
            
            print(color_gradient(f"✨  Found {len(media_items)} items from Letterboxd list!", "#00ff00", "#00aa00"))
            logging.info(f"Letterboxd list fetched successfully. Found {len(media_items)} items across {page} pages.")
            return media_items
        
    except Exception as e:
        print(color_gradient(f"💥  Failed to fetch Letterboxd list. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching Letterboxd list: {str(e)}")
        raise

def normalize_title(title: str) -> str:
    """Normalize a title for comparison by removing special characters and converting to lowercase."""
    # Remove special characters, keeping only alphanumeric and spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    # Convert to lowercase and remove extra spaces
    normalized = ' '.join(normalized.lower().split())
    return normalized
<<<<<<< Updated upstream
=======

def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate fuzzy match similarity between two titles."""
    # Convert to lowercase for comparison but keep articles
    t1 = title1.lower()
    t2 = title2.lower()
    
    # Calculate Levenshtein distance
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Get the Levenshtein distance
    distance = levenshtein(t1, t2)
    max_length = max(len(t1), len(t2))
    
    # Convert distance to similarity score (0 to 1)
    similarity = 1 - (distance / max_length)
    return similarity
>>>>>>> Stashed changes

def search_media_in_overseerr(overseerr_url, api_key, media_title, media_type, release_year=None):
    headers = {"X-Api-Key": api_key}
    overseerr_url = overseerr_url.rstrip('/')
    search_url = f"{overseerr_url}/api/v1/search"
    
    # Always search with just the title
    search_title = media_title
    
    page = 1
    best_match = None
    best_score = 0
    
    while True:
        try:
<<<<<<< Updated upstream
            encoded_query = requests.utils.quote(media_title)
            url = f"{search_url}?query={encoded_query}&page={page}&language=en"
            
            logging.debug(f"Searching for '{media_title}' (normalized: '{search_title_normalized}')")
=======
            encoded_query = requests.utils.quote(search_title)
            url = f"{search_url}?query={encoded_query}&page={page}&language=en"
            
            logging.debug(f"Searching for '{search_title}' (Year: {release_year})")
>>>>>>> Stashed changes
            response = requests.get(url, headers=headers, timeout=10)
            
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
<<<<<<< Updated upstream
                
                result_title_normalized = normalize_title(result_title)
                
                # Log all potential matches for debugging
                logging.debug(f"Comparing '{result_title}' (normalized: '{result_title_normalized}')")
                
                # Check for exact title match first
                if result_title_normalized == search_title_normalized:
                    logging.info(f"Found exact title match: '{result_title}'")
                    
                    # Get year if available
                    result_year = None
                    try:
                        if media_type == "movie" and "releaseDate" in result:
                            result_year = int(result["releaseDate"][:4])
                        elif media_type == "tv" and "firstAirDate" in result:
                            result_year = int(result["firstAirDate"][:4])
                    except (ValueError, TypeError):
                        pass
                    
                    # If we have a year to match against
                    if release_year and result_year:
                        year_diff = abs(result_year - release_year)
                        if year_diff < closest_year_diff:
                            closest_year_diff = year_diff
                            best_match = result
                            logging.info(f"Updated best match due to closer year: {result_title} ({result_year})")
                    elif not best_match:  # If no year to match against, take the first exact title match
                        best_match = result
                        logging.info(f"Taking first exact match: {result_title}")
                        break  # We found an exact title match, no need to keep searching
            
            if best_match or page >= search_results.get("totalPages", 1):
=======
                
                # Get year
                result_year = None
                try:
                    if media_type == "movie" and "releaseDate" in result:
                        result_year = int(result["releaseDate"][:4])
                    elif media_type == "tv" and "firstAirDate" in result:
                        result_year = int(result["firstAirDate"][:4])
                except (ValueError, TypeError):
                    pass
                
                # Calculate title similarity
                similarity = calculate_title_similarity(search_title, result_title)
                
                # Calculate final score
                score = similarity
                
                # Year matching
                if release_year and result_year:
                    if release_year == result_year:
                        score *= 2  # Double score for exact year match
                        logging.debug(f"Exact year match for '{result_title}' ({result_year}) - Base similarity: {similarity}")
                    elif abs(release_year - result_year) <= 1:
                        score *= 1.5  # 1.5x score for off-by-one year
                        logging.debug(f"Close year match for '{result_title}' ({result_year}) - Base similarity: {similarity}")
                
                logging.debug(f"Match candidate: '{result_title}' ({result_year}) - Score: {score}")
                
                # Update best match if we have a better score
                # For exact year matches, require a lower similarity threshold
                min_similarity = 0.5 if (release_year and result_year and release_year == result_year) else 0.7
                
                if score > best_score and similarity >= min_similarity:
                    best_score = score
                    best_match = result
                    logging.info(f"New best match: '{result_title}' ({result_year}) - Score: {score}")
            
            # Only continue to next page if we haven't found a good match
            if best_score > 1.5 or page >= search_results.get("totalPages", 1):
>>>>>>> Stashed changes
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
<<<<<<< Updated upstream
            logging.error(f'Error searching for "{media_title}": {str(e)}')
=======
            logging.error(f'Error searching for "{search_title}": {str(e)}')
>>>>>>> Stashed changes
            if "429" in str(e):
                time.sleep(5)
                continue
            raise

    if best_match:
        result_title = best_match.get("title") if media_type == "movie" else best_match.get("name")
        result_year = None
        try:
            if media_type == "movie" and "releaseDate" in best_match:
                result_year = best_match["releaseDate"][:4]
            elif media_type == "tv" and "firstAirDate" in best_match:
                result_year = best_match["firstAirDate"][:4]
        except (ValueError, TypeError):
            pass
        
<<<<<<< Updated upstream
        logging.info(f"Final match for '{media_title}': '{result_title}' ({result_year})")
=======
        logging.info(f"Final match for '{media_title}' ({release_year}): '{result_title}' ({result_year}) - Score: {best_score}")
>>>>>>> Stashed changes
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
    title = item.get('title', 'Unknown Title').strip()
    media_type = item.get('media_type', 'unknown')
    year = item.get('year')
    
<<<<<<< Updated upstream
    # Add year and media_type to the return data
    result = {
        "title": title,
=======
    # Strip any year from the title (e.g., "Cinderella 1997" -> "Cinderella")
    search_title = re.sub(r'\s*\(?(?:19|20)\d{2}\)?$', '', title).strip()
    
    # Add year and media_type to the return data
    result = {
        "title": title,  # Keep original title for display
>>>>>>> Stashed changes
        "year": year,
        "media_type": media_type,
        "error_message": None
    }

    if dry_run:
        result["status"] = "would_be_synced"
        return result

    try:
        search_result = search_media_in_overseerr(
            overseerr_url, 
            api_key, 
            search_title,  # Use cleaned title for search
            media_type,
            year
        )
        if search_result:
            overseerr_id = search_result["id"]
            
            # Check if we should skip this item based on last sync time
            if not should_sync_item(overseerr_id):
<<<<<<< Updated upstream
=======
                save_sync_result(title, media_type, None, overseerr_id, "skipped")
>>>>>>> Stashed changes
                return {"title": title, "status": "skipped", "year": year, "media_type": media_type}

            is_available, is_requested, number_of_seasons = confirm_media_status(overseerr_url, api_key, overseerr_id, search_result["mediaType"])
            
            if is_available:
<<<<<<< Updated upstream
                save_sync_result(title, media_type, None, None, "already_available")
                return {"title": title, "status": "already_available", "year": year, "media_type": media_type}
            elif is_requested:
                save_sync_result(title, media_type, None, None, "already_requested")
=======
                save_sync_result(title, media_type, None, overseerr_id, "already_available")
                return {"title": title, "status": "already_available", "year": year, "media_type": media_type}
            elif is_requested:
                save_sync_result(title, media_type, None, overseerr_id, "already_requested")
>>>>>>> Stashed changes
                return {"title": title, "status": "already_requested", "year": year, "media_type": media_type}
            else:
                if search_result["mediaType"] == 'tv':
                    request_status = request_tv_series_in_overseerr(overseerr_url, api_key, requester_user_id, overseerr_id, number_of_seasons)
                else:
                    request_status = request_media_in_overseerr(overseerr_url, api_key, requester_user_id, overseerr_id, search_result["mediaType"])
                
                if request_status == "success":
<<<<<<< Updated upstream
                    save_sync_result(title, media_type, None, None, "requested")
                    return {"title": title, "status": "requested", "year": year, "media_type": media_type}
                else:
                    save_sync_result(title, media_type, None, None, "request_failed")
=======
                    save_sync_result(title, media_type, None, overseerr_id, "requested")
                    return {"title": title, "status": "requested", "year": year, "media_type": media_type}
                else:
                    save_sync_result(title, media_type, None, overseerr_id, "request_failed")
>>>>>>> Stashed changes
                    return {"title": title, "status": "request_failed", "year": year, "media_type": media_type}
        else:
            save_sync_result(title, media_type, None, None, "not_found")
            return {"title": title, "status": "not_found", "year": year, "media_type": media_type}
    except Exception as e:
        result["status"] = "error"
        result["error_message"] = str(e)
        return result

<<<<<<< Updated upstream
    return result
=======
def sleep_with_countdown(seconds, overseerr_url, api_key, requester_user_id, setup_logging):
    """Sleep with countdown and handle keyboard interrupts for exit or sync."""
    import select
    import termios
    import tty
    
    def is_data():
        """Check if there's data waiting on stdin."""
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    
    def show_controls():
        """Display the available controls."""
        print(color_gradient("\n⌨️  Controls:", "#00aaff", "#00ffaa"))
        print(color_gradient("• Press Ctrl+C to exit", "#ffaa00", "#ff5500"))
        print(color_gradient("• Press 's' to sync now", "#ffaa00", "#ff5500"))
        print(color_gradient("• Press 'e' to edit lists", "#ffaa00", "#ff5500"))
    
    start_time = time.time()
    end_time = start_time + seconds
    
    # Show initial controls
    show_controls()
    
    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        while time.time() < end_time:
            remaining = end_time - time.time()
            print(f'\r{color_gradient(f"😴  Next sync in: {format_time_remaining(remaining)}", "#00aaff", "#00ffaa")}', end='', flush=True)
            
            # Check for interrupt.txt
            if os.path.exists(f"{DATA_DIR}/interrupt.txt"):
                os.remove(f"{DATA_DIR}/interrupt.txt")
                raise KeyboardInterrupt()
            
            # Check for keyboard input
            if is_data():
                c = sys.stdin.read(1)
                if c == 's':
                    # Restore terminal settings before printing
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    print(color_gradient("\n\n🔄 Running manual sync...", "#00ff00", "#00aa00"))
                    start_sync(overseerr_url, api_key, requester_user_id, setup_logging())
                    # Reset the timer
                    start_time = time.time()
                    end_time = start_time + seconds
                    # Show controls again after sync
                    show_controls()
                    # Set terminal back to raw mode
                    tty.setraw(sys.stdin.fileno())
                elif c == 'e':
                    # Restore terminal settings before editing
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    print(color_gradient("\n\n📝 Editing lists...", "#00ff00", "#00aa00"))
                    manage_lists()
                    # Reset the timer
                    start_time = time.time()
                    end_time = start_time + seconds
                    # Show controls again after editing
                    show_controls()
                    # Set terminal back to raw mode
                    tty.setraw(sys.stdin.fileno())
                elif c == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(color_gradient("\n\n👋 Exiting automated sync mode...", "#ffaa00", "#ff5500"))
        raise
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
>>>>>>> Stashed changes

def process_media(media_items: List[Dict[str, Any]], overseerr_url: str, api_key: str, requester_user_id: str, dry_run: bool = False):
    sync_results = SyncResults()
    sync_results.total_items = len(media_items)
    current_item = 0

    print(color_gradient(f"\n🎬  Processing {sync_results.total_items} media items...", "#00aaff", "#00ffaa") + "\n")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_media_item, item, overseerr_url, api_key, requester_user_id, dry_run): item for item in media_items}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            current_item += 1
            try:
                result = future.result()
                status = result["status"]
                sync_results.results[status] += 1
                
                # Track additional information
                if status == "not_found":
<<<<<<< Updated upstream
                    sync_results.not_found_items.append({
                        "title": result["title"],
                        "year": result["year"]
=======
                    # Ensure consistent title (year) format
                    title = result["title"].strip()
                    year = result["year"]
                    # Remove any existing year format first
                    if year:
                        title_with_year = f"{title} ({year})"
                    else:
                        title_with_year = title
                    sync_results.not_found_items.append({
                        "title": title_with_year,
                        "year": year
>>>>>>> Stashed changes
                    })
                elif status == "error":
                    sync_results.error_items.append({
                        "title": result["title"],
                        "error": result["error_message"]
                    })
                
                # Track media type counts
                if result["media_type"] in sync_results.media_type_counts:
                    sync_results.media_type_counts[result["media_type"]] += 1
                
                # Track year distribution
                if result["year"]:
                    year = int(result["year"])
                    if year < 1980:
                        sync_results.year_distribution["pre-1980"] += 1
                    elif year < 2000:
                        sync_results.year_distribution["1980-1999"] += 1
                    elif year < 2020:
                        sync_results.year_distribution["2000-2019"] += 1
                    else:
                        sync_results.year_distribution["2020+"] += 1

                # Add this status printing code:
                if dry_run:
                    print(color_gradient(f"🔍 {result['title']}: Would be synced ({current_item}/{sync_results.total_items})", "#ffaa00", "#ff5500") + "\n")
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
                    message = f"{result['title']}: {status_text} ({current_item}/{sync_results.total_items})"
                    print(f"{emoji} {color_gradient(message, start_color, end_color)}\n")

            except Exception as exc:
                sync_results.results["error"] += 1
                sync_results.error_items.append({
                    "title": item["title"],
                    "error": str(exc)
                })

    if not dry_run:
        display_summary(sync_results)

def display_summary(sync_results: SyncResults):
<<<<<<< Updated upstream
    processing_time = time.time() - sync_results.start_time
    total_items = sync_results.total_items or 1
    avg_time = processing_time / total_items if total_items > 0 else 0
    
    # Create box-drawing characters
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    
    def create_box(title: str, content: str, width: int) -> List[str]:
        lines = []
        lines.append(f"{TOP_LEFT}{HORIZONTAL * 2} {title} {HORIZONTAL * (width - len(title) - 4)}{TOP_RIGHT}")
        content_lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in content_lines:
            lines.append(f"{VERTICAL} {line:<{width-2}} {VERTICAL}")
        lines.append(f"{BOTTOM_LEFT}{HORIZONTAL * width}{BOTTOM_RIGHT}")
        return lines

    # Create header
    summary = "\n" + "─" * 50 + "\n"
    summary += "                 Sync Summary\n"
    summary += "─" * 50 + "\n\n"

    # Create boxes for different sections
    stats_box = create_box("Processing Stats", f"""
Total Items: {sync_results.total_items}
Total Time: {int(processing_time // 60)}m {int(processing_time % 60)}s
Avg Time: {avg_time:.1f}s/item""", 35)

    status_box = create_box("Status Summary", f"""
✅ Requested: {sync_results.results['requested']}
☑️  Available: {sync_results.results['already_available']}
📌 Already Requested: {sync_results.results['already_requested']}
⏭️  Skipped: {sync_results.results['skipped']}""", 35)

    media_box = create_box("Media Types", f"""
Movies: {sync_results.media_type_counts['movie']} ({sync_results.media_type_counts['movie']/total_items*100:.1f}%)
TV Shows: {sync_results.media_type_counts['tv']} ({sync_results.media_type_counts['tv']/total_items*100:.1f}%)""", 35)

    year_box = create_box("Year Distribution", f"""
Pre-1980: {sync_results.year_distribution['pre-1980']}
1980-1999: {sync_results.year_distribution['1980-1999']}
2000-2019: {sync_results.year_distribution['2000-2019']}
2020+: {sync_results.year_distribution['2020+']}""", 35)

    # Create not found items box with consistent year formatting
    not_found_items = []
    for item in sync_results.not_found_items:
        title = item['title']
        year = item.get('year')
        not_found_items.append(f"• {title}" + (f" ({year})" if year else ""))
    
    not_found_box = create_box(f"Not Found Items ({len(sync_results.not_found_items)})", 
                              "\n".join(not_found_items), 72)

    # Create error items box if there are any
    if sync_results.error_items:
        error_box = create_box("Errors", "\n".join(
            f"• {item['title']}: {item['error']}"
            for item in sync_results.error_items
        ), 72)
    else:
        error_box = []

    # Combine boxes horizontally and vertically
    # First row: Stats and Status
    max_lines = max(len(stats_box), len(status_box))
    while len(stats_box) < max_lines:
        stats_box.insert(-1, f"{VERTICAL} {' ' * 33} {VERTICAL}")
    while len(status_box) < max_lines:
        status_box.insert(-1, f"{VERTICAL} {' ' * 33} {VERTICAL}")

    for i in range(max_lines):
        summary += f"{stats_box[i]}  {status_box[i]}\n"
    summary += "\n"

    # Second row: Media Types and Year Distribution
    max_lines = max(len(media_box), len(year_box))
    while len(media_box) < max_lines:
        media_box.insert(-1, f"{VERTICAL} {' ' * 33} {VERTICAL}")
    while len(year_box) < max_lines:
        year_box.insert(-1, f"{VERTICAL} {' ' * 33} {VERTICAL}")

    for i in range(max_lines):
        summary += f"{media_box[i]}  {year_box[i]}\n"
    summary += "\n"

    # Third row: Not Found Items
    for line in not_found_box:
        summary += f"{line}\n"

    # Fourth row: Errors (if any)
    if error_box:
        for line in error_box:
            summary += f"{line}\n"

    print(color_gradient(summary, "#00aaff", "#00ffaa") + Style.RESET_ALL)
=======
    """Display sync results in a simple vertical format."""
    processing_time = time.time() - sync_results.start_time
    total_items = sync_results.total_items or 1
    avg_time_ms = (processing_time / total_items) * 1000  # Convert to milliseconds

    # Create header
    summary = "\n" + "-" * 62 + "\n"
    summary += "Soluify - List Sync Summary\n"
    summary += "-" * 62 + "\n\n"

    # Processing Stats
    summary += "Processing Stats\n"
    summary += "───────────────\n"
    summary += f"Total Items: {sync_results.total_items}\n"
    summary += f"Total Time: {int(processing_time // 60)}m {int(processing_time % 60)}s\n"
    summary += f"Avg Time: {avg_time_ms:.1f}ms/item\n\n"

    # Status Summary
    summary += "Status Summary\n"
    summary += "─────────────\n"
    summary += f"✅ Requested: {sync_results.results['requested']}\n"
    summary += f"☑️ Available: {sync_results.results['already_available']}\n"
    summary += f"📌 Already Requested: {sync_results.results['already_requested']}\n"
    summary += f"⏭️ Skipped: {sync_results.results['skipped']}\n\n"

    # Media Types
    summary += "Media Types\n"
    summary += "──────────\n"
    summary += f"Movies: {sync_results.media_type_counts['movie']} ({sync_results.media_type_counts['movie']/total_items*100:.1f}%)\n"
    summary += f"TV Shows: {sync_results.media_type_counts['tv']} ({sync_results.media_type_counts['tv']/total_items*100:.1f}%)\n\n"

    # Not Found Items (if any)
    if sync_results.not_found_items:
        summary += f"\nNot Found Items ({len(sync_results.not_found_items)})\n"
        summary += "───────────────\n"
        for item in sync_results.not_found_items:
            summary += f"• {item['title']}\n"

    print(color_gradient(summary, "#9400D3", "#00FF00") + Style.RESET_ALL)
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
        
        # Split by comma but preserve commas in URLs
        def smart_split(input_str):
            parts = []
            current = []
            in_url = False
            
            for char in input_str:
                if char == ',' and not in_url:
                    if current:
                        parts.append(''.join(current).strip())
                        current = []
                else:
                    if char == '?' or 'trakt.tv' in ''.join(current):
                        in_url = True
                    current.append(char)
            
            if current:
                parts.append(''.join(current).strip())
            
            return parts
        
        list_ids = smart_split(list_ids)
        
        for list_id in list_ids:
            try:
                # Determine list type and validate
                if list_id.startswith(('http://', 'https://')):
                    if 'imdb.com' in list_id:
                        list_type = "imdb"
                    elif 'trakt.tv' in list_id:
                        list_type = "trakt"
                        # Don't strip query parameters from Trakt URLs
                        list_id = list_id.strip()
                    elif 'letterboxd.com' in list_id and '/list/' in list_id:
                        list_type = "letterboxd"
                        list_id = list_id.rstrip('/')
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

=======
        add_list_to_sync()
>>>>>>> Stashed changes
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
        print(color_gradient("2. Add New List", "#ffaa00", "#ff5500"))
        print(color_gradient("3. Delete a List", "#ffaa00", "#ff5500"))
        print(color_gradient("4. Edit Lists", "#ffaa00", "#ff5500"))
        print(color_gradient("5. Return to Previous Menu", "#ffaa00", "#ff5500"))
        
        choice = custom_input(color_gradient("\nEnter your choice: ", "#ffaa00", "#ff5500"))
        
        if choice == "1":
            display_lists()
        elif choice == "2":
            add_list_to_sync()
        elif choice == "3":
            delete_list()
        elif choice == "4":
            edit_lists()
        elif choice == "5":
            break
        else:
            print(color_gradient("\n❌ Invalid choice. Please try again.", "#ff0000", "#aa0000"))

def add_list_to_sync():
    """Add a single list to sync."""
    list_id = custom_input(color_gradient("\n🎬  Enter List ID or URL: ", "#ffaa00", "#ff5500")).strip()
    
    try:
        # Check for IMDb URLs or chart IDs
        if list_id.startswith(('http://', 'https://')):
            if 'imdb.com' in list_id:
                list_type = "imdb"
            elif 'trakt.tv' in list_id:
                list_type = "trakt"
            elif 'letterboxd.com' in list_id and '/list/' in list_id:
                list_type = "letterboxd"
            else:
                print(color_gradient("\n❌  Invalid URL format. Must be IMDb, Trakt, or Letterboxd URL.", "#ff0000", "#aa0000"))
                return
        elif list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
            list_type = "imdb"
        elif list_id.startswith(('ls', 'ur')):
            list_type = "imdb"
        elif list_id.isdigit():
            list_type = "trakt"
        else:
            print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'.", "#ff0000", "#aa0000"))
            return

        # Confirm with user
        confirmation_message = f"Are you sure this {list_type.upper()} list is correct? (ID/URL: {list_id})"
        add_to_sync = custom_input(color_gradient(f"\n🚨  {confirmation_message} (y/n): ", "#ffaa00", "#ff5500")).lower()
        if add_to_sync == "y":
            save_list_id(list_id, list_type)
            print(color_gradient(f"\n✅  Added {list_type.upper()} list: {list_id}", "#00ff00", "#00aa00"))
    except Exception as e:
        print(color_gradient(f"\n❌  Error adding list: {str(e)}", "#ff0000", "#aa0000"))

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

def load_env_config():
    """Load configuration from environment variables."""
    url = os.getenv('OVERSEERR_URL')
    api_key = os.getenv('OVERSEERR_API_KEY')
    user_id = os.getenv('OVERSEERR_USER_ID')
    sync_interval = os.getenv('SYNC_INTERVAL')
    
    # Only return the config if all required variables are present
    if url and api_key:
        try:
            # Test the API connection
            test_overseerr_api(url, api_key)
            # If user_id not specified, use default
            if not user_id:
                user_id = "1"
            # If sync_interval not specified, default to 0 (interactive mode)
            if not sync_interval:
                sync_interval = "0"
            return url, api_key, user_id, int(sync_interval)
        except Exception as e:
            logging.error(f"Error testing Overseerr API with environment variables: {e}")
    return None, None, None, 0

def load_env_lists():
    """Load lists from environment variables."""
    lists_added = False
    
    # Clear existing lists first
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        conn.commit()
    
    # Process IMDB lists
    if imdb_lists := os.getenv('IMDB_LISTS'):
        for list_id in imdb_lists.split(','):
            if list_id.strip():
                save_list_id(list_id.strip(), "imdb")
                lists_added = True
    
    # Process Trakt lists
    if trakt_lists := os.getenv('TRAKT_LISTS'):
        for list_id in trakt_lists.split(','):
            if list_id.strip():
                save_list_id(list_id.strip(), "trakt")
                lists_added = True
    
    # Process Letterboxd lists
    if letterboxd_lists := os.getenv('LETTERBOXD_LISTS'):
        for list_id in letterboxd_lists.split(','):
            if list_id.strip():
                save_list_id(list_id.strip(), "letterboxd")
                lists_added = True
    
    return lists_added

def format_time_remaining(seconds):
    """Format seconds into hours, minutes, seconds."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{int(hours)}h {int(minutes)}m {int(secs)}s"

def main():
    ensure_data_directory_exists()
    init_database()
    init_selenium_driver()

    display_banner()
    display_ascii_art()

    # Try to load configuration from environment first
    overseerr_url, api_key, requester_user_id, sync_interval = load_env_config()
    
    # If environment config exists and is valid
    if overseerr_url and api_key and requester_user_id:
        print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")
        print(color_gradient("📝 Using configuration from environment variables", "#00aaff", "#00ffaa"))
        
        # Load lists from environment if available
        lists_loaded = load_env_lists()
        if lists_loaded:
            print(color_gradient("📋 Lists loaded from environment variables", "#00aaff", "#00ffaa"))
        
        # If sync interval is set, go straight to automated mode
        if sync_interval > 0:
            print(color_gradient(f"\n⚙️  Starting automated sync mode (interval: {sync_interval} hours)...", "#00aaff", "#00ffaa"))
            while True:
                try:
                    start_sync(overseerr_url, api_key, requester_user_id, setup_logging())
                    sleep_with_countdown(sync_interval * 3600, overseerr_url, api_key, requester_user_id, setup_logging)
                except KeyboardInterrupt:
                    print(color_gradient("\n👋 Exiting automated sync mode...", "#ffaa00", "#ff5500"))
                    return
    else:
        # Interactive setup and menu
        print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")
        
        # Load or create config
        overseerr_url, api_key, requester_user_id = load_config()
        if not all([overseerr_url, api_key, requester_user_id]):
            print(color_gradient("\n🔧 First-time setup required", "#ffaa00", "#ff5500"))
            overseerr_url = custom_input(color_gradient("\n🌐 Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
            api_key = custom_input(color_gradient("🔑 Enter your API key: ", "#ffaa00", "#ff5500"))
            requester_user_id = set_requester_user(overseerr_url, api_key)
            save_config(overseerr_url, api_key, requester_user_id)
        
        while True:
            display_menu()
            choice = custom_input(color_gradient("\nEnter your choice: ", "#ffaa00", "#ff5500"))
            
            try:
                if choice == "1":
                    add_new_lists()
                elif choice == "2":
                    start_sync(overseerr_url, api_key, requester_user_id, setup_logging())
                elif choice == "3":
                    one_time_list_sync(overseerr_url, api_key, requester_user_id, setup_logging())
                elif choice == "4":
                    manage_lists()
                elif choice == "5":
                    configure_sync_interval()
                    interval = load_sync_interval()
                    if interval > 0:
                        print(color_gradient(f"\n⚙️  Starting automated sync mode (interval: {interval} hours)...", "#00aaff", "#00ffaa"))
                        while True:
                            try:
                                start_sync(overseerr_url, api_key, requester_user_id, setup_logging())
                                sleep_with_countdown(interval * 3600, overseerr_url, api_key, requester_user_id, setup_logging)
                            except KeyboardInterrupt:
                                print(color_gradient("\n👋 Exiting automated sync mode...", "#ffaa00", "#ff5500"))
                                break
                elif choice == "6":
                    start_sync(overseerr_url, api_key, requester_user_id, setup_logging(), dry_run=True)
                elif choice == "7":
                    print(color_gradient("\n👋 Thanks for using ListSync!", "#00aaff", "#00ffaa"))
                    break
                else:
                    print(color_gradient("\n❌ Invalid choice. Please try again.", "#ff0000", "#aa0000"))
            except Exception as e:
                print(color_gradient(f"\n❌ Error: {str(e)}", "#ff0000", "#aa0000"))
                logging.error(f"Error in menu option {choice}: {str(e)}")
                continue

if __name__ == "__main__":
    main()

# =======================================================================================================
# Soluify  |  You actually read it? Nice work, stay safe out there people!  |  {list-sync v0.5.4}
# =======================================================================================================
