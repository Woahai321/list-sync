"""
Database operations for ListSync.
"""

import sqlite3
import os
import logging
from typing import Dict, List, Optional, Any

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


def remove_simkl_column():
    """Remove the simkl_id column from synced_items table since SIMKL is disabled."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Check if simkl_id column exists
        cursor.execute("PRAGMA table_info(synced_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'simkl_id' in columns:
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            logging.info("Removing simkl_id column from synced_items table")
            
            # Create new table without simkl_id column
            cursor.execute('''
                CREATE TABLE synced_items_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    year INTEGER,
                    imdb_id TEXT,
                    tmdb_id TEXT,
                    overseerr_id INTEGER,
                    status TEXT,
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data from old table to new table (excluding simkl_id)
            cursor.execute('''
                INSERT INTO synced_items_new (id, title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, last_synced)
                SELECT id, title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, last_synced
                FROM synced_items
            ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE synced_items')
            cursor.execute('ALTER TABLE synced_items_new RENAME TO synced_items')
            
            conn.commit()
            logging.info("Successfully removed simkl_id column from synced_items table")
        else:
            logging.info("simkl_id column does not exist in synced_items table")

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
        
        # Add tmdb_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE synced_items ADD COLUMN tmdb_id TEXT')
            logging.info("Added tmdb_id column to synced_items table")
        except sqlite3.OperationalError:
            # Column already exists or other error
            pass
        
        # SIMKL is disabled, so we don't add simkl_id column anymore
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_interval (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interval_hours REAL NOT NULL
            )
        ''')
        
        # Junction table to track which lists each item came from
        # This allows many-to-many relationship (one item can come from multiple lists)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                list_type TEXT NOT NULL,
                list_id TEXT NOT NULL,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES synced_items(id) ON DELETE CASCADE,
                UNIQUE(item_id, list_type, list_id)
            )
        ''')
        
        # Create index for faster lookups
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_lists_item_id ON item_lists(item_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_lists_list ON item_lists(list_type, list_id)')
        except sqlite3.OperationalError:
            # Indexes might already exist
            pass
        
        # Sync history table - tracks all sync operations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                sync_type TEXT NOT NULL,
                in_progress INTEGER DEFAULT 1,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT,
                list_type TEXT,
                list_id TEXT,
                pid INTEGER,
                total_items INTEGER DEFAULT 0,
                items_requested INTEGER DEFAULT 0,
                items_skipped INTEGER DEFAULT 0,
                items_errors INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        # Sync items table - tracks individual items processed during each sync
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_id INTEGER NOT NULL,
                item_id INTEGER,
                title TEXT,
                media_type TEXT,
                year INTEGER,
                imdb_id TEXT,
                tmdb_id TEXT,
                overseerr_id INTEGER,
                status TEXT,
                list_type TEXT,
                list_id TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sync_id) REFERENCES sync_history(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES synced_items(id) ON DELETE SET NULL
            )
        ''')
        
        # Create indexes for sync tables
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_history_in_progress ON sync_history(in_progress)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_history_session_id ON sync_history(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_history_start_time ON sync_history(start_time DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_items_sync_id ON sync_items(sync_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_items_item_id ON sync_items(item_id)')
        except sqlite3.OperationalError:
            # Indexes might already exist
            pass
        
        conn.commit()
    
    # Migrate existing lists to populate URLs and add item_count column
    migrate_list_urls()
    
    # Remove SIMKL column since SIMKL is disabled
    remove_simkl_column()
    
    # Initialize configuration tables
    create_settings_tables()


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


def save_sync_result(title: str, media_type: str, imdb_id: Optional[str], overseerr_id: Optional[int], status: str, year: Optional[int] = None, tmdb_id: Optional[str] = None, list_type: Optional[str] = None, list_id: Optional[str] = None):
    """
    Save the result of a sync operation and track which list(s) it came from.
    
    Args:
        title: Media title
        media_type: Media type (movie/tv)
        imdb_id: IMDb ID
        overseerr_id: Overseerr ID
        status: Sync status
        year: Release year
        tmdb_id: TMDB ID
        list_type: Type of list this item came from (e.g., 'imdb', 'trakt')
        list_id: ID of the list this item came from
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Get or create the item record
        # Try to find existing item by multiple possible keys (overseerr_id is most reliable)
        item_db_id = None
        
        # Try overseerr_id first (most reliable)
        if overseerr_id:
            cursor.execute('SELECT id FROM synced_items WHERE overseerr_id = ?', (overseerr_id,))
            existing = cursor.fetchone()
            if existing:
                item_db_id = existing[0]
        
        # If not found by overseerr_id, try imdb_id
        if not item_db_id and imdb_id:
            cursor.execute('SELECT id FROM synced_items WHERE imdb_id = ?', (imdb_id,))
            existing = cursor.fetchone()
            if existing:
                item_db_id = existing[0]
        
        # If still not found, try tmdb_id
        if not item_db_id and tmdb_id:
            cursor.execute('SELECT id FROM synced_items WHERE tmdb_id = ?', (tmdb_id,))
            existing = cursor.fetchone()
            if existing:
                item_db_id = existing[0]
        
        if status == "skipped":
            # For skipped items, only insert if it doesn't exist (don't update last_synced)
            if item_db_id:
                # Item already exists, just update status if needed
                cursor.execute('''
                    UPDATE synced_items 
                    SET status = ?, title = ?, media_type = ?, year = ?, imdb_id = ?, tmdb_id = ?
                    WHERE id = ?
                ''', (status, title, media_type, year, imdb_id, tmdb_id, item_db_id))
            else:
                # Insert new item
                cursor.execute('''
                    INSERT INTO synced_items 
                    (title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, last_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (title, media_type, year, imdb_id, tmdb_id, overseerr_id, status))
                item_db_id = cursor.lastrowid
        else:
            # For non-skipped items, update last_synced timestamp
            if item_db_id:
                # Update existing item
                cursor.execute('''
                    UPDATE synced_items 
                    SET title = ?, media_type = ?, year = ?, imdb_id = ?, tmdb_id = ?, 
                        overseerr_id = ?, status = ?, last_synced = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, item_db_id))
            else:
                # Insert new item
                cursor.execute('''
                    INSERT INTO synced_items 
                    (title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, last_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (title, media_type, year, imdb_id, tmdb_id, overseerr_id, status))
                item_db_id = cursor.lastrowid
        
        # Link item to list(s) if list information provided
        if item_db_id and list_type and list_id:
            cursor.execute('''
                INSERT OR IGNORE INTO item_lists (item_id, list_type, list_id, synced_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (item_db_id, list_type, list_id))
        
        conn.commit()
        
        return item_db_id


def get_item_lists(item_id: int) -> List[Dict[str, str]]:
    """
    Get all lists that an item came from.
    
    Args:
        item_id: The database ID of the item
        
    Returns:
        List of dictionaries with 'type' and 'id' keys for each list
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT list_type, list_id 
            FROM item_lists 
            WHERE item_id = ?
        ''', (item_id,))
        results = []
        for row in cursor.fetchall():
            results.append({'type': row[0], 'id': row[1]})
        return results


def get_list_items(list_type: str, list_id: str) -> List[Dict[str, Any]]:
    """
    Get all items that came from a specific list.
    
    Args:
        list_type: Type of list (e.g., 'imdb', 'trakt')
        list_id: ID of the list
        
    Returns:
        List of item dictionaries with all item information
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT si.id, si.title, si.media_type, si.year, si.imdb_id, si.tmdb_id, 
                   si.overseerr_id, si.status, si.last_synced
            FROM synced_items si
            INNER JOIN item_lists il ON si.id = il.item_id
            WHERE il.list_type = ? AND il.list_id = ?
            ORDER BY si.last_synced DESC
        ''', (list_type, list_id))
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'media_type': row[2],
                'year': row[3],
                'imdb_id': row[4],
                'tmdb_id': row[5],
                'overseerr_id': row[6],
                'status': row[7],
                'last_synced': row[8]
            })
        return results


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


# ============================================================================
# Sync History Management - Database-Based Sync Tracking
# ============================================================================

def start_sync_in_db(
    session_id: str,
    sync_type: str,
    list_type: Optional[str] = None,
    list_id: Optional[str] = None,
    pid: Optional[int] = None
) -> int:
    """
    Start a sync operation in the database.
    
    Args:
        session_id: Unique session identifier
        sync_type: 'full' or 'single'
        list_type: List type for single list syncs (optional)
        list_id: List ID for single list syncs (optional)
        pid: Process ID (optional)
    
    Returns:
        int: The sync_id (primary key) of the created sync record
    """
    import os
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sync_history (
                session_id, sync_type, in_progress, start_time,
                list_type, list_id, pid, status
            ) VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?, ?, ?, 'running')
        ''', (session_id, sync_type, list_type, list_id, pid or os.getpid()))
        sync_id = cursor.lastrowid
        conn.commit()
        logging.info(f"Started sync in database: session_id={session_id}, sync_id={sync_id}")
        return sync_id


def end_sync_in_db(
    session_id: str,
    status: str = 'completed',
    total_items: int = 0,
    items_requested: int = 0,
    items_skipped: int = 0,
    items_errors: int = 0,
    error_message: Optional[str] = None
) -> bool:
    """
    End a sync operation in the database.
    
    Args:
        session_id: Session identifier
        status: Final status ('completed', 'failed', 'no_lists', 'no_items', etc.)
        total_items: Total items processed
        items_requested: Items successfully requested
        items_skipped: Items skipped
        items_errors: Items with errors
        error_message: Error message if any
    
    Returns:
        bool: True if updated successfully
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sync_history
            SET in_progress = 0,
                end_time = CURRENT_TIMESTAMP,
                status = ?,
                total_items = ?,
                items_requested = ?,
                items_skipped = ?,
                items_errors = ?,
                error_message = ?
            WHERE session_id = ?
        ''', (status, total_items, items_requested, items_skipped, items_errors, error_message, session_id))
        updated = cursor.rowcount > 0
        conn.commit()
        if updated:
            logging.info(f"Ended sync in database: session_id={session_id}, status={status}")
        else:
            logging.warning(f"Sync not found in database: session_id={session_id}")
        return updated


def add_item_to_sync(
    sync_id: int,
    item_id: Optional[int],
    title: str,
    media_type: str,
    status: str,
    list_type: Optional[str] = None,
    list_id: Optional[str] = None,
    year: Optional[int] = None,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    overseerr_id: Optional[int] = None
) -> int:
    """
    Add an item to a sync operation.
    
    Args:
        sync_id: The sync history record ID
        item_id: The synced_items ID (if item exists in database)
        title: Item title
        media_type: 'movie' or 'tv'
        status: Item processing status ('requested', 'skipped', 'error', etc.)
        list_type: Source list type
        list_id: Source list ID
        year: Release year
        imdb_id: IMDB ID
        tmdb_id: TMDB ID
        overseerr_id: Overseerr ID
    
    Returns:
        int: The sync_items record ID
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sync_items (
                sync_id, item_id, title, media_type, year,
                imdb_id, tmdb_id, overseerr_id, status,
                list_type, list_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sync_id, item_id, title, media_type, year, imdb_id, tmdb_id, overseerr_id, status, list_type, list_id))
        item_record_id = cursor.lastrowid
        conn.commit()
        return item_record_id


def get_current_sync_status() -> Optional[Dict[str, Any]]:
    """
    Get the current in-progress sync status from database.
    
    Returns:
        dict: Current sync status or None if no sync in progress
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sync_history
            WHERE in_progress = 1
            ORDER BY start_time DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_sync_history(limit: int = 50, include_completed: bool = True) -> List[Dict[str, Any]]:
    """
    Get sync history from database.
    
    Args:
        limit: Maximum number of records to return
        include_completed: Whether to include completed syncs
    
    Returns:
        list: List of sync history records
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if include_completed:
            cursor.execute('''
                SELECT * FROM sync_history
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT * FROM sync_history
                WHERE in_progress = 1
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_sync_items(sync_id: int) -> List[Dict[str, Any]]:
    """
    Get all items processed during a sync.
    
    Args:
        sync_id: The sync history record ID
    
    Returns:
        list: List of sync items
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sync_items
            WHERE sync_id = ?
            ORDER BY processed_at
        ''', (sync_id,))
        return [dict(row) for row in cursor.fetchall()]


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


# ============================================================================
# Configuration Management - Database-Backed Settings
# ============================================================================

def create_settings_tables():
    """
    Create app_settings and setup_status tables for database-backed configuration.
    Called during database initialization.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # App settings table - stores all configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                is_encrypted INTEGER DEFAULT 0,
                setting_type TEXT DEFAULT 'string',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Setup status table - tracks if initial wizard completed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setup_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_completed INTEGER DEFAULT 0,
                completed_at TEXT,
                setup_version TEXT DEFAULT '1.0'
            )
        ''')
        
        # Initialize setup_status row if it doesn't exist
        cursor.execute('''
            INSERT OR IGNORE INTO setup_status (id, is_completed)
            VALUES (1, 0)
        ''')
        
        conn.commit()
        logging.info("Configuration tables initialized")


def save_setting(key: str, value: str, is_encrypted: bool = False, setting_type: str = 'string'):
    """
    Save a configuration setting to the database.
    
    Args:
        key: Setting key name
        value: Setting value (already encrypted if is_encrypted=True)
        is_encrypted: Whether the value is encrypted
        setting_type: Type of setting (string, boolean, integer, list)
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO app_settings 
            (key, value, is_encrypted, setting_type, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value, 1 if is_encrypted else 0, setting_type))
        conn.commit()


def get_setting(key: str) -> Optional[tuple]:
    """
    Get a configuration setting from the database.
    
    Args:
        key: Setting key name
    
    Returns:
        tuple: (value, is_encrypted, setting_type) or None if not found
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value, is_encrypted, setting_type
            FROM app_settings
            WHERE key = ?
        ''', (key,))
        result = cursor.fetchone()
        return result if result else None


def get_all_settings() -> Dict[str, tuple]:
    """
    Get all configuration settings from the database.
    
    Returns:
        dict: Dictionary of {key: (value, is_encrypted, setting_type)}
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key, value, is_encrypted, setting_type
            FROM app_settings
        ''')
        results = cursor.fetchall()
        return {row[0]: (row[1], row[2], row[3]) for row in results}


def delete_setting(key: str):
    """Delete a configuration setting from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM app_settings WHERE key = ?', (key,))
        conn.commit()


def is_setup_completed() -> bool:
    """Check if the initial setup wizard has been completed."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_completed FROM setup_status WHERE id = 1')
        result = cursor.fetchone()
        return bool(result[0]) if result else False


def mark_setup_complete():
    """Mark the initial setup wizard as completed."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE setup_status
            SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''')
        conn.commit()
        logging.info("Setup marked as completed in database")


def reset_setup_status():
    """Reset setup status (for testing/debugging)."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE setup_status
            SET is_completed = 0, completed_at = NULL
            WHERE id = 1
        ''')
        conn.commit()


def count_settings() -> int:
    """Count the number of settings in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM app_settings')
        result = cursor.fetchone()
        return result[0] if result else 0
