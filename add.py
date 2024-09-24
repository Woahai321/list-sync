# ==============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {imdb-to-overseerr v1.0}
# ==============================================================================
#  __         _   
# (_  _ |   .(_   
# __)(_)||_||| \/ 
#              /
# © 2024 Soluify LLC
# ------------------------------------------------------------------------------
import json
import logging
import os
import time
import html
import requests
import bs4
from halo import Halo
from colorama import Fore, Style, init
from cryptography.fernet import Fernet
import getpass
import base64
from urllib.parse import quote

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Set up detailed logging for the main process
logging.basicConfig(filename='overseerr_sync.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a separate logger for successfully added items
added_logger = logging.getLogger('added_items')
added_logger.setLevel(logging.INFO)
added_handler = logging.FileHandler('added.log')
added_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
added_logger.addHandler(added_handler)

def display_ascii_art():
    ascii_art = """
  ___ __  __ ___  ___     __    ___ ___ ___ ___ ___ 
 |_ _|  \/  |   \| _ )  __\ \  / __| __| __| _ \ _ \\
  | || |\/| | |) | _ \ |___> > \__ \ _|| _||   /   /
 |___|_|  |_|___/|___/    /_/  |___/___|___|_|_\_|_\\
    """
    art_lines = ascii_art.split('\n')
    for line in art_lines:
        print(Fore.CYAN + line)
        time.sleep(0.1)
    print(Style.RESET_ALL)

def encrypt_config(data, password):
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode())

def decrypt_config(encrypted_data, password):
    key = base64.urlsafe_b64encode(password.encode().ljust(32)[:32])
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode())

def save_config(overseerr_url, api_key):
    config = {
        'overseerr_url': overseerr_url,
        'api_key': api_key
    }
    password = getpass.getpass('🔐 Enter a password to encrypt your config: ')
    encrypted_config = encrypt_config(config, password)
    with open('config.enc', 'wb') as f:
        f.write(encrypted_config)
    print(f'\n{Fore.GREEN}✅ Config saved and encrypted. Remember your password!{Style.RESET_ALL}\n')

def load_config():
    if os.path.exists('config.enc'):
        with open('config.enc', 'rb') as f:
            encrypted_config = f.read()
        password = getpass.getpass('🔑 Enter your config password: ')
        try:
            config = decrypt_config(encrypted_config, password)
            return config['overseerr_url'], config['api_key']
        except:
            print(f'\n{Fore.RED}❌ Incorrect password. Unable to decrypt config.{Style.RESET_ALL}')
            if input('\n🗑️ Delete this config and start over? (y/n): ').lower() == 'y':
                os.remove('config.enc')
                print(f'\n{Fore.YELLOW}🔄 Config deleted. Rerun the script to set it up again.{Style.RESET_ALL}\n')
            return None, None
    return None, None

def test_overseerr_api(overseerr_url, api_key):
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    test_url = f"{overseerr_url}/api/v1/status"
    spinner = Halo(text=f'{Fore.YELLOW}🔍 Testing Overseerr API connection...{Style.RESET_ALL}', spinner='dots')
    spinner.start()
    try:
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        spinner.succeed(f'{Fore.GREEN}🎉 Overseerr API connection successful!{Style.RESET_ALL}')
        logging.info('Overseerr API connection successful!')
    except Exception as e:
        spinner.fail(f'{Fore.RED}❌ Overseerr API connection failed. Error: {str(e)}{Style.RESET_ALL}')
        logging.error(f'Overseerr API connection failed. Error: {str(e)}')
        raise

def fetch_imdb_list(list_id):
    spinner = Halo(text=f'{Fore.YELLOW}📚 Fetching IMDB list...{Style.RESET_ALL}', spinner='dots')
    spinner.start()
    try:
        r = requests.get(f'https://www.imdb.com/list/{list_id}', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        ld_json = json.loads(soup.find("script", {"type": "application/ld+json"}).text)
        movies = [{"title": html.unescape(row["item"]["name"]), "imdb_id": row["item"]["url"].split("/")[-2]} for row in ld_json["itemListElement"]]
        spinner.succeed(f'{Fore.GREEN}✨ Successfully fetched {len(movies)} movies from IMDB list!{Style.RESET_ALL}')
        logging.info(f'IMDB list fetched successfully. Found {len(movies)} items.')
        return movies
    except Exception as e:
        spinner.fail(f'{Fore.RED}💥 Failed to fetch IMDB list. Error: {str(e)}{Style.RESET_ALL}')
        logging.error(f'Error fetching IMDB list: {str(e)}')
        raise

def search_movie_in_overseerr(overseerr_url, api_key, movie_title):
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    search_url = f'{overseerr_url}/api/v1/search?query={quote(movie_title)}'
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        search_results = response.json()
        logging.debug(f'Search response for "{movie_title}": {json.dumps(search_results)}')
        
        for result in search_results.get('results', []):
            if result['mediaType'] == 'movie':
                movie_id = result['id']
                media_type = result['mediaType']
                
                # Get detailed movie information
                movie_url = f'{overseerr_url}/api/v1/movie/{movie_id}'
                movie_response = requests.get(movie_url, headers=headers)
                movie_response.raise_for_status()
                movie_data = movie_response.json()
                
                media_info = movie_data.get('mediaInfo', {})
                
                is_available_to_watch = media_info.get('status') == 'available'
                is_requested = any(
                    request['status'] in ['pending', 'processing', 'approved'] 
                    for request in movie_data.get('requests', [])
                )
                return {
                    'id': movie_id,
                    'mediaType': media_type,
                    'is_available_to_watch': is_available_to_watch,
                    'is_requested': is_requested
                }
        return None
    except Exception as e:
        logging.error(f'Error searching for movie "{movie_title}": {str(e)}')
        raise

def request_movie_in_overseerr(overseerr_url, api_key, movie_id, media_type):
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    request_url = f'{overseerr_url}/api/v1/request'
    payload = {'mediaId': movie_id, 'mediaType': media_type, 'is4k': False}
    try:
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.debug(f'Request response for movie ID {movie_id}: {json.dumps(response.json())}')
        return 'success'
    except Exception as e:
        logging.error(f'Error requesting movie ID {movie_id}: {str(e)}')
        return 'error'

def main():
    display_ascii_art()
    
    print(f'{Fore.CYAN}👋 Welcome to the IMDB to Overseerr Sync Tool!{Style.RESET_ALL}\n')
    
    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url = input(f'\n{Fore.MAGENTA}🌐 Enter your Overseerr URL: {Style.RESET_ALL}')
        api_key = input(f'\n{Fore.MAGENTA}🔑 Enter your Overseerr API key: {Style.RESET_ALL}')
        save_config(overseerr_url, api_key)
    
    imdb_list_id = input(f'\n{Fore.MAGENTA}📋 Enter IMDB List ID (e.g., ls012345678): {Style.RESET_ALL}')

    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(f'\n{Fore.RED}❌ Error testing Overseerr API: {e}{Style.RESET_ALL}\n')
        logging.error(f'Error testing Overseerr API: {e}')
        return

    try:
        movies = fetch_imdb_list(imdb_list_id)
    except Exception as e:
        print(f'\n{Fore.RED}❌ Error fetching IMDB list: {e}{Style.RESET_ALL}\n')
        logging.error(f'Error fetching IMDB list: {e}')
        return

    total_movies = len(movies)
    requested_movies = 0
    already_requested_movies = 0
    already_available_movies = 0
    failed_movies = 0
    not_found_movies = 0

    print(f'\n{Fore.CYAN}🎬 Processing movies...{Style.RESET_ALL}\n')
    for idx, movie in enumerate(movies, 1):
        print(f'{Fore.YELLOW}📽 {idx}/{total_movies} - {movie["title"]}{Style.RESET_ALL}\n')
        logging.info(f'Processing movie {idx}/{total_movies}: {movie["title"]}')
        try:
            search_result = search_movie_in_overseerr(overseerr_url, api_key, movie['title'])
            if search_result:
                if search_result['is_available_to_watch']:  # Available to watch
                    print(f'{Fore.CYAN}✅ Already available: {movie["title"]}{Style.RESET_ALL}\n')
                    logging.info(f'Movie already available: {movie["title"]}')
                    already_available_movies += 1
                elif search_result['is_requested']:  # Already requested, not yet available
                    print(f'{Fore.YELLOW}📌 Already requested: {movie["title"]}{Style.RESET_ALL}\n')
                    logging.info(f'Movie already requested: {movie["title"]}')
                    already_requested_movies += 1
                else:  # Available to request
                    request_status = request_movie_in_overseerr(overseerr_url, api_key, search_result['id'], search_result['mediaType'])
                    if request_status == 'success':
                        print(f'{Fore.GREEN}🎉 Requested: {movie["title"]}{Style.RESET_ALL}\n')
                        logging.info(f'Requested movie: {movie["title"]}')
                        added_logger.info(f'Requested: {movie["title"]} (IMDB ID: {movie["imdb_id"]})')
                        requested_movies += 1
                    else:
                        print(f'{Fore.RED}❌ Failed to request: {movie["title"]}{Style.RESET_ALL}\n')
                        logging.error(f'Failed to request movie: {movie["title"]}')
                        failed_movies += 1
            else:
                print(f'{Fore.RED}❓ Not found: {movie["title"]}{Style.RESET_ALL}\n')
                logging.error(f'Movie not found in Overseerr: {movie["title"]}')
                not_found_movies += 1
        except Exception as e:
            print(f'{Fore.RED}❌ Error processing: {movie["title"]}{Style.RESET_ALL}\n')
            logging.error(f'Error processing movie {movie["title"]}: {e}')
            failed_movies += 1
        time.sleep(1)  # Rate limiting

    print(f'\n{Fore.CYAN}📊 Summary{Style.RESET_ALL}\n')
    print(f'{Fore.BLUE}🎥 Total movies in list: {total_movies}{Style.RESET_ALL}\n')
    print(f'{Fore.GREEN}✅ Successfully requested: {requested_movies}{Style.RESET_ALL}\n')
    print(f'{Fore.YELLOW}📌 Already requested: {already_requested_movies}{Style.RESET_ALL}\n')
    print(f'{Fore.CYAN}🍿 Already available: {already_available_movies}{Style.RESET_ALL}\n')
    print(f'{Fore.RED}❓ Not found: {not_found_movies}{Style.RESET_ALL}\n')
    print(f'{Fore.RED}❌ Failed to process: {failed_movies}{Style.RESET_ALL}\n')
    logging.info(f'Summary: Total: {total_movies}, Requested: {requested_movies}, Already Requested: {already_requested_movies}, Already Available: {already_available_movies}, Not Found: {not_found_movies}, Failed: {failed_movies}')

if __name__ == "__main__":
    main()
