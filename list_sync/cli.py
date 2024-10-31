# list_sync/cli.py

import os
import time
from .utils import color_gradient, custom_input
from .config import load_config, save_config
from .database import init_database, load_sync_interval, configure_sync_interval
from .lists import add_new_lists, one_time_list_sync, manage_lists, display_lists, delete_list, edit_lists
from .sync import process_media
from .overseerr import test_overseerr_api
from .utils import setup_logging

def display_banner():
    """Display the application banner."""
    banner = """
    ==============================================================
             Soluify - {servarr-tools_list-sync_v0.5.1}
    ==============================================================
    """
    print(color_gradient(banner, "#aa00aa", "#00aa00"))

def display_ascii_art():
    """Display ASCII art with a gradient effect."""
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
    print()

def display_menu():
    """Display the main menu."""
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
    print(color_gradient(menu, "#00aaff", "#00ffaa"))

def start_sync(overseerr_url, api_key, added_logger, dry_run=False):
    """Start the synchronization process."""
    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000"))
        return

    media_items = []
    for list_info in load_list_ids():
        try:
            if list_info['type'] == "imdb":
                media_items.extend(fetch_imdb_list(list_info['id']))
            elif list_info['type'] == "trakt":
                media_items.extend(fetch_trakt_list(list_info['id']))
        except Exception as e:
            print(color_gradient(f"\n❌  Error fetching list: {e}", "#ff0000", "#aa0000"))
            continue

    process_media(media_items, overseerr_url, api_key, dry_run)

def main():
    """Main function to run the CLI application."""
    init_database()
    added_logger = setup_logging()

    display_banner()
    display_ascii_art()

    print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")

    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url = custom_input(color_gradient("\n🌐  Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
        api_key = custom_input(color_gradient("\n🔑  Enter your Overseerr API key: ", "#ffaa00", "#ff5500"))
        save_config(overseerr_url, api_key)

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
            add_new_lists()

        elif choice == "2":
            start_sync(overseerr_url, api_key, added_logger)

        elif choice == "3":
            one_time_list_sync(overseerr_url, api_key, added_logger)

        elif choice == "4":
            manage_lists()

        elif choice == "5":
            configure_sync_interval()
            sync_interval = load_sync_interval()

        elif choice == "6":
            start_sync(overseerr_url, api_key, added_logger, dry_run=True)

        elif choice == "7":
            print(color_gradient("Exiting the application. Goodbye! 👋", "#00aaff", "#00ffaa"))
            return

        else:
            print(color_gradient("\n❌  Invalid choice. Please select a valid option.", "#ff0000", "#aa0000"))

        if sync_interval:
            print(f'\n{color_gradient(f"😴  Sleeping for {sync_interval} hours. Press Ctrl + C to return to the main menu.", "#00aaff", "#00ffaa")}')
            try:
                for _ in range(sync_interval * 3600):
                    time.sleep(1)
                start_sync(overseerr_url, api_key, added_logger)
            except KeyboardInterrupt:
                print(color_gradient("\nReturning to the main menu...", "#00aaff", "#00ffaa"))
                continue
