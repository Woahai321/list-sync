"""
Collections provider for ListSync.
Loads popular movie collections from JSON file and provides them as a list source.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from . import register_provider

# Path to the popular collections JSON file
COLLECTIONS_FILE = Path(__file__).parent / "popular-collections-revised.json"

# Cache for loaded collections data
_collections_cache: Optional[Dict[str, Any]] = None
_cache_file_mtime: Optional[float] = None


def _load_collections() -> Dict[str, Any]:
    """Load collections data from JSON file with caching and auto-reload on file change."""
    global _collections_cache, _cache_file_mtime
    
    # Check if file has been modified since last load
    if _collections_cache is not None and COLLECTIONS_FILE.exists():
        try:
            current_mtime = COLLECTIONS_FILE.stat().st_mtime
            if _cache_file_mtime is not None and current_mtime == _cache_file_mtime:
                # File hasn't changed, return cached data
                return _collections_cache
            # File has changed, clear cache and reload
            logging.info(f"Collections file modified, reloading...")
            _collections_cache = None
        except OSError:
            # File might have been deleted, clear cache
            _collections_cache = None
            _cache_file_mtime = None
    
    try:
        if not COLLECTIONS_FILE.exists():
            logging.error(f"Collections file not found: {COLLECTIONS_FILE}")
            return {"collections": [], "totalCollections": 0}
        
        with open(COLLECTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update cache and modification time
        _collections_cache = data
        _cache_file_mtime = COLLECTIONS_FILE.stat().st_mtime
        
        # Update totalCollections count based on actual collections array length
        actual_count = len(data.get("collections", []))
        if "totalCollections" not in data or data.get("totalCollections") != actual_count:
            data["totalCollections"] = actual_count
        
        logging.info(f"Loaded {actual_count} collections from JSON file")
        return data
    except Exception as e:
        logging.error(f"Error loading collections file: {str(e)}")
        return {"collections": [], "totalCollections": 0}


def clear_collections_cache():
    """Clear the collections cache to force reload on next access."""
    global _collections_cache, _cache_file_mtime
    _collections_cache = None
    _cache_file_mtime = None
    logging.info("Collections cache cleared")


def get_all_collections() -> List[Dict[str, Any]]:
    """
    Get all collections with their metadata.
    
    Returns:
        List[Dict[str, Any]]: List of all collections
    """
    data = _load_collections()
    return data.get("collections", [])


def get_collection_by_name(franchise_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific collection by franchise name.
    
    Args:
        franchise_name (str): The franchise name (e.g., "Harry Potter Collection")
        
    Returns:
        Optional[Dict[str, Any]]: Collection data or None if not found
    """
    collections = get_all_collections()
    for collection in collections:
        if collection.get("franchise") == franchise_name:
            return collection
    return None


def get_oldest_movie_id(collection: Dict[str, Any]) -> Optional[int]:
    """
    Find the movie ID with the most votes from a collection for poster fetching.
    Uses the most popular/voted movie instead of the oldest.
    
    Args:
        collection (Dict[str, Any]): Collection data
        
    Returns:
        Optional[int]: TMDB ID of the movie with most votes, or None if not found
    """
    movie_ratings = collection.get("movieRatings", [])
    if not movie_ratings:
        # Fallback to movieIds if movieRatings not available
        movie_ids = collection.get("movieIds", [])
        return movie_ids[0] if movie_ids else None
    
    # Find movie with most votes
    most_voted_movie = None
    max_votes = 0
    
    for movie in movie_ratings:
        vote_count = movie.get("voteCount", 0)
        if vote_count and vote_count > max_votes:
            max_votes = vote_count
            most_voted_movie = movie
    
    if most_voted_movie:
        return most_voted_movie.get("id")
    
    # Fallback to first movie ID if no votes found
    movie_ids = collection.get("movieIds", [])
    return movie_ids[0] if movie_ids else None


@register_provider("collections")
def fetch_collection(franchise_name: str) -> List[Dict[str, Any]]:
    """
    Fetch movies from a collection by franchise name.
    
    Args:
        franchise_name (str): The franchise name (e.g., "Harry Potter Collection")
        
    Returns:
        List[Dict[str, Any]]: List of media items in standard format
    """
    collection = get_collection_by_name(franchise_name)
    
    if not collection:
        logging.warning(f"Collection not found: {franchise_name}")
        return []
    
    movie_items = []
    movie_ratings = collection.get("movieRatings", [])
    movie_ids = collection.get("movieIds", [])
    
    # Create a map of movie ID to rating data for quick lookup
    rating_map = {movie.get("id"): movie for movie in movie_ratings}
    
    # Process each movie ID
    for movie_id in movie_ids:
        # Get rating data if available
        movie_data = rating_map.get(movie_id, {})
        
        # Extract title
        title = movie_data.get("title", "")
        if not title:
            # If no title in rating data, we'll need to fetch it later
            # For now, use a placeholder
            title = f"Movie {movie_id}"
        
        # Extract year from release date
        year = None
        release_date = movie_data.get("releaseDate")
        if release_date:
            try:
                # Extract year from YYYY-MM-DD format
                year = int(release_date.split("-")[0])
            except (ValueError, AttributeError):
                pass
        
        # Extract IMDB ID if available (enables fast IMDB → Trakt → TMDB lookup path)
        imdb_id = movie_data.get("imdb_id")
        
        # Create item in standard format
        # Ensure movie_id is an integer (may be string from JSON)
        try:
            movie_id_int = int(movie_id)
        except (ValueError, TypeError):
            logging.warning(f"Invalid movie ID in collection: {movie_id} (type: {type(movie_id)})")
            continue  # Skip this item
        
        item = {
            "title": title,
            "media_type": "movie",  # Collections are all movies
            "year": year,
            "tmdb_id": movie_id_int,  # Keep as integer, not string
            "imdb_id": imdb_id  # Include IMDB ID if available (enables fast lookup path)
        }
        
        movie_items.append(item)
    
    logging.info(f"Fetched {len(movie_items)} movies from collection: {franchise_name}")
    return movie_items

