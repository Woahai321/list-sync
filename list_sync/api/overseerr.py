"""
Overseerr API client for the ListSync application.
"""

import json
import logging
import requests
from typing import Dict, Any, Tuple, Optional
from urllib.parse import quote

from ..utils.helpers import calculate_title_similarity, custom_input, color_gradient

class OverseerrClient:
    """Client for interacting with the Overseerr API."""
    
    def __init__(self, overseerr_url: str, api_key: str, requester_user_id: str = "1"):
        """
        Initialize the Overseerr API client.
        
        Args:
            overseerr_url (str): Overseerr server URL
            api_key (str): API key
            requester_user_id (str, optional): Requester user ID. Defaults to "1".
        """
        self.overseerr_url = overseerr_url.rstrip('/')
        self.api_key = api_key
        self.requester_user_id = requester_user_id
        self.headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
        self.request_headers = {"X-Api-Key": api_key, "X-Api-User": requester_user_id, "Content-Type": "application/json"}
    
    def test_connection(self):
        """
        Test the connection to the Overseerr API.
        
        Raises:
            Exception: If the connection test fails
        """
        test_url = f"{self.overseerr_url}/api/v1/status"
        try:
            response = requests.get(test_url, headers=self.headers)
            response.raise_for_status()
            logging.info("Overseerr API connection successful!")
            return True
        except Exception as e:
            logging.error(f"Overseerr API connection failed. Error: {str(e)}")
            raise
    
    def set_requester_user(self) -> str:
        """
        Set the requester user based on available users.
        
        Returns:
            str: The requester user ID
        """
        users_url = f"{self.overseerr_url}/api/v1/user"
        try:
            requester_user_id = "1"
            response = requests.get(users_url, headers=self.headers)
            response.raise_for_status()
            jsonResult = response.json()
            
            if jsonResult['pageInfo']['results'] > 1:
                print(color_gradient("\n📋 Multiple users detected, you can choose which user will make the requests on ListSync behalf.\n", "#00aaff", "#00ffaa"))
                for result in jsonResult['results']:
                    print(color_gradient(f"{result['id']}. {result['displayName']}", "#ffaa00", "#ff5500"))
                requester_user_id = custom_input(color_gradient("\nEnter the number of the user to use as requester: ", "#ffaa00", "#ff5500"))
                if not next((x for x in jsonResult['results'] if str(x['id']) == requester_user_id), None):
                    requester_user_id = "1"
                    print(color_gradient("\n❌  Invalid option, using admin as requester user.", "#ff0000", "#aa0000"))
                
            logging.info("Requester user set!")
            return requester_user_id
        except Exception as e:
            logging.error(f"Failed to set requester user. Error: {str(e)}")
            return "1"  # Default fallback
    
    def search_media(self, media_title: str, media_type: str, release_year: int = None) -> Optional[Dict[str, Any]]:
        """
        Search for media in Overseerr.
        
        Args:
            media_title (str): Title to search for
            media_type (str): Media type (movie or tv)
            release_year (int, optional): Release year. Defaults to None.
            
        Returns:
            Optional[Dict[str, Any]]: Search result or None if not found
        """
        search_url = f"{self.overseerr_url}/api/v1/search"
        search_title = media_title  # Use the provided title
        
        page = 1
        best_match = None
        best_score = 0
        
        while True:
            try:
                # Use quote to properly encode all special characters including forward slashes
                # quote() encodes spaces as %20 and slashes as %2F (unlike requests.utils.quote which doesn't encode /)
                encoded_query = quote(search_title, safe='')
                url = f"{search_url}?query={encoded_query}&page={page}&language=en"
                
                logging.debug(f"Searching for '{search_title}' (Year: {release_year})")
                logging.debug(f"Encoded URL: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 429:
                    logging.warning("Rate limited, waiting 5 seconds...")
                    import time
                    time.sleep(5)
                    continue
                    
                response.raise_for_status()
                search_results = response.json()
                
                if not search_results.get("results"):
                    break
                    
                for result in search_results["results"]:
                    result_type = result.get("mediaType")
                    if result_type != media_type:
                        continue
                    
                    # Get the title based on media type
                    result_title = result.get("title") if media_type == "movie" else result.get("name")
                    if not result_title:
                        continue
                    
                    # Get year
                    result_year = None
                    try:
                        if media_type == "movie" and "releaseDate" in result:
                            result_year = int(result["releaseDate"][:4])
                        elif media_type == "tv" and "firstAirDate" in result:
                            result_year = int(result["firstAirDate"][:4])
                    except (ValueError, TypeError):
                        pass
                    
                    # Calculate title similarity
                    similarity = calculate_title_similarity(search_title, result_title)
                    
                    # Calculate final score
                    score = similarity
                    
                    # Year matching
                    if release_year and result_year:
                        if release_year == result_year:
                            score *= 2  # Double score for exact year match
                            logging.debug(f"Exact year match for '{result_title}' ({result_year}) - Base similarity: {similarity}")
                        elif abs(release_year - result_year) <= 1:
                            score *= 1.5  # 1.5x score for off-by-one year
                            logging.debug(f"Close year match for '{result_title}' ({result_year}) - Base similarity: {similarity}")
                    
                    logging.debug(f"Match candidate: '{result_title}' ({result_year}) - Score: {score}")
                    
                    # Update best match if we have a better score
                    # For exact year matches, require a lower similarity threshold
                    min_similarity = 0.5 if (release_year and result_year and release_year == result_year) else 0.7
                    
                    if score > best_score and similarity >= min_similarity:
                        best_score = score
                        best_match = result
                        logging.info(f"New best match: '{result_title}' ({result_year}) - Score: {score}")
                
                # Only continue to next page if we haven't found a good match
                if best_score > 1.5 or page >= search_results.get("totalPages", 1):
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                logging.error(f'Error searching for "{search_title}": {str(e)}')
                if "429" in str(e):
                    import time
                    time.sleep(5)
                    continue
                raise

        if best_match:
            result_title = best_match.get("title") if media_type == "movie" else best_match.get("name")
            result_year = None
            try:
                if media_type == "movie" and "releaseDate" in best_match:
                    result_year = best_match["releaseDate"][:4]
                elif media_type == "tv" and "firstAirDate" in best_match:
                    result_year = best_match["firstAirDate"][:4]
            except (ValueError, TypeError):
                pass
            
            logging.info(f"Final match for '{media_title}' ({release_year}): '{result_title}' ({result_year}) - Score: {best_score}")
            return {
                "id": best_match["id"],
                "mediaType": best_match["mediaType"],
            }
        
        logging.warning(f'No matching results found for "{media_title}" ({release_year}) of type "{media_type}"')
        return None
    
    def get_media_status(self, media_id: int, media_type: str) -> Tuple[bool, bool, int]:
        """
        Get the status of media in Overseerr.
        
        Args:
            media_id (int): Media ID
            media_type (str): Media type (movie or tv)
            
        Returns:
            Tuple[bool, bool, int]: Availability, requested status, and number of seasons
        """
        media_url = f"{self.overseerr_url}/api/v1/{media_type}/{media_id}"
        
        try:
            response = requests.get(media_url, headers=self.headers)
            response.raise_for_status()
            media_data = response.json()
            logging.debug(f"Detailed response for {media_type} ID {media_id}: {json.dumps(media_data)}")

            media_info = media_data.get("mediaInfo", {})
            status = media_info.get("status")
            number_of_seasons = self.extract_number_of_seasons(media_data)

            logging.debug(f"Status for {media_type} ID {media_id}: {status}")
            logging.debug(f"Number of seasons for {media_type} ID {media_id}: {number_of_seasons}")

            # Status codes:
            # 2: PENDING
            # 3: PROCESSING
            # 4: PARTIALLY_AVAILABLE
            # 5: AVAILABLE
            is_available_to_watch = status in [4, 5]
            is_requested = status in [2, 3]

            return is_available_to_watch, is_requested, number_of_seasons
        except Exception as e:
            logging.error(f"Error confirming status for {media_type} ID {media_id}: {str(e)}")
            raise
    
    def extract_number_of_seasons(self, media_data):
        """
        Extract the number of seasons from media data.
        
        Args:
            media_data (dict): Media data from Overseerr
            
        Returns:
            int: Number of seasons (defaults to 1)
        """
        number_of_seasons = media_data.get("numberOfSeasons")
        logging.debug(f"Extracted number of seasons: {number_of_seasons}")
        return number_of_seasons if number_of_seasons is not None else 1
    
    def request_media(self, media_id: int, media_type: str, is_4k: bool = False) -> str:
        """
        Request media in Overseerr.
        
        Args:
            media_id (int): Media ID
            media_type (str): Media type (movie or tv)
            is_4k (bool, optional): Whether to request 4K. Defaults to False.
            
        Returns:
            str: Status of the request ("success" or "error")
        """
        request_url = f"{self.overseerr_url}/api/v1/request"
        payload = {
            "mediaId": media_id,
            "mediaType": media_type,
            "is4k": is_4k
        }
        
        try:
            response = requests.post(request_url, headers=self.request_headers, json=payload)
            response.raise_for_status()
            logging.debug(f"Request response for {media_type} ID {media_id}: {json.dumps(response.json())}")
            return "success"
        except Exception as e:
            logging.error(f"Error requesting {media_type} ID {media_id}: {str(e)}")
            return "error"
    
    def request_tv_series(self, tv_id: int, number_of_seasons: int, is_4k: bool = False) -> str:
        """
        Request TV series in Overseerr with specific seasons.
        
        Args:
            tv_id (int): TV series ID
            number_of_seasons (int): Number of seasons to request
            is_4k (bool, optional): Whether to request 4K. Defaults to False.
            
        Returns:
            str: Status of the request ("success" or "error")
        """
        request_url = f"{self.overseerr_url}/api/v1/request"
        
        seasons_list = [i for i in range(1, number_of_seasons + 1)]
        logging.debug(f"Seasons list for TV series ID {tv_id}: {seasons_list}")
        
        payload = {
            "mediaId": tv_id,
            "mediaType": "tv",
            "is4k": is_4k,
            "seasons": seasons_list
        }
        
        logging.debug(f"Request payload for TV series ID {tv_id}: {json.dumps(payload, indent=4)}")

        try:
            response = requests.post(request_url, headers=self.request_headers, json=payload)
            response.raise_for_status()
            logging.debug(f"Request response for TV series ID {tv_id}: {response.json()}")
            return "success"
        except Exception as e:
            logging.error(f"Error requesting TV series ID {tv_id}: {str(e)}")
            return "error"
