# list_sync/sync.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from .utils import color_gradient, logging
from .overseerr import search_media_in_overseerr, request_media_in_overseerr, request_tv_series_in_overseerr
from .database import save_sync_result, load_list_ids
from .lists import fetch_imdb_list, fetch_trakt_list

def process_media_item(item: Dict[str, Any], overseerr_url: str, api_key: str, dry_run: bool) -> Dict[str, Any]:
    """Process a single media item for synchronization."""
    title = item.get('title', 'Unknown Title')
    media_type = item.get('media_type', 'unknown')
    imdb_id = item.get('imdb_id')

    if dry_run:
        return {"title": title, "status": "would_be_synced"}

    try:
        search_result = search_media_in_overseerr(overseerr_url, api_key, title, media_type)
        if search_result:
            overseerr_id = search_result["id"]
            is_available, is_requested, number_of_seasons = confirm_media_status(overseerr_url, api_key, overseerr_id, search_result["mediaType"])
            
            if is_available:
                save_sync_result(title, media_type, imdb_id, overseerr_id, "already_available")
                return {"title": title, "status": "already_available"}
            elif is_requested:
                save_sync_result(title, media_type, imdb_id, overseerr_id, "already_requested")
                return {"title": title, "status": "already_requested"}
            else:
                if search_result["mediaType"] == 'tv':
                    request_status = request_tv_series_in_overseerr(overseerr_url, api_key, overseerr_id, number_of_seasons)
                else:
                    request_status = request_media_in_overseerr(overseerr_url, api_key, overseerr_id, search_result["mediaType"])
                
                if request_status == "success":
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "requested")
                    return {"title": title, "status": "requested"}
                else:
                    save_sync_result(title, media_type, imdb_id, overseerr_id, "request_failed")
                    return {"title": title, "status": "request_failed"}
        else:
            save_sync_result(title, media_type, imdb_id, None, "not_found")
            return {"title": title, "status": "not_found"}
    except Exception as e:
        logging.error(f'Error processing item {title}: {str(e)}')
        return {"title": title, "status": "error"}

def process_media(media_items: List[Dict[str, Any]], overseerr_url: str, api_key: str, dry_run: bool = False):
    """Process a list of media items for synchronization."""
    total_items = len(media_items)
    results = {
        "requested": 0,
        "already_requested": 0,
        "already_available": 0,
        "not_found": 0,
        "error": 0,
        "skipped": 0
    }

    print(color_gradient(f"\n🎬  Processing {total_items} media items...", "#00aaff", "#00ffaa") + "\n")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_media_item, item, overseerr_url, api_key, dry_run): item for item in media_items}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                status = result["status"]
                results[status] = results.get(status, 0) + 1
                
                if dry_run:
                    print(color_gradient("🔍 {}: Would be synced".format(result['title']), "#ffaa00", "#ff5500") + "\n")
                else:
                    status_info = {
                    "requested": ("✅", "Successfully Requested", "#4CAF50", "#45a049"),
                    "already_requested": ("📌", "Already Requested", "#2196F3", "#1E88E5"),
                    "already_available": ("☑️ ", "Already Available", "#00BCD4", "#00ACC1"),
                    "not_found": ("❓", "Not Found", "#FFC107", "#FFA000"),
                    "error": ("❌", "Error", "#F44336", "#E53935"),
                    "skipped": ("⏭️ ", "Skipped", "#9E9E9E", "#757575")
                    }.get(status, ("➖", "Unknown Status", "#607D8B", "#546E7A"))

                    
                    emoji, status_text, start_color, end_color = status_info
                    message = "{}: {}".format(result['title'], status_text)
                    print("{} {}\n".format(emoji,  color_gradient(message, start_color, end_color)))
            except Exception as exc:
                print(color_gradient("❌ {} generated an exception: {}".format(item['title'], exc), "#ff0000", "#aa0000") + "\n")
                results["error"] += 1

    if not dry_run:
        display_summary(total_items, results)

def display_summary(total_items: int, results: Dict[str, int]):
    """Display a summary of the synchronization results."""
    summary = f"""
==============================================================
                    All done! Here's the Summary!
==============================================================
🔁 Total Items Processed: {total_items}

☑️  Items Already Available: {results["already_available"]}

✅ Items Successfully Requested: {results["requested"]}

📌 Items Already Requested: {results["already_requested"]}

❓ Items Not Found: {results["not_found"]}

⏭️  Items Skipped: {results["skipped"]}

❌ Items Failed: {results["error"]}
==============================================================
"""
    print(color_gradient(summary, "#00aaff", "#00ffaa"))
