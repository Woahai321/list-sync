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


def get_tmdb_api_key() -> Optional[str]:
    """
    Get TMDB API Key from environment variables.
    
    Returns:
        Optional[str]: TMDB API Key if set, None otherwise
    """
    # Load environment variables if .env exists
    if os.path.exists('.env'):
        load_dotenv()
    
    api_key = os.getenv('TMDB_KEY')
    if api_key:
        import logging
        logging.info("TMDB API Key loaded from environment")
    else:
        import logging
        logging.warning("TMDB_KEY not set - TMDB will use web scraping fallback")
    
    return api_key


def get_tvdb_api_key() -> Optional[str]:
    """
    Get TVDB API Key from environment variables.
    
    Returns:
        Optional[str]: TVDB API Key if set, None otherwise
    """
    # Load environment variables if .env exists
    if os.path.exists('.env'):
        load_dotenv()
    
    api_key = os.getenv('TVDB_KEY')
    if api_key:
        import logging
        logging.info("TVDB API Key loaded from environment")
    else:
        import logging
        logging.warning("TVDB_KEY not set - TVDB will use web scraping fallback")
    
    return api_key


def load_env_config() -> Tuple[Optional[str], Optional[str], Optional[str], float, bool, bool]:
    """
    Load configuration from database or environment variables (database preferred).
    
    Returns:
        Tuple: Overseerr URL, API key, user ID, sync interval (float), automated mode flag, 4K flag
    """
    import logging
    
    # Try to load from database first (if ConfigManager available)
    try:
        config_manager = ConfigManager()
        
        # Get settings from database or environment
        url = config_manager.get_setting('overseerr_url')
        api_key = config_manager.get_setting('overseerr_api_key')
        user_id = config_manager.get_setting('overseerr_user_id', '1')
        
        sync_interval_val = config_manager.get_setting('sync_interval', '12')
        try:
            sync_interval = float(sync_interval_val)
        except:
            sync_interval = 12.0
        
        automated_mode_val = config_manager.get_setting('auto_sync', 'true')
        if isinstance(automated_mode_val, bool):
            automated_mode = automated_mode_val
        else:
            automated_mode = str(automated_mode_val).lower() == 'true'
        
        is_4k_val = config_manager.get_setting('overseerr_4k', 'false')
        if isinstance(is_4k_val, bool):
            is_4k = is_4k_val
        else:
            is_4k = str(is_4k_val).lower() == 'true'
        
        discord_webhook_url = config_manager.get_setting('discord_webhook')
        
        # Log if Discord webhook is configured
        if discord_webhook_url:
            logging.info("Discord webhook integration enabled")
        
        # Only return the config if required variables are present
        if url and api_key:
            try:
                # Test the API connection
                test_overseerr_api(url, api_key)
                logging.info("Configuration loaded from database")
                return url, api_key, user_id, sync_interval, automated_mode, is_4k
            except Exception as e:
                logging.error(f"Error testing Overseerr API with database config: {e}")
                print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000"))
        
        return None, None, None, 0.0, False, False
        
    except Exception as e:
        # Fallback to environment variables if database fails
        logging.debug(f"Could not load from database, falling back to environment: {e}")
        
        # Load environment variables if .env exists
        if os.path.exists('.env'):
            load_dotenv()
            
        url = os.getenv('OVERSEERR_URL')
        api_key = os.getenv('OVERSEERR_API_KEY')
        user_id = os.getenv('OVERSEERR_USER_ID', '1')
        sync_interval = os.getenv('SYNC_INTERVAL', '12')
        automated_mode = os.getenv('AUTOMATED_MODE', 'true').lower() == 'true'
        is_4k = os.getenv('OVERSEERR_4K', 'false').lower() == 'true'
        discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Log if Discord webhook is configured
        if discord_webhook_url:
            logging.info("Discord webhook integration enabled")
        
        # Only return the config if required variables are present
        if url and api_key:
            try:
                # Test the API connection
                test_overseerr_api(url, api_key)
                logging.info("Configuration loaded from environment variables")
                return url, api_key, user_id, float(sync_interval), automated_mode, is_4k
            except Exception as e:
                logging.error(f"Error testing Overseerr API with environment variables: {e}")
                print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000"))
        
        return None, None, None, 0.0, False, False

def load_env_lists() -> bool:
    """
    Load lists from database configuration or environment variables and add them to the database.
    Only adds new lists that don't already exist - preserves existing lists.
    
    Returns:
        bool: True if any new lists were added, False otherwise
    """
    from .database import save_list_id, load_list_ids, DB_FILE
    import logging
    
    lists_added = False
    
    try:
        # Try to use ConfigManager for settings
        try:
            config_manager = ConfigManager()
            get_list_setting = lambda key: config_manager.get_setting(key, '')
        except:
            # Fallback to environment if ConfigManager fails
            get_list_setting = lambda key: os.getenv(key.upper(), '')
        
        # Get existing lists from database to avoid duplicates
        existing_lists = load_list_ids()
        existing_set = {(list_info['type'], list_info['id']) for list_info in existing_lists}
        
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
        if imdb_lists := get_list_setting('imdb_lists'):
            for list_id in imdb_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "imdb")
        
        # Process Trakt lists
        if trakt_lists := get_list_setting('trakt_lists'):
            for list_id in trakt_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "trakt")
                    
        # Process special Trakt lists
        if trakt_special_lists := get_list_setting('trakt_special_lists'):
            for list_id in trakt_special_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "trakt_special")
                    if (("trakt_special", list_id.strip()) not in existing_set):
                        trakt_limit = get_list_setting('trakt_special_items_limit') or '20'
                        logging.info(f"Special Trakt list configured with max {trakt_limit} items")
        
        # Process Letterboxd lists
        if letterboxd_lists := get_list_setting('letterboxd_lists'):
            for list_id in letterboxd_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "letterboxd")
        
        # Process AniList lists
        if anilist_lists := get_list_setting('anilist_lists'):
            for list_id in anilist_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "anilist")
        
        # Process MDBList lists
        if mdblist_lists := get_list_setting('mdblist_lists'):
            for list_id in mdblist_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "mdblist")
        
        # Process Steven Lu lists
        if stevenlu_lists := get_list_setting('stevenlu_lists'):
            if 'stevenlu' in stevenlu_lists.lower():
                add_list_if_new("stevenlu", "stevenlu")
                if (("stevenlu", "stevenlu") not in existing_set):
                    logging.info("Steven Lu popular movies list configured")
        
        # Process TMDB lists
        if tmdb_lists := get_list_setting('tmdb_lists'):
            for list_id in tmdb_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "tmdb")
        
        # Process Simkl lists (API-only, requires authentication)
        simkl_client_id = get_list_setting('simkl_client_id')
        simkl_user_token = get_list_setting('simkl_user_token')
        simkl_lists = get_list_setting('simkl_lists')
        
        # Check for deprecated SIMKL_LISTS without API credentials
        if simkl_lists and not (simkl_client_id and simkl_user_token):
            logging.warning("SIMKL_LISTS is deprecated. SIMKL now uses API authentication.")
            logging.warning("Please set SIMKL_CLIENT_ID and SIMKL_USER_TOKEN instead.")
            logging.warning("Get credentials at: https://simkl.com/settings/developer/")
            logging.warning("SIMKL API only supports authenticated user watchlists, not custom public lists.")
        
        # Only process SIMKL if both credentials are provided
        if simkl_client_id and simkl_user_token:
            if simkl_lists:
                for list_id in simkl_lists.split(','):
                    if list_id.strip():
                        add_list_if_new(list_id.strip(), "simkl")
            else:
                # Default to authenticated user watchlist if no specific lists provided
                add_list_if_new("user_watchlist", "simkl")
                logging.info("SIMKL: Using authenticated user watchlist (no specific lists configured)")
        elif simkl_lists:
            logging.warning("SIMKL lists configured but missing API credentials. Skipping SIMKL provider.")
        
        # Process TVDB lists
        if tvdb_lists := get_list_setting('tvdb_lists'):
            for list_id in tvdb_lists.split(','):
                if list_id.strip():
                    add_list_if_new(list_id.strip(), "tvdb")
        
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


def is_masked_value(value: str) -> bool:
    """
    Check if a value is a masked placeholder (e.g., '****abc123').
    
    Masked values are used in the UI to hide sensitive information while
    still showing that a value exists. They start with 4+ asterisks.
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if value is a masked placeholder, False otherwise
    """
    if not value or not isinstance(value, str):
        return False
    return value.startswith('****') and len(value) >= 4


# ============================================================================
# ConfigManager - Database-Backed Configuration with .env Fallback
# ============================================================================

class ConfigManager:
    """
    Manages application configuration with priority:
    1. Database settings (if setup complete)
    2. Environment variables (.env file)
    3. Defaults
    
    Handles encryption/decryption of sensitive settings.
    """
    
    def __init__(self):
        """Initialize ConfigManager and load configuration."""
        from . import encryption
        from . import database
        
        self.encryption = encryption
        self.database = database
        self._cache = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from database or environment."""
        import logging
        
        # Check if .env file exists
        if os.path.exists('.env'):
            load_dotenv()
            logging.info("Loaded .env file")
        
        # Try to load from database first
        try:
            if self.database.count_settings() > 0:
                logging.info("Loading configuration from database")
                self._load_from_database()
            else:
                logging.info("No database configuration found, using environment variables")
                self._cache = {}
        except Exception as e:
            logging.warning(f"Error loading from database: {e}")
            self._cache = {}
    
    def _load_from_database(self):
        """Load all settings from database into cache."""
        import logging
        
        all_settings = self.database.get_all_settings()
        for key, (value, is_encrypted, setting_type) in all_settings.items():
            # Decrypt if needed
            if is_encrypted:
                try:
                    value = self.encryption.decrypt_value(value)
                except Exception as e:
                    logging.error(f"Failed to decrypt setting {key}: {e}")
                    value = ""
            
            # Convert type
            if setting_type == 'boolean':
                value = value.lower() in ('true', '1', 'yes')
            elif setting_type == 'integer':
                try:
                    value = int(value)
                except:
                    value = 0
            elif setting_type == 'float':
                try:
                    value = float(value)
                except:
                    value = 0.0
            
            self._cache[key] = value
    
    def get_setting(self, key: str, default: any = None) -> any:
        """
        Get a configuration setting.
        
        Priority:
        1. Database cache (if loaded)
        2. Environment variable
        3. Default value
        
        Args:
            key: Setting key name
            default: Default value if not found
        
        Returns:
            Setting value or default
        """
        # Try cache first (database settings)
        if key in self._cache:
            return self._cache[key]
        
        # Try environment variable
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value
        
        # Return default
        return default
    
    def save_setting(self, key: str, value: any, encrypt: bool = None):
        """
        Save a configuration setting to the database.
        
        Args:
            key: Setting key name
            value: Setting value
            encrypt: Whether to encrypt (auto-detects if None)
        """
        import logging
        
        # Auto-detect if should encrypt
        if encrypt is None:
            encrypt = self.encryption.should_encrypt(key)
        
        # Convert value to string
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
            setting_type = 'boolean'
        elif isinstance(value, int):
            str_value = str(value)
            setting_type = 'integer'
        elif isinstance(value, float):
            str_value = str(value)
            setting_type = 'float'
        else:
            str_value = str(value)
            setting_type = 'string'
        
        # CRITICAL FIX: Don't overwrite real values with masked placeholders
        # Masked values (****...) are displayed in the UI for security but should
        # never be saved back to the database as they would overwrite real API keys
        if encrypt and is_masked_value(str_value):
            logging.info(f"Skipping masked value for '{key}' (preserving existing encrypted value)")
            return  # Skip saving, keep existing value in database
        
        # Encrypt if needed
        if encrypt and str_value:
            try:
                str_value = self.encryption.encrypt_value(str_value)
            except Exception as e:
                logging.error(f"Failed to encrypt setting {key}: {e}")
                raise
        
        # Save to database
        self.database.save_setting(key, str_value, encrypt, setting_type)
        
        # Update cache
        self._cache[key] = value
        
        logging.info(f"Saved setting: {key} (encrypted: {encrypt})")
    
    def save_settings_batch(self, settings: dict):
        """
        Save multiple settings at once.
        
        Args:
            settings: Dictionary of {key: value}
        """
        for key, value in settings.items():
            self.save_setting(key, value)
    
    def is_setup_complete(self) -> bool:
        """Check if the initial setup wizard has been completed."""
        return self.database.is_setup_completed()
    
    def mark_setup_complete(self):
        """Mark setup as completed."""
        self.database.mark_setup_complete()
    
    def migrate_env_to_database(self) -> int:
        """
        Migrate all settings from environment variables to database.
        
        Returns:
            int: Number of settings migrated
        """
        import logging
        
        logging.info("Starting environment to database migration")
        
        settings_to_migrate = {
            # Overseerr
            'overseerr_url': os.getenv('OVERSEERR_URL', ''),
            'overseerr_api_key': os.getenv('OVERSEERR_API_KEY', ''),
            'overseerr_user_id': os.getenv('OVERSEERR_USER_ID', '1'),
            'overseerr_4k': os.getenv('OVERSEERR_4K', 'false').lower() == 'true',
            
            # Trakt
            'trakt_client_id': os.getenv('TRAKT_CLIENT_ID', ''),
            
            # Sync Settings
            'sync_interval': int(os.getenv('SYNC_INTERVAL', '24') or '24'),
            'auto_sync': os.getenv('AUTOMATED_MODE', 'true').lower() == 'true',
            'timezone': os.getenv('TZ', 'UTC'),
            
            # Notifications
            'discord_webhook': os.getenv('DISCORD_WEBHOOK_URL', ''),
            'discord_enabled': bool(os.getenv('DISCORD_WEBHOOK_URL', '')),
            
            # Service Endpoints
            'frontend_domain': os.getenv('FRONTEND_DOMAIN', 'http://localhost:3222'),
            'backend_domain': os.getenv('BACKEND_DOMAIN', 'http://localhost:4222'),
            'nuxt_public_api_url': os.getenv('NUXT_PUBLIC_API_URL', 'http://localhost:4222'),
            
            # Content Sources
            'imdb_lists': os.getenv('IMDB_LISTS', ''),
            'trakt_lists': os.getenv('TRAKT_LISTS', ''),
            'trakt_special_lists': os.getenv('TRAKT_SPECIAL_LISTS', ''),
            'trakt_special_items_limit': int(os.getenv('TRAKT_SPECIAL_ITEMS_LIMIT', '20') or '20'),
            'letterboxd_lists': os.getenv('LETTERBOXD_LISTS', ''),
            'anilist_lists': os.getenv('ANILIST_LISTS', ''),
            'mdblist_lists': os.getenv('MDBLIST_LISTS', ''),
            'stevenlu_lists': os.getenv('STEVENLU_LISTS', ''),
            'tmdb_key': os.getenv('TMDB_KEY', ''),
            'tmdb_lists': os.getenv('TMDB_LISTS', ''),
            'tvdb_lists': os.getenv('TVDB_LISTS', ''),
            'simkl_lists': os.getenv('SIMKL_LISTS', ''),
        }
        
        # Save all settings
        migrated_count = 0
        for key, value in settings_to_migrate.items():
            if value:  # Only save non-empty values
                try:
                    self.save_setting(key, value)
                    migrated_count += 1
                except Exception as e:
                    logging.error(f"Failed to migrate setting {key}: {e}")
        
        logging.info(f"Migration complete: {migrated_count} settings migrated to database")
        return migrated_count
    
    def has_env_config(self) -> bool:
        """Check if .env file exists and has basic configuration."""
        if not os.path.exists('.env'):
            return False
        
        load_dotenv()
        return bool(os.getenv('OVERSEERR_URL') and os.getenv('OVERSEERR_API_KEY'))
    
    def reload(self):
        """Reload configuration from database."""
        self._cache = {}
        self._load_config()
