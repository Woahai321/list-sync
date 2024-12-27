import json
from utils.base_plugin import ListScraper
import bs4
import requests

class TSPDT(ListScraper):

    _alias_ = 'tspdt'

    def get_list(list_id, config=None):
        r = requests.get("https://www.theyshootpictures.com/gf1000_all1000films_table.php")
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        movies = []


        for row in soup.find_all('tr')[1:]:
            values = row.find_all('td')
            movie_title = values[2].text
            for suffix in ["The", "A", "La", "Le", "L'"]:
                if movie_title.endswith(", "+suffix):
                    movie_title = suffix + " " + movie_title[:-len(suffix)-2]
            movie_year = values[4].text
            movies.append({'title': movie_title, 'release_year': movie_year, 'media_type': 'movie'})
        return {'name': "TSPDT Top 1000 Greatest", 'items': movies, "description": "Compiled from 16,000+ film lists and ballots, The TSPDT 1,000 Greatest Films is quite possibly the most definitive collection of the most critically acclaimed films you will find."}
