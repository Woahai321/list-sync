"""
Command-line interface for the ListSync application.
"""

import logging
from typing import List, Dict, Any, Callable

from ..database import save_list_id, delete_list, configure_sync_interval, load_list_ids
from ..utils.helpers import custom_input, color_gradient
from .display import display_manage_lists_menu, display_lists
from ..providers import get_provider


def validate_provider(list_type: str, list_id: str) -> bool:
    """
    Validate that a provider can successfully fetch data from a list.
    
    Args:
        list_type (str): Type of provider (imdb, trakt, tmdb, simkl, etc.)
        list_id (str): List ID or URL
        
    Returns:
        bool: True if provider can fetch data, False otherwise
    """
    try:
        # Get the provider function
        provider_func = get_provider(list_type)
        
        # Test the provider with a small sample (limit to 5 items for testing)
        print(color_gradient(f"🔍  Testing {list_type.upper()} provider with list: {list_id}", "#ffaa00", "#ff5500"))
        
        # Import the provider function and test it
        items = provider_func(list_id)
        
        if items and len(items) > 0:
            print(color_gradient(f"✅  Provider validation successful! Found {len(items)} items", "#00ff00", "#00aa00"))
            return True
        else:
            print(color_gradient(f"❌  Provider validation failed: No items found", "#ff0000", "#aa0000"))
            return False
            
    except Exception as e:
        print(color_gradient(f"❌  Provider validation failed: {str(e)}", "#ff0000", "#aa0000"))
        return False


def handle_menu_choice(
    choice: str, 
    overseerr_client,
    run_sync_func: Callable,
    load_list_ids_func: Callable,
    display_lists_func: Callable,
    handle_manage_lists_func: Callable
):
    """
    Handle the main menu choice.
    
    Args:
        choice (str): User's choice
        overseerr_client: Overseerr API client
        run_sync_func (Callable): Function to run sync
        load_list_ids_func (Callable): Function to load list IDs
        display_lists_func (Callable): Function to display lists
        handle_manage_lists_func (Callable): Function to handle manage lists menu
    """
    if choice == "1":
        # Add new lists
        add_new_lists()
    elif choice == "2":
        # Start sync with saved lists
        run_sync_func(overseerr_client)
    elif choice == "3":
        # One-time list sync
        one_time_list_sync(overseerr_client, run_sync_func)
    elif choice == "4":
        # Manage existing lists
        manage_lists()
    elif choice == "5":
        # Configure sync interval
        configure_sync_interval_menu()
    elif choice == "6":
        # Run dry sync
        run_sync_func(overseerr_client, dry_run=True)
    else:
        print(color_gradient("\n❌ Invalid choice. Please try again.", "#ff0000", "#aa0000"))


def add_new_lists():
    """Add new lists and start sync."""
    add_list_to_sync()


def add_list_to_sync():
    """
    Add new lists to sync. Handles multiple lists separated by commas.
    """
    print(color_gradient("\n📋  Supported Providers:", "#00aaff", "#00ffaa"))
    print(color_gradient("   • IMDb: ls123456, ur123456, or https://imdb.com/list/ls123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Trakt: 123456 or https://trakt.tv/lists/123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Letterboxd: username/listname or https://letterboxd.com/username/listname", "#ffaa00", "#ff5500"))
    print(color_gradient("   • MDBList: username/listname or https://mdblist.com/lists/username/listname", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Steven Lu: stevenlu or https://movies.stevenlu.com", "#ffaa00", "#ff5500"))
    print(color_gradient("   • TMDB: 123456 or https://themoviedb.org/list/123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Simkl: 123456 or https://simkl.com/5/list/123456", "#ffaa00", "#ff5500"))
    
    list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) or URL(s) (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
    list_ids = [id.strip() for id in list_ids.split(',')]
    
    for list_id in list_ids:
        if not list_id:  # Skip empty strings
            continue
            
        try:
            list_type = None
            
            # Check for URLs
            if list_id.startswith(('http://', 'https://')):
                if 'imdb.com' in list_id:
                    list_type = "imdb"
                elif 'trakt.tv' in list_id:
                    # Check if this is a special Trakt list
                    special_patterns = [
                        '/movies/trending', '/movies/streaming',
                        '/movies/anticipated', '/movies/popular', '/movies/favorited',
                        '/movies/watched', '/movies/boxoffice',
                        '/shows/trending', '/shows/streaming',
                        '/shows/anticipated', '/shows/popular', '/shows/favorited',
                        '/shows/watched'
                    ]
                    
                    is_special_list = False
                    for pattern in special_patterns:
                        if pattern in list_id:
                            is_special_list = True
                            break
                    
                    if is_special_list:
                        list_type = "trakt_special"
                    else:
                        list_type = "trakt"
                elif 'letterboxd.com' in list_id and '/list/' in list_id:
                    list_type = "letterboxd"
                elif 'mdblist.com/lists/' in list_id:
                    list_type = "mdblist"
                elif 'movies.stevenlu.com' in list_id or 's3.amazonaws.com/popular-movies' in list_id:
                    list_type = "stevenlu"
                    # For Steven Lu, we don't need the specific URL as there's only one list
                    list_id = "stevenlu" 
                elif 'themoviedb.org' in list_id and '/list/' in list_id:
                    list_type = "tmdb"
                elif 'simkl.com' in list_id and '/list/' in list_id:
                    list_type = "simkl"
                else:
                    print(color_gradient(f"\n❌  Invalid URL format for '{list_id}'. Must be IMDb, Trakt, Letterboxd, MDBList, Steven Lu, TMDB, or Simkl URL.", "#ff0000", "#aa0000"))
                    continue
            elif list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
                list_type = "imdb"
            elif list_id.startswith(('ls', 'ur')):
                list_type = "imdb"
            # Check for special Trakt list formats like "trending:movies"
            elif ':' in list_id:
                parts = list_id.split(':')
                if len(parts) == 2:
                    category, media_type = parts
                    if media_type.lower() in ['movies', 'movie', 'shows', 'show', 'tv']:
                        list_type = "trakt_special"
                    else:
                        print(color_gradient(f"\n❌  Invalid media type in special list format: {list_id}", "#ff0000", "#aa0000"))
                        continue
                else:
                    print(color_gradient(f"\n❌  Invalid special list format: {list_id}", "#ff0000", "#aa0000"))
                    continue
            # Handle TMDB list IDs (numeric, typically 4+ digits)
            elif list_id.isdigit() and len(list_id) >= 4:
                list_type = "tmdb"
            # Handle Simkl list IDs (numeric, typically 3+ digits)
            elif list_id.isdigit() and len(list_id) >= 3:
                list_type = "simkl"
            # Handle Trakt list IDs (numeric, typically 1-3 digits)
            elif list_id.isdigit():
                list_type = "trakt"
            # Check for MDBList in format username/listname
            elif list_id.count('/') == 1 and not list_id.startswith(('ls', 'ur')):
                list_type = "mdblist"
            # Handle Steven Lu keywords
            elif list_id.lower() in ['stevenlu', 'steven', 'steven-lu', 'stevenlu-movies', 'stevenlumovies']:
                list_type = "stevenlu"
                list_id = "stevenlu"  # Standardize the ID
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'.", "#ff0000", "#aa0000"))
                continue

            # Ensure we have a valid list_type before proceeding
            if list_type is None:
                print(color_gradient(f"\n❌  Could not determine list type for '{list_id}'.", "#ff0000", "#aa0000"))
                continue
            
            # Validate provider before saving
            if not validate_provider(list_type, list_id):
                print(color_gradient(f"\n❌  Skipping {list_type.upper()} list: {list_id} (validation failed)", "#ff0000", "#aa0000"))
                continue
                
            # Save list and show confirmation
            try:
                save_list_id(list_id, list_type)
                print(color_gradient(f"\n✅  Added {list_type.upper()} list: {list_id}", "#00ff00", "#00aa00"))
            except Exception as save_error:
                print(color_gradient(f"\n❌  Error saving list {list_id}: {str(save_error)}", "#ff0000", "#aa0000"))
                continue
            
        except Exception as e:
            print(color_gradient(f"\n❌  Error processing list '{list_id}': {str(e)}", "#ff0000", "#aa0000"))
            import traceback
            traceback.print_exc()  # This will help debug any hidden issues
            continue


def one_time_list_sync(overseerr_client, run_sync_func):
    """
    Perform a one-time list sync with provided list IDs.
    
    Args:
        overseerr_client: Overseerr API client
        run_sync_func: Function to run sync
    """
    print(color_gradient("\n📋  Supported Providers:", "#00aaff", "#00ffaa"))
    print(color_gradient("   • IMDb: ls123456, ur123456, or https://imdb.com/list/ls123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Trakt: 123456 or https://trakt.tv/lists/123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Letterboxd: username/listname or https://letterboxd.com/username/listname", "#ffaa00", "#ff5500"))
    print(color_gradient("   • MDBList: username/listname or https://mdblist.com/lists/username/listname", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Steven Lu: stevenlu or https://movies.stevenlu.com", "#ffaa00", "#ff5500"))
    print(color_gradient("   • TMDB: 123456 or https://themoviedb.org/list/123456", "#ffaa00", "#ff5500"))
    print(color_gradient("   • Simkl: 123456 or https://simkl.com/5/list/123456", "#ffaa00", "#ff5500"))
    
    list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) for one-time sync (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
    list_ids = [id.strip() for id in list_ids.split(',')]
    
    temp_lists = []  # Track temporarily added lists for cleanup
    
    for list_id in list_ids:
        try:
            # Check for URLs
            if list_id.startswith(('http://', 'https://')):
                if 'imdb.com' in list_id:
                    list_type = "imdb"
                elif 'trakt.tv' in list_id:
                    # Check if this is a special Trakt list
                    special_patterns = [
                        '/movies/trending', '/movies/streaming',
                        '/movies/anticipated', '/movies/popular', '/movies/favorited',
                        '/movies/watched', '/movies/boxoffice',
                        '/shows/trending', '/shows/streaming',
                        '/shows/anticipated', '/shows/popular', '/shows/favorited',
                        '/shows/watched'
                    ]
                    
                    is_special_list = False
                    for pattern in special_patterns:
                        if pattern in list_id:
                            is_special_list = True
                            break
                    
                    if is_special_list:
                        list_type = "trakt_special"
                    else:
                        list_type = "trakt"
                elif 'letterboxd.com' in list_id and '/list/' in list_id:
                    list_type = "letterboxd"
                elif 'mdblist.com/lists/' in list_id:
                    list_type = "mdblist"
                elif 'movies.stevenlu.com' in list_id or 's3.amazonaws.com/popular-movies' in list_id:
                    list_type = "stevenlu"
                    list_id = "stevenlu"
                elif 'themoviedb.org' in list_id and '/list/' in list_id:
                    list_type = "tmdb"
                elif 'simkl.com' in list_id and '/list/' in list_id:
                    list_type = "simkl"
                else:
                    print(color_gradient("\n❌  Invalid URL format. Must be IMDb, Trakt, Letterboxd, MDBList, Steven Lu, TMDB, or Simkl URL.", "#ff0000", "#aa0000"))
                    continue
            elif list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
                list_type = "imdb"
            # Check for IMDb list IDs
            elif list_id.startswith(('ls', 'ur')):
                list_type = "imdb"
            # Check for Trakt special list shortcuts
            elif ':' in list_id:
                parts = list_id.split(':')
                if len(parts) == 2:
                    list_type, media_type = parts
                    # Convert shorthand to URL (e.g., "trending:movies" -> "https://trakt.tv/movies/trending")
                    if media_type.lower() in ['movies', 'movie']:
                        list_type = "trakt_special"
                    elif media_type.lower() in ['shows', 'show', 'tv']:
                        list_type = "trakt_special"
                    else:
                        print(color_gradient(f"\n❌  Invalid media type in special list format: {list_id}", "#ff0000", "#aa0000"))
                        continue
                else:
                    print(color_gradient(f"\n❌  Invalid special list format: {list_id}", "#ff0000", "#aa0000"))
                    continue
            # Handle TMDB list IDs (numeric, typically 4+ digits)
            elif list_id.isdigit() and len(list_id) >= 4:
                list_type = "tmdb"
            # Handle Simkl list IDs (numeric, typically 3+ digits)
            elif list_id.isdigit() and len(list_id) >= 3:
                list_type = "simkl"
            # Check for Trakt IDs (numeric, typically 1-3 digits)
            elif list_id.isdigit():
                list_type = "trakt"
            # Check for MDBList in format username/listname
            elif list_id.count('/') == 1 and not list_id.startswith(('ls', 'ur')):
                list_type = "mdblist"
            # Handle 'stevenlu' as a keyword to fetch Steven Lu's list
            elif list_id.lower() in ['stevenlu', 'steven', 'steven-lu', 'stevenlu-movies', 'stevenlumovies']:
                list_type = "stevenlu"
                list_id = "stevenlu"
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. Skipping this ID.", "#ff0000", "#aa0000"))
                continue
            
            # Validate provider before saving
            if not validate_provider(list_type, list_id):
                print(color_gradient(f"\n❌  Skipping {list_type.upper()} list: {list_id} (validation failed)", "#ff0000", "#aa0000"))
                continue
            
            # Save the list temporarily
            save_list_id(list_id, list_type)
            temp_lists.append((list_type, list_id))
            print(color_gradient(f"\n✅  Added {list_type.upper()} list: {list_id}", "#00ff00", "#00aa00"))
            
        except Exception as e:
            print(color_gradient(f"\n❌  Error processing list {list_id}: {e}", "#ff0000", "#aa0000") + "\n")
            logging.error(f"Error processing list {list_id}: {e}")
            continue
    
    if temp_lists:
        # Run the sync
        try:
            run_sync_func(overseerr_client)
        except Exception as e:
            print(color_gradient(f"\n❌  Error during sync: {e}", "#ff0000", "#aa0000"))
            logging.error(f"Error during sync: {e}")
        
        # Ask if user wants to keep the lists for future use
        keep_lists = custom_input(color_gradient("\n💾  Save these lists for future syncs? (y/n): ", "#ffaa00", "#ff5500")).lower() == "y"
        
        if not keep_lists:
            # Remove temporary lists
            for list_type, list_id in temp_lists:
                delete_list(list_type, list_id)
            print(color_gradient("\n🗑️  Temporary lists removed.", "#ffaa00", "#ff5500"))
        else:
            print(color_gradient("\n✅  Lists saved for future syncs.", "#00ff00", "#00aa00"))
    else:
        print(color_gradient("\n❌  No valid lists were processed.", "#ff0000", "#aa0000"))


def manage_lists():
    """Manage lists menu."""
    while True:
        print(color_gradient("\n📋 Manage Lists:", "#00aaff", "#00ffaa"))
        print(color_gradient("1. View Lists", "#ffaa00", "#ff5500"))
        print(color_gradient("2. Add New List", "#ffaa00", "#ff5500"))
        print(color_gradient("3. Delete a List", "#ffaa00", "#ff5500"))
        print(color_gradient("4. Edit Lists", "#ffaa00", "#ff5500"))
        print(color_gradient("5. Return to Previous Menu", "#ffaa00", "#ff5500"))
        
        choice = custom_input(color_gradient("\nEnter your choice: ", "#ffaa00", "#ff5500"))
        
        if choice == "1":
            lists = load_list_ids()
            display_lists(lists)
        elif choice == "2":
            add_list_to_sync()
        elif choice == "3":
            delete_list_menu()
        elif choice == "4":
            edit_lists()
        elif choice == "5":
            break
        else:
            print(color_gradient("\n❌ Invalid choice. Please try again.", "#ff0000", "#aa0000"))


def delete_list_menu():
    """Delete a list from the database."""
    lists = load_list_ids()
    if not lists:
        print(color_gradient("\n❌ No lists found.", "#ff0000", "#aa0000"))
        return
    
    display_lists(lists)
    choice = custom_input(color_gradient("\nEnter the number of the list to delete (or 'c' to cancel): ", "#ffaa00", "#ff5500"))
    if choice.lower() == 'c':
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(lists):
            list_to_delete = lists[idx]
            success = delete_list(list_to_delete['type'], list_to_delete['id'])
            if success:
                print(color_gradient(f"\n✅ List {list_to_delete['type'].upper()}: {list_to_delete['id']} deleted.", "#00ff00", "#00aa00"))
            else:
                print(color_gradient(f"\n❌ Failed to delete list.", "#ff0000", "#aa0000"))
        else:
            print(color_gradient("\n❌ Invalid list number.", "#ff0000", "#aa0000"))
    except ValueError:
        print(color_gradient("\n❌ Invalid input. Please enter a number.", "#ff0000", "#aa0000"))


def edit_lists():
    """Edit existing lists."""
    lists = load_list_ids()
    if not lists:
        print(color_gradient("\n❌ No lists found to edit.", "#ff0000", "#aa0000"))
        return
        
    display_lists(lists)
    print(color_gradient("\nEnter new list IDs (or press Enter to keep the current ID):", "#00aaff", "#00ffaa"))
    updated_lists = []
    for list_info in lists:
        new_id = custom_input(color_gradient(f"{list_info['type'].upper()}: {list_info['id']} -> ", "#ffaa00", "#ff5500"))
        updated_lists.append({
            "type": list_info['type'],
            "id": new_id if new_id else list_info['id']
        })
    
    # Update database
    import sqlite3
    from ..database import DB_FILE
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        cursor.executemany(
            "INSERT INTO lists (list_type, list_id) VALUES (?, ?)",
            [(list_info['type'], list_info['id']) for list_info in updated_lists]
        )
        conn.commit()
    print(color_gradient("\n✅ Lists updated successfully.", "#00ff00", "#00aa00"))


def configure_sync_interval_menu():
    """Configure the sync interval."""
    print(color_gradient("\n💡  Recommendation: Minimum 1 hour interval (you can use 0.5 for 30 minutes)", "#ffaa00", "#ff5500"))
    interval = custom_input(color_gradient("\n🕒  How often do you want to sync your lists (in hours, e.g., 1, 0.5, 2.5)? ", "#ffaa00", "#ff5500"))
    try:
        interval_hours = float(interval)
        if interval_hours < 0.5:
            print(color_gradient("\n⚠️  Warning: Intervals less than 0.5 hours (30 minutes) are not recommended.", "#ffaa00", "#ff5500"))
            confirm = custom_input(color_gradient("Continue anyway? (y/n): ", "#ffaa00", "#ff5500")).lower()
            if confirm != 'y':
                return
        elif interval_hours < 1:
            print(color_gradient("\n⚠️  Warning: Intervals less than 1 hour may cause excessive API calls.", "#ffaa00", "#ff5500"))
        
        configure_sync_interval(interval_hours)
        # Format the display nicely
        if interval_hours == int(interval_hours):
            display_interval = f"{int(interval_hours)} hour{'s' if interval_hours != 1 else ''}"
        else:
            minutes = interval_hours * 60
            if minutes == int(minutes):
                display_interval = f"{int(minutes)} minutes"
            else:
                display_interval = f"{interval_hours} hours"
        print(f'\n{color_gradient(f"✅  Sync interval configured to {display_interval}.", "#00ff00", "#00aa00")}\n')
    except ValueError:
        print(color_gradient("\n❌ Please enter a valid number (e.g., 1, 0.5, 2.5).", "#ff0000", "#aa0000"))


