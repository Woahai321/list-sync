# list_sync/overseerr.py

import requests
import logging
from urllib.parse import quote
from .utils import color_gradient
from .database import save_sync_result

def test_overseerr_api(overseerr_url, api_key):
    """Test the connection to the Overseerr API."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    test_url = f"{overseerr_url}/api/v1/status"
    try:
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        print(color_gradient("🎉  API connection successful!", "#00ff00", "#00aa00"))
        logging.info("Overseerr API connection successful!")
    except Exception as e:
        print(color_gradient(f"❌  Overseerr API connection failed. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Overseerr API connection failed. Error: {str(e)}")
        raise

def search_media_in_overseerr(overseerr_url, api_key, media_title, media_type):
    """Search for media in Overseerr."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    search_url = f"{overseerr_url}/api/v1/search?query={quote(media_title)}"
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        search_results = response.json()
        logging.debug(f'Search response for "{media_title}": {search_results}')

        for result in search_results.get("results", []):
            if (media_type in ["show", "tv"] and result["mediaType"] == "tv") or (result["mediaType"] == media_type):
                return {
                    "id": result["id"],
                    "mediaType": result["mediaType"],
                }
        logging.warning(f'No matching results found for "{media_title}" of type "{media_type}"')
        return None
    except Exception as e:
        logging.error(f'Error searching for {media_type} "{media_title}": {str(e)}')
        raise

def request_media_in_overseerr(overseerr_url, api_key, media_id, media_type):
    """Request media in Overseerr."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    request_url = f"{overseerr_url}/api/v1/request"
    payload = {
        "mediaId": media_id,
        "mediaType": media_type,
        "is4k": False
    }
    try:
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.debug(f"Request response for {media_type} ID {media_id}: {response.json()}")
        return "success"
    except Exception as e:
        logging.error(f"Error requesting {media_type} ID {media_id}: {str(e)}")
        return "error"

def request_tv_series_in_overseerr(overseerr_url, api_key, tv_id, number_of_seasons):
    """Request all seasons of a TV series in Overseerr."""
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    request_url = f"{overseerr_url}/api/v1/request"
    
    seasons_list = [i for i in range(1, number_of_seasons + 1)]
    logging.debug(f"Seasons list for TV series ID {tv_id}: {seasons_list}")
    
    payload = {
        "mediaId": tv_id,
        "mediaType": "tv",
        "is4k": False,
        "seasons": seasons_list
    }
    
    logging.debug(f"Request payload for TV series ID {tv_id}: {payload}")

    try:
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.debug(f"Request response for TV series ID {tv_id}: {response.json()}")
        return "success"
    except Exception as e:
        logging.error(f"Error requesting TV series ID {tv_id}: {str(e)}")
        return "error"
