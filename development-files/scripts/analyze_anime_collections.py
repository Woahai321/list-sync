#!/usr/bin/env python3
"""
Script to analyze popular-collections.json and identify anime collections.
Uses TMDB API to check if movies/shows are anime (genre ID 16).
"""

import json
import os
import sys
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from list_sync.config import get_tmdb_api_key

# TMDB API configuration
TMDB_BASE_URL = "https://api.themoviedb.org/3"
ANIME_GENRE_ID = 16  # TMDB genre ID for Anime

# Rate limiting
REQUEST_DELAY = 0.25  # Delay between API requests (seconds)


def get_tmdb_movie_details(tmdb_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch movie details from TMDB API.
    
    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key
        
    Returns:
        Movie details dict or None if not found
    """
    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    
    try:
        time.sleep(REQUEST_DELAY)  # Rate limiting
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Error fetching movie {tmdb_id}: {e}")
        return None


def get_tmdb_tv_details(tmdb_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch TV show details from TMDB API.
    
    Args:
        tmdb_id: TMDB TV ID
        api_key: TMDB API key
        
    Returns:
        TV show details dict or None if not found
    """
    url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"
    params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    
    try:
        time.sleep(REQUEST_DELAY)  # Rate limiting
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Error fetching TV {tmdb_id}: {e}")
        return None


def is_anime(tmdb_id: int, api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a TMDB ID is anime by checking genres.
    Tries movie endpoint first, then TV if movie fails.
    
    Args:
        tmdb_id: TMDB ID
        api_key: TMDB API key
        
    Returns:
        Tuple of (is_anime: bool, media_type: Optional[str])
        media_type will be "movie", "tv", or None if not found
    """
    # Try movie first
    details = get_tmdb_movie_details(tmdb_id, api_key)
    if details:
        genres = details.get('genres', [])
        genre_ids = [g.get('id') for g in genres if g.get('id')]
        return (ANIME_GENRE_ID in genre_ids, "movie")
    
    # If movie not found, try TV
    details = get_tmdb_tv_details(tmdb_id, api_key)
    if details:
        genres = details.get('genres', [])
        genre_ids = [g.get('id') for g in genres if g.get('id')]
        return (ANIME_GENRE_ID in genre_ids, "tv")
    
    # Not found in either
    return (False, None)


def analyze_collection(collection: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Analyze a collection to determine if it contains anime.
    
    Args:
        collection: Collection dict from JSON
        api_key: TMDB API key
        
    Returns:
        Dict with analysis results
    """
    franchise = collection.get('franchise', 'Unknown')
    movie_ids = collection.get('movieIds', [])
    
    anime_movies = []
    non_anime_movies = []
    errors = []
    
    print(f"\n📊 Analyzing: {franchise} ({len(movie_ids)} movies)")
    
    for movie_id in movie_ids:
        try:
            is_anime_result, media_type = is_anime(movie_id, api_key)
            if is_anime_result:
                anime_movies.append(movie_id)
                print(f"  🎌 {media_type.upper()} {movie_id}: ANIME")
            elif media_type:
                non_anime_movies.append(movie_id)
            else:
                errors.append((movie_id, "Not found in TMDB"))
                print(f"  ⚠️  {movie_id}: Not found in TMDB")
        except Exception as e:
            errors.append((movie_id, str(e)))
            print(f"  ❌ Error checking {movie_id}: {e}")
    
    is_anime_collection = len(anime_movies) > 0
    
    result = {
        'franchise': franchise,
        'is_anime': is_anime_collection,
        'anime_count': len(anime_movies),
        'non_anime_count': len(non_anime_movies),
        'anime_movie_ids': anime_movies,
        'total_movies': len(movie_ids),
        'errors': errors
    }
    
    if is_anime_collection:
        print(f"  🎌 Collection contains {len(anime_movies)} anime movie(s)")
    else:
        print(f"  ✅ No anime found in collection")
    
    return result


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str):
    """Save JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main function."""
    # Get file paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_file = project_root / "list_sync" / "providers" / "popular-collections.json"
    output_file = project_root / "list_sync" / "providers" / "popular-collections-revised.json"
    
    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Get TMDB API key
    api_key = get_tmdb_api_key()
    if not api_key:
        print("❌ Error: TMDB API key not found!")
        print("   Please set TMDB_KEY environment variable or add it to .env file")
        sys.exit(1)
    
    print("=" * 80)
    print("🎌 Anime Collection Analyzer")
    print("=" * 80)
    print(f"📁 Input file: {input_file}")
    print(f"📁 Output file: {output_file}")
    print(f"🔑 TMDB API key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    print()
    
    # Load JSON
    print("📖 Loading JSON file...")
    data = load_json_file(str(input_file))
    collections = data.get('collections', [])
    total_collections = len(collections)
    
    print(f"✅ Loaded {total_collections} collections")
    print()
    
    # Analyze all collections
    print("🔍 Analyzing collections for anime content...")
    print("   (This may take a while due to API rate limiting)")
    print()
    
    analysis_results = []
    anime_collections = []
    
    for i, collection in enumerate(collections, 1):
        print(f"[{i}/{total_collections}]", end="")
        result = analyze_collection(collection, api_key)
        analysis_results.append(result)
        
        if result['is_anime']:
            anime_collections.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total collections analyzed: {total_collections}")
    print(f"Collections with anime: {len(anime_collections)}")
    print(f"Collections without anime: {total_collections - len(anime_collections)}")
    print()
    
    # Show anime collections for review
    if anime_collections:
        print("🎌 COLLECTIONS CONTAINING ANIME:")
        print("-" * 80)
        for result in anime_collections:
            print(f"\n📺 {result['franchise']}")
            print(f"   Anime movies: {result['anime_count']}/{result['total_movies']}")
            print(f"   Anime IDs: {result['anime_movie_ids']}")
        
        print("\n" + "=" * 80)
        print("👤 USER REVIEW")
        print("=" * 80)
        print("\nPlease review the collections above.")
        print("For each collection, decide if it should be removed.")
        print()
        
        # Get user decisions
        collections_to_remove = []
        for result in anime_collections:
            franchise = result['franchise']
            anime_count = result['anime_count']
            total = result['total_movies']
            
            while True:
                response = input(
                    f"❓ Remove '{franchise}'? "
                    f"({anime_count}/{total} anime) [y/n]: "
                ).strip().lower()
                
                if response in ['y', 'yes']:
                    collections_to_remove.append(franchise)
                    print(f"  ✅ Marked for removal: {franchise}")
                    break
                elif response in ['n', 'no']:
                    print(f"  ⏭️  Keeping: {franchise}")
                    break
                else:
                    print("  ⚠️  Please enter 'y' or 'n'")
        
        # Create revised JSON
        print("\n" + "=" * 80)
        print("💾 CREATING REVISED JSON")
        print("=" * 80)
        
        # Filter out collections marked for removal
        revised_collections = [
            coll for coll in collections
            if coll.get('franchise') not in collections_to_remove
        ]
        
        # Update metadata
        revised_data = data.copy()
        revised_data['collections'] = revised_collections
        revised_data['totalCollections'] = len(revised_collections)
        
        # Recalculate totalMovies
        total_movies = sum(coll.get('totalMovies', 0) for coll in revised_collections)
        revised_data['totalMovies'] = total_movies
        
        # Save revised JSON
        save_json_file(revised_data, str(output_file))
        
        print(f"✅ Revised JSON saved to: {output_file}")
        print(f"   Removed {len(collections_to_remove)} collections")
        print(f"   Remaining collections: {len(revised_collections)}")
        print(f"   Remaining movies: {total_movies}")
        
    else:
        print("✅ No anime collections found! No changes needed.")
        print(f"   (You can still create a copy if needed)")
        
        response = input("\nCreate a copy anyway? [y/n]: ").strip().lower()
        if response in ['y', 'yes']:
            save_json_file(data, str(output_file))
            print(f"✅ Copy saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

