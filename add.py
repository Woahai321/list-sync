# =============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {list-sync v0.5.2}
# =============================================================================
#  __         _
# (_  _ |   .(_
# __)(_)||_||| \/
#              /
# © 2024
# -----------------------------------------------------------------------------
import base64
import getpass
import html
import json
import logging
import os
import sqlite3
import time
import readline
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from colorama import Style, init
from cryptography.fernet import Fernet
from halo import Halo

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
    logging.basicConfig(
        filename=os.path.join(DATA_DIR, "list_sync.log"),
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    added_logger = logging.getLogger("added_items")
    added_logger.setLevel(logging.INFO)
    added_handler = logging.FileHandler(os.path.join(DATA_DIR, "added.log"))
    added_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    added_logger.addHandler(added_handler)
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
             Soluify - {servarr-tools_list-sync_v0.5.2}
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

def save_config(overseerr_url, api_key):
    config = {"overseerr_url": overseerr_url, "api_key": api_key}
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
            return config["overseerr_url"], config["api_key"]
        except Exception:
            print(f'\n{color_gradient("❌  Incorrect password. Unable to decrypt config.", "#ff0000", "#aa0000")}')
            if custom_input("\n🗑️  Delete this config and start over? (y/n): ").lower() == "y":
                os.remove(CONFIG_FILE)
                print(f'\n{color_gradient("🔄  Config deleted. Rerun the script to set it up again.", "#ffaa00", "#ff5500")}\n')
            return None, None
    return None, None

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

def fetch_imdb_list(list_id):
    spinner = Halo(text=color_gradient("📚  Fetching IMDB list...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    try:
        if list_id.startswith("ls"):
            base_url = f"https://www.imdb.com/list/{list_id}/"
        elif list_id.startswith("ur"):
            base_url = f"https://www.imdb.com/user/{list_id}/watchlist/"
        else:
            raise ValueError("Invalid IMDb list ID format. It should start with 'ls' for lists or 'ur' for watchlists.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Fetch the initial page
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the list ID and key from the page
        script_tag = soup.find('script', id="__NEXT_DATA__")
        if not script_tag:
            raise ValueError("Unable to find necessary data on the page.")

        script_content = script_tag.string
        json_data = json.loads(script_content)

        list_id = json_data['props']['pageProps']['mainColumnData']['list']['id']
        list_key = json_data['props']['pageProps']['mainColumnData']['list']['name']['originalText']

        # Function to fetch items
        def fetch_items(page_number):
            ajax_url = f"https://www.imdb.com/tr/?ref_=ls_ip_fetch&pt=list&spt=main&const={list_id}&ht=actionOnly&pageAction=pagination-next"
            params = {
                "page": page_number
            }
            response = requests.get(ajax_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        media_items = []
        page_number = 1
        total_items = float('inf')

        while len(media_items) < total_items:
            data = fetch_items(page_number)
            if 'total' in data:
                total_items = data['total']
            
            for item in data['items']:
                title = item['titleText']['text']
                imdb_id = item['id']
                year = item['releaseYear']['year'] if 'releaseYear' in item else 'N/A'
                media_type = 'tv' if item['titleType']['id'] == 'tvSeries' else 'movie'
                
                media_items.append({
                    "title": title,
                    "imdb_id": imdb_id,
                    "media_type": media_type,
                    "year": year
                })
            
            page_number += 1
            time.sleep(1)  # Be respectful with rate limiting

        spinner.succeed(color_gradient(f"✨  Found {len(media_items)} items from IMDB list {list_id}!", "#00ff00", "#00aa00"))
        logging.info(f"IMDB list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items

    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch IMDB list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching IMDB list {list_id}: {str(e)}")
        raise

def fetch_trakt_list(list_id):
    base_url = f"https://trakt.tv/lists/{list_id}"
    headers = {"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    spinner = Halo(text=color_gradient("📚  Fetching Trakt list...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    
    try:
        # First request to get the final URL after redirection
        response = requests.get(base_url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        final_base_url = response.url.split('?')[0]  # Remove any query parameters
        logging.info(f"Final Trakt URL: {final_base_url}")

        media_items = []
        page = 1
        total_pages = 1  # Default to 1 page if we can't determine the total

        while True:
            url = f"{final_base_url}?page={page}&sort=added,asc"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check the total page count
            grid = soup.find("div", class_="row posters without-rank added")
            if grid and 'data-page-count' in grid.attrs:
                total_pages = int(grid['data-page-count'])
                logging.info(f"Total pages: {total_pages}")
            
            items = soup.find_all("div", class_="grid-item")
            
            if not items:
                # If no items found, we've reached the end
                break
            
            for item in items:
                title_element = item.find("h3", class_="ellipsify")
                if title_element:
                    title = title_element.text.strip()
                    media_type = "tv" if item.get("data-type") == "show" else item.get("data-type", "movie")
                    media_items.append({"title": title, "media_type": media_type})
            
            logging.info(f"Fetched {len(items)} items from page {page}")
            
            if page >= total_pages:
                # Check if there's a "next" link
                next_link = soup.find("a", rel="next")
                if not next_link:
                    break
            
            page += 1
        
        spinner.succeed(color_gradient(f"✨  Found {len(media_items)} items from Trakt list {list_id}!", "#00ff00", "#00aa00"))
        logging.info(f"Trakt list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items
    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch Trakt list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching Trakt list {list_id}: {str(e)}")
        raise

def search_media_in_overseerr(overseerr_url, api_key, media_title, media_type):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    search_url = f"{overseerr_url}/api/v1/search?query={quote(media_title)}"
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        search_results = response.json()
        logging.debug(f'Search response for "{media_title}": {json.dumps(search_results)}')

        for result in search_results.get("results", []):
            if (media_type in ["show", "tv"] and result["mediaType"] == "tv") or (result["mediaType"] == media_type):
                return {
                    "id": result["id"],
                    "mediaType": result["mediaType"],
                }
        logging.warning(f'No matching results found for "{media_title}" of type "{media_type}"')
        return None
    except Exception as e:
        logging.error(f'Error searching for {media_type} "{media_title}": {str(e)}')
        raise

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

        is_available_to_watch = status in [4, 5]
        is_requested = status in [2, 3]

        return is_available_to_watch, is_requested, number_of_seasons
    except Exception as e:
        logging.error(f"Error confirming status for {media_type} ID {media_id}: {str(e)}")
        raise

def request_media_in_overseerr(overseerr_url, api_key, media_id, media_type):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
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

def request_tv_series_in_overseerr(overseerr_url, api_key, tv_id, number_of_seasons):
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO lists (list_type, list_id) VALUES (?, ?)",
            (list_type, list_id)
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

def process_media_item(item: Dict[str, Any], overseerr_url: str, api_key: str, dry_run: bool) -> Dict[str, Any]:
    title = item.get('title', 'Unknown Title')
    media_type = item.get('media_type', 'unknown')
    imdb_id = item.get('imdb_id')

    if dry_run:
        return {"title": title, "status": "would_be_synced"}

    try:
        search_result = search_media_in_overseerr(overseerr_url, api_key, title, media_type)
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
                    request_status = request_tv_series_in_overseerr(overseerr_url, api_key, overseerr_id, number_of_seasons)
                else:
                    request_status = request_media_in_overseerr(overseerr_url, api_key, overseerr_id, search_result["mediaType"])
                
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

def process_media(media_items: List[Dict[str, Any]], overseerr_url: str, api_key: str, dry_run: bool = False):
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
        future_to_item = {executor.submit(process_media_item, item, overseerr_url, api_key, dry_run): item for item in media_items}
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

def start_sync(overseerr_url, api_key, added_logger, dry_run=False):
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
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error fetching list: {e}")
            continue

    process_media(media_items, overseerr_url, api_key, dry_run)

def add_new_lists():
    add_new_list = True
    while add_new_list:
        list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
        list_ids = [id.strip() for id in list_ids.split(',')]
        
        for list_id in list_ids:
            # Automatically detect list type
            if list_id.startswith(('ls', 'ur')):
                list_type = "imdb"
                confirmation_message = f"Are you sure the IMDb list ID '{list_id}' is correct?"
            elif list_id.isdigit():
                list_type = "trakt"
                confirmation_message = f"Are you sure the Trakt list ID '{list_id}' is correct?"
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. Skipping this ID.", "#ff0000", "#aa0000"))
                continue

            add_to_sync = custom_input(color_gradient(f"\n🚨  {confirmation_message} (y/n): ", "#ffaa00", "#ff5500")).lower()
            if add_to_sync == "y":
                save_list_id(list_id, list_type)

        more_lists = custom_input(color_gradient("\n🏁  Do you want to import any other lists? (y/n): ", "#ffaa00", "#ff5500")).lower()
        if more_lists != "y":
            add_new_list = False

    # Start sync immediately after adding new lists
    overseerr_url, api_key = load_config()
    if overseerr_url and api_key:
        start_sync(overseerr_url, api_key, setup_logging())

def one_time_list_sync(overseerr_url, api_key, added_logger):
    list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) for one-time sync (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
    list_ids = [id.strip() for id in list_ids.split(',')]
    
    media_items = []
    for list_id in list_ids:
        try:
            if list_id.startswith(('ls', 'ur')):
                media_items.extend(fetch_imdb_list(list_id))
            elif list_id.isdigit():
                media_items.extend(fetch_trakt_list(list_id))
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. Skipping this ID.", "#ff0000", "#aa0000"))
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list {list_id}: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error fetching list {list_id}: {e}")
    
    if media_items:
        process_media(media_items, overseerr_url, api_key)
    else:
        print(color_gradient("\n❌  No valid lists were processed.", "#ff0000", "#aa0000"))

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

def main():
    ensure_data_directory_exists()
    added_logger = setup_logging()
    init_database()

    display_banner()
    display_ascii_art()

    print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")

    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url = custom_input(color_gradient("\n🌐  Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
        api_key = custom_input(color_gradient("\n🔑  Enter your Overseerr API key: ", "#ffaa00", "#ff5500"))
        save_config(overseerr_url, api_key)

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
            start_sync(overseerr_url, api_key, added_logger)

        elif choice == "3":
            # One-Time List Sync
            one_time_list_sync(overseerr_url, api_key, added_logger)

        elif choice == "4":
            # Manage Existing Lists
            manage_lists()

        elif choice == "5":
            # Configure Sync Interval
            configure_sync_interval()
            sync_interval = load_sync_interval()

        elif choice == "6":
            # Run Dry Sync
            start_sync(overseerr_url, api_key, added_logger, dry_run=True)

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
                start_sync(overseerr_url, api_key, added_logger)
            except KeyboardInterrupt:
                print(color_gradient("\nReturning to the main menu...", "#00aaff", "#00ffaa"))
                continue

if __name__ == "__main__":
    main()

# =======================================================================================================
# Soluify  |  You actually read it? Nice work, stay safe out there people!  |  {list-sync v0.5.2}
# =======================================================================================================
