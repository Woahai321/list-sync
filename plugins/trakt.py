import json
from utils.base_plugin import ListScraper
import bs4
import os
import requests
from loguru import logger
import time

class Trakt(ListScraper):

    _alias_ = 'trakt'
    _access_token_file = '.trakt_access_token'

    _chart_types = {
            "movies/trending": {
                "title": "Trending Movies",
                "description": "The most watched movies right now."
            },
            "movies/popular": {
                "title": "Popular Movies",
                "description": "The most popular movies of all time."
            },
            "movies/favorited": {
                "title": "Most Favorited Movies",
                "description": "The most favorited movies for the last week."
            },
            "movies/watched": {
                "title": "Most Watched Movies",
                "description": "The most watched movies for the last week."
            },
            "movies/collected": {
                "title": "Most Collected Movies",
                "description": "The most collected movies for the last week."
            },
            "movies/played": {
                "title": "Most Played Movies",
                "description": "The most played movies for the last week."
            },
            "movies/anticipated": {
                "title": "Most Anticipated Movies",
                "description": "The most anticipated movies based on the number of lists a movie appears on."
            },
            "movies/boxoffice": {
                "title": "Box Office Movies",
                "description": "The top 10 movies in the US box office last weekend."
            },
            "shows/trending": {
                "title": "Trending Shows",
                "description": "The most watched shows right now."
            },
            "shows/popular": {
                "title": "Popular Shows",
                "description": "The most popular shows of all time. Popularity is calculated using the rating percentage and the number of ratings."
            },
            "shows/favorited": {
                "title": "Most Favorited Shows",
                "description": "The most favorited shows for the last week."
            },
            "shows/watched": {
                "title": "Most Watched Shows",
                "description": "The most watched shows for the last week."
            },
            "shows/collected": {
                "title": "Most Collected Shows",
                "description": "The most collected shows for the last week."
            },
            "shows/played": {
                "title": "Most Played Shows",
                "description": "Returns the most played (a single user can watch multiple episodes multiple times) shows for the last week."
            },
            "shows/anticipated": {
                "title": "Most Anticipated Shows",
                "description": "The most anticipated shows based on the number of lists a show appears on."
            }
        }



    def _get_auth_token(config):
        '''Get the authentication token for the Trakt API'''

        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": config["client_id"]
        }

        if os.path.exists(Trakt._access_token_file):
            # If we have already authenticated, read the access token from the file
            with open(Trakt._access_token_file, 'r') as f:
                access_token = f.read()
        else:
            # If we have not authenticated, get the access token from the user
            r = requests.post("https://api.trakt.tv/oauth/device/code", headers=headers, json={"client_id": config["client_id"]})
            device_code = r.json()["device_code"]
            user_code = r.json()["user_code"]
            interval = r.json()["interval"]

            print("Authentication with Trakt API required")
            print(f"Please visit the following URL to get your access token: {r.json()['verification_url']}")
            print()
            print(f"Your device code is: {user_code}")
            print()

            # Poll the API until the user has authenticated
            while True:
                r = requests.post("https://api.trakt.tv/oauth/device/token", headers=headers, json={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": device_code
                })
                if r.status_code == 200:
                    break
                time.sleep(interval)

            access_token = r.json()["access_token"]

            # Save the access token to a file
            with open(Trakt._access_token_file, 'w') as f:
                f.write(access_token)
            print("Successfully authenticated with Trakt API")
        return access_token


    def get_list(list_id, config=None):

        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": config["client_id"]
        }

        access_token = Trakt._get_auth_token(config)
        headers["Authorization"] = f"Bearer {access_token}"

        if list_id.startswith("shows/") or list_id.startswith("movies/"):
            # Chart
            r = requests.get(f"https://api.trakt.tv/{list_id}", headers=headers)
            list_name = Trakt._chart_types[list_id]["title"]
            description = Trakt._chart_types[list_id]["description"]

            if list_id.startswith("shows/"):
                item_types = "show"
            else:
                item_types = "movie"

            items_data = r.json()
        else:
            r = requests.get(f"https://api.trakt.tv/lists/{list_id}", headers=headers)
            list_name = r.json()["name"]
            description = r.json()["description"]
            r = requests.get(f"https://api.trakt.tv/lists/{list_id}/items", headers=headers)
            items_data = r.json()


        # Process the items
        items = []
        for item_data in items_data:
            if "type" in item_data:
                item = {"media_type": item_data["type"]}
            else:
                item = {"media_type": item_types}

            if "ids" in item_data:
                meta = item_data
            else:
                meta = item_data[item["media_type"]]

            if "imdb" in meta["ids"]:
                item["imdb_id"] = meta["ids"]["imdb"]
            item["title"] = meta["title"]
            if "year" in meta:
                item["release_year"] = meta["year"]
            items.append(item)

        return {
            "name": list_name,
            "description": description,
            "items": items
        }
