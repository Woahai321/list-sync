"""
Configuration management for ListSync.
"""

import base64
import getpass
import json
import os
import sqlite3
import time
from typing import Optional, Tuple

import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from halo import Halo

from .utils.helpers import custom_input, color_gradient
from .utils.logger import DATA_DIR

# Define paths for config and database
CONFIG_FILE = os.path.join(DATA_DIR, "config.enc")

def encrypt_config(data, password):
    """
    Encrypt configuration data with a password.
    
    Args:
        data (dict): Configuration data
        password (str): Encryption password
        
    Returns:
        bytes: Encrypted data
    """
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode())

def decrypt_config(encrypted_data, password):
    """
    Decrypt configuration data with a password.
    
    Args:
        encrypted_data (bytes): Encrypted configuration data
        password (str): Decryption password
        
    Returns:
        dict: Decrypted configuration data
    """
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode())

def save_config(overseerr_url, api_key, requester_user_id):
    """
    Save configuration to encrypted file.
    
    Args:
        overseerr_url (str): Overseerr URL
        api_key (str): API key
        requester_user_id (str): Requester user ID
    """
    config = {"overseerr_url": overseerr_url, "api_key": api_key, "requester_user_id": requester_user_id}
    print(color_gradient("🔐  Enter a password to encrypt your API details: ", "#ff0000", "#aa0000"), end="")
    password = getpass.getpass("")
    encrypted_config = encrypt_config(config, password)
    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted_config)
    print(f'\n{color_gradient("✅  Details encrypted. Remember your password!", "#00ff00", "#00aa00")}\n')

def load_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Load configuration from encrypted file.
    
    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: Overseerr URL, API key, and requester user ID
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "rb") as f:
            encrypted_config = f.read()
        
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            print()  # Ensure password prompt is on a new line
            password = getpass.getpass(color_gradient("🔑  Enter your password: ", "#ff0000", "#aa0000"))
            try:
                config = decrypt_config(encrypted_config, password)
                print()  # Add a newline after successful password entry
                return config["overseerr_url"], config["api_key"], config["requester_user_id"]
            except Exception:
                current_attempt += 1
                if current_attempt < max_attempts:
                    print(color_gradient("\n❌  Incorrect password. Please try again.", "#ff0000", "#aa0000"))
                else:
                    print(color_gradient("\n❌  Maximum password attempts reached.", "#ff0000", "#aa0000"))
                    if custom_input("\n🗑️  Delete this config and start over? (y/n): ").lower() == "y":
                        os.remove(CONFIG_FILE)
                        print(color_gradient("\n🔄  Config deleted. Rerun the script to set it up again.", "#ffaa00", "#ff5500") + "\n")
                    return None, None, None
    return None, None, None

def test_overseerr_api(overseerr_url, api_key):
    """Test Overseerr API connection."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    test_url = f"{overseerr_url}/api/v1/status"
    spinner = Halo(text=color_gradient("🔍  Testing API connection...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    try:
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        spinner.succeed(color_gradient("🎉  API connection successful!", "#00ff00", "#00aa00"))
        import logging
        logging.info("Overseerr API connection successful!")
    except Exception as e:
        spinner.fail(color_gradient(f"❌  Overseerr API connection failed. Error: {str(e)}", "#ff0000", "#aa0000"))
        import logging
        logging.error(f"Overseerr API connection failed. Error: {str(e)}")
        raise

def set_requester_user(overseerr_url, api_key):
    """Set the requester user for API requests."""
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

        import logging
        logging.info("Requester user set!")
        return requester_user_id
    except Exception as e:
        import logging
        logging.error(f"Overseerr API connection failed. Error: {str(e)}")
        return 1

def get_trakt_client_id() -> Optional[str]:
    """
    Get Trakt API Client ID from environment variables.
    
    Returns:
        Optional[str]: Trakt Client ID if set, None otherwise
    """
    # Load environment variables if .env exists
    if os.path.exists('.env'):
        load_dotenv()
    
    client_id = os.getenv('TRAKT_CLIENT_ID')
    if client_id:
        import logging
        logging.info("Trakt API Client ID loaded from environment")
    else:
        import logging
        logging.warning("TRAKT_CLIENT_ID not set - Trakt integration will not work")
    
    return client_id


def load_env_config() -> Tuple[Optional[str], Optional[str], Optional[str], float, bool, bool]:
    """
    Load configuration from environment variables.
    
    Returns:
        Tuple: Overseerr URL, API key, user ID, sync interval (float), automated mode flag, 4K flag
    """
    # Load environment variables if .env exists
    if os.path.exists('.env'):
        load_dotenv()
        
    url = os.getenv('OVERSEERR_URL')
    api_key = os.getenv('OVERSEERR_API_KEY')
    user_id = os.getenv('OVERSEERR_USER_ID', '1')  # Default to 1 if not set
    sync_interval = os.getenv('SYNC_INTERVAL', '12')  # Default to 12 if not set
    automated_mode = os.getenv('AUTOMATED_MODE', 'true').lower() == 'true'  # New env var
    is_4k = os.getenv('OVERSEERR_4K', 'false').lower() == 'true'  # New 4K setting
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # New webhook URL
    
    # Log if Discord webhook is configured
    if discord_webhook_url:
        import logging
        logging.info("Discord webhook integration enabled")
    
    # Only return the config if required variables are present
    if url and api_key:
        try:
            # Test the API connection
            test_overseerr_api(url, api_key)
            return url, api_key, user_id, float(sync_interval), automated_mode, is_4k
        except Exception as e:
            import logging
            logging.error(f"Error testing Overseerr API with environment variables: {e}")
            print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000"))
    return None, None, None, 0.0, False, False

def load_env_lists() -> bool:
    """
    Load lists from environment variables and add them to the database.
    Only adds new lists that don't already exist - preserves existing lists.
    
    Returns:
        bool: True if any new lists were added, False otherwise
    """
    from .database import save_list_id, load_list_ids, DB_FILE
    
    lists_added = False
    
    try:
        # Get existing lists from database to avoid duplicates
        existing_lists = load_list_ids()
        existing_set = {(list_info['type'], list_info['id']) for list_info in existing_lists}
        
        import logging
        logging.info(f"Found {len(existing_lists)} existing lists in database")
        
        # Helper function to add list if it doesn't exist
        def add_list_if_new(list_id: str, list_type: str):
            nonlocal lists_added
            if (list_type, list_id) not in existing_set:
                save_list_id(list_id, list_type)
                lists_added = True
                logging.info(f"Added new {list_type.upper()} list: {list_id}")
                print(f"✅ Added new {list_type.upper()} list: {list_id}")
            else:
                logging.info(f"Skipping existing {list_type.upper()} list: {list_id}")
        
        # Process IMDB lists
        if imdb_lists := os.getenv('IMDB_LISTS'):
            for list_id in imdb_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "imdb")
        
        # Process Trakt lists
        if trakt_lists := os.getenv('TRAKT_LISTS'):
            for list_id in trakt_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "trakt")
                    
        # Process special Trakt lists
        if trakt_special_lists := os.getenv('TRAKT_SPECIAL_LISTS'):
            for list_id in trakt_special_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "trakt_special")
                    if (("trakt_special", list_id.strip()) not in existing_set):
                        trakt_limit = os.getenv('TRAKT_SPECIAL_ITEMS_LIMIT', '20')
                        logging.info(f"Special Trakt list configured with max {trakt_limit} items")
        
        # Process Letterboxd lists
        if letterboxd_lists := os.getenv('LETTERBOXD_LISTS'):
            for list_id in letterboxd_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "letterboxd")
        
        # Process MDBList lists
        if mdblist_lists := os.getenv('MDBLIST_LISTS'):
            for list_id in mdblist_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "mdblist")
        
        # Process Steven Lu lists
        if stevenlu_lists := os.getenv('STEVENLU_LISTS'):
            if 'stevenlu' in stevenlu_lists.lower():
                add_list_if_new("stevenlu", "stevenlu")
                if (("stevenlu", "stevenlu") not in existing_set):
                    logging.info("Steven Lu popular movies list configured")
        
        if lists_added:
            logging.info(f"Environment sync complete: {len([l for l in existing_lists])} existing + {sum(1 for _ in [True for _ in range(len(load_list_ids()) - len(existing_lists))])} new lists")
            print(f"📊 Environment sync complete: preserved {len(existing_lists)} existing lists, added new lists")
        else:
            logging.info("No new lists found in environment variables (all existing lists preserved)")
            print("📊 No new lists to add from environment (all existing lists preserved)")
        
        return lists_added
    except Exception as e:
        import logging
        logging.error(f"Error loading lists from environment: {str(e)}")
        print(color_gradient(f"\n❌  Error loading lists: {str(e)}", "#ff0000", "#aa0000"))
        return False

def format_time_remaining(seconds):
    """Format seconds into hours, minutes, seconds."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{int(hours)}h {int(minutes)}m {int(secs)}s"
