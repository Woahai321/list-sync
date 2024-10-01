# =============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {list-sync v0.4.3}
# =============================================================================
#  __         _
# (_  _ |   .(_
# __)(_)||_||| \/
#              /
# © 2024 Soluify LLC
# -----------------------------------------------------------------------------
import base64
import getpass
import html
import json
import logging
import os
import time
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from colorama import Style, init
from cryptography.fernet import Fernet
from halo import Halo

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Define paths for config, list ids, and sync interval files
DATA_DIR = "./data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.enc")
LIST_IDS_FILE = os.path.join(DATA_DIR, "list_ids.txt")
SYNC_INTERVAL_FILE = os.path.join(DATA_DIR, "sync_interval.txt")

def ensure_data_directory_exists():
    os.makedirs(DATA_DIR, exist_ok=True)

def setup_logging():
    logging.basicConfig(
        filename=os.path.join(DATA_DIR, "overseerr_sync.log"),
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    added_logger = logging.getLogger("added_items")
    added_logger.setLevel(logging.INFO)
    added_handler = logging.FileHandler(os.path.join(DATA_DIR, "added.log"))
    added_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    added_logger.addHandler(added_handler)
    return added_logger

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
             Soluify - {servarr-tools_list-sync_v0.4.3}
    ==============================================================
    """
    print(color_gradient(banner, "#aa00aa", "#00aa00") + Style.RESET_ALL)

def display_summary(
    total_items, requested_items, already_requested_items,
    already_available_items, not_found_items, failed_items, already_checked_items
):
    summary = f"""
==============================================================
                    All done! Here's the Summary!
==============================================================
🔁 Total Items Processed: {total_items}

☑️  Items Already Available: {already_available_items}

✅ Items Successfully Requested: {requested_items}

📌 Items Already Requested: {already_requested_items}

✔️  Items Already Checked: {already_checked_items}

❓ Items Not Found: {not_found_items}

❌ Items Failed: {failed_items}
==============================================================
"""
    print(color_gradient(summary, "#00aaff", "#00ffaa") + Style.RESET_ALL)

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
        password = getpass.getpass(color_gradient("🔑  Enter your password: ", "#ff0000", "#aa0000"))
        try:
            config = decrypt_config(encrypted_config, password)
            return config["overseerr_url"], config["api_key"]
        except Exception:
            print(f'\n{color_gradient("❌  Incorrect password. Unable to decrypt config.", "#ff0000", "#aa0000")}')
            if input("\n🗑️  Delete this config and start over? (y/n): ").lower() == "y":
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
            url = f"https://www.imdb.com/list/{list_id}"
        elif list_id.startswith("ur"):
            url = f"https://www.imdb.com/user/{list_id}/watchlist"
        else:
            raise ValueError("Invalid IMDb list ID format. It should start with 'ls' for lists or 'ur' for watchlists.")
        
        headers = {"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        script_tag = soup.find("script", {"type": "application/ld+json"})
        
        if script_tag:
            ld_json = json.loads(script_tag.string)
        else:
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            if not script_tag:
                raise ValueError("Could not find ld+json or __NEXT_DATA__ script tag in the IMDb page")
            next_data = json.loads(script_tag.string)
            ld_json = next_data["props"]["pageProps"]["mainColumnData"]["predefinedList"]["titleListItemSearch"]
        
        media_items = []
        
        if "itemListElement" in ld_json:
            for row in ld_json["itemListElement"]:
                item = row["item"]
                media_items.append({
                    "title": html.unescape(item["name"]),
                    "imdb_id": item["url"].split("/")[-2],
                    "media_type": "tv" if item["@type"] == "TVSeries" else "movie"
                })
        elif "edges" in ld_json:
            for row in ld_json["edges"]:
                item = row["listItem"]
                media_items.append({
                    "title": html.unescape(item["titleText"]["text"]),
                    "imdb_id": item["id"],
                    "media_type": "tv" if item["titleType"]["id"] == "tvSeries" else "movie"
                })
        
        spinner.succeed(color_gradient(f"✨  Found {len(media_items)} items from IMDB list {list_id}!", "#00ff00", "#00aa00"))
        logging.info(f"IMDB list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items
    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch IMDB list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching IMDB list {list_id}: {str(e)}")
        raise

def fetch_trakt_list(list_id):
    url = f"https://trakt.tv/lists/{list_id}"
    headers = {"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0"}
    
    spinner = Halo(text=color_gradient("📚  Fetching Trakt list...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    
    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        final_url = response.url
        logging.info(f"Final Trakt URL: {final_url}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        items = soup.find_all("div", class_="grid-item")
        
        media_items = []
        for item in items:
            title_element = item.find("h3", class_="ellipsify")
            if title_element:
                title = title_element.text.strip()
                media_type = "tv" if item.get("data-type") == "show" else item.get("data-type", "unknown")
                media_items.append({"title": title, "media_type": media_type})
        
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

def save_list_id(list_id, list_type):
    with open(LIST_IDS_FILE, "a") as f:
        f.write(f"{list_type}:{list_id}\n")

def load_list_ids():
    if os.path.exists(LIST_IDS_FILE):
        with open(LIST_IDS_FILE, "r") as f:
            return [line.strip().split(":") for line in f.readlines() if ":" in line]
    return []

def configure_sync_interval():
    interval = input(color_gradient("\n🕒  How often do you want to sync your lists (in hours)? ", "#ffaa00", "#ff5500"))
    with open(SYNC_INTERVAL_FILE, "w") as f:
        f.write(interval)
    print(f'\n{color_gradient("✅  Sync interval configured.", "#00ff00", "#00aa00")}\n')

def load_sync_interval():
    if os.path.exists(SYNC_INTERVAL_FILE):
        with open(SYNC_INTERVAL_FILE, "r") as f:
            return int(f.read().strip())
    return None

def process_media(media_items, overseerr_url, api_key, added_logger):
    total_items = len(media_items)
    requested_items = 0
    already_requested_items = 0
    already_available_items = 0
    failed_items = 0
    not_found_items = 0
    already_checked_items = 0

    processed_items = set()

    print(color_gradient(f"\n🎬  Processing {total_items} media items...", "#00aaff", "#00ffaa") + "\n")
    
    for idx, item in enumerate(media_items, 1):
        title = item.get('title', 'Unknown Title')
        media_type = item.get('media_type', 'unknown')
        unique_id = item.get('imdb_id', title)

        if unique_id in processed_items:
            item_status = f"{idx}/{total_items} {title}: Already checked ✔️"
            print(color_gradient(item_status, "#aaaaaa", "#00ff00"))
            logging.info(f'Item already checked: {title}')
            already_checked_items += 1
            continue
        
        processed_items.add(unique_id)

        item_status = f"{idx}/{total_items} {title}: Processing..."
        print(color_gradient(item_status, "#ffaa00", "#ff5500"), end="\r")
        logging.info(f'Processing item {idx}/{total_items}: {title} (Type: {media_type})')
        
        try:
            search_result = search_media_in_overseerr(overseerr_url, api_key, title, media_type)
            if search_result:
                is_available, is_requested, number_of_seasons = confirm_media_status(overseerr_url, api_key, search_result["id"], search_result["mediaType"])
                
                if is_available:
                    item_status = f"{idx}/{total_items} {title}: Already available ☑️"
                    print(color_gradient(item_status, "#aaaaaa", "#00ff00"))
                    logging.info(f'Item already available: {title}')
                    already_available_items += 1
                elif is_requested:
                    item_status = f"{idx}/{total_items} {title}: Already requested 📌"
                    print(color_gradient(item_status, "#aaaaaa", "#ffff00"))
                    logging.info(f'Item already requested: {title}')
                    already_requested_items += 1
                else:
                    if search_result["mediaType"] == 'tv':
                        request_status = request_tv_series_in_overseerr(overseerr_url, api_key, search_result["id"], number_of_seasons)
                    else:
                        request_status = request_media_in_overseerr(overseerr_url, api_key, search_result["id"], search_result["mediaType"])
                    
                    if request_status == "success":
                        item_status = f"{idx}/{total_items} {title}: Successfully requested ✅"
                        print(color_gradient(item_status, "#00ff00", "#00aa00"))
                        logging.info(f'Requested item: {title}')
                        added_logger.info(f'Requested: {title} (IMDB ID: {item.get("imdb_id", "N/A")})')
                        requested_items += 1
                    else:
                        item_status = f"{idx}/{total_items} {title}: Failed to request ❌"
                        print(color_gradient(item_status, "#ff0000", "#aa0000"))
                        logging.error(f'Failed to request item: {title}')
                        failed_items += 1
            else:
                item_status = f"{idx}/{total_items} {title}: Not found ❓"
                print(color_gradient(item_status, "#ff0000", "#aa0000"))
                logging.error(f'Item not found in Overseerr: {title}')
                not_found_items += 1
        except Exception as e:
            item_status = f"{idx}/{total_items} {title}: Error processing ❌"
            print(color_gradient(item_status, "#ff0000", "#aa0000"))
            logging.error(f'Error processing item {title}: {str(e)}')
            failed_items += 1
        
        time.sleep(0.1)  # Rate limiting

    display_summary(
        total_items,
        requested_items,
        already_requested_items,
        already_available_items,
        not_found_items,
        failed_items,
        already_checked_items
    )

def display_menu():
    menu = """
==============================================================
                    🛠️  Soluify - List Sync Tool 🛠️
==============================================================
1. 🔄 Start Sync with Saved Lists 🔄
2. ➕ Add New Lists ➕
3. ⏰ Configure Sync Interval ⏰
4. ❌ Exit ❌
==============================================================
"""
    print(color_gradient(menu, "#00aaff", "#00ffaa") + Style.RESET_ALL)

def start_sync(overseerr_url, api_key, added_logger):
    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000") + "\n")
        logging.error(f"Error testing Overseerr API: {e}")
        return

    media_items = []
    for list_type, list_id in load_list_ids():
        try:
            if list_type == "imdb":
                media_items.extend(fetch_imdb_list(list_id))
            elif list_type == "trakt":
                media_items.extend(fetch_trakt_list(list_id))
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error fetching list: {e}")
            continue

    process_media(media_items, overseerr_url, api_key, added_logger)

def add_new_lists():
    add_new_list = True
    while add_new_list:
        source = input(color_gradient("\n🍿  Are you importing from 'i'mbd or 't'rakt? (i/t): ", "#ffaa00", "#ff5500")).lower()

        if source == "i":
            imdb_list_id = input(color_gradient("\n🎬  Enter IMDB List ID (e.g., ls012345678): ", "#ffaa00", "#ff5500"))
            imdb_list_ids = []
            for item in imdb_list_id.split(","):
                item = item.strip()
                if "imdb.com/list/" in item:
                    imdb_list_ids.append(urlparse(item).path.split("/")[2])
                else:
                    imdb_list_ids.append(item)

            for list_id in imdb_list_ids:
                add_to_sync = input(color_gradient(f"\n🚨  Are you sure {list_id} is correct? (y/n): ", "#ffaa00", "#ff5500")).lower()
                if add_to_sync == "y":
                    save_list_id(list_id, "imdb")

        elif source == "t":
            trakt_list_id = input(color_gradient("\n🎬  Enter Trakt List ID (e.g., 20492796): ", "#ffaa00", "#ff5500"))
            trakt_list_ids = []
            for item in trakt_list_id.split(","):
                item = item.strip()
                if "trakt.tv/lists/" in item:
                    trakt_list_ids.append(urlparse(item).path.split("/")[2])
                else:
                    trakt_list_ids.append(item)

            for list_id in trakt_list_ids:
                add_to_sync = input(color_gradient(f"\n🚨  Are you sure {list_id} is correct? (y/n): ", "#ffaa00", "#ff5500")).lower()
                if add_to_sync == "y":
                    save_list_id(list_id, "trakt")

        else:
            print(color_gradient("\n❌  Invalid choice. Please enter 'i' for IMDb or 't' for Trakt.", "#ff0000", "#aa0000"))
            continue

        more_lists = input(color_gradient("\n🏁  Do you want to import any other lists? (y/n): ", "#ffaa00", "#ff5500")).lower()
        if more_lists != "y":
            add_new_list = False

def main():
    ensure_data_directory_exists()
    added_logger = setup_logging()

    display_banner()
    display_ascii_art()

    print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")

    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url = input(color_gradient("\n🌐  Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
        api_key = input(color_gradient("\n🔑  Enter your Overseerr API key: ", "#ffaa00", "#ff5500"))
        save_config(overseerr_url, api_key)

    sync_interval = load_sync_interval()
    if sync_interval:
        print(f'\n{color_gradient(f"🔄  Syncing every {sync_interval} hours.", "#00aaff", "#00ffaa")}')

    while True:
        display_menu()
        choice = input(color_gradient("Please select an option: ", "#ffaa00", "#ff5500"))

        if choice == "1":
            # Start Sync with Saved Lists
            start_sync(overseerr_url, api_key, added_logger)

        elif choice == "2":
            # Add New Lists
            add_new_lists()
            # Start sync immediately after adding new lists
            start_sync(overseerr_url, api_key, added_logger)

        elif choice == "3":
            # Configure Sync Interval
            configure_sync_interval()
            sync_interval = load_sync_interval()

        elif choice == "4":
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
                        raise KeyboardInterrupt()
            except KeyboardInterrupt:
                print(color_gradient("\nReturning to the main menu...", "#00aaff", "#00ffaa"))
                continue

if __name__ == "__main__":
    main()

# =======================================================================================================
# Soluify  |  You actually read it? Nice work, stay safe out there people!  |  {list-sync v0.4.3}
# =======================================================================================================
