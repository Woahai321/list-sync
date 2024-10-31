# list_sync/lists.py

import os
import json
import html
import requests
from bs4 import BeautifulSoup
from halo import Halo
from typing import List, Dict
from .utils import color_gradient, custom_input, logging
from .database import save_list_id, load_list_ids

def fetch_imdb_list(list_id: str) -> List[Dict[str, str]]:
    """Fetch media items from an IMDb list."""
    spinner = Halo(text=color_gradient("📚  Fetching IMDB list...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()
    try:
        if list_id.startswith("ls"):
            url = f"https://www.imdb.com/list/{list_id}"
        elif list_id.startswith("ur"):
            url = f"https://www.imdb.com/user/{list_id}/watchlist"
        else:
            raise ValueError("Invalid IMDb list ID format. It should start with 'ls' for lists or 'ur' for watchlists.")
        
        headers = {"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", {"type": "application/ld+json"})

        if script_tag:
            ld_json = json.loads(script_tag.string)
        else:
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            if not script_tag:
                raise ValueError("Could not find ld+json or __NEXT_DATA__ script tag in the IMDb page")
            next_data = json.loads(script_tag.string)
            ld_json = next_data["props"]["pageProps"]["mainColumnData"]["predefinedList"]["titleListItemSearch"]

        media_items = []

        if "itemListElement" in ld_json:
            for row in ld_json["itemListElement"]:
                item = row["item"]
                media_items.append({
                    "title": html.unescape(item["name"]),
                    "imdb_id": item["url"].split("/")[-2],
                    "media_type": "tv" if item["@type"] == "TVSeries" else "movie"
                })
        elif "edges" in ld_json:
            for row in ld_json["edges"]:
                item = row["listItem"]
                media_items.append({
                    "title": html.unescape(item["titleText"]["text"]),
                    "imdb_id": item["id"],
                    "media_type": "tv" if item["titleType"]["id"] == "tvSeries" else "movie"
                })

        spinner.succeed(color_gradient(f"✨  Found {len(media_items)} items from IMDB list {list_id}!", "#00ff00", "#00aa00"))
        logging.info(f"IMDB list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items
    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch IMDB list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching IMDB list {list_id}: {str(e)}")
        raise

def fetch_trakt_list(list_id: str) -> List[Dict[str, str]]:
    """Fetch media items from a Trakt list."""
    base_url = f"https://trakt.tv/lists/{list_id}"
    headers = {"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0"}

    spinner = Halo(text=color_gradient("📚  Fetching Trakt list...", "#ffaa00", "#ff5500"), spinner="dots")
    spinner.start()

    try:
        response = requests.get(base_url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        final_base_url = response.url.split('?')[0]
        logging.info(f"Final Trakt URL: {final_base_url}")

        media_items = []
        page = 1
        total_pages = 1

        while True:
            url = f"{final_base_url}?page={page}&sort=added,asc"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            grid = soup.find("div", class_="row posters without-rank added")
            if grid and 'data-page-count' in grid.attrs:
                total_pages = int(grid['data-page-count'])
                logging.info(f"Total pages: {total_pages}")

            items = soup.find_all("div", class_="grid-item")

            if not items:
                break

            for item in items:
                title_element = item.find("h3", class_="ellipsify")
                if title_element:
                    title = title_element.text.strip()
                    media_type = "tv" if item.get("data-type") == "show" else item.get("data-type", "movie")
                    media_items.append({"title": title, "media_type": media_type})

            logging.info(f"Fetched {len(items)} items from page {page}")

            if page >= total_pages:
                next_link = soup.find("a", rel="next")
                if not next_link:
                    break

            page += 1

        spinner.succeed(color_gradient(f"✨  Found {len(media_items)} items from Trakt list {list_id}!", "#00ff00", "#00aa00"))
        logging.info(f"Trakt list {list_id} fetched successfully. Found {len(media_items)} items.")
        return media_items
    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch Trakt list {list_id}. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f"Error fetching Trakt list {list_id}: {str(e)}")
        raise

def display_lists():
    """Display saved lists."""
    lists = load_list_ids()
    print(color_gradient("\nSaved Lists:", "#00aaff", "#00ffaa"))
    for idx, list_info in enumerate(lists, 1):
        print(color_gradient(f"{idx}. {list_info['type'].upper()}: {list_info['id']}", "#ffaa00", "#ff5500"))

def delete_list():
    """Delete a list from the database."""
    lists = load_list_ids()
    display_lists()
    choice = custom_input(color_gradient("\nEnter the number of the list to delete (or 'c' to cancel): ", "#ffaa00", "#ff5500"))
    if choice.lower() == 'c':
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(lists):
            list_to_delete = lists[idx]
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM lists WHERE list_type = ? AND list_id = ?",
                    (list_to_delete['type'], list_to_delete['id'])
                )
                conn.commit()
            print(color_gradient(f"\nList {list_to_delete['type'].upper()}: {list_to_delete['id']} deleted.", "#00ff00", "#00aa00"))
        else:
            print(color_gradient("\nInvalid list number.", "#ff0000", "#aa0000"))
    except ValueError:
        print(color_gradient("\nInvalid input. Please enter a number.", "#ff0000", "#aa0000"))

def edit_lists():
    """Edit saved lists."""
    lists = load_list_ids()
    display_lists()
    print(color_gradient("\nEnter new list IDs (or press Enter to keep the current ID):", "#00aaff", "#00ffaa"))
    updated_lists = []
    for list_info in lists:
        new_id = custom_input(color_gradient(f"{list_info['type'].upper()}: {list_info['id']} -> ", "#ffaa00", "#ff5500"))
        updated_lists.append({
            "type": list_info['type'],
            "id": new_id if new_id else list_info['id']
        })
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        cursor.executemany(
            "INSERT INTO lists (list_type, list_id) VALUES (?, ?)",
            [(list_info['type'], list_info['id']) for list_info in updated_lists]
        )
        conn.commit()
    print(color_gradient("\nLists updated successfully.", "#00ff00", "#00aa00"))

def add_new_lists():
    """Add new lists interactively and save to the database."""
    add_new_list = True
    while add_new_list:
        list_ids = custom_input(color_gradient("\n🎬  Enter List ID(s) (comma-separated for multiple): ", "#ffaa00", "#ff5500"))
        list_ids = [id.strip() for id in list_ids.split(',')]
        
        for list_id in list_ids:
            if list_id.startswith(('ls', 'ur')):
                list_type = "imdb"
            elif list_id.isdigit():
                list_type = "trakt"
            else:
                print(color_gradient(f"\n❌  Invalid list ID format for '{list_id}'. Skipping this ID.", "#ff0000", "#aa0000"))
                continue

            add_to_sync = custom_input(color_gradient(f"\n🚨  Are you sure the list ID '{list_id}' is correct for '{list_type}'? (y/n): ", "#ffaa00", "#ff5500")).lower()
            if add_to_sync == "y":
                save_list_id(list_id, list_type)

        more_lists = custom_input(color_gradient("\n🏁  Do you want to import any other lists? (y/n): ", "#ffaa00", "#ff5500")).lower()
        if more_lists != "y":
            add_new_list = False
