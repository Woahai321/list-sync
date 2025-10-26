"""
AniList provider for fetching anime lists via GraphQL API.

Supports:
- User lists by status (Planning, Watching, Completed, Paused, Dropped)
- Custom lists
- Anime only (manga not supported yet)

URL Format: https://anilist.co/user/{username}/animelist/{status}
            https://anilist.co/user/{username}/animelist

The provider resolves anime titles to TMDB IDs via Trakt API for Overseerr compatibility.
"""

import logging
import re
import requests
from typing import Dict, Any, List, Optional
from . import register_provider
from .trakt import search_trakt_by_title

# AniList GraphQL API endpoint
ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"


def parse_anilist_url(list_id: str) -> Dict[str, str]:
    """
    Parse AniList URL to extract username and optional list status.
    
    Supported formats:
    - https://anilist.co/user/{username}/animelist
    - https://anilist.co/user/{username}/animelist/{status}
    - Just username (defaults to all lists)
    
    Args:
        list_id (str): AniList URL or username
        
    Returns:
        Dict[str, str]: Dictionary with 'username' and optional 'status'
        
    Raises:
        ValueError: If URL format is invalid
    """
    # Pattern 1: Full URL with optional status
    # https://anilist.co/user/demo/animelist or https://anilist.co/user/demo/animelist/Planning
    pattern_full = r'https?://(?:www\.)?anilist\.co/user/([^/]+)/animelist/?([^/]*)'
    
    # Pattern 2: Just username
    pattern_username = r'^[a-zA-Z0-9_-]+$'
    
    match_full = re.match(pattern_full, list_id)
    if match_full:
        username = match_full.group(1)
        status = match_full.group(2).strip('/') if match_full.group(2) else None
        
        # Normalize status (capitalize first letter)
        if status:
            status = status.upper() if status.upper() in ['PLANNING', 'WATCHING', 'COMPLETED', 'PAUSED', 'DROPPED'] else status.capitalize()
        
        return {"username": username, "status": status}
    
    # Try just username
    match_username = re.match(pattern_username, list_id)
    if match_username:
        return {"username": list_id, "status": None}
    
    raise ValueError(
        f"Invalid AniList list ID format: {list_id}. "
        "Expected: https://anilist.co/user/{{username}}/animelist or just username"
    )


def fetch_anilist_animelist_graphql(username: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch anime list from AniList using GraphQL API.
    
    Args:
        username (str): AniList username
        status_filter (Optional[str]): Filter by status (Planning, Watching, etc.) or None for all
        
    Returns:
        List[Dict[str, Any]]: List of anime with title, year, and metadata
    """
    # GraphQL query to fetch user's anime list
    query = """
    query ($userName: String!, $type: MediaType!) {
      MediaListCollection(userName: $userName, type: $type) {
        lists {
          name
          isCustomList
          status
          entries {
            id
            status
            score
            progress
            media {
              id
              idMal
              title {
                romaji
                english
                native
              }
              type
              format
              status
              startDate {
                year
              }
              episodes
              season
              seasonYear
            }
          }
        }
      }
    }
    """
    
    variables = {
        "userName": username,
        "type": "ANIME"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        logging.info(f"🔍 AniList API: Fetching anime list for user '{username}'")
        
        response = requests.post(ANILIST_GRAPHQL_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            error_messages = [err.get("message", "Unknown error") for err in data["errors"]]
            raise ValueError(f"AniList GraphQL errors: {', '.join(error_messages)}")
        
        # Extract lists
        lists = data.get("data", {}).get("MediaListCollection", {}).get("lists", [])
        
        if not lists:
            logging.warning(f"No anime lists found for user '{username}'")
            return []
        
        # Collect all entries, filtering by status if specified
        all_entries = []
        total_count = 0
        
        for list_data in lists:
            list_name = list_data.get("name")
            list_status = list_data.get("status")
            is_custom = list_data.get("isCustomList", False)
            entries = list_data.get("entries", [])
            
            # Filter by status if specified
            if status_filter:
                # Match by list status or entry status
                if list_status and list_status.upper() == status_filter.upper():
                    all_entries.extend(entries)
                    total_count += len(entries)
                    logging.info(f"  📋 {list_name}: {len(entries)} entries")
                elif any(e.get('status', '').upper() == status_filter.upper() for e in entries):
                    filtered = [e for e in entries if e.get('status', '').upper() == status_filter.upper()]
                    all_entries.extend(filtered)
                    total_count += len(filtered)
                    logging.info(f"  📋 {list_name}: {len(filtered)}/{len(entries)} entries (filtered)")
            else:
                # Include all entries
                all_entries.extend(entries)
                total_count += len(entries)
                list_type = "Custom" if is_custom else "Status"
                logging.info(f"  📋 [{list_type}] {list_name}: {len(entries)} entries")
        
        logging.info(f"✅ AniList: Found {total_count} anime entries" + (f" with status '{status_filter}'" if status_filter else ""))
        
        return all_entries
        
    except requests.exceptions.HTTPError as e:
        logging.error(f"❌ AniList API HTTP error: {e}")
        if e.response.status_code == 404:
            raise ValueError(f"AniList user '{username}' not found")
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ AniList API request failed: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ AniList API error: {e}")
        raise


def extract_media_from_anilist_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract and normalize media information from an AniList list entry.
    
    Args:
        entry (Dict[str, Any]): AniList list entry
        
    Returns:
        Optional[Dict[str, Any]]: Normalized media item with title, year, media_type
    """
    try:
        media = entry.get("media", {})
        
        if not media:
            logging.warning(f"No media object in entry: {entry.get('id')}")
            return None
        
        # Get titles (prefer English, fallback to Romaji)
        title_obj = media.get("title", {})
        title_english = title_obj.get("english")
        title_romaji = title_obj.get("romaji")
        
        # Use English title if available, otherwise Romaji
        title = title_english if title_english else title_romaji
        
        if not title:
            logging.warning(f"No title found for AniList entry {entry.get('id')}")
            return None
        
        # Get year
        year = media.get("startDate", {}).get("year")
        
        # AniList IDs (for reference, not used for Overseerr)
        anilist_id = media.get("id")
        mal_id = media.get("idMal")
        
        return {
            "title": title,
            "year": year,
            "media_type": "tv",  # AniList anime is always TV type for Overseerr
            "anilist_id": anilist_id,
            "mal_id": mal_id,
            "title_english": title_english,
            "title_romaji": title_romaji,
        }
        
    except Exception as e:
        logging.warning(f"Failed to extract media from AniList entry: {str(e)}")
        return None


@register_provider("anilist")
def fetch_anilist_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch anime list from AniList and resolve to TMDB IDs via Trakt.
    
    This is the main entry point for the AniList provider, decorated with @register_provider.
    
    Args:
        list_id (str): AniList URL or username
        
    Returns:
        List[Dict[str, Any]]: List of media items with title, year, media_type, and TMDB IDs
        
    Raises:
        ValueError: If URL is invalid or user not found
    """
    # Parse the list ID/URL
    parsed = parse_anilist_url(list_id)
    username = parsed["username"]
    status_filter = parsed.get("status")
    
    logging.info(f"🎌 AniList Provider: Fetching list for user '{username}'" + 
                 (f" (status: {status_filter})" if status_filter else ""))
    
    # Fetch entries from AniList
    entries = fetch_anilist_animelist_graphql(username, status_filter)
    
    if not entries:
        logging.warning(f"No entries found for AniList user '{username}'")
        return []
    
    # Extract and normalize media items
    media_items = []
    
    for entry in entries:
        media = extract_media_from_anilist_entry(entry)
        
        if not media:
            continue
        
        title = media["title"]
        year = media.get("year")
        
        # Try to resolve TMDB ID via Trakt API
        # Try English title first, then Romaji if English fails
        tmdb_id = None
        imdb_id = None
        
        # Attempt 1: English title
        if media.get("title_english"):
            trakt_result = search_trakt_by_title(media["title_english"], year, "tv")
            if trakt_result and trakt_result.get("tmdb_id"):
                tmdb_id = trakt_result["tmdb_id"]
                imdb_id = trakt_result.get("imdb_id")
                logging.debug(f"  ✓ Resolved via English title: {title} -> TMDB {tmdb_id}")
        
        # Attempt 2: Romaji title (if English failed)
        if not tmdb_id and media.get("title_romaji") and media["title_romaji"] != media.get("title_english"):
            trakt_result = search_trakt_by_title(media["title_romaji"], year, "tv")
            if trakt_result and trakt_result.get("tmdb_id"):
                tmdb_id = trakt_result["tmdb_id"]
                imdb_id = trakt_result.get("imdb_id")
                logging.debug(f"  ✓ Resolved via Romaji title: {title} -> TMDB {tmdb_id}")
        
        # Add to results
        media_items.append({
            "title": title,
            "year": year,
            "media_type": "tv",
            "tmdb_id": tmdb_id,
            "imdb_id": imdb_id,
            # Keep AniList metadata for reference
            "anilist_id": media.get("anilist_id"),
            "mal_id": media.get("mal_id"),
        })
        
        # Log progress periodically
        if len(media_items) % 25 == 0 or len(media_items) <= 5:
            resolved_count = sum(1 for m in media_items if m.get("tmdb_id"))
            logging.info(f"  📊 Progress: {len(media_items)}/{len(entries)} processed, {resolved_count} resolved")
    
    # Final summary
    resolved_count = sum(1 for m in media_items if m.get("tmdb_id"))
    logging.info(f"✅ AniList Provider: {len(media_items)} anime processed, {resolved_count} resolved to TMDB IDs ({resolved_count/len(media_items)*100:.1f}%)")
    
    return media_items

