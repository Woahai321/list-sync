import bs4
import requests
from utils.base_plugin import ListScraper
import json

class IMDBChart(ListScraper):

    _alias_ = 'imdb_chart'

    def get_list(list_id, config=None):
        res = requests.get(f'https://www.imdb.com/chart/{list_id}', headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US'})
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        list_name = soup.find('title').text
        description = soup.find('meta', property='og:description')['content']
        movies = []

        data = soup.find('script', id='__NEXT_DATA__')
        data = json.loads(data.text)

        for movie in next(iter(data["props"]["pageProps"]["pageData"].values()))["edges"]:
            movie = movie["node"]
            if "titleText" not in movie:
                # Get item details
                res = requests.get(f'https://www.imdb.com/title/{movie["release"]["titles"][0]["id"]}', headers={'User-Agent': 'Mozilla/5.0'})
                soup = bs4.BeautifulSoup(res.text, 'html.parser')
                item_data = json.loads(soup.find('script', id='__NEXT_DATA__').text)
                movie = item_data["props"]["pageProps"]["aboveTheFoldData"]

            title = movie["titleText"]["text"]

            release_year = None
            if movie["releaseYear"] is not None:
                release_year = movie["releaseYear"]["year"]

            media_type = movie["titleType"]["id"]
            imdb_id = movie["id"]

            movies.append({'title': title, 'release_year': release_year, "media_type": media_type, "imdb_id": imdb_id})
        return {'name': list_name, 'items': movies, "description": description}
