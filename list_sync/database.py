"""
Database operations for ListSync.
"""

import sqlite3
import os
from typing import Dict, List, Optional

from .utils.logger import DATA_DIR

# Define database file path
DB_FILE = os.path.join(DATA_DIR, "list_sync.db")


def init_database():
    """Initialize the SQLite database with required tables."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_type TEXT NOT NULL,
                list_id TEXT NOT NULL,
                UNIQUE(list_type, list_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synced_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL,
                imdb_id TEXT,
                overseerr_id INTEGER,
                status TEXT,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_interval (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interval_hours REAL NOT NULL
            )
        ''')
        conn.commit()


def save_list_id(list_id: str, list_type: str):
    """Save list ID to database, converting URLs to IDs if needed."""
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
            
        cursor.execute(
            "INSERT OR REPLACE INTO lists (list_type, list_id) VALUES (?, ?)",
            (list_type, id_to_save)
        )
        conn.commit()


def load_list_ids() -> List[Dict[str, str]]:
    """Load all saved list IDs from database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT list_type, list_id FROM lists")
        return [{"type": row[0], "id": row[1]} for row in cursor.fetchall()]


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
        import logging
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


def save_sync_result(title: str, media_type: str, imdb_id: Optional[str], overseerr_id: Optional[int], status: str):
    """Save the result of a sync operation."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO synced_items 
            (title, media_type, imdb_id, overseerr_id, status, last_synced)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (title, media_type, imdb_id, overseerr_id, status))
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
