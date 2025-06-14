"""
Database operations for ListSync.
"""

import sqlite3
import os
import logging
from typing import Dict, List, Optional

from .utils.logger import DATA_DIR

# Define database file path
DB_FILE = os.path.join(DATA_DIR, "list_sync.db")


def update_existing_list_urls():
    """Update URLs for existing lists that may have incorrect URLs stored."""
    from .utils.helpers import construct_list_url
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Get all lists to check their URLs
        cursor.execute("SELECT list_type, list_id, list_url FROM lists")
        all_lists = cursor.fetchall()
        
        updated_count = 0
        for list_type, list_id, current_url in all_lists:
            try:
                # Generate the correct URL
                correct_url = construct_list_url(list_type, list_id)
                
                # Update if the URLs don't match
                if current_url != correct_url:
                    cursor.execute(
                        "UPDATE lists SET list_url = ? WHERE list_type = ? AND list_id = ?",
                        (correct_url, list_type, list_id)
                    )
                    updated_count += 1
                    logging.info(f"Updated URL for {list_type} list {list_id}: {current_url} -> {correct_url}")
                    
            except Exception as e:
                logging.warning(f"Failed to update URL for {list_type} list {list_id}: {e}")
        
        if updated_count > 0:
            conn.commit()
            logging.info(f"Updated {updated_count} list URLs")
        else:
            logging.info("All list URLs are correct")


def migrate_list_urls():
    """Migrate existing lists to populate missing URLs and add item_count and last_synced columns."""
    from .utils.helpers import construct_list_url
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Add item_count column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE lists ADD COLUMN item_count INTEGER DEFAULT 0')
            logging.info("Added item_count column to lists table")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Add last_synced column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE lists ADD COLUMN last_synced TIMESTAMP')
            logging.info("Added last_synced column to lists table")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Get all lists that don't have URLs
        cursor.execute("SELECT list_type, list_id FROM lists WHERE list_url IS NULL OR list_url = ''")
        lists_without_urls = cursor.fetchall()
        
        if lists_without_urls:
            logging.info(f"Migrating {len(lists_without_urls)} lists to add URLs")
            
            for list_type, list_id in lists_without_urls:
                try:
                    list_url = construct_list_url(list_type, list_id)
                    cursor.execute(
                        "UPDATE lists SET list_url = ? WHERE list_type = ? AND list_id = ?",
                        (list_url, list_type, list_id)
                    )
                    logging.info(f"Added URL for {list_type} list {list_id}: {list_url}")
                except Exception as e:
                    logging.warning(f"Failed to generate URL for {list_type} list {list_id}: {e}")
            
            conn.commit()
            logging.info("URL migration completed")
        
        # Also update any existing URLs that might be incorrect
        update_existing_list_urls()


def init_database():
    """Initialize the SQLite database with required tables."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_type TEXT NOT NULL,
                list_id TEXT NOT NULL,
                list_url TEXT,
                item_count INTEGER DEFAULT 0,
                last_synced TIMESTAMP,
                UNIQUE(list_type, list_id)
            )
        ''')
        
        # Add list_url column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE lists ADD COLUMN list_url TEXT')
        except sqlite3.OperationalError:
            # Column already exists or other error
            pass
        
        # Add item_count column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE lists ADD COLUMN item_count INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            # Column already exists or other error
            pass
        
        # Add last_synced column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE lists ADD COLUMN last_synced TIMESTAMP')
        except sqlite3.OperationalError:
            # Column already exists or other error
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synced_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL,
                year INTEGER,
                imdb_id TEXT,
                overseerr_id INTEGER,
                status TEXT,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add year column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE synced_items ADD COLUMN year INTEGER')
            logging.info("Added year column to synced_items table")
        except sqlite3.OperationalError:
            # Column already exists or other error
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_interval (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interval_hours REAL NOT NULL
            )
        ''')
        conn.commit()
    
    # Migrate existing lists to populate URLs and add item_count column
    migrate_list_urls()


def save_list_id(list_id: str, list_type: str, list_url: Optional[str] = None, item_count: Optional[int] = None):
    """Save list ID, URL, and item count to database, converting URLs to IDs if needed."""
    from .utils.helpers import construct_list_url
    
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
        # For MDBList URLs, store the full URL
        elif list_type == "mdblist" and list_id.startswith(('http://', 'https://')):
            id_to_save = list_id.rstrip('/')
        else:
            # For traditional IDs (ls, ur, numeric) or MDBList username/listname format, store as is
            id_to_save = list_id
        
        # Generate URL if not provided
        if list_url is None:
            list_url = construct_list_url(list_type, id_to_save)
        
        # Set default item count if not provided
        if item_count is None:
            item_count = 0
            
        cursor.execute(
            "INSERT OR REPLACE INTO lists (list_type, list_id, list_url, item_count) VALUES (?, ?, ?, ?)",
            (list_type, id_to_save, list_url, item_count)
        )
        conn.commit()


def update_list_item_count(list_type: str, list_id: str, item_count: int):
    """Update the item count for an existing list."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lists SET item_count = ? WHERE list_type = ? AND list_id = ?",
            (item_count, list_type, list_id)
        )
        conn.commit()


def update_list_last_synced(list_type: str, list_id: str):
    """Update the last_synced timestamp for a list to the current time."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lists SET last_synced = CURRENT_TIMESTAMP WHERE list_type = ? AND list_id = ?",
            (list_type, list_id)
        )
        conn.commit()


def update_list_sync_info(list_type: str, list_id: str, item_count: int):
    """Update both item count and last_synced timestamp for a list."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lists SET item_count = ?, last_synced = CURRENT_TIMESTAMP WHERE list_type = ? AND list_id = ?",
            (item_count, list_type, list_id)
        )
        conn.commit()


def load_list_ids() -> List[Dict[str, str]]:
    """Load all saved list IDs from database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT list_type, list_id, list_url, item_count, last_synced FROM lists")
        results = []
        for row in cursor.fetchall():
            list_item = {"type": row[0], "id": row[1]}
            # Handle cases where list_url might be None (for existing databases)
            if len(row) > 2 and row[2]:
                list_item["url"] = row[2]
            else:
                # Generate URL if missing
                from .utils.helpers import construct_list_url
                list_item["url"] = construct_list_url(row[0], row[1])
            
            # Add item count (default to 0 if None)
            if len(row) > 3 and row[3] is not None:
                list_item["item_count"] = row[3]
            else:
                list_item["item_count"] = 0
            
            # Add last_synced timestamp
            if len(row) > 4 and row[4] is not None:
                list_item["last_synced"] = row[4]
            else:
                list_item["last_synced"] = None
                
            results.append(list_item)
        return results


def delete_list(list_type: str, list_id: str) -> bool:
    """Delete a list from the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM lists WHERE list_type = ? AND list_id = ?",
                (list_type, list_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logging.error(f"Error deleting list: {str(e)}")
        return False


def configure_sync_interval(interval_hours: float):
    """Configure the sync interval in hours (can be decimal like 0.5 for 30 minutes)."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_interval")
        cursor.execute("INSERT INTO sync_interval (interval_hours) VALUES (?)", (interval_hours,))
        conn.commit()


def load_sync_interval() -> float:
    """Load the configured sync interval."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT interval_hours FROM sync_interval")
        result = cursor.fetchone()
        return result[0] if result else 0.0  # Default to 0.0 hours if not set


def should_sync_item(overseerr_id: int) -> bool:
    """Check if an item should be synced based on last sync time."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT last_synced FROM synced_items
            WHERE overseerr_id = ?
            AND last_synced > datetime('now', '-48 hours')
        ''', (overseerr_id,))
        result = cursor.fetchone()
        return result is None


def save_sync_result(title: str, media_type: str, imdb_id: Optional[str], overseerr_id: Optional[int], status: str, year: Optional[int] = None):
    """Save the result of a sync operation."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO synced_items 
            (title, media_type, year, imdb_id, overseerr_id, status, last_synced)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (title, media_type, year, imdb_id, overseerr_id, status))
        conn.commit()


def clear_all_lists():
    """Clear all lists from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        conn.commit()


def get_sync_stats() -> Dict[str, int]:
    """Get sync statistics from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM synced_items 
            WHERE last_synced > datetime('now', '-7 days') 
            GROUP BY status
        ''')
        stats = dict(cursor.fetchall())
        return stats


def cleanup_old_sync_results(days: int = 30):
    """Clean up sync results older than specified days."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM synced_items 
            WHERE last_synced < datetime('now', '-{} days')
        '''.format(days))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
