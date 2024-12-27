import bs4
import requests
import json
from utils.base_plugin import ListScraper

class JellyfinAPI(ListScraper):
    '''Generate collections based on Jellyfin API queries'''

    _alias_ = 'jellyfin_api'

    def get_list(list_id, config=None):
        '''Call jellyfin API
           list_id should be a dict to pass to https://api.jellyfin.org/#tag/Items/operation/GetItems
        '''
        params = {
            "enableTotalRecordCount": "false",
            "enableImages": "false",
            "Recursive": "true",
            "fields": ["ProviderIds", "ProductionYear"]
        }
        params = {**params, **list_id}

        res = requests.get(f'{config["server_url"]}/Users/{config["user_id"]}/Items',headers={"X-Emby-Token": config["api_key"]}, params=params)

        items = []
        for item in res.json()["Items"]:
            items.append({
                "title": item["Name"],
                "release_year": item.get("ProductionYear", None),
                "media_type": item["Type"],
                "imdb_id": item["ProviderIds"].get("Imdb", None)
            })

        return {
            "name": f"{list_id}",
            "description": "Movies which match the jellyfin API query: {list_id}",
            "items": items
        }
