"""
Display and UI components for ListSync.
"""

import time
from typing import Dict, List

from colorama import Style, init

from ..utils.helpers import color_gradient

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

class SyncResults:
    """Class to track sync operation results and statistics."""

    def __init__(self):
        self.start_time = time.time()
        self.not_found_items = []  # For #1
        self.error_items = []      # For #4
        self.media_type_counts = {"movie": 0, "tv": 0}  # For #5
        self.year_distribution = {
            "pre-1980": 0,
            "1980-1999": 0,
            "2000-2019": 0,
            "2020+": 0,
        }  # For #8
        self.total_items = 0
        self.synced_lists = []  # Track which lists were synced
        self.results = {
            "requested": 0,
            "already_requested": 0,
            "already_available": 0,
            "not_found": 0,
            "error": 0,
            "skipped": 0,
        }

    def __str__(self):
        """Return a string representation of the sync results."""
        processing_time = time.time() - self.start_time
        total_items = self.total_items or 1
        avg_time_ms = (processing_time / total_items) * 1000

        summary = "\n" + "-" * 62 + "\n"
        summary += "Soluify - List Sync Summary\n"
        summary += "-" * 62 + "\n\n"
        summary += "Processing Stats\n"
        summary += "───────────────\n"
        summary += f"Total Items: {self.total_items}\n"
        summary += f"Total Time: {int(processing_time // 60)}m {int(processing_time % 60)}s\n"
        summary += f"Avg Time: {avg_time_ms:.1f}ms/item\n\n"
        summary += "Results\n"
        summary += "─────────────\n"
        summary += f"✅ Requested: {self.results['requested']}\n"
        summary += f"☑️ Available: {self.results['already_available']}\n"
        summary += f"📌 Already Requested: {self.results['already_requested']}\n"
        summary += f"⏭️ Skipped: {self.results['skipped']}\n\n"
        summary += "Media Types\n"
        summary += "──────────\n"
        summary += f"Movies: {self.media_type_counts['movie']} ({self.media_type_counts['movie']/total_items*100:.1f}%)\n"
        summary += f"TV Shows: {self.media_type_counts['tv']} ({self.media_type_counts['tv']/total_items*100:.1f}%)\n\n"

        # Synced Lists section
        if self.synced_lists:
            summary += "Synced Lists\n"
            summary += "────────────\n"
            for list_info in self.synced_lists:
                list_type = list_info.get("type", "Unknown").upper()
                list_url = list_info.get("url", "No URL")
                summary += f"📋 {list_type}: {list_url}\n"
            summary += "\n"

        # Not Found Items (including both not found and error items)
        all_failed_items = []

        # Add not found items
        for item in self.not_found_items:
            all_failed_items.append(f"• {item['title']} (Not Found)")

        # Add error items
        for item in self.error_items:
            error_msg = item.get("error", "Unknown error")
            all_failed_items.append(f"• {item['title']} (Error: {error_msg})")

        if all_failed_items:
            summary += f"\nNot Found Items ({len(all_failed_items)})\n"
            summary += "───────────────\n"
            for item_line in all_failed_items:
                summary += f"{item_line}\n"

        return summary

def display_ascii_art():
    """Display the ASCII art splash screen."""
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
    """Display the application banner."""
    banner = """
==============================================================
Soluify - {servarr-tools_list-sync_v0.5.8}
==============================================================
"""
    print(color_gradient(banner, "#00aaff", "#00ffaa"))

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
    print(color_gradient(menu, "#00aaff", "#00ffaa") + Style.RESET_ALL)

def display_lists(lists: List[Dict[str, str]]):
    """Display a list of saved lists."""
    if not lists:
        print(color_gradient("\n❌ No lists found.", "#ff0000", "#aa0000"))
        return

    print(color_gradient("\nSaved Lists:", "#00aaff", "#00ffaa"))
    for idx, list_info in enumerate(lists, 1):
        print(color_gradient(f"{idx}. {list_info['type'].upper()}: {list_info['id']}", "#ffaa00", "#ff5500"))

def display_manage_lists_menu():
    """Display the manage lists submenu."""
    print(color_gradient("\n📋 Manage Lists:", "#00aaff", "#00ffaa"))
    print(color_gradient("1. View Lists", "#ffaa00", "#ff5500"))
    print(color_gradient("2. Add New List", "#ffaa00", "#ff5500"))
    print(color_gradient("3. Delete a List", "#ffaa00", "#ff5500"))
    print(color_gradient("4. Edit Lists", "#ffaa00", "#ff5500"))
    print(color_gradient("5. Return to Previous Menu", "#ffaa00", "#ff5500"))

def display_item_status(result: Dict, current_item: int, total_items: int, dry_run: bool = False):
    """Display the status of a processed item."""
    if dry_run:
        print(color_gradient(f"🔍 {result['title']}: Would be synced ({current_item}/{total_items})", "#ffaa00", "#ff5500") + "\n")
    else:
        status_info = {
            "requested": ("✅", "Successfully Requested", "#4CAF50", "#45a049"),
            "already_requested": ("📌", "Already Requested", "#2196F3", "#1E88E5"),
            "already_available": ("☑️ ", "Already Available", "#00BCD4", "#00ACC1"),
            "not_found": ("❓", "Not Found", "#FFC107", "#FFA000"),
            "error": ("❌", "Error", "#F44336", "#E53935"),
            "skipped": ("⏭️ ", "Skipped", "#9E9E9E", "#757575"),
        }.get(result["status"], ("➖", "Unknown Status", "#607D8B", "#546E7A"))

        emoji, status_text, start_color, end_color = status_info
        message = f"{result['title']}: {status_text} ({current_item}/{total_items})"
        print(f"{emoji} {color_gradient(message, start_color, end_color)}\n")

def display_summary(sync_results: SyncResults):
    """Display sync results in a formatted summary."""
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

    # Results Summary
    summary += "Results\n"
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

    # Synced Lists section
    if sync_results.synced_lists:
        summary += "Synced Lists\n"
        summary += "────────────\n"
        for list_info in sync_results.synced_lists:
            list_type = list_info.get("type", "Unknown").upper()
            list_url = list_info.get("url", "No URL")
            summary += f"📋 {list_type}: {list_url}\n"
        summary += "\n"

    # Not Found Items (including both not found and error items)
    all_failed_items = []

    # Add not found items
    for item in sync_results.not_found_items:
        all_failed_items.append(f"• {item['title']} (Not Found)")

    # Add error items
    for item in sync_results.error_items:
        error_msg = item.get("error", "Unknown error")
        all_failed_items.append(f"• {item['title']} (Error: {error_msg})")

    if all_failed_items:
        summary += f"\nNot Found Items ({len(all_failed_items)})\n"
        summary += "───────────────\n"
        for item_line in all_failed_items:
            summary += f"{item_line}\n"

    print(color_gradient(summary, "#9400D3", "#00FF00") + Style.RESET_ALL)

def display_welcome_message():
    """Display the welcome message."""
    print(color_gradient("👋  Welcome to the List to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")

def display_config_message(source: str):
    """Display configuration source message."""
    if source == "env":
        print(color_gradient("📝 Using configuration from environment variables", "#00aaff", "#00ffaa"))
    elif source == "dotenv":
        print(color_gradient("📝 Using configuration from .env file", "#00aaff", "#00ffaa"))
    elif source == "setup":
        print(color_gradient("\n🔧 First-time setup required", "#ffaa00", "#ff5500"))

def display_automated_mode_message(sync_interval: float):
    """Display automated mode startup message."""
    # Format the interval nicely
    if sync_interval == int(sync_interval):
        interval_text = f"{int(sync_interval)} hour{'s' if sync_interval != 1 else ''}"
    else:
        minutes = sync_interval * 60
        if minutes == int(minutes):
            interval_text = f"{int(minutes)} minutes"
        else:
            interval_text = f"{sync_interval} hours"

    print(color_gradient(f"\n⚙️  Starting automated sync mode (interval: {interval_text})...", "#00aaff", "#00ffaa"))

def display_lists_loaded_message():
    """Display message when lists are loaded from environment."""
    print(color_gradient("📋 Lists loaded from environment variables", "#00aaff", "#00ffaa"))

def display_exit_message():
    """Display exit message."""
    print("\n👋 Exiting. Goodbye!")

def display_error_message(message: str):
    """Display an error message."""
    print(color_gradient(f"\n❌ {message}", "#ff0000", "#aa0000"))

def display_success_message(message: str):
    """Display a success message."""
    print(color_gradient(f"\n✅ {message}", "#00ff00", "#00aa00"))

def display_warning_message(message: str):
    """Display a warning message."""
    print(color_gradient(f"\n⚠️ {message}", "#ffaa00", "#ff5500"))
