import json
from utils.base_plugin import ListScraper
import bs4
import requests
from loguru import logger

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'

    def get_list(list_id, config=None):
        page_number = 1
        list_name = None
        description = None
        movies = []
        config = config or {}

        while True:
            print("Page number: ", page_number)
            watchlist = list_id.endswith("/watchlist")
            likeslist = list_id.endswith("/likes/films")


            if watchlist:
                list_name = list_id.split("/")[0] + " Watchlist"
                description = "Watchlist for " + list_id.split("/")[0]
            elif likeslist:
                list_name = list_id.split("/")[0] + " Likes"
                description = "Likes list for " + list_id.split("/")[0]


            url_format = "https://letterboxd.com/{list_id}{maybe_detail}/by/release-earliest/page/{page_number}/"
            maybe_detail = "" if watchlist or likeslist  else "/detail"
            r = requests.get(
                url_format.format(list_id=list_id, maybe_detail=maybe_detail, page_number=page_number),
                headers={'User-Agent': 'Mozilla/5.0'},
            )

            soup = bs4.BeautifulSoup(r.text, 'html.parser')

            if list_name is None:
                list_name = soup.find('h1', {'class': 'title-1 prettify'}).text

            if description is None:
                description = soup.find('div', {'class': 'body-text'})
                if description is not None:
                    description = "\n".join([p.text for p in description.find_all('p')])
                else:
                    description = ""

            if watchlist or likeslist:
                page = soup.find_all('li', {'class': 'poster-container'})
            else:
                page = soup.find_all('div', {'class': 'film-detail-content'})

            for movie_soup in page:
                if watchlist or likeslist:
                    movie = {"title": movie_soup.find('img').attrs['alt'], "media_type": "movie"}
                    link = movie_soup.find('div', {'class': 'film-poster'})['data-target-link']
                else:
                    movie = {"title": movie_soup.find('h2', {'class': 'headline-2 prettify'}).find('a').text, "media_type": "movie"}
                    movie_year = movie_soup.find('small', {'class': 'metadata'})
                    if movie_year is not None:
                        movie["release_year"] = movie_year.text

                    link = movie_soup.find('a')['href']


                if config.get("imdb_id_filter", False) or 'release_year' not in movie:
                    logger.info(f"Getting release year and imdb details for: {movie['title']}")

                    # Find the imdb id and release year
                    r = requests.get(f"https://letterboxd.com{link}", headers={'User-Agent': 'Mozilla/5.0'})
                    movie_soup = bs4.BeautifulSoup(r.text, 'html.parser')

                    imdb_id = movie_soup.find("a", {"data-track-action":"IMDb"})
                    movie_year = movie_soup.find("div", {"class": "releaseyear"})

                    if imdb_id is not None:
                        movie["imdb_id"] = imdb_id["href"].split("/title/")[1].split("/")[0]

                    if movie_year is not None:
                        movie["release_year"] = movie_year.text

                # If a movie doesn't have a year, that means that the movie is only just announced and we don't even know when it's coming out. We can easily ignore these because movies will have a year of release by the time they come out.
                if 'release_year' in movie:
                    movies.append(movie)

            if soup.find('a', {'class': 'next'}):
                page_number += 1
            else:
                break

        return {'name': list_name, 'items': movies, "description": description}
