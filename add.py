# ==============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {imdb-to-overseerr v1.0}
# ==============================================================================
#  __         _   
# (_  _ |   .(_   
# __)(_)||_||| \/ 
#              /
# © 2024 Soluify LLC
# ------------------------------------------------------------------------------
import requests
import bs4
import json
import logging
from colorama import Fore, Style, init
import time
import os
from urllib.parse import quote
from halo import Halo

init(autoreset=True)

# ASCII Art with subtle animation
def display_ascii_art():
    ascii_art = """
  ___ __  __ ___  ___     __    ___ ___ ___ ___ ___ 
 |_ _|  \/  |   \| _ )  __\ \  / __| __| __| _ \ _ \\
  | || |\/| | |) | _ \ |___> > \__ \ _|| _||   /   /
 |___|_|  |_|___/|___/    /_/  |___/___|___|_|_\_|_\\
    """
    art_lines = ascii_art.split("\n")
    for line in art_lines:
        print(Fore.CYAN + line)
        time.sleep(0.1)
    print(Style.RESET_ALL)

# Colorful dividers with gradient
def print_divider(character='=', length=40):
    gradient = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    for i in range(length):
        print(gradient[i % len(gradient)] + character, end='', flush=True)
        time.sleep(0.01)
    print(Style.RESET_ALL)

# Setup logging
logging.basicConfig(filename='add.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to get user input
def get_user_input():
    print(f"{Fore.CYAN}{Style.BRIGHT}=== Hey there! Welcome to the IMDB to Overseerr Sync Tool! ==={Style.RESET_ALL}")
    overseerr_url = input(f"{Fore.MAGENTA}Alright, let's get started! Enter your Overseerr URL: {Style.RESET_ALL}")
    api_key = input(f"{Fore.MAGENTA}Great! Now, enter your Overseerr API Key: {Style.RESET_ALL}")
    imdb_list_id = input(f"{Fore.MAGENTA}Awesome! Finally, enter your IMDB List ID: {Style.RESET_ALL}")
    return overseerr_url, api_key, imdb_list_id

# Function to save Overseerr details to config.json
def save_config(overseerr_url, api_key):
    config = {
        "overseerr_url": overseerr_url,
        "api_key": api_key
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)

# Function to load Overseerr details from config.json
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config['overseerr_url'], config['api_key']
    return None, None

# Function to test Overseerr API connection
def test_overseerr_api(overseerr_url, api_key):
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    test_url = f"{overseerr_url}/api/v1/status"
    spinner = Halo(text=f'{Fore.YELLOW}Hang tight! Connecting to the Overseerr API...{Style.RESET_ALL}', spinner='dots')
    spinner.start()
    response = requests.get(test_url, headers=headers)
    if response.status_code == 200:
        spinner.succeed(f"{Fore.GREEN}🎉 Huzzah! Overseerr API connection successful!{Style.RESET_ALL}")
        logging.info("Overseerr API connection successful!")
    else:
        spinner.fail(f"{Fore.RED}🚨 Oh no! Overseerr API connection failed. Status code: {response.status_code}{Style.RESET_ALL}")
        logging.error(f"Overseerr API connection failed. Status code: {response.status_code}")
        raise Exception("Overseerr API connection failed.")

# Function to fetch and parse IMDB list
def fetch_imdb_list(list_id):
    spinner = Halo(text=f'{Fore.YELLOW}Fetching that IMDB list for you...{Style.RESET_ALL}', spinner='dots')
    spinner.start()
    r = requests.get(f'https://www.imdb.com/list/{list_id}', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US'})
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    list_name = soup.find('h1').text
    description = soup.find("div", {"class": "list-description"}).text

    ld_json = soup.find("script", {"type": "application/ld+json"}).text
    ld_json = json.loads(ld_json)
    movies = []
    for row in ld_json["itemListElement"]:
        url_parts = row["item"]["url"].split("/")
        url_parts = [p for p in url_parts if p != ""]

        movies.append({
            "title": row["item"]["name"],
            "media_type": row["item"]["@type"],
            "imdb_id": url_parts[-1]
        })

    spinner.succeed(f'{Fore.GREEN}✨ Boom! IMDB list fetched successfully! Found {len(movies)} items.{Style.RESET_ALL}')
    return {'name': list_name, 'items': movies, "description": description}

# Function to search for a movie in Overseerr
def search_movie_in_overseerr(overseerr_url, api_key, movie_title):
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    encoded_title = quote(movie_title)
    search_url = f"{overseerr_url}/api/v1/search?query={encoded_title}"
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Uh-oh, hit a snag while searching for the movie: {response.status_code}, Response: {response.text}")
    search_results = response.json()
    if not search_results['results']:
        return None
    for result in search_results['results']:
        if result['mediaType'] == 'movie':
            return result['id'], result['mediaType']
    return None

# Function to request a movie in Overseerr
def request_movie_in_overseerr(overseerr_url, api_key, movie_id, media_type):
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    request_url = f"{overseerr_url}/api/v1/request"
    payload = {
        "mediaId": movie_id,
        "mediaType": media_type,
        "is4k": False
    }
    response = requests.post(request_url, headers=headers, json=payload)
    if response.status_code == 409:
        return "already_exists"
    elif response.status_code == 201:
        return "success"
    else:
        raise Exception(f"Yikes! Couldn't request the movie: {response.status_code}, Response: {response.text}")

# Main function
def main():
    display_ascii_art()
    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url, api_key, imdb_list_id = get_user_input()
        save_config(overseerr_url, api_key)
    else:
        imdb_list_id = input(f"{Fore.MAGENTA}Enter IMDB List ID: (e.g. ls012345678) {Style.RESET_ALL}")

    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(f"{Fore.RED}🚫 Error testing Overseerr API: {e}{Style.RESET_ALL}")
        logging.error(f"Error testing Overseerr API: {e}")
        return

    try:
        imdb_list = fetch_imdb_list(imdb_list_id)
        movie_titles = [movie['title'] for movie in imdb_list['items']]
    except Exception as e:
        print(f"{Fore.RED}🌧️ Error fetching IMDB list: {e}{Style.RESET_ALL}")
        logging.error(f"Error fetching IMDB list: {e}")
        return

    total_movies = len(movie_titles)
    requested_movies = 0
    failed_movies = 0
    already_requested_movies = 0
    
    print_divider()

    for idx, movie_title in enumerate(movie_titles, 1):
        print(f"{Fore.YELLOW}Processing movie {Style.BRIGHT}{idx}/{total_movies}{Style.NORMAL}: {movie_title}{Style.RESET_ALL}")
        logging.info(f"Processing movie {idx}/{total_movies}: {movie_title}")
        try:
            search_result = search_movie_in_overseerr(overseerr_url, api_key, movie_title)
            if search_result:
                movie_id, media_type = search_result
                request_status = request_movie_in_overseerr(overseerr_url, api_key, movie_id, media_type)
                if request_status == "success":
                    print(f"{Fore.GREEN}✅ Movie requested successfully: {movie_title}{Style.RESET_ALL}")
                    logging.info(f"Requested movie: {movie_title}")
                    requested_movies += 1
                elif request_status == "already_exists":
                    print(f"{Fore.YELLOW}☑️ Movie already exists in Overseerr: {movie_title}{Style.RESET_ALL}")
                    logging.info(f"Movie already exists in Overseerr: {movie_title}")
                    already_requested_movies += 1
            else:
                print(f"{Fore.RED}🔔 Movie not found in Overseerr: {movie_title}{Style.RESET_ALL}")
                logging.error(f"Movie not found in Overseerr: {movie_title}")
                failed_movies += 1
        except Exception as e:
            print(f"{Fore.RED}❌ Uh-oh, encountered an error with movie {movie_title}: {e}{Style.RESET_ALL}")
            logging.error(f"Error processing movie {movie_title}: {e}")
            failed_movies += 1
        time.sleep(1)  # To avoid rate limiting

    print_divider()

    print(f"{Fore.CYAN}{Style.BRIGHT}=== All done! Here's the summary! ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}Total movies processed: {total_movies}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Movies successfully requested: {requested_movies}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Movies already requested: {already_requested_movies}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Movies not found: {failed_movies}{Style.RESET_ALL}")
    logging.info(f"Summary: Total movies processed: {total_movies}, Requested: {requested_movies}, Already Requested: {already_requested_movies}, Not Found: {failed_movies}")

if __name__ == "__main__":
    main()
