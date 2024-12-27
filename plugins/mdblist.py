import json
from utils.base_plugin import ListScraper
import bs4
import requests

class MDBList(ListScraper):

    _alias_ = 'mdblist'

    def get_list(list_id, config=None):

        # Get the list name
        r = requests.get(f"https://mdblist.com/lists/{list_id}")
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        list_name = soup.find('div', class_='ui form').find('h3').text.strip()
        description = soup.find("div", {"class": "ui form"}).find("div", {"class": "fourteen wide field"}).find_all("p")
        description = "\n".join([p.text for p in description])

        # Get the list items
        r = requests.get(f"https://mdblist.com/lists/{list_id}/json")
        movies = r.json()
        movies = [{**movie, 'media_type': movie["mediatype"]} for movie in movies]

        return {'name': list_name, 'items': movies, 'description': description}
