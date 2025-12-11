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
    save_sync_result, update_list_item_count, update_list_sync_info, DB_FILE,
    start_sync_in_db, end_sync_in_db, add_item_to_sync, update_sync_lists_in_db
)
from .notifications.discord import send_to_discord_webhook
from .providers import get_provider, get_available_providers, SyncCancelledException
from .ui.cli import handle_menu_choice, manage_lists
from .ui.display import (
    display_ascii_art, display_banner, display_menu, display_lists,
    display_item_status, display_summary, SyncResults
)
from .utils.helpers import custom_input, format_time_remaining, init_selenium_driver, color_gradient, construct_list_url
from .utils.logger import setup_logging, ensure_data_directory_exists
from .utils.log_rotation import get_log_rotator, check_and_rotate_logs
from .utils.sync_status import (
    get_sync_tracker,
    is_cancel_requested_persisted,
    clear_cancel_request,
    set_cancel_request,
    get_pause_until,
    clear_pause_until,
    set_pause_until,
)
# Removed in-memory sync tracker - now using database-based tracking

# Global variable to track current sync session for signal handlers
_current_sync_session_id: Optional[str] = None


def _handle_termination_signal(signum, frame):
    """
    Handle SIGTERM/SIGINT for immediate sync termination.
    This is called when the cancel button forcefully terminates the sync process.
    """
    global _current_sync_session_id
    
    logging.warning(f"⚠️ Received termination signal {signum} - requesting graceful stop")
    
    # Get the sync tracker and clean up
    try:
        sync_tracker = get_sync_tracker()
        session_id = _current_sync_session_id or sync_tracker.get_state().get('session_id')
        
        # Persist cancel request so the running loop can see it
        if session_id:
            try:
                set_cancel_request(session_id)
            except Exception:
                pass
        
        # Update database to mark sync as cancelled
        if session_id:
            try:
                import sqlite3
                from .database import DB_FILE
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sync_history 
                    SET status = 'cancelled',
                        end_time = CURRENT_TIMESTAMP
                    WHERE session_id = ? AND status = 'running'
                """, (session_id,))
                conn.commit()
                conn.close()
                logging.info(f"Marked sync session {session_id} as cancelled in database (signal handler)")
            except Exception as e:
                logging.error(f"Error updating database in signal handler: {e}")
        
        # Clear the tracker state and persisted flag
        sync_tracker.end_sync()
        if session_id:
            try:
                clear_cancel_request(session_id)
            except Exception:
                pass
        
    except Exception as e:
        logging.error(f"Error in termination signal handler: {e}")
    
    # Do not exit the process; allow the loop to notice cancellation and return


def setup_sync_signal_handlers():
    """
    Set up signal handlers for sync termination.
    Call this at the start of sync operations.
    """
    try:
        signal.signal(signal.SIGTERM, _handle_termination_signal)
        signal.signal(signal.SIGINT, _handle_termination_signal)
        logging.debug("Sync termination signal handlers installed")
    except Exception as e:
        logging.warning(f"Could not set up signal handlers: {e}")


def check_cancellation_requested(session_id: Optional[str] = None) -> bool:
    """
    Check if sync cancellation has been requested.
    
    Returns:
        bool: True if cancellation requested, False otherwise
    """
    try:
        sync_tracker = get_sync_tracker()
        in_mem = sync_tracker.is_cancellation_requested()
        
        # Also check persisted flag to support cross-process cancellation
        sid = session_id or _current_sync_session_id
        persisted = is_cancel_requested_persisted(sid) if sid else False
        return in_mem or persisted
    except Exception as e:
        logging.warning(f"Error checking cancellation status: {e}")
        return False


def handle_cancellation(sync_tracker, session_id: Optional[str] = None):
    """
    Handle sync cancellation gracefully.
    
    Args:
        sync_tracker: SyncStatusTracker instance
        session_id: Optional session ID for database tracking
    """
    logging.warning("⚠️ Sync cancellation requested - stopping gracefully")
    
    # Clear cancellation flag
    sync_tracker.clear_cancellation()
    if session_id:
        clear_cancel_request(session_id)
    
    # End sync in tracker
    sync_tracker.end_sync()
    
    # Update database if session_id provided
    if session_id:
        try:
            import sqlite3
            from .database import DB_FILE
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_history 
                SET status = 'cancelled',
                    end_time = CURRENT_TIMESTAMP
                WHERE session_id = ? AND status = 'running'
            """, (session_id,))
            conn.commit()
            conn.close()
            logging.info(f"Marked sync session {session_id} as cancelled in database")
        except Exception as e:
            logging.error(f"Error updating database for cancelled sync: {e}")


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


def fetch_media_from_lists(list_ids: List[Dict[str, str]], is_single_list: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Fetch media items from all configured lists.
    
    Args:
        list_ids (List[Dict[str, str]]): List of dictionaries with list type and ID
        is_single_list (bool): Whether this is a single list sync (affects log message format)
        
    Returns:
        tuple: (List of media items from all sources, List of synced list info with URLs)
    """
    all_media = []
    synced_lists = []
    
    for list_info in list_ids:
        # Check for cancellation request
        if check_cancellation_requested():
            logging.warning("⚠️ Cancellation detected while fetching lists")
            # Return what we have so far
            return all_media, synced_lists
        
        list_type = list_info["type"]
        list_id = list_info["id"]
        list_user_id = list_info.get("user_id", "1")
        
        try:
            # Display progress message to user
            print(color_gradient(f"\n🔍  Fetching items from {list_type.upper()} list: {list_id}... (check backend logs for details - this can take some time)", "#ffaa00", "#ff5500"))
            
            logging.info(f"Fetching {list_type.upper()} list: {list_id}")
            # Get the appropriate provider function
            provider_func = get_provider(list_type)
            media_items = provider_func(list_id)
            
            # Construct the URL for this list
            list_url = construct_list_url(list_type, list_id)
            
            if media_items:
                # Filter out items with empty titles and clean up problematic characters
                valid_items = []
                for item in media_items:
                    title = item.get('title', '').strip()
                    # Clean up backslashes and other problematic characters
                    title = title.replace('\\', '').strip()
                    if title:  # Only keep items with non-empty titles
                        item['title'] = title  # Update the cleaned title
                        # Attach list information to each item
                        # This allows tracking which list(s) each item came from (with user)
                        item['_source_list_type'] = list_type
                        item['_source_list_id'] = list_id
                        item['_source_list_user_id'] = list_user_id
                        valid_items.append(item)
                    else:
                        logging.warning(f"Skipping item with empty title from {list_type.upper()} list: {list_id}")
                
                # Display success message to user
                print(color_gradient(f"✅  Found {len(valid_items)} items in {list_type.upper()} list: {list_id}", "#00ff00", "#00aa00"))
                logging.info(f"Found {len(valid_items)} items in {list_type.upper()} list: {list_id}")
                all_media.extend(valid_items)
                
                # Track this list as successfully synced
                synced_lists.append({
                    'type': list_type,
                    'id': list_id,
                    'url': list_url,
                    'item_count': len(media_items),
                    'user_id': list_user_id
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
                    'item_count': 0,
                    'user_id': list_user_id
                })
        except SyncCancelledException:
            # Cancellation was requested - return what we have so far
            logging.warning(f"⚠️ Sync cancelled during fetch of {list_type.upper()} list: {list_id}")
            print(color_gradient(f"⚠️  Sync cancelled - stopping list fetch", "#ffaa00", "#ff5500"))
            return all_media, synced_lists
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
    
    # Remove duplicates (by IMDb ID if available) while preserving list information
    # Track all lists each item came from
    seen_imdb_ids = {}
    seen_tmdb_ids = {}
    seen_titles = {}
    unique_media = []
    
    for item in all_media:
        imdb_id = item.get("imdb_id")
        tmdb_id = item.get("tmdb_id")
        title_key = f"{item.get('title', '')}|{item.get('year', '')}|{item.get('media_type', '')}"
        list_type = item.get('_source_list_type')
        list_id = item.get('_source_list_id')
        
        # Track which list this item came from
        list_user_id = item.get('_source_list_user_id', "1")
        list_info = {'type': list_type, 'id': list_id, 'user_id': list_user_id}
        
        # Try to match by IMDb ID first (most reliable)
        if imdb_id:
            if imdb_id not in seen_imdb_ids:
                seen_imdb_ids[imdb_id] = item
                # Initialize source_lists array
                item['_source_lists'] = [list_info]
                unique_media.append(item)
            else:
                # Item already exists, add this list to source_lists if not already present
                existing_item = seen_imdb_ids[imdb_id]
                if '_source_lists' not in existing_item:
                    existing_item['_source_lists'] = []
                # Check if this list is already tracked (by comparing type and id)
                list_key = f"{list_type}:{list_id}:{list_user_id}"
                existing_keys = [f"{l['type']}:{l['id']}:{l.get('user_id','1')}" for l in existing_item['_source_lists']]
                if list_key not in existing_keys:
                    existing_item['_source_lists'].append(list_info)
        # Try TMDB ID as fallback
        elif tmdb_id:
            if tmdb_id not in seen_tmdb_ids:
                seen_tmdb_ids[tmdb_id] = item
                item['_source_lists'] = [list_info]
                unique_media.append(item)
            else:
                existing_item = seen_tmdb_ids[tmdb_id]
                if '_source_lists' not in existing_item:
                    existing_item['_source_lists'] = []
                list_key = f"{list_type}:{list_id}:{list_user_id}"
                existing_keys = [f"{l['type']}:{l['id']}:{l.get('user_id','1')}" for l in existing_item['_source_lists']]
                if list_key not in existing_keys:
                    existing_item['_source_lists'].append(list_info)
        # Fallback to title + year + media_type
        else:
            if title_key not in seen_titles:
                seen_titles[title_key] = item
                item['_source_lists'] = [list_info]
                unique_media.append(item)
            else:
                existing_item = seen_titles[title_key]
                if '_source_lists' not in existing_item:
                    existing_item['_source_lists'] = []
                list_key = f"{list_type}:{list_id}:{list_user_id}"
                existing_keys = [f"{l['type']}:{l['id']}:{l.get('user_id','1')}" for l in existing_item['_source_lists']]
                if list_key not in existing_keys:
                    existing_item['_source_lists'].append(list_info)
    
    if len(all_media) != len(unique_media):
        print(color_gradient(f"\n🔄  Removed {len(all_media) - len(unique_media)} duplicate items", "#ffaa00", "#ff5500"))
    
    # Use different log message for single list syncs to avoid false FULL sync detection
    if is_single_list:
        print(color_gradient(f"\n📋  Found {len(unique_media)} unique media items from list", "#00aaff", "#00ffaa"))
        logging.info(f"Fetched {len(unique_media)} unique media items from single list")
    else:
        print(color_gradient(f"\n📊  Total unique media items ready for sync: {len(unique_media)}", "#00aaff", "#00ffaa"))
        logging.info(f"Fetched {len(unique_media)} unique media items from all lists")
    return unique_media, synced_lists


def get_source_lists_from_item(item: Dict[str, Any], list_type: Optional[str] = None, list_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extract source lists from an item, with multiple fallback strategies.
    
    Args:
        item: The media item dictionary
        list_type: Optional list type parameter
        list_id: Optional list ID parameter
        
    Returns:
        List of source list dictionaries with 'type' and 'id' keys
    """
    # First, try _source_lists (for items that came from multiple lists)
    source_lists = item.get('_source_lists', [])
    
    # Fallback 1: Use _source_list_type and _source_list_id (for single-list items)
    if not source_lists:
        source_list_type = item.get('_source_list_type')
        source_list_id = item.get('_source_list_id')
        source_list_user_id = item.get('_source_list_user_id', "1")
        if source_list_type and source_list_id:
            source_lists = [{'type': source_list_type, 'id': source_list_id, 'user_id': source_list_user_id}]
    
    # Fallback 2: Use function parameters
    if not source_lists and list_type and list_id:
        source_lists = [{'type': list_type, 'id': list_id, 'user_id': item.get('_source_list_user_id', "1")}]
    
    # Ensure all source list entries carry user_id (default to "1")
    for sl in source_lists:
        if 'user_id' not in sl or sl['user_id'] is None:
            sl['user_id'] = "1"
        else:
            sl['user_id'] = str(sl['user_id'])
    
    return source_lists


def choose_request_user_id(source_lists: List[Dict[str, Any]], default_user_id: str) -> str:
    """
    Choose which Overseerr requester user_id to use for this item.
    Prefers the first source list that has a user_id; falls back to the client's default.
    """
    for source in source_lists:
        user_id = source.get('user_id')
        if user_id:
            return str(user_id)
    return str(default_user_id or "1")


def process_media_item(item: Dict[str, Any], overseerr_client: OverseerrClient, dry_run: bool, is_4k: bool = False, list_type: Optional[str] = None, list_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single media item for sync to Overseerr using smart ID-based matching.
    
    Workflow:
    1. Try direct TMDB ID lookup (if available)
    2. Try IMDB ID → Trakt → TMDB ID (if IMDB ID available)
    3. Try Title/Year → Trakt → TMDB ID
    4. Fallback to Overseerr title search (less reliable)
    
    Args:
        item (Dict[str, Any]): Media item to process
        overseerr_client (OverseerrClient): Overseerr API client
        dry_run (bool): Whether to perform a dry run
        is_4k (bool, optional): Whether to request 4K. Defaults to False.
        
    Returns:
        Dict[str, Any]: Processing result
    """
    # Check for cancellation before processing
    if check_cancellation_requested():
        title = item.get('title', 'Unknown Title').strip()
        media_type = item.get('media_type', 'unknown')
        year = item.get('year')
        return {"title": title, "status": "cancelled", "year": year, "media_type": media_type}
    
    title = item.get('title', 'Unknown Title').strip()
    # Clean up backslashes and other problematic characters
    title = title.replace('\\', '').strip()
    media_type = item.get('media_type', 'unknown')
    year = item.get('year')
    imdb_id = item.get('imdb_id')
    tmdb_id = item.get('tmdb_id')
    season_number = item.get('season_number')  # Check if specific season is requested
    
    # Log item details (boundaries handled at batch level)
    season_info = f" Season {season_number}" if season_number else ""
    logging.info(f"🎬 PROCESSING: '{title}' ({year}) [{media_type}]{season_info}")
    logging.info(f"   IDs: TMDB={tmdb_id}, IMDB={imdb_id}")
    
    # Strip any year from the title (e.g., "Cinderella 1997" -> "Cinderella")
    # But only if there's text remaining after removal (to handle titles like "1917")
    search_title = re.sub(r'\s*\(?(?:19|20)\d{2}\)?$', '', title).strip()
    
    # If stripping the year left us with nothing, use the original title
    # This handles movies whose title IS a year (e.g., "1917", "2012")
    if not search_title:
        search_title = title
    
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
        # Import Trakt search functions
        from .providers.trakt import search_trakt_by_imdb_id, search_trakt_by_title
        
        search_result = None
        match_method = None
        
        # METHOD 1: Direct TMDB ID lookup (fastest, most reliable)
        if tmdb_id:
            # Ensure tmdb_id is an integer (may be string from collections)
            try:
                tmdb_id_int = int(tmdb_id)
            except (ValueError, TypeError):
                logging.warning(f"Invalid TMDB ID format: {tmdb_id} (type: {type(tmdb_id)})")
                tmdb_id_int = None
            
            if tmdb_id_int:
                logging.info(f"🎯 METHOD 1: Direct TMDB ID lookup (ID: {tmdb_id_int})")
                search_result = overseerr_client.get_media_by_tmdb_id(tmdb_id_int, media_type)
            if search_result:
                match_method = "TMDB_ID_DIRECT"
                logging.info(f"✅ SUCCESS: Direct TMDB ID lookup")
        
        # METHOD 2: IMDB ID → Trakt → TMDB ID
        if not search_result and imdb_id:
            logging.info(f"🔍 METHOD 2: IMDB ID → Trakt → TMDB ID (IMDB: {imdb_id})")
            trakt_result = search_trakt_by_imdb_id(imdb_id)
            if trakt_result and trakt_result.get('tmdb_id'):
                resolved_tmdb_id = trakt_result['tmdb_id']
                # Ensure it's an integer
                try:
                    resolved_tmdb_id = int(resolved_tmdb_id)
                except (ValueError, TypeError):
                    logging.warning(f"Invalid resolved TMDB ID format: {resolved_tmdb_id}")
                    resolved_tmdb_id = None
                
                if resolved_tmdb_id:
                    logging.info(f"✅ Trakt resolved IMDB {imdb_id} → TMDB {resolved_tmdb_id}")
                    search_result = overseerr_client.get_media_by_tmdb_id(resolved_tmdb_id, media_type)
                if search_result:
                    match_method = "IMDB_TO_TMDB"
                    logging.info(f"✅ SUCCESS: IMDB→Trakt→TMDB chain")
                    # Update tmdb_id for database storage
                    tmdb_id = resolved_tmdb_id
            else:
                logging.info(f"⚠️  WARNING: Trakt could not resolve IMDB ID {imdb_id} to TMDB ID")
        
        # METHOD 3: Title/Year → Trakt → TMDB ID
        if not search_result:
            logging.info(f"🔍 METHOD 3: Title/Year → Trakt → TMDB ID")
            trakt_result = search_trakt_by_title(search_title, year, media_type)
            if trakt_result and trakt_result.get('tmdb_id'):
                resolved_tmdb_id = trakt_result['tmdb_id']
                # Ensure it's an integer
                try:
                    resolved_tmdb_id = int(resolved_tmdb_id)
                except (ValueError, TypeError):
                    logging.warning(f"Invalid resolved TMDB ID format: {resolved_tmdb_id}")
                    resolved_tmdb_id = None
                
                if resolved_tmdb_id:
                    logging.info(f"✅ Trakt resolved '{search_title}' ({year}) → TMDB {resolved_tmdb_id}")
                    search_result = overseerr_client.get_media_by_tmdb_id(resolved_tmdb_id, media_type)
                if search_result:
                    match_method = "TITLE_TO_TMDB"
                    logging.info(f"✅ SUCCESS: Title→Trakt→TMDB chain")
                    # Update IDs for database storage
                    tmdb_id = resolved_tmdb_id
                    if trakt_result.get('imdb_id') and not imdb_id:
                        imdb_id = trakt_result['imdb_id']
            else:
                logging.info(f"⚠️  Trakt could not find TMDB ID for '{search_title}' ({year})")
        
        # METHOD 4: Fallback to Overseerr title search (least reliable)
        if not search_result:
            logging.warning(f"⚠️  METHOD 4: Falling back to Overseerr title search (less reliable)")
            search_result = overseerr_client.search_media(
                search_title,  # Use cleaned title for search
                media_type,
                year
            )
            if search_result:
                match_method = "OVERSEERR_SEARCH_FALLBACK"
                logging.warning(f"⚠️  SUCCESS: Fallback title search (may be less accurate)")
        
        if search_result:
            overseerr_id = search_result["id"]
            
            # Ensure overseerr_id is an integer (may be string from API response)
            try:
                overseerr_id = int(overseerr_id)
            except (ValueError, TypeError):
                logging.error(f"Invalid Overseerr ID format: {overseerr_id} (type: {type(overseerr_id)})")
                return {"title": title, "status": "error", "year": year, "media_type": media_type}
            
            logging.info(f"📊 MATCH SUMMARY: Method={match_method}, Overseerr_ID={overseerr_id}")
            
            # Get list information from item using helper function
            source_lists = get_source_lists_from_item(item, list_type, list_id)
            
            # Debug: Log source lists
            if source_lists:
                list_keys = [f"{l['type']}:{l['id']}" for l in source_lists]
                logging.info(f"📋 Item will be linked to {len(source_lists)} list(s): {list_keys}")
            else:
                logging.error(f"❌ CRITICAL: No source lists found for item '{title}'! _source_lists={item.get('_source_lists')}, _source_list_type={item.get('_source_list_type')}, _source_list_id={item.get('_source_list_id')}, list_type={list_type}, list_id={list_id}")
                # Don't proceed without list information - this will cause items to not be linked to lists

            # Determine which Overseerr user to request as
            requester_user_id = choose_request_user_id(source_lists, overseerr_client.requester_user_id)
            logging.info(f"🙋 Using Overseerr user_id {requester_user_id} for '{title}'")
            
            # Check if we should skip this item based on last sync time
            if not should_sync_item(overseerr_id):
                logging.info(f"⏭️  SKIP: Recently synced (within skip window)")
                # Save relationship for all source lists
                for source_list in source_lists:
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "skipped", year, tmdb_id, source_list['type'], source_list['id'])
                return {"title": title, "status": "skipped", "year": year, "media_type": media_type}

            logging.info(f"🔍 Checking media status in Overseerr...")
            is_available, is_requested, number_of_seasons = overseerr_client.get_media_status(overseerr_id, search_result["mediaType"])
            
            # Log status interpretation for debugging
            if not is_available and not is_requested:
                logging.debug(f"Media status: Not available, not requested - will attempt to request")
            
            if is_available:
                logging.info(f"☑️ STATUS: Already available in library")
                # Save relationship for all source lists
                for source_list in source_lists:
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "already_available", year, tmdb_id, source_list['type'], source_list['id'])
                return {"title": title, "status": "already_available", "year": year, "media_type": media_type}
            elif is_requested:
                logging.info(f"📌 STATUS: Already requested (pending)")
                # Save relationship for all source lists
                for source_list in source_lists:
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "already_requested", year, tmdb_id, source_list['type'], source_list['id'])
                return {"title": title, "status": "already_requested", "year": year, "media_type": media_type}
            else:
                logging.info(f"🚀 STATUS: Requesting media...")
                if search_result["mediaType"] == 'tv':
                    # Check if a specific season is requested
                    if season_number is not None:
                        logging.info(f"📺 TV SERIES: Requesting Season {season_number} specifically")
                        request_status = overseerr_client.request_specific_season(overseerr_id, season_number, is_4k, requester_user_id=requester_user_id)
                    else:
                        logging.info(f"📺 TV SERIES: Requesting {number_of_seasons} season(s)")
                        request_status = overseerr_client.request_tv_series(overseerr_id, number_of_seasons, is_4k, requester_user_id=requester_user_id)
                else:
                    logging.info(f"🎬 MOVIE: Submitting request")
                    request_status = overseerr_client.request_media(overseerr_id, search_result["mediaType"], is_4k, requester_user_id=requester_user_id)
                
                if request_status == "success":
                    logging.info(f"✅ SUCCESS: Request submitted successfully!")
                    # Save relationship for all source lists
                    for source_list in source_lists:
                        save_sync_result(title, media_type, imdb_id, overseerr_id, "requested", year, tmdb_id, source_list['type'], source_list['id'])
                    return {"title": title, "status": "requested", "year": year, "media_type": media_type}
                elif request_status == "already_requested":
                    logging.info(f"📌 STATUS: Already requested (detected from API response)")
                    # Save relationship for all source lists
                    for source_list in source_lists:
                        save_sync_result(title, media_type, imdb_id, overseerr_id, "already_requested", year, tmdb_id, source_list['type'], source_list['id'])
                    return {"title": title, "status": "already_requested", "year": year, "media_type": media_type}
                else:
                    logging.error(f"❌ ERROR: Request failed")
                    # Save relationship for all source lists
                    for source_list in source_lists:
                        save_sync_result(title, media_type, imdb_id, overseerr_id, "request_failed", year, tmdb_id, source_list['type'], source_list['id'])
                    return {"title": title, "status": "request_failed", "year": year, "media_type": media_type}
        else:
            logging.error(f"❌ ERROR: Could not find match using any method")
            # Get list information from item using helper function
            source_lists = get_source_lists_from_item(item, list_type, list_id)
            # Save relationship for all source lists
            if source_lists:
                for source_list in source_lists:
                    save_sync_result(title, media_type, imdb_id, None, "not_found", year, tmdb_id, source_list['type'], source_list['id'])
            else:
                logging.error(f"❌ CRITICAL: Cannot save 'not_found' item without list information!")
            return {"title": title, "status": "not_found", "year": year, "media_type": media_type}
    except Exception as e:
        logging.error(f"❌ ERROR: Exception during processing: {str(e)}")
        logging.debug(f"Exception details:", exc_info=True)
        result["status"] = "error"
        result["error_message"] = str(e)
        # Try to save error status with list information if available
        try:
            source_lists = get_source_lists_from_item(item, list_type, list_id)
            if source_lists:
                title = item.get('title', 'Unknown')
                media_type = item.get('media_type', 'movie')
                imdb_id = item.get('imdb_id')
                year = item.get('year')
                tmdb_id = item.get('tmdb_id')
                for source_list in source_lists:
                    save_sync_result(title, media_type, imdb_id, None, "error", year, tmdb_id, source_list['type'], source_list['id'])
        except Exception as save_error:
            logging.error(f"Failed to save error status: {save_error}")
        return result


def sync_media_to_overseerr(
    media_items: List[Dict[str, Any]],
    overseerr_client: OverseerrClient,
    synced_lists: List[Dict[str, str]] = None,
    is_4k: bool = False,
    dry_run: bool = False,
    automated_mode: bool = False,
    sync_id: Optional[int] = None,
    session_id: Optional[str] = None
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
    
    # Intelligent batching for optimal performance with readable logs
    batch_size = int(os.getenv('LISTSYNC_BATCH_SIZE', '3') or '3')  # Default batch size of 3
    sequential_mode = os.getenv('LISTSYNC_SEQUENTIAL_MODE', 'false').lower() == 'true'
    
    if sequential_mode:
        logging.info("🔄 Sequential processing mode enabled (LISTSYNC_SEQUENTIAL_MODE=true)")
        print("🔄 Sequential processing mode enabled")
        
        # Process items sequentially to avoid race conditions
        for i, item in enumerate(media_items, 1):
            # Check for cancellation request
            if check_cancellation_requested():
                logging.warning(f"⚠️ Cancellation detected during sequential processing at item {i}/{sync_results.total_items}")
                handle_cancellation(get_sync_tracker(), session_id)
                sync_results.cancelled = True
                return sync_results
            
            try:
                result = process_media_item(item, overseerr_client, dry_run, is_4k)
                status = result["status"]
                sync_results.results[status] += 1
                
                # Display progress
                title = item.get('title', 'Unknown')
                year = item.get('year', '')
                year_str = f" ({year})" if year else ""
                
                if status == "requested":
                    print(f"✅ {title}{year_str}: Successfully Requested ({i}/{sync_results.total_items})")
                elif status == "already_available":
                    print(f"☑️ {title}{year_str}: Already Available ({i}/{sync_results.total_items})")
                elif status == "already_requested":
                    print(f"📌 {title}{year_str}: Already Requested ({i}/{sync_results.total_items})")
                elif status == "skipped":
                    print(f"⏭️  {title}{year_str}: Skipped ({i}/{sync_results.total_items})")
                else:
                    print(f"❓ {title}{year_str}: {status} ({i}/{sync_results.total_items})")
                
                current_item += 1
                
            except Exception as e:
                logging.error(f"❌ ERROR: Exception during processing: {str(e)}")
                sync_results.results["error"] += 1
                current_item += 1
    else:
        logging.info(f"⚡ Intelligent batching mode enabled (batch size: {batch_size})")
        print(f"⚡ Intelligent batching mode enabled - processing {batch_size} items at a time")
        
        # Process items in batches for optimal performance with clean logging
        total_batches = (len(media_items) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            # Check for cancellation request before each batch
            if check_cancellation_requested():
                logging.warning(f"⚠️ Cancellation detected before batch {batch_num + 1}/{total_batches}")
                handle_cancellation(get_sync_tracker(), session_id)
                sync_results.cancelled = True
                return sync_results
            
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(media_items))
            batch_items = media_items[start_idx:end_idx]
            
            logging.info(f"📦 BATCH {batch_num + 1}/{total_batches}: Processing items {start_idx + 1}-{end_idx}")
            
            # Process batch items sequentially to maintain clean log boundaries
            for i, item in enumerate(batch_items):
                # Add clear log boundary before each item
                logging.info(f"\n{'='*80}")
                logging.info(f"🎬 PROCESSING ITEM {start_idx + i + 1}/{sync_results.total_items}")
                logging.info(f"{'='*80}")
                
                try:
                    result = process_media_item(item, overseerr_client, dry_run, is_4k)
                    status = result["status"]
                    sync_results.results[status] += 1
                    
                    # Add clear log boundary after each item
                    logging.info(f"{'='*80}")
                    logging.info(f"✅ COMPLETED ITEM {start_idx + i + 1}/{sync_results.total_items} - Status: {status.upper()}")
                    logging.info(f"{'='*80}\n")
                    
                    # Display each item individually
                    title = item.get('title', 'Unknown')
                    year = item.get('year', '')
                    year_str = f" ({year})" if year else ""
                    index = start_idx + i + 1
                    
                    if status == "requested":
                        print(f"✅ {title}{year_str}: Successfully Requested ({index}/{sync_results.total_items})")
                    elif status == "already_available":
                        print(f"☑️ {title}{year_str}: Already Available ({index}/{sync_results.total_items})")
                    elif status == "already_requested":
                        print(f"📌 {title}{year_str}: Already Requested ({index}/{sync_results.total_items})")
                    elif status == "skipped":
                        print(f"⏭️ {title}{year_str}: Skipped ({index}/{sync_results.total_items})")
                    else:
                        print(f"❓ {title}{year_str}: {status} ({index}/{sync_results.total_items})")
                    
                    current_item += 1
                    
                    # Check for cancellation after processing each item
                    if check_cancellation_requested():
                        logging.warning(f"⚠️ Cancellation detected after item {start_idx + i + 1}/{sync_results.total_items}")
                        handle_cancellation(get_sync_tracker(), session_id)
                        sync_results.cancelled = True
                        return sync_results
                    
                    # Track additional information
                    if status == "not_found":
                        title = result["title"].strip()
                        year = result["year"]
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
                            "error": result.get("error_message", "Unknown error")
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
                    
                except Exception as e:
                    # Add clear log boundary for errors too
                    logging.error(f"{'='*80}")
                    logging.error(f"❌ ERROR PROCESSING ITEM {start_idx + i + 1}/{sync_results.total_items}: {str(e)}")
                    logging.error(f"{'='*80}\n")
                    sync_results.results["error"] += 1
                    current_item += 1
            
            # Display progress
            logging.info(f"📊 PROGRESS: {current_item}/{sync_results.total_items} items processed")

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
    
    def perform_sync(force_full_sync=False, ignore_pause=False):
        """
        Perform a single sync operation
        
        Args:
            force_full_sync (bool): If True, skip single list sync checks and perform full sync
            ignore_pause (bool): If True, ignore any pause_until timer (e.g. for manual triggers)
        """
        # Honor pause-until if set (from prior cancellation)
        try:
            if not ignore_pause:
                pause_until = get_pause_until()
                if pause_until:
                    from datetime import datetime
                    now = datetime.utcnow()
                    try:
                        pause_dt = datetime.fromisoformat(pause_until)
                    except Exception:
                        pause_dt = None
                    if pause_dt and now < pause_dt:
                        remaining = (pause_dt - now).total_seconds()
                        logging.info(f"⏸️  Sync paused until {pause_dt.isoformat()} (about {int(remaining)}s remaining)")
                        time.sleep(max(remaining, 0))
                    # Clear pause so next run can proceed
                    clear_pause_until()
        except Exception as e:
            logging.warning(f"Pause check failed: {e}")
        
        # Check for cancellation at the start
        if check_cancellation_requested():
            logging.warning("⚠️ Cancellation detected before sync started")
            return False
        
        try:
            # Check for single list sync request files (both legacy and queued)
            # Skip this check if force_full_sync is True (e.g., on startup)
            import os
            import json
            import glob
            
            # Initialize queued_syncs list
            queued_syncs = []
            
            # Only check for single list syncs if not forcing full sync
            if not force_full_sync:
                # First check for queued sync requests in data/sync_requests/
                sync_requests_dir = "data/sync_requests"
                
                if os.path.exists(sync_requests_dir):
                    # Get all pending sync request files, sorted by timestamp
                    request_files = sorted(glob.glob(os.path.join(sync_requests_dir, "single_sync_*.json")))
                    
                    for request_file in request_files:
                        try:
                            with open(request_file, 'r') as f:
                                request_data = json.load(f)
                            
                            list_type = request_data.get("list_type")
                            list_id = request_data.get("list_id")
                            
                            if list_type and list_id:
                                queued_syncs.append({
                                    "list_type": list_type,
                                    "list_id": list_id,
                                    "file": request_file,
                                    "timestamp": request_data.get("timestamp")
                                })
                            else:
                                # Remove invalid request file
                                os.remove(request_file)
                                logging.warning(f"Removed invalid sync request file: {request_file}")
                                
                        except Exception as e:
                            logging.error(f"Error reading queued sync request {request_file}: {e}")
                            # Remove corrupted file
                            try:
                                os.remove(request_file)
                            except:
                                pass
                
                # Also check legacy single file for backwards compatibility
                single_list_request_file = "data/single_list_sync_request.json"
                
                if os.path.exists(single_list_request_file):
                    try:
                        with open(single_list_request_file, 'r') as f:
                            request_data = json.load(f)
                        
                        list_type = request_data.get("list_type")
                        list_id = request_data.get("list_id")
                        
                        if list_type and list_id:
                            # Add to queue if not already there
                            if not any(s["list_type"] == list_type and s["list_id"] == list_id for s in queued_syncs):
                                queued_syncs.append({
                                    "list_type": list_type,
                                    "list_id": list_id,
                                    "file": single_list_request_file,
                                    "timestamp": request_data.get("timestamp")
                                })
                    except Exception as e:
                        logging.error(f"Error reading legacy sync request file: {e}")
            
            # Process all queued single list syncs
            if queued_syncs:
                logging.info(f"Found {len(queued_syncs)} queued sync request(s)")
                
                for sync_req in queued_syncs:
                    # Check for cancellation between queued syncs
                    if check_cancellation_requested():
                        logging.warning("⚠️ Cancellation detected while processing queued syncs")
                        return False
                    
                    list_type = sync_req["list_type"]
                    list_id = sync_req["list_id"]
                    request_file = sync_req["file"]
                    
                    try:
                        logging.info(f"Processing queued single list sync: {list_type}:{list_id}")
                        
                        # Use the sync_single_list function
                        try:
                            # Get environment config for single list sync
                            from list_sync.config import load_env_config
                            overseerr_url, overseerr_api_key, _, _, _, is_4k_env = load_env_config()
                            
                            # Pass user_id=None so sync_single_list fetches the per-list user_id from database
                            result = sync_single_list(
                                list_type,
                                list_id,
                                overseerr_url,
                                overseerr_api_key,
                                None,  # Let sync_single_list fetch user_id from list's database record
                                is_4k_env or is_4k,  # Use environment 4K setting or current setting
                                False  # dry_run=False
                            )
                            
                            if result.get("success", False):
                                logging.info(f"Queued single list sync completed successfully: {list_type}:{list_id}")
                            else:
                                logging.error(f"Queued single list sync failed for {list_type}:{list_id}: {result}")
                                
                        except Exception as e:
                            logging.error(f"Error processing queued single list sync for {list_type}:{list_id}: {str(e)}")
                        
                        finally:
                            # Remove the processed request file
                            try:
                                os.remove(request_file)
                                logging.info(f"Removed processed sync request file: {request_file}")
                            except Exception as e:
                                logging.warning(f"Failed to remove sync request file {request_file}: {e}")
                        
                    except Exception as e:
                        logging.error(f"Error processing sync request: {e}")
                
                # After processing all queued syncs, return True
                logging.info(f"Processed {len(queued_syncs)} queued sync request(s)")
                return True
            
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
                    overseerr_url, overseerr_api_key, _, _, _, is_4k_env = load_env_config()
                    
                    # Pass user_id=None so sync_single_list fetches the per-list user_id from database
                    result = sync_single_list(
                        single_list_type,
                        single_list_id,
                        overseerr_url,
                        overseerr_api_key,
                        None,  # Let sync_single_list fetch user_id from list's database record
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
            
            # Regular full sync (if no single sync was triggered or if force_full_sync is True)
            # Use run_sync() for full syncs to leverage existing tracking and logic
            logging.info("Starting full sync operation")
            
            # Use run_sync() which handles tracking automatically
            from list_sync.config import load_env_config
            overseerr_url, overseerr_api_key, user_id, _, _, is_4k_env = load_env_config()
            overseerr_client_temp = OverseerrClient(overseerr_url, overseerr_api_key, user_id)
            
            run_sync(
                overseerr_client_temp,
                dry_run=False,
                is_4k=is_4k_env or is_4k,
                automated_mode=automated_mode
            )
            
            logging.info("Full sync operation completed successfully")
            return True
            
            # OLD CODE BELOW - Replaced with run_sync() call above
            """
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
            send_to_discord_webhook(summary_text, sync_results, automated=automated_mode)
            
            """
            # OLD CODE END
            
        except Exception as e:
            logging.error(f"Error in sync operation: {str(e)}")
            # Ensure sync state is cleared on error
            try:
                sync_tracker = get_sync_tracker()
                sync_tracker.end_sync()
            except:
                pass
            return False
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum} in automated_sync loop")
        immediate_sync_requested.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)
    logging.info("Signal handler for SIGUSR1 installed in automated_sync")
    
    logging.info(f"Starting automated sync mode (initial interval: {current_interval_hours} hours)")
    logging.info(f"Process PID: {os.getpid()} - Send SIGUSR1 to trigger immediate sync")
    
    # Perform initial sync (always force full sync on startup)
    # This ensures that on app reboot, we always sync all configured lists,
    # not just process queued single list syncs
    perform_sync(force_full_sync=True)
    
    while True:
        try:
            # Check for updated interval from database before each wait
            new_interval = get_current_interval()
            if new_interval != current_interval_hours:
                logging.info(f"Sync interval updated from {current_interval_hours} to {new_interval} hours")
                current_interval_hours = new_interval
            
            wait_seconds = max(current_interval_hours * 3600, 0)
            
            # Also respect pause-until if set (e.g., from a cancellation)
            pause_until = None
            try:
                from datetime import datetime
                pause_str = get_pause_until()
                if pause_str:
                    pause_until = datetime.fromisoformat(pause_str)
                    now = datetime.utcnow()
                    if pause_until > now:
                        wait_seconds = max(wait_seconds, (pause_until - now).total_seconds())
                        logging.info(f"⏸️  Waiting until {pause_until.isoformat()} before next sync")
            except Exception as e:
                logging.warning(f"Pause wait check failed: {e}")
            
            # Wait for the interval or immediate sync signal
            logging.info(f"Waiting for sync... (Timeout: {wait_seconds}s)")
            if immediate_sync_requested.wait(timeout=wait_seconds):
                # Signal received - perform immediate sync
                logging.info(f"Immediate sync requested via signal (Flag set: {immediate_sync_requested.is_set()})")
                immediate_sync_requested.clear()  # Reset the flag
                logging.info("Calling perform_sync(ignore_pause=True)")
                perform_sync(ignore_pause=True)
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
    global _current_sync_session_id
    
    # Set up signal handlers for immediate termination support
    setup_sync_signal_handlers()
    
    # Check and rotate logs if necessary before starting sync
    check_and_rotate_logs()
    
    # Generate unique session ID for this sync
    import uuid
    session_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # Store session ID globally for signal handlers
    _current_sync_session_id = session_id
    
    try:
        # Track sync start in database
        sync_id = start_sync_in_db(session_id=session_id, sync_type='full')
        
        # Register subprocess PID in tracker for immediate termination
        sync_tracker = get_sync_tracker()
        sync_tracker.set_subprocess_pid(os.getpid())
        
        # Log sync start with clear marker
        sync_start_marker = f"========== SYNC START [FULL] - Session: {session_id} =========="
        logging.info(sync_start_marker)
        print(color_gradient(f"\n{sync_start_marker}", "#00aaff", "#00ffaa"))
        
        # Load lists
        list_ids = load_list_ids()
        
        if not list_ids:
            logging.warning("No lists configured")
            print("\n⚠️  No lists configured. Please add lists first.")
            # Log sync end marker even for early exit
            sync_end_marker = f"========== SYNC COMPLETE [FULL] - Session: {session_id} - Status: NO_LISTS =========="
            logging.info(sync_end_marker)
            # Mark sync as ended in database
            end_sync_in_db(session_id=session_id, status='no_lists')
            return
        
        # Fetch media from lists
        media_items, synced_lists = fetch_media_from_lists(list_ids)
        
        if not media_items:
            logging.warning("No media items found in configured lists")
            print("\n⚠️  No media items found in configured lists.")
            # Log sync end marker for early exit
            sync_end_marker = f"========== SYNC COMPLETE [FULL] - Session: {session_id} - Status: NO_ITEMS =========="
            logging.info(sync_end_marker)
            # Mark sync as ended in database
            end_sync_in_db(session_id=session_id, status='no_items')
            return
        
        # Update sync_history with list information for full syncs
        try:
            update_sync_lists_in_db(session_id=session_id, synced_lists=synced_lists)
        except Exception as e:
            logging.warning(f"Failed to update sync lists in database: {e}")
        
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
            automated_mode=automated_mode,
            sync_id=sync_id,
            session_id=session_id
        )
        
        # Display summary
        summary_text = str(sync_results)
        display_summary(sync_results)
        
        # Send to Discord webhook if configured
        if not dry_run:
            send_to_discord_webhook(summary_text, sync_results, automated=automated_mode)
        
        # Log sync complete with clear marker
        sync_end_marker = f"========== SYNC COMPLETE [FULL] - Session: {session_id} - Status: SUCCESS =========="
        logging.info(sync_end_marker)
        print(color_gradient(f"\n{sync_end_marker}", "#00ff00", "#00aa00"))
        
        # Mark sync as ended in database
        end_sync_in_db(
            session_id=session_id,
            status='completed',
            total_items=sync_results.total_items,
            items_requested=sync_results.results.get('requested', 0),
            items_skipped=sync_results.results.get('skipped', 0),
            items_errors=sync_results.results.get('error', 0)
        )
        
    finally:
        # Clear global session ID to prevent zombie cancellation state
        _current_sync_session_id = None


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
        user_id (Optional[str]): User ID for requests (if None, will be fetched from database)
        is_4k (bool): Whether to request 4K versions
        dry_run (bool): Whether to run in dry-run mode
        
    Returns:
        Dict[str, Any]: Sync results
    """
    global _current_sync_session_id
    
    try:
        # Set up signal handlers for immediate termination support
        setup_sync_signal_handlers()
        
        # Check and rotate logs if necessary before starting sync
        check_and_rotate_logs()
        
        # Generate unique session ID for this sync
        import uuid
        session_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Store session ID globally for signal handlers
        _current_sync_session_id = session_id
        
        try:
            # Track sync start in database
            sync_id = start_sync_in_db(
                session_id=session_id,
                sync_type='single',
                list_type=list_type,
                list_id=list_id
            )
            
            # Register subprocess PID in tracker for immediate termination
            sync_tracker = get_sync_tracker()
            sync_tracker.set_subprocess_pid(os.getpid())
            
            # Log sync start with clear marker
            sync_start_marker = f"========== SYNC START [SINGLE] - Session: {session_id} - List: {list_type}:{list_id} =========="
            logging.info(sync_start_marker)
            print(color_gradient(f"\n{sync_start_marker}", "#00aaff", "#00ffaa"))
            print(color_gradient(f"🎯  Single List Sync: {list_type.upper()}:{list_id}", "#00aaff", "#00ffaa"))
            
            # Get user_id from database if not provided
            if user_id is None:
                from .database import load_list_ids
                lists = load_list_ids()
                for list_item in lists:
                    if list_item['type'] == list_type and list_item['id'] == list_id:
                        user_id = list_item.get('user_id', '1')
                        logging.info(f"Using user_id {user_id} from list configuration")
                        break
                if user_id is None:
                    user_id = '1'  # Default fallback
                    logging.warning(f"List not found in database, using default user_id: 1")
            
            # Validate that the user exists in Overseerr
            from .database import get_overseerr_user_by_id
            user_exists = get_overseerr_user_by_id(user_id)
            if not user_exists:
                logging.warning(f"User ID {user_id} not found in local user database. This may cause issues if the user doesn't exist in Overseerr.")
                # Try to fetch from Overseerr directly
                try:
                    import requests
                    users_url = f"{overseerr_url.rstrip('/')}/api/v1/user"
                    headers = {"X-Api-Key": overseerr_api_key}
                    response = requests.get(users_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        users_data = response.json()
                        users = users_data.get('results', [])
                        user_found = any(str(user.get('id')) == str(user_id) for user in users)
                        if not user_found:
                            logging.warning(f"User ID {user_id} not found in Overseerr. Falling back to default user ID 1.")
                            user_id = '1'
                except Exception as e:
                    logging.warning(f"Failed to validate user in Overseerr: {e}. Proceeding with user_id {user_id}")
            
            # Create Overseerr client with the appropriate user_id
            overseerr_client = OverseerrClient(overseerr_url, overseerr_api_key, user_id)
            
            # Create a single list info dictionary (carry user_id so requests use correct requester)
            single_list_info = [{"type": list_type, "id": list_id, "user_id": user_id}]
            
            # Fetch media from the single list
            media_items, synced_lists = fetch_media_from_lists(single_list_info, is_single_list=True)
            
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
                # Mark sync as ended in database
                end_sync_in_db(session_id=session_id, status='no_items')
                return result
            
            # Sync the media items to Overseerr
            sync_results = sync_media_to_overseerr(
                media_items=media_items,
                overseerr_client=overseerr_client,
                synced_lists=synced_lists,
                is_4k=is_4k,
                dry_run=dry_run,
                automated_mode=True,  # Treat single sync as automated to avoid interactive prompts
                sync_id=sync_id,
                session_id=session_id
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
            
            # Send to Discord webhook if configured (only if not dry run)
            if not dry_run:
                summary_text = f"Single list sync completed for {list_type}:{list_id}"
                send_to_discord_webhook(summary_text, sync_results, automated=True, is_single_list=True)
            
            # Log sync complete with clear marker
            sync_end_marker = f"========== SYNC COMPLETE [SINGLE] - Session: {session_id} - List: {list_type}:{list_id} - Status: SUCCESS =========="
            logging.info(sync_end_marker)
            print(color_gradient(f"\n{sync_end_marker}", "#00ff00", "#00aa00"))
            
            # Mark sync as ended in database
            end_sync_in_db(
                session_id=session_id,
                status='completed',
                total_items=sync_results.total_items,
                items_requested=sync_results.results.get('requested', 0),
                items_skipped=sync_results.results.get('skipped', 0),
                items_errors=sync_results.results.get('error', 0)
            )
            
            return result
        
        finally:
            # Clear global session ID to prevent zombie cancellation state
            _current_sync_session_id = None
            
    except Exception as e:
        error_message = f"Error in single list sync for {list_type}:{list_id}: {str(e)}"
        logging.error(error_message)
        print(color_gradient(f"❌  {error_message}", "#ff0000", "#aa0000"))
        
        # Mark sync as ended in database (even on error)
        try:
            end_sync_in_db(session_id=session_id, status='failed', error_message=str(e))
        except:
            pass
        
        # Log sync complete with error marker
        # Need to generate session_id if we haven't yet (error before session_id creation)
        try:
            import uuid
            session_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            sync_end_marker = f"========== SYNC COMPLETE [SINGLE] - Session: {session_id} - List: {list_type}:{list_id} - Status: ERROR =========="
            logging.info(sync_end_marker)
        except:
            pass
        
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
        
        # Check if setup is complete before proceeding
        from .config import ConfigManager
        config_manager = ConfigManager()
        
        # First, do a silent check (no messages)
        if not config_manager.is_setup_complete():
            # Wait 5 seconds silently to allow migration/initialization to complete
            logging.debug("Setup not complete on first check, waiting 5 seconds for initialization...")
            time.sleep(5)
            
            # Reload config and check again silently
            config_manager.reload()
            
            # If still not complete after 5 seconds, show waiting message
            if not config_manager.is_setup_complete():
                logging.info("Setup not complete. Waiting for configuration...")
                print("\n⏳ ListSync is waiting for initial configuration.")
                print("   Please complete the setup wizard at the web interface.")
                print("   Checking every 30 seconds...\n")
                
                # Wait loop - check every 30 seconds for setup completion
                while not config_manager.is_setup_complete():
                    time.sleep(30)
                    config_manager.reload()  # Reload config from database
                
                logging.info("Setup completed! Starting sync service...")
                print("✅ Configuration detected! Starting sync service...\n")
            else:
                # Setup completed during the 5 second wait
                logging.info("Setup completed during initialization wait! Starting sync service...")
                print("✅ Configuration detected! Starting sync service...\n")
        
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
