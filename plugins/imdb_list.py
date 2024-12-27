import bs4
import requests
import json
from utils.base_plugin import ListScraper

class IMDBList(ListScraper):

    _alias_ = 'imdb_list'

    def get_list(list_id, config=None):
        r = requests.get(f'https://www.imdb.com/list/{list_id}', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US'})
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        list_name = soup.find('h1').text
        description = soup.find("div", {"class": "list-description"}).text

        ld_json = soup.find("script", {"type": "application/ld+json"}).text
        ld_json = json.loads(ld_json)
        movies = []
        for row in ld_json["itemListElement"]:
            url_parts = row["item"]["url"].split("/")
            url_parts = [p for p in url_parts if p!=""]

            release_year = None
            if config.get("add_release_year", False):
                # Get release_date
                r = requests.get(row["item"]["url"], headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US'})
                soup = bs4.BeautifulSoup(r.text, 'html.parser')
                movie_json = soup.find("script", {"type": "application/ld+json"}).text
                release_year = json.loads(movie_json)["datePublished"].split("-")[0]

            movies.append({
                "title": row["item"]["name"],
                "release_year": release_year,
                "media_type": row["item"]["@type"],
                "imdb_id": url_parts[-1]
            })

        return {'name': list_name, 'items': movies, "description": description}
