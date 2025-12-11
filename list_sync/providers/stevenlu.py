"""
Steven Lu popular movies provider for ListSync.
"""

import logging
import requests
from typing import List, Dict, Any

from . import register_provider


@register_provider("stevenlu")
def fetch_stevenlu_list(list_id=None) -> List[Dict[str, Any]]:
    """
    Fetch Steven Lu's popular movies list from the JSON endpoint
    
    Args:
        list_id: JSON URL or preset identifier (e.g., "stevenlu", "movies-metacritic-min70.json", or full URL)
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    
    # Determine the JSON URL
    if not list_id or list_id == "stevenlu":
        # Default to original list
        json_url = "https://s3.amazonaws.com/popular-movies/movies.json"
    elif list_id.startswith("http://") or list_id.startswith("https://"):
        # Full URL provided
        json_url = list_id
    elif list_id.endswith(".json"):
        # Just the filename, construct full URL
        json_url = f"https://movies.stevenlu.com/{list_id}"
    else:
        # Preset identifier, construct URL
        json_url = f"https://movies.stevenlu.com/{list_id}.json" if not list_id.endswith(".json") else f"https://movies.stevenlu.com/{list_id}"
    
    logging.info(f"Fetching Steven Lu movies from: {json_url}")
    
    try:
        response = requests.get(json_url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        movies_data = response.json()
        logging.info(f"Found {len(movies_data)} movies in Steven Lu's list")
        
        # Import Trakt search function for enrichment
        from .trakt import search_trakt_by_imdb_id
        
        logging.info(f"Enriching items with year data from Trakt API...")
        items_enriched = 0
        
        for idx, movie in enumerate(movies_data):
            try:
                title = movie.get('title', '').strip()
                imdb_id = movie.get('imdb_id')
                tmdb_id = movie.get('tmdb_id')
                
                if not title:
                    logging.warning(f"Skipping movie with empty title: {movie}")
                    continue
                
                # Enrich with year data from Trakt if imdb_id is available
                year = None
                if imdb_id:
                    try:
                        trakt_result = search_trakt_by_imdb_id(imdb_id)
                        if trakt_result and trakt_result.get('year'):
                            year = trakt_result['year']
                            items_enriched += 1
                    except Exception as e:
                        logging.debug(f"Could not enrich '{title}' (IMDB: {imdb_id}) with Trakt: {e}")
                
                # All items from this source are movies
                media_items.append({
                    "title": title,
                    "imdb_id": imdb_id,
                    "tmdb_id": tmdb_id,
                    "media_type": "movie",
                    "year": year  # Enriched from Trakt API
                })
                
                # Log progress every 50 items
                if len(media_items) % 50 == 0:
                    year_str = f"({year})" if year else "(year unknown)"
                    logging.info(f"Progress: {len(media_items)}/{len(movies_data)} items processed, {items_enriched} enriched with year data")
                elif len(media_items) <= 3:
                    year_str = f"({year})" if year else "(year unknown)"
                    logging.info(f"Added movie: {title} {year_str} (IMDB: {imdb_id}, TMDB: {tmdb_id})")
                
            except Exception as e:
                logging.warning(f"Failed to parse movie data: {str(e)}")
                continue
        
        logging.info(f"Steven Lu list fetched successfully. Found {len(media_items)} movies.")
        logging.info(f"Successfully enriched {items_enriched}/{len(media_items)} items with year data from Trakt API")
        return media_items
        
    except Exception as e:
        logging.error(f"Error fetching Steven Lu list from {json_url}: {str(e)}")
        raise
