"""
Steven Lu popular movies provider for ListSync.
"""

import logging
from typing import Any, Dict, List

import requests

from . import register_provider


@register_provider("stevenlu")
def fetch_stevenlu_list(list_id=None) -> List[Dict[str, Any]]:
    """
    Fetch Steven Lu's popular movies list from the JSON endpoint
    
    Args:
        list_id: Unused parameter for consistency with other providers
        
    Returns:
        List[Dict[str, Any]]: List of media items
    """
    media_items = []
    logging.info("Fetching Steven Lu's popular movies list...")

    try:
        # The list_id parameter is ignored as there's only one list
        json_url = "https://s3.amazonaws.com/popular-movies/movies.json"

        logging.info(f"Attempting to fetch Steven Lu movies from: {json_url}")
        response = requests.get(json_url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        movies_data = response.json()
        logging.info(f"Found {len(movies_data)} movies in Steven Lu's list")

        for movie in movies_data:
            try:
                title = movie.get("title", "").strip()
                imdb_id = movie.get("imdb_id")

                if not title:
                    logging.warning(f"Skipping movie with empty title: {movie}")
                    continue

                # All items from this source are movies
                media_items.append({
                    "title": title,
                    "imdb_id": imdb_id,
                    "media_type": "movie",
                    "year": None,  # Year is not provided in this data source
                })
                logging.info(f"Added movie: {title} (IMDB ID: {imdb_id})")

            except Exception as e:
                logging.warning(f"Failed to parse movie data: {e!s}")
                continue

        logging.info(f"Steven Lu list fetched successfully. Found {len(media_items)} movies.")
        return media_items

    except Exception as e:
        logging.exception(f"Error fetching Steven Lu list: {e!s}")
        raise
