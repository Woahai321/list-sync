"""
Main entry point for the List-Sync application.
"""

import datetime
import logging
import os
import re
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

from .api.overseerr import OverseerrClient
from .config import (
    load_config, load_env_config, load_env_lists, save_config,
    CONFIG_FILE
)
from .database import (
    init_database, load_list_ids, save_list_id, delete_list,
    load_sync_interval, configure_sync_interval, should_sync_item,
    save_sync_result, update_list_item_count, update_list_sync_info, DB_FILE
)
from .notifications.discord import send_to_discord_webhook
from .providers import get_provider, get_available_providers
from .ui.cli import handle_menu_choice, manage_lists
from .ui.display import (
    display_ascii_art, display_banner, display_menu, display_lists,
    display_item_status, display_summary, SyncResults
)
from .utils.helpers import custom_input, format_time_remaining, init_selenium_driver, color_gradient, construct_list_url
from .utils.logger import setup_logging, ensure_data_directory_exists


def startup():
    """Initialize application and ensure required directories and files exist."""
    ensure_data_directory_exists()
    init_database()
    init_selenium_driver()


def initialize_sync_interval():
    """Initialize sync interval from environment and save to database if needed."""
    try:
        # Check if there's already a sync interval in the database
        db_interval = load_sync_interval()
        
        if db_interval > 0:
            logging.info(f"Using existing sync interval from database: {db_interval} hours")
            return db_interval
        
        # No database interval, check environment
        _, _, _, env_interval, _, _ = load_env_config()
        
        if env_interval > 0:
            # Save environment interval to database
            configure_sync_interval(env_interval)
            logging.info(f"Initialized sync interval from environment: {env_interval} hours (saved to database)")
            return env_interval
        
        # No interval found anywhere, return 0 (will need to be set manually)
        logging.info("No sync interval configured in database or environment")
        return 0
        
    except Exception as e:
        logging.warning(f"Error initializing sync interval: {e}")
        return 0


def get_credentials() -> tuple:
    """
    Get Overseerr API credentials from configuration or user input.
    
    Returns:
        tuple: Overseerr URL, API key, requester user ID
    """
    # Check for Docker environment variables first
    url, api_key, user_id, _, _, _ = load_env_config()
    
    if url and api_key:
        logging.info("Using credentials from environment variables")
        return url, api_key, user_id
    
    # Check for saved credentials
    url, api_key, user_id = load_config()
    
    if url and api_key:
        logging.info("Using saved credentials")
        return url, api_key, user_id
    
    # If no credentials found, prompt user for input
    print("\n🔑 No saved credentials found. Let's set up your Overseerr connection.")
    url = custom_input("Enter Overseerr URL (e.g. http://localhost:5055): ")
    api_key = custom_input("Enter Overseerr API key: ")
    
    # Create a client to set requester user
    client = OverseerrClient(url, api_key)
    
    try:
        user_id = client.set_requester_user()
        # Save the credentials
        save_config(url, api_key, user_id)
        return url, api_key, user_id
    except Exception as e:
        logging.error(f"Failed to configure API: {str(e)}")
        sys.exit(1)


def fetch_media_from_lists(list_ids: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Fetch media items from all configured lists.
    
    Args:
        list_ids (List[Dict[str, str]]): List of dictionaries with list type and ID
        
    Returns:
        tuple: (List of media items from all sources, List of synced list info with URLs)
    """
    all_media = []
    synced_lists = []
    
    for list_info in list_ids:
        list_type = list_info["type"]
        list_id = list_info["id"]
        
        try:
            # Display progress message to user
            print(color_gradient(f"\n🔍  Fetching items from {list_type.upper()} list: {list_id}...", "#ffaa00", "#ff5500"))
            
            logging.info(f"Fetching {list_type.upper()} list: {list_id}")
            # Get the appropriate provider function
            provider_func = get_provider(list_type)
            media_items = provider_func(list_id)
            
            # Construct the URL for this list
            list_url = construct_list_url(list_type, list_id)
            
            if media_items:
                # Display success message to user
                print(color_gradient(f"✅  Found {len(media_items)} items in {list_type.upper()} list: {list_id}", "#00ff00", "#00aa00"))
                logging.info(f"Found {len(media_items)} items in {list_type.upper()} list: {list_id}")
                all_media.extend(media_items)
                
                # Track this list as successfully synced
                synced_lists.append({
                    'type': list_type,
                    'id': list_id,
                    'url': list_url,
                    'item_count': len(media_items)
                })
            else:
                # Display warning message to user
                print(color_gradient(f"⚠️   No items found in {list_type.upper()} list: {list_id}", "#ffaa00", "#ff5500"))
                logging.warning(f"No items found in {list_type.upper()} list: {list_id}")
                
                # Still track the list even if no items found
                synced_lists.append({
                    'type': list_type,
                    'id': list_id,
                    'url': list_url,
                    'item_count': 0
                })
        except Exception as e:
            # Display error message to user
            print(color_gradient(f"❌  Error fetching {list_type.upper()} list {list_id}: {str(e)}", "#ff0000", "#aa0000"))
            logging.error(f"Error fetching {list_type.upper()} list {list_id}: {str(e)}")
            
            # Track failed lists too
            list_url = construct_list_url(list_type, list_id)
            synced_lists.append({
                'type': list_type,
                'id': list_id,
                'url': list_url,
                'item_count': 0,
                'error': str(e)
            })
    
    # Remove duplicates (by IMDb ID if available)
    seen_imdb_ids = set()
    unique_media = []
    
    for item in all_media:
        imdb_id = item.get("imdb_id")
        if imdb_id:
            if imdb_id not in seen_imdb_ids:
                seen_imdb_ids.add(imdb_id)
                unique_media.append(item)
        else:
            # If no IMDb ID, keep the item
            unique_media.append(item)
    
    if len(all_media) != len(unique_media):
        print(color_gradient(f"\n🔄  Removed {len(all_media) - len(unique_media)} duplicate items", "#ffaa00", "#ff5500"))
    
    print(color_gradient(f"\n📊  Total unique media items ready for sync: {len(unique_media)}", "#00aaff", "#00ffaa"))
    logging.info(f"Fetched {len(unique_media)} unique media items from all lists")
    return unique_media, synced_lists


def process_media_item(item: Dict[str, Any], overseerr_client: OverseerrClient, dry_run: bool, is_4k: bool = False) -> Dict[str, Any]:
    """
    Process a single media item for sync to Overseerr.
    
    Args:
        item (Dict[str, Any]): Media item to process
        overseerr_client (OverseerrClient): Overseerr API client
        dry_run (bool): Whether to perform a dry run
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        
    Returns:
        Dict[str, Any]: Processing result
    """
    title = item.get('title', 'Unknown Title').strip()
    media_type = item.get('media_type', 'unknown')
    year = item.get('year')
    
    # Strip any year from the title (e.g., "Cinderella 1997" -> "Cinderella")
    search_title = re.sub(r'\s*\(?(?:19|20)\d{2}\)?$', '', title).strip()
    
    # Add year and media_type to the return data
    result = {
        "title": title,  # Keep original title for display
        "year": year,
        "media_type": media_type,
        "error_message": None
    }

    if dry_run:
        result["status"] = "would_be_synced"
        return result

    try:
        search_result = overseerr_client.search_media(
            search_title,  # Use cleaned title for search
            media_type,
            year
        )
        if search_result:
            overseerr_id = search_result["id"]
            
            # Check if we should skip this item based on last sync time
            if not should_sync_item(overseerr_id):
                save_sync_result(title, media_type, None, overseerr_id, "skipped", year)
                return {"title": title, "status": "skipped", "year": year, "media_type": media_type}

            is_available, is_requested, number_of_seasons = overseerr_client.get_media_status(overseerr_id, search_result["mediaType"])
            
            if is_available:
                save_sync_result(title, media_type, None, overseerr_id, "already_available", year)
                return {"title": title, "status": "already_available", "year": year, "media_type": media_type}
            elif is_requested:
                save_sync_result(title, media_type, None, overseerr_id, "already_requested", year)
                return {"title": title, "status": "already_requested", "year": year, "media_type": media_type}
            else:
                if search_result["mediaType"] == 'tv':
                    request_status = overseerr_client.request_tv_series(overseerr_id, number_of_seasons, is_4k)
                else:
                    request_status = overseerr_client.request_media(overseerr_id, search_result["mediaType"], is_4k)
                
                if request_status == "success":
                    save_sync_result(title, media_type, None, overseerr_id, "requested", year)
                    return {"title": title, "status": "requested", "year": year, "media_type": media_type}
                else:
                    save_sync_result(title, media_type, None, overseerr_id, "request_failed", year)
                    return {"title": title, "status": "request_failed", "year": year, "media_type": media_type}
        else:
            save_sync_result(title, media_type, None, None, "not_found", year)
            return {"title": title, "status": "not_found", "year": year, "media_type": media_type}
    except Exception as e:
        result["status"] = "error"
        result["error_message"] = str(e)
        return result


def sync_media_to_overseerr(
    media_items: List[Dict[str, Any]],
    overseerr_client: OverseerrClient,
    synced_lists: List[Dict[str, str]] = None,
    is_4k: bool = False,
    dry_run: bool = False,
    automated_mode: bool = False
) -> SyncResults:
    """
    Sync media items to Overseerr using ThreadPoolExecutor for concurrent processing.
    
    Args:
        media_items (List[Dict[str, Any]]): List of media items to sync
        overseerr_client (OverseerrClient): Overseerr API client
        synced_lists (List[Dict[str, str]], optional): List of synced list information. Defaults to None.
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        dry_run (bool, optional): Whether to perform a dry run. Defaults to False.
        automated_mode (bool, optional): Whether to run in automated mode. Defaults to False.
        
    Returns:
        SyncResults: Sync results
    """
    sync_results = SyncResults()
    sync_results.total_items = len(media_items)
    sync_results.synced_lists = synced_lists or []
    current_item = 0

    print(f"\n🎬  Processing {sync_results.total_items} media items...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_media_item, item, overseerr_client, dry_run, is_4k): item for item in media_items}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            current_item += 1
            try:
                result = future.result()
                status = result["status"]
                sync_results.results[status] += 1
                
                # Track additional information
                if status == "not_found":
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

                # Display status
                display_item_status(result, current_item, sync_results.total_items, dry_run)

            except Exception as exc:
                sync_results.results["error"] += 1
                sync_results.error_items.append({
                    "title": item["title"],
                    "error": str(exc)
                })

    return sync_results


def automated_sync(
    overseerr_client: OverseerrClient,
    initial_interval_hours: float,
    is_4k: bool = False,
    automated_mode: bool = True
):
    """
    Run automated sync at specified intervals.
    
    Args:
        overseerr_client (OverseerrClient): Overseerr API client
        initial_interval_hours (float): Initial sync interval in hours (can be decimal like 0.5)
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        automated_mode (bool, optional): Whether to run in automated mode. Defaults to True.
    """
    # Current interval - will be updated from database
    current_interval_hours = initial_interval_hours
    
    # Global flag to trigger immediate sync
    immediate_sync_requested = threading.Event()
    
    def signal_handler(sig, frame):
        if sig == signal.SIGTERM or sig == signal.SIGINT:
            logging.info("Received signal to terminate, exiting...")
            sys.exit(0)
        elif sig == signal.SIGUSR1:
            logging.info("Received SIGUSR1 signal - triggering immediate sync")
            immediate_sync_requested.set()
    
    def get_current_interval():
        """Get the current sync interval from database."""
        try:
            db_interval = load_sync_interval()
            if db_interval > 0:
                return db_interval
            return current_interval_hours  # Fallback to current
        except Exception as e:
            logging.warning(f"Error loading sync interval from database: {e}")
            return current_interval_hours  # Fallback to current
    
    def perform_sync():
        """Perform a single sync operation"""
        try:
            # Check for single list sync request file
            import os
            import json
            single_list_request_file = "data/single_list_sync_request.json"
            
            if os.path.exists(single_list_request_file):
                try:
                    with open(single_list_request_file, 'r') as f:
                        request_data = json.load(f)
                    
                    # Remove the request file after reading
                    os.remove(single_list_request_file)
                    
                    list_type = request_data.get("list_type")
                    list_id = request_data.get("list_id")
                    
                    if list_type and list_id:
                        logging.info(f"Single list sync requested via file: {list_type}:{list_id}")
                        
                        # Use the sync_single_list function
                        try:
                            # Get environment config for single list sync
                            from list_sync.config import load_env_config
                            overseerr_url, overseerr_api_key, user_id, _, _, is_4k_env = load_env_config()
                            
                            result = sync_single_list(
                                list_type,
                                list_id,
                                overseerr_url,
                                overseerr_api_key,
                                user_id,
                                is_4k_env or is_4k,  # Use environment 4K setting or current setting
                                False  # dry_run=False
                            )
                            
                            if result.get("success", False):
                                logging.info(f"Single list sync completed successfully: {result}")
                                return True
                            else:
                                logging.error(f"Single list sync failed: {result}")
                                return False
                                
                        except Exception as e:
                            logging.error(f"Error in single list sync: {str(e)}")
                            return False
                    else:
                        logging.warning("Invalid single list sync request: missing list_type or list_id")
                        
                except Exception as e:
                    logging.error(f"Error reading single list sync request file: {e}")
                    # Continue with normal sync if file is corrupted
            
            # Check for single list sync environment variables (fallback method)
            single_list_sync = os.environ.get("SINGLE_LIST_SYNC", "").lower() == "true"
            single_list_type = os.environ.get("SINGLE_LIST_TYPE")
            single_list_id = os.environ.get("SINGLE_LIST_ID")
            
            if single_list_sync and single_list_type and single_list_id:
                logging.info(f"Single list sync requested via environment: {single_list_type}:{single_list_id}")
                
                # Clear environment variables after reading them
                os.environ.pop("SINGLE_LIST_SYNC", None)
                os.environ.pop("SINGLE_LIST_TYPE", None)
                os.environ.pop("SINGLE_LIST_ID", None)
                
                # Use the sync_single_list function
                try:
                    # Get environment config for single list sync
                    from list_sync.config import load_env_config
                    overseerr_url, overseerr_api_key, user_id, _, _, is_4k_env = load_env_config()
                    
                    result = sync_single_list(
                        single_list_type,
                        single_list_id,
                        overseerr_url,
                        overseerr_api_key,
                        user_id,
                        is_4k_env or is_4k,  # Use environment 4K setting or current setting
                        False  # dry_run=False
                    )
                    
                    if result.get("success", False):
                        logging.info(f"Single list sync completed successfully: {result}")
                        return True
                    else:
                        logging.error(f"Single list sync failed: {result}")
                        return False
                        
                except Exception as e:
                    logging.error(f"Error in single list sync: {str(e)}")
                    return False
            else:
                # Regular full sync
                logging.info("Starting full sync operation")
                list_ids = load_list_ids()
                
                if not list_ids:
                    logging.warning("No lists configured, checking for environment variables")
                    # Try to load from environment
                    lists_loaded = load_env_lists()
                    if lists_loaded:
                        list_ids = load_list_ids()
                        logging.info(f"Loaded {len(list_ids)} lists from environment variables")
                    else:
                        logging.error("No lists configured in database or environment")
                        return False
                
                media_items, synced_lists = fetch_media_from_lists(list_ids)
                
                if not media_items:
                    logging.warning("No media items found in configured lists")
                    return False
                
                # Update item counts and last_synced timestamps in database for all processed lists
                for list_info in synced_lists:
                    try:
                        update_list_sync_info(list_info['type'], list_info['id'], list_info['item_count'])
                        logging.info(f"Updated sync info for {list_info['type']} list {list_info['id']}: {list_info['item_count']} items")
                    except Exception as e:
                        logging.warning(f"Failed to update sync info for {list_info['type']} list {list_info['id']}: {e}")
                
                # Perform the sync
                sync_results = sync_media_to_overseerr(
                    media_items,
                    overseerr_client,
                    synced_lists=synced_lists,
                    is_4k=is_4k,
                    automated_mode=automated_mode
                )
                
                # Display summary
                summary_text = str(sync_results)
                display_summary(sync_results)
                
                # Send to Discord webhook if configured
                send_to_discord_webhook(summary_text, sync_results)
                
                logging.info("Full sync operation completed successfully")
                return True
            
        except Exception as e:
            logging.error(f"Error in sync operation: {str(e)}")
            return False
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)
    
    logging.info(f"Starting automated sync mode (initial interval: {current_interval_hours} hours)")
    logging.info(f"Process PID: {os.getpid()} - Send SIGUSR1 to trigger immediate sync")
    
    # Perform initial sync
    perform_sync()
    
    while True:
        try:
            # Check for updated interval from database before each wait
            new_interval = get_current_interval()
            if new_interval != current_interval_hours:
                logging.info(f"Sync interval updated from {current_interval_hours} to {new_interval} hours")
                current_interval_hours = new_interval
            
            # Wait for the interval or immediate sync signal
            if immediate_sync_requested.wait(timeout=current_interval_hours * 3600):
                # Signal received - perform immediate sync
                logging.info("Immediate sync requested via signal")
                immediate_sync_requested.clear()  # Reset the flag
                perform_sync()
            else:
                # Timeout reached - perform scheduled sync
                logging.info(f"Scheduled sync interval reached ({current_interval_hours} hours)")
                perform_sync()
                
        except Exception as e:
            logging.error(f"Error in automated sync loop: {str(e)}")
            # Sleep for an hour before retrying on error
            time.sleep(3600)


def schedule_next_sync(interval_hours: float, is_4k: bool = False, automated_mode: bool = True):
    """
    Calculate next sync time and start a scheduler thread.
    
    Args:
        interval_hours (float): Sync interval in hours (can be decimal like 0.5)
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        automated_mode (bool, optional): Whether to run in automated mode. Defaults to True.
    """
    # Calculate next run time
    next_run = datetime.datetime.now() + datetime.timedelta(hours=interval_hours)
    logging.info(f"Next sync scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create and start the scheduler thread
    def run_scheduler():
        time.sleep(interval_hours * 3600)
        # Get fresh credentials in case they changed
        url, api_key, user_id = get_credentials()
        overseerr_client = OverseerrClient(url, api_key, user_id)
        run_sync(overseerr_client, is_4k=is_4k, automated_mode=automated_mode)
        # Reschedule next run
        schedule_next_sync(interval_hours, is_4k, automated_mode)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()


def run_sync(
    overseerr_client: OverseerrClient,
    dry_run: bool = False,
    is_4k: bool = False,
    automated_mode: bool = False
):
    """
    Run a sync operation.
    
    Args:
        overseerr_client (OverseerrClient): Overseerr API client
        dry_run (bool, optional): Whether to perform a dry run. Defaults to False.
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        automated_mode (bool, optional): Whether to run in automated mode. Defaults to False.
    """
    # Load lists
    list_ids = load_list_ids()
    
    if not list_ids:
        logging.warning("No lists configured")
        print("\n⚠️  No lists configured. Please add lists first.")
        return
    
    # Fetch media from lists
    media_items, synced_lists = fetch_media_from_lists(list_ids)
    
    if not media_items:
        logging.warning("No media items found in configured lists")
        print("\n⚠️  No media items found in configured lists.")
        return
    
    # Update item counts and last_synced timestamps in database for all processed lists
    for list_info in synced_lists:
        try:
            update_list_sync_info(list_info['type'], list_info['id'], list_info['item_count'])
            logging.info(f"Updated sync info for {list_info['type']} list {list_info['id']}: {list_info['item_count']} items")
        except Exception as e:
            logging.warning(f"Failed to update sync info for {list_info['type']} list {list_info['id']}: {e}")
    
    # Perform the sync
    sync_results = sync_media_to_overseerr(
        media_items,
        overseerr_client,
        synced_lists=synced_lists,
        is_4k=is_4k,
        dry_run=dry_run,
        automated_mode=automated_mode
    )
    
    # Display summary
    summary_text = str(sync_results)
    display_summary(sync_results)
    
    # Send to Discord webhook if configured
    if not dry_run:
        send_to_discord_webhook(summary_text, sync_results)


def sync_single_list(
    list_type: str,
    list_id: str,
    overseerr_url: str,
    overseerr_api_key: str,
    user_id: Optional[str] = None,
    is_4k: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sync a single specific list instead of all configured lists.
    
    Args:
        list_type (str): Type of list (e.g., 'imdb', 'trakt')
        list_id (str): ID of the specific list to sync
        overseerr_url (str): Overseerr URL
        overseerr_api_key (str): Overseerr API key
        user_id (Optional[str]): User ID for requests
        is_4k (bool): Whether to request 4K versions
        dry_run (bool): Whether to run in dry-run mode
        
    Returns:
        Dict[str, Any]: Sync results
    """
    try:
        logging.info(f"Starting single list sync for {list_type}:{list_id}")
        print(color_gradient(f"\n🎯  Single List Sync: {list_type.upper()}:{list_id}", "#00aaff", "#00ffaa"))
        
        # Create Overseerr client
        overseerr_client = OverseerrClient(overseerr_url, overseerr_api_key, user_id)
        
        # Create a single list info dictionary
        single_list_info = [{"type": list_type, "id": list_id}]
        
        # Fetch media from the single list
        media_items, synced_lists = fetch_media_from_lists(single_list_info)
        
        if not media_items:
            result = {
                "success": True,
                "message": f"No items found in {list_type}:{list_id}",
                "items_processed": 0,
                "items_requested": 0,
                "errors": 0,
                "list_info": synced_lists[0] if synced_lists else None
            }
            logging.info(f"Single list sync completed - no items found")
            return result
        
        # Sync the media items to Overseerr
        sync_results = sync_media_to_overseerr(
            media_items=media_items,
            overseerr_client=overseerr_client,
            synced_lists=synced_lists,
            is_4k=is_4k,
            dry_run=dry_run,
            automated_mode=True  # Treat single sync as automated to avoid interactive prompts
        )
        
        # Update item count for the synced list
        if synced_lists:
            list_info = synced_lists[0]
            update_list_sync_info(list_type, list_id, list_info.get('item_count', 0))
        
        # Convert sync results to return format
        result = {
            "success": True,
            "message": f"Single list sync completed for {list_type}:{list_id}",
            "items_processed": sync_results.total_items,
            "items_requested": sync_results.results["requested"],
            "items_already_available": sync_results.results["already_available"],
            "items_already_requested": sync_results.results["already_requested"],
            "items_skipped": sync_results.results["skipped"],
            "items_not_found": sync_results.results["not_found"],
            "errors": sync_results.results["error"],
            "list_info": synced_lists[0] if synced_lists else None,
            "dry_run": dry_run
        }
        
        logging.info(f"Single list sync completed successfully: {result}")
        print(color_gradient(f"✅  Single list sync completed: {sync_results.results['requested']} requested, {sync_results.results['error']} errors", "#00ff00", "#00aa00"))
        
        return result
        
    except Exception as e:
        error_message = f"Error in single list sync for {list_type}:{list_id}: {str(e)}"
        logging.error(error_message)
        print(color_gradient(f"❌  {error_message}", "#ff0000", "#aa0000"))
        
        return {
            "success": False,
            "message": error_message,
            "error": str(e),
            "items_processed": 0,
            "items_requested": 0,
            "errors": 1
        }


def main():
    """Main entry point for the application."""
    try:
        # Initialize application
        startup()
        added_logger = setup_logging()
        
        # Initialize sync interval (environment -> database if needed)
        sync_interval = initialize_sync_interval()
        
        # Display splash screen
        display_ascii_art()
        display_banner()
        
        # Check for Docker environment variables
        url, api_key, user_id, _, automated_mode, is_4k = load_env_config()
        
        # If in automated mode, bypass menu and start syncing
        if url and api_key and automated_mode:
            logging.info("Starting in automated mode")
            overseerr_client = OverseerrClient(url, api_key, user_id)
            try:
                # Test connection to make sure credentials are valid
                overseerr_client.test_connection()
                # Try to load lists from environment if none exist
                load_env_lists()
                
                # Always use the database sync interval (which was initialized from env if needed)
                if sync_interval > 0:
                    logging.info(f"Starting automated sync with {sync_interval} hour interval (from database)")
                    automated_sync(overseerr_client, sync_interval, is_4k, automated_mode)
                else:
                    logging.info("Running one-time sync in automated mode (no interval configured)")
                    run_sync(overseerr_client, is_4k=is_4k, automated_mode=automated_mode)
                    sys.exit(0)
            except Exception as e:
                logging.error(f"Error in automated mode: {str(e)}")
                # Continue to interactive menu if automated mode fails
        
        # Get API credentials if not in automated mode
        url, api_key, user_id = get_credentials()
        overseerr_client = OverseerrClient(url, api_key, user_id)
        
        # Test connection
        try:
            overseerr_client.test_connection()
        except Exception as e:
            logging.error(f"Failed to connect to Overseerr: {str(e)}")
            print(f"\n❌ Failed to connect to Overseerr: {str(e)}")
            if os.path.exists(CONFIG_FILE):
                if custom_input("\n🗑️  Delete the current config and start over? (y/n): ").lower() == "y":
                    os.remove(CONFIG_FILE)
                    print("\n🔄  Config deleted. Please restart the script.")
            sys.exit(1)
        
        # Main menu loop
        while True:
            display_menu()
            choice = custom_input("Enter your choice (1-7): ")
            
            if choice == "7":
                print("\n👋 Exiting. Goodbye!")
                sys.exit(0)
            
            handle_menu_choice(
                choice, overseerr_client, run_sync, 
                load_list_ids, display_lists, manage_lists
            )
    
    except KeyboardInterrupt:
        print("\n\n👋 Exiting. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        print(f"\n❌ An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
