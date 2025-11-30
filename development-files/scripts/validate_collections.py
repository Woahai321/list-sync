#!/usr/bin/env python3
"""
Script to validate collections in popular-collections.json against TMDB API.
Ensures each collection contains all movies from the official TMDB collection.

Usage:
    python validate_collections.py [--update] [--collection "Collection Name"]
    
Options:
    --update: Update the JSON file with missing movies (creates backup first)
    --collection: Only validate a specific collection by name
"""

import json
import os
import sys
import time
import requests
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from list_sync.config import get_tmdb_api_key

# TMDB API configuration
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Rate limiting (TMDB allows 40 requests per 10 seconds)
REQUEST_DELAY = 0.26  # ~38 requests per 10 seconds to be safe


def search_collection(query: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Search for a collection by name using TMDB API.
    
    Args:
        query: Collection name to search for
        api_key: TMDB API key
        
    Returns:
        Collection search result or None if not found
    """
    url = f"{TMDB_BASE_URL}/search/collection"
    params = {
        'api_key': api_key,
        'query': query,
        'language': 'en-US',
        'include_adult': False
    }
    
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Return first result if available
        results = data.get('results', [])
        if results:
            return results[0]
        
        return None
    except Exception as e:
        print(f"  ⚠️  Error searching for collection '{query}': {e}")
        return None


def get_collection_details(collection_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Get full collection details including all movies.
    
    Args:
        collection_id: TMDB collection ID
        api_key: TMDB API key
        
    Returns:
        Collection details dict or None if not found
    """
    url = f"{TMDB_BASE_URL}/collection/{collection_id}"
    params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Error fetching collection {collection_id}: {e}")
        return None


def get_movie_collection_id(movie_id: int, api_key: str) -> Optional[int]:
    """
    Get the collection ID for a movie by checking its belongs_to_collection field.
    
    Args:
        movie_id: TMDB movie ID
        api_key: TMDB API key
        
    Returns:
        Collection ID or None if movie doesn't belong to a collection
    """
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        belongs_to_collection = data.get('belongs_to_collection')
        if belongs_to_collection:
            return belongs_to_collection.get('id')
        
        return None
    except Exception as e:
        print(f"  ⚠️  Error fetching movie {movie_id}: {e}")
        return None


def get_movie_details(movie_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Get full movie details from TMDB API.
    
    Args:
        movie_id: TMDB movie ID
        api_key: TMDB API key
        
    Returns:
        Full movie details dict or None if not found
    """
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Error fetching movie details {movie_id}: {e}")
        return None


def enrich_movie_data(movie_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format relevant movie data from TMDB API response.
    
    Args:
        movie_data: Full movie data from TMDB API
        
    Returns:
        Enriched movie data dict
    """
    return {
        'id': movie_data.get('id'),
        'title': movie_data.get('title', ''),
        'original_title': movie_data.get('original_title', ''),
        'rating': movie_data.get('vote_average', 0),
        'voteCount': movie_data.get('vote_count', 0),
        'releaseDate': movie_data.get('release_date', ''),
        'poster_path': movie_data.get('poster_path'),
        'backdrop_path': movie_data.get('backdrop_path'),
        'overview': movie_data.get('overview', ''),
        'tagline': movie_data.get('tagline', ''),
        'runtime': movie_data.get('runtime'),
        'genres': [g.get('name', '') for g in movie_data.get('genres', [])],
        'imdb_id': movie_data.get('imdb_id'),
        'popularity': movie_data.get('popularity', 0),
        'budget': movie_data.get('budget'),
        'revenue': movie_data.get('revenue'),
        'status': movie_data.get('status', ''),
        'original_language': movie_data.get('original_language', ''),
        'production_countries': [c.get('name', '') for c in movie_data.get('production_countries', [])],
        'spoken_languages': [l.get('english_name', '') for l in movie_data.get('spoken_languages', [])]
    }


def validate_collection(
    collection: Dict[str, Any],
    api_key: str,
    use_movie_lookup: bool = True
) -> Dict[str, Any]:
    """
    Validate a collection against TMDB API by getting collection ID from movies.
    
    Args:
        collection: Collection dict from JSON
        api_key: TMDB API key
        use_movie_lookup: If True, get collection ID from first movie (default: True)
        
    Returns:
        Dict with validation results
    """
    franchise = collection.get('franchise', 'Unknown')
    movie_ids = list(collection.get('movieIds', []))
    
    print(f"\n📊 Validating: {franchise}")
    print(f"   Local movies: {len(movie_ids)}")
    
    collection_id = None
    tmdb_collection = None
    
    # Method 1: Get collection ID from first movie's belongs_to_collection
    if use_movie_lookup and movie_ids:
        # Try multiple movies in case first one doesn't have collection info
        for movie_id in movie_ids[:3]:  # Try up to 3 movies
            collection_id = get_movie_collection_id(movie_id, api_key)
            if collection_id:
                print(f"   Found collection ID from movie {movie_id}: {collection_id}")
                tmdb_collection = get_collection_details(collection_id, api_key)
                if tmdb_collection:
                    collection_name = tmdb_collection.get('name', '')
                    print(f"   TMDB Collection: '{collection_name}' (ID: {collection_id})")
                    break
        
        # If still no collection found, try searching as fallback
        if not tmdb_collection:
            print(f"   No collection found from movies, trying name search as fallback...")
            collection_search_result = search_collection(franchise, api_key)
            if collection_search_result:
                collection_id = collection_search_result.get('id')
                collection_name = collection_search_result.get('name', '')
                print(f"   Found via search: '{collection_name}' (ID: {collection_id})")
                tmdb_collection = get_collection_details(collection_id, api_key)
    
    if not tmdb_collection:
        return {
            'franchise': franchise,
            'status': 'not_found',
            'error': 'Collection not found in TMDB (movies may not belong to a collection)',
            'missing_movies': [],
            'extra_movies': [],
            'tmdb_movie_count': 0,
            'local_movie_count': len(movie_ids),
            'tmdb_collection': None
        }
    
    # Extract movie IDs from TMDB collection
    parts = tmdb_collection.get('parts', [])
    tmdb_movie_ids = {movie.get('id') for movie in parts if movie.get('id')}
    local_movie_ids = set(movie_ids)
    
    # Compare
    missing_movies = tmdb_movie_ids - local_movie_ids
    extra_movies = local_movie_ids - tmdb_movie_ids
    
    # Get details for missing movies
    missing_movie_details = []
    for movie_id in missing_movies:
        for movie in parts:
            if movie.get('id') == movie_id:
                missing_movie_details.append({
                    'id': movie_id,
                    'title': movie.get('title', 'Unknown'),
                    'release_date': movie.get('release_date', 'Unknown')
                })
                break
    
    status = 'valid'
    if missing_movies:
        status = 'missing_movies'
    elif extra_movies:
        status = 'has_extra'
    
    result = {
        'franchise': franchise,
        'collection_id': collection_id,
        'status': status,
        'missing_movies': list(missing_movies),
        'missing_movie_details': missing_movie_details,
        'extra_movies': list(extra_movies),
        'tmdb_movie_count': len(tmdb_movie_ids),
        'local_movie_count': len(local_movie_ids),
        'tmdb_collection_name': tmdb_collection.get('name', ''),
        'tmdb_collection': tmdb_collection  # Include full collection data
    }
    
    # Print results
    if missing_movies:
        print(f"   ⚠️  MISSING {len(missing_movies)} movie(s) from local data:")
        for movie in missing_movie_details:
            print(f"      - {movie['title']} ({movie['id']}) - {movie['release_date']}")
    
    if extra_movies:
        print(f"   ⚠️  EXTRA {len(extra_movies)} movie(s) in local data (not in TMDB collection):")
        print(f"      These movies may not belong to this collection:")
        for movie_id in sorted(extra_movies):
            # Try to get movie title for better reporting
            movie_data = get_movie_details(movie_id, api_key)
            if movie_data:
                title = movie_data.get('title', f'Movie {movie_id}')
                print(f"      - {title} ({movie_id})")
            else:
                print(f"      - Movie ID: {movie_id}")
    
    if not missing_movies and not extra_movies:
        print(f"   ✅ Collection is complete and accurate!")
    
    return result


def update_collection(
    collection: Dict[str, Any],
    validation_result: Dict[str, Any],
    api_key: str,
    enrich_all_movies: bool = True
) -> Dict[str, Any]:
    """
    Update a collection with missing movies and enrich with collection ID and movie data.
    
    Args:
        collection: Original collection dict
        validation_result: Validation result with missing movies and collection data
        api_key: TMDB API key for fetching movie details
        enrich_all_movies: If True, fetch and enrich all movies with full TMDB data
        
    Returns:
        Updated collection dict
    """
    updated_collection = collection.copy()
    
    # Add collection ID
    collection_id = validation_result.get('collection_id')
    if collection_id:
        updated_collection['collectionId'] = collection_id
        print(f"   ✅ Added collectionId: {collection_id}")
    
    # Add collection metadata from TMDB
    tmdb_collection = validation_result.get('tmdb_collection')
    if tmdb_collection:
        if tmdb_collection.get('poster_path'):
            updated_collection['poster_path'] = tmdb_collection.get('poster_path')
        if tmdb_collection.get('backdrop_path'):
            updated_collection['backdrop_path'] = tmdb_collection.get('backdrop_path')
        if tmdb_collection.get('overview'):
            updated_collection['overview'] = tmdb_collection.get('overview')
    
    # Add missing movie IDs
    current_movie_ids = set(collection.get('movieIds', []))
    missing_movie_ids = set(validation_result.get('missing_movies', []))
    updated_movie_ids = sorted(list(current_movie_ids | missing_movie_ids))
    
    updated_collection['movieIds'] = updated_movie_ids
    updated_collection['totalMovies'] = len(updated_movie_ids)
    
    # Get or create movieRatings array
    movie_ratings = collection.get('movieRatings', [])
    existing_ids = {m.get('id') for m in movie_ratings}
    
    # Fetch and enrich missing movies
    missing_details = validation_result.get('missing_movie_details', [])
    if missing_details:
        print(f"   📥 Fetching details for {len(missing_details)} missing movie(s)...")
        for detail in missing_details:
            movie_id = detail['id']
            if movie_id not in existing_ids:
                # Fetch full movie details
                movie_data = get_movie_details(movie_id, api_key)
                if movie_data:
                    enriched = enrich_movie_data(movie_data)
                    movie_ratings.append(enriched)
                    print(f"      ✅ Enriched: {enriched['title']}")
                else:
                    # Fallback to basic data
                    movie_ratings.append({
                        'id': detail['id'],
                        'title': detail['title'],
                        'rating': 0,
                        'voteCount': 0,
                        'releaseDate': detail['release_date']
                    })
                    print(f"      ⚠️  Basic data only: {detail['title']}")
    
    # Enrich all existing movies if requested
    if enrich_all_movies:
        print(f"   📥 Enriching {len(movie_ratings)} existing movie(s) with full TMDB data...")
        enriched_ratings = []
        for i, movie_rating in enumerate(movie_ratings):
            movie_id = movie_rating.get('id')
            if not movie_id:
                enriched_ratings.append(movie_rating)
                continue
            
            # Check if already enriched (has poster_path or other enriched fields)
            if movie_rating.get('poster_path') or movie_rating.get('overview'):
                # Already enriched, keep it
                enriched_ratings.append(movie_rating)
            else:
                # Fetch and enrich
                movie_data = get_movie_details(movie_id, api_key)
                if movie_data:
                    enriched = enrich_movie_data(movie_data)
                    # Preserve existing rating/voteCount if they exist and are better
                    if movie_rating.get('rating', 0) > 0:
                        enriched['rating'] = movie_rating.get('rating', enriched['rating'])
                    if movie_rating.get('voteCount', 0) > 0:
                        enriched['voteCount'] = movie_rating.get('voteCount', enriched['voteCount'])
                    enriched_ratings.append(enriched)
                    if (i + 1) % 5 == 0:
                        print(f"      Progress: {i + 1}/{len(movie_ratings)}")
                else:
                    # Keep existing data if fetch fails
                    enriched_ratings.append(movie_rating)
        
        movie_ratings = enriched_ratings
    
    # Sort movieRatings by release date
    movie_ratings.sort(key=lambda x: x.get('releaseDate', ''))
    
    updated_collection['movieRatings'] = movie_ratings
    
    return updated_collection


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str):
    """Save JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_backup(file_path: str) -> str:
    """Create a backup of the file."""
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(file_path, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    return backup_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Validate collections in popular-collections.json against TMDB API'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update JSON file: add collectionId, enrich all movies with TMDB data, and add missing movies (creates backup first)'
    )
    parser.add_argument(
        '--collection',
        type=str,
        help='Only validate a specific collection by name'
    )
    parser.add_argument(
        '--use-name-search',
        action='store_true',
        help='Use name-based search instead of movie belongs_to_collection (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Get file paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_file = project_root / "list_sync" / "providers" / "popular-collections.json"
    
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
    print("🔍 Collection Validator")
    print("=" * 80)
    print(f"📁 Input file: {input_file}")
    print(f"🔑 TMDB API key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    if args.update:
        print(f"⚠️  UPDATE MODE: Will add collectionId, enrich all movies with TMDB data, and add missing movies")
    if args.collection:
        print(f"🎯 Validating only: {args.collection}")
    print()
    
    # Load JSON
    print("📖 Loading JSON file...")
    data = load_json_file(str(input_file))
    collections = data.get('collections', [])
    total_collections = len(collections)
    
    print(f"✅ Loaded {total_collections} collections")
    print()
    
    # Filter collections if specific one requested
    if args.collection:
        collections = [
            c for c in collections
            if args.collection.lower() in c.get('franchise', '').lower()
        ]
        if not collections:
            print(f"❌ No collection found matching '{args.collection}'")
            sys.exit(1)
        print(f"🎯 Found {len(collections)} matching collection(s)")
        print()
    
    # If updating, process and save incrementally
    if args.update:
        print("🔍 Validating and updating collections against TMDB API...")
        print("   (This may take a while due to API rate limiting)")
        print("   (Progress will be saved after each collection)")
        print()
        
        # Create backup
        backup_path = create_backup(str(input_file))
        print(f"✅ Backup created: {backup_path}")
        
        # Determine output file (save to revised file)
        output_file = project_root / "list_sync" / "providers" / "popular-collections-revised.json"
        print(f"📁 Output file: {output_file}")
        print()
        
        # Initialize updated data structure
        updated_data = data.copy()
        updated_collections = []
        total_movies_added = 0
        collections_updated = 0
        validation_results = []
        
        # Process each collection: validate -> update -> save
        for i, collection in enumerate(collections, 1):
            print(f"[{i}/{len(collections)}]", end="")
            # Use name search only if explicitly requested, otherwise use movie lookup (default)
            use_movie_lookup = not args.use_name_search
            result = validate_collection(collection, api_key, use_movie_lookup)
            validation_results.append(result)
            
            # Update collection if it has a collection_id
            if result.get('collection_id'):
                updated_collection = update_collection(
                    collection,
                    result,
                    api_key,
                    enrich_all_movies=True
                )
                
                movies_added = len(result.get('missing_movies', []))
                if movies_added > 0:
                    total_movies_added += movies_added
                
                collections_updated += 1
                updated_collections.append(updated_collection)
            else:
                # No collection_id found, keep as is
                updated_collections.append(collection)
            
            # Save progress after each collection
            updated_data['collections'] = updated_collections
            updated_data['totalCollections'] = len(updated_collections)
            updated_data['totalMovies'] = sum(c.get('totalMovies', 0) for c in updated_collections)
            updated_data['lastValidated'] = datetime.now().isoformat()
            updated_data['progress'] = f"{i}/{len(collections)}"
            
            # Save to file after each collection
            try:
                save_json_file(updated_data, str(output_file))
                if i % 10 == 0 or i == len(collections):
                    print(f"   💾 Progress saved: {i}/{len(collections)} collections processed")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not save progress: {e}")
        
        # Final metadata update (remove progress tracking)
        updated_data.pop('progress', None)
        save_json_file(updated_data, str(output_file))
        
        print(f"\n✅ JSON file saved: {output_file}")
        print(f"   Original file preserved: {input_file}")
        print(f"   Collections updated: {collections_updated}")
        print(f"   Added {total_movies_added} total movie(s)")
        print(f"   Total collections: {len(updated_collections)}")
        print(f"   Total movies: {updated_data['totalMovies']}")
        
        # Still show summary
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        valid_count = sum(1 for r in validation_results if r['status'] == 'valid')
        missing_count = sum(1 for r in validation_results if r['status'] == 'missing_movies')
        extra_count = sum(1 for r in validation_results if r['status'] == 'has_extra')
        not_found_count = sum(1 for r in validation_results if r['status'] == 'not_found')
        
        print(f"Total collections validated: {len(validation_results)}")
        print(f"✅ Valid (complete): {valid_count}")
        print(f"⚠️  Missing movies: {missing_count}")
        print(f"ℹ️  Has extra movies: {extra_count}")
        print(f"❌ Not found in TMDB: {not_found_count}")
        print()
    else:
        # Just validate, don't update
        print("🔍 Validating collections against TMDB API...")
        print("   (This may take a while due to API rate limiting)")
        print()
        
        validation_results = []
        
        for i, collection in enumerate(collections, 1):
            print(f"[{i}/{len(collections)}]", end="")
            # Use name search only if explicitly requested, otherwise use movie lookup (default)
            use_movie_lookup = not args.use_name_search
            result = validate_collection(collection, api_key, use_movie_lookup)
            validation_results.append(result)
    
    # Summary (only if not in update mode, since update mode shows it earlier)
    if not args.update:
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        valid_count = sum(1 for r in validation_results if r['status'] == 'valid')
        missing_count = sum(1 for r in validation_results if r['status'] == 'missing_movies')
        extra_count = sum(1 for r in validation_results if r['status'] == 'has_extra')
        not_found_count = sum(1 for r in validation_results if r['status'] == 'not_found')
        
        print(f"Total collections validated: {len(validation_results)}")
        print(f"✅ Valid (complete): {valid_count}")
        print(f"⚠️  Missing movies: {missing_count}")
        print(f"ℹ️  Has extra movies: {extra_count}")
        print(f"❌ Not found in TMDB: {not_found_count}")
        print()
        
        # Show details
        if missing_count > 0:
            print("⚠️  COLLECTIONS WITH MISSING MOVIES:")
            print("-" * 80)
            for result in validation_results:
                if result['status'] == 'missing_movies':
                    print(f"\n📺 {result['franchise']}")
                    print(f"   TMDB Collection: {result.get('tmdb_collection_name', 'N/A')}")
                    print(f"   Collection ID: {result.get('collection_id', 'N/A')}")
                    print(f"   Missing: {len(result['missing_movies'])} movie(s)")
                    print(f"   Local: {result['local_movie_count']} | TMDB: {result['tmdb_movie_count']}")
                    for movie in result.get('missing_movie_details', []):
                        print(f"      - {movie['title']} ({movie['id']}) - {movie['release_date']}")
        
        if not_found_count > 0:
            print("\n❌ COLLECTIONS NOT FOUND IN TMDB:")
            print("-" * 80)
            for result in validation_results:
                if result['status'] == 'not_found':
                    print(f"   - {result['franchise']} ({result['local_movie_count']} movies)")
    
    print("\n" + "=" * 80)
    print("✅ Validation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

