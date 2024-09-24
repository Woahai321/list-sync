# ==============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {servarr-tools_imdb-overseer_v0.2}
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

def color_gradient(text, start_color, end_color):
    def hex_to_rgb(hex_code):
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    
    start_rgb = hex_to_rgb(start_color.lstrip('#'))
    end_rgb = hex_to_rgb(end_color.lstrip('#'))
    
    gradient_text = ""
    steps = len(text)
    
    for i, char in enumerate(text):
        ratio = i / steps
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        gradient_text += f'\033[38;2;{r};{g};{b}m{char}'
    
    return gradient_text + Style.RESET_ALL

def display_ascii_art():
    ascii_art = """
  ___ __  __ ___  ___     __    ___ ___ ___ ___ ___ 
 |_ _|  \/  |   \| _ )  __\ \  / __| __| __| _ \ _ \\
  | || |\/| | |) | _ \ |___> > \__ \ _|| _||   /   /
 |___|_|  |_|___/|___/    /_/  |___/___|___|_|_\_|_\\
    """
    art_lines = ascii_art.split('\n')
    for line in art_lines:
        print(color_gradient(line, "#00aaff", "#00ffaa"))
        time.sleep(0.1)
    print(Style.RESET_ALL)

def display_banner():
    banner = """
    ==============================================================
             Soluify - {servarr-tools_imdb-overseer_v0.2}         
    ==============================================================
    """
    print(color_gradient(banner, "#aa00aa", "#00aa00") + Style.RESET_ALL)

def display_summary(total_movies, requested_movies, already_requested_movies, already_available_movies, not_found_movies, failed_movies):
    summary = f"""
    ==============================================================
                    All done! Here's the summary!                
    ==============================================================
    🔁 Total movies processed: {total_movies}

    ✅ Movies successfully requested: {requested_movies}

    📌 Movies already requested: {already_requested_movies}

    ☑️  Movies already available: {already_available_movies} 

    ❓ Movies not found: {not_found_movies}

    ❌ Movies failed to process: {failed_movies}
    ==============================================================
    """
    print(color_gradient(summary, "#00aaff", "#00ffaa") + Style.RESET_ALL)

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
    password = getpass.getpass('🔐  Enter a password to encrypt your config: ')
    encrypted_config = encrypt_config(config, password)
    with open('config.enc', 'wb') as f:
        f.write(encrypted_config)
    print(f'\n{color_gradient("✅  Config saved and encrypted. Remember your password!", "#00ff00", "#00aa00")}\n')

def load_config():
    if os.path.exists('config.enc'):
        with open('config.enc', 'rb') as f:
            encrypted_config = f.read()
        password = getpass.getpass('🔑  Enter your config password: ')
        try:
            config = decrypt_config(encrypted_config, password)
            return config['overseerr_url'], config['api_key']
        except:
            print(f'\n{color_gradient("❌  Incorrect password. Unable to decrypt config.", "#ff0000", "#aa0000")}')
            if input('\n🗑️  Delete this config and start over? (y/n): ').lower() == 'y':
                os.remove('config.enc')
                print(f'\n{color_gradient("🔄  Config deleted. Rerun the script to set it up again.", "#ffaa00", "#ff5500")}\n')
            return None, None
    return None, None

def test_overseerr_api(overseerr_url, api_key):
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    test_url = f"{overseerr_url}/api/v1/status"
    spinner = Halo(text=color_gradient("🔍  Testing Overseerr API connection...", "#ffaa00", "#ff5500"), spinner='dots')
    spinner.start()
    try:
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        spinner.succeed(color_gradient("🎉  Overseerr API connection successful!", "#00ff00", "#00aa00"))
        logging.info('Overseerr API connection successful!')
    except Exception as e:
        spinner.fail(color_gradient(f"❌  Overseerr API connection failed. Error: {str(e)}", "#ff0000", "#aa0000"))
        logging.error(f'Overseerr API connection failed. Error: {str(e)}')
        raise

def fetch_imdb_list(list_id):
    spinner = Halo(text=color_gradient("📚  Fetching IMDB list...", "#ffaa00", "#ff5500"), spinner='dots')
    spinner.start()
    try:
        r = requests.get(f'https://www.imdb.com/list/{list_id}', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        ld_json = json.loads(soup.find("script", {"type": "application/ld+json"}).text)
        movies = [{"title": html.unescape(row["item"]["name"]), "imdb_id": row["item"]["url"].split("/")[-2]} for row in ld_json["itemListElement"]]
        spinner.succeed(color_gradient(f"✨  Successfully fetched {len(movies)} movies from IMDB list!", "#00ff00", "#00aa00"))
        logging.info(f'IMDB list fetched successfully. Found {len(movies)} items.')
        return movies
    except Exception as e:
        spinner.fail(color_gradient(f"💥  Failed to fetch IMDB list. Error: {str(e)}", "#ff0000", "#aa0000"))
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
                return {
                    'id': movie_id,
                    'mediaType': media_type,
                }
        return None
    except Exception as e:
        logging.error(f'Error searching for movie "{movie_title}": {str(e)}')
        raise

def confirm_movie_status(overseerr_url, api_key, movie_id):
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    movie_url = f'{overseerr_url}/api/v1/movie/{movie_id}'
    try:
        response = requests.get(movie_url, headers=headers)
        response.raise_for_status()
        movie_data = response.json()
        logging.debug(f'Detailed response for movie ID {movie_id}: {json.dumps(movie_data)}')

        media_info = movie_data.get('mediaInfo', {})
        status = media_info.get('status')

        is_available_to_watch = status == 5
        is_requested = status in [2, 3]

        logging.debug(f'Movie ID {movie_id} - Available: {is_available_to_watch}, Requested: {is_requested}')
        return is_available_to_watch, is_requested
    except Exception as e:
        logging.error(f'Error confirming status for movie ID {movie_id}: {str(e)}')
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
    display_banner()
    display_ascii_art()
    
    print(color_gradient("👋  Welcome to the IMDB to Overseerr Sync Tool!", "#00aaff", "#00ffaa") + "\n")
    
    overseerr_url, api_key = load_config()
    if not overseerr_url or not api_key:
        overseerr_url = input(color_gradient("\n🌐  Enter your Overseerr URL: ", "#ffaa00", "#ff5500"))
        api_key = input(color_gradient("\n🔑  Enter your Overseerr API key: ", "#ffaa00", "#ff5500"))
        save_config(overseerr_url, api_key)
    
    imdb_list_id = input(color_gradient("\n📋  Enter IMDB List ID (e.g., ls012345678): ", "#ffaa00", "#ff5500"))

    try:
        test_overseerr_api(overseerr_url, api_key)
    except Exception as e:
        print(color_gradient(f"\n❌  Error testing Overseerr API: {e}", "#ff0000", "#aa0000") + "\n")
        logging.error(f'Error testing Overseerr API: {e}')
        return

    try:
        movies = fetch_imdb_list(imdb_list_id)
    except Exception as e:
        print(color_gradient(f"\n❌  Error fetching IMDB list: {e}", "#ff0000", "#aa0000") + "\n")
        logging.error(f'Error fetching IMDB list: {e}')
        return

    total_movies = len(movies)
    requested_movies = 0
    already_requested_movies = 0
    already_available_movies = 0
    failed_movies = 0
    not_found_movies = 0

    print(color_gradient("\n🎬  Processing movies...", "#00aaff", "#00ffaa") + "\n")
    for idx, movie in enumerate(movies, 1):
        movie_status = f"{idx}/{total_movies} {movie['title']}: Processing..."
        print(color_gradient(movie_status, "#ffaa00", "#ff5500"), end='\r')
        logging.info(f'Processing movie {idx}/{total_movies}: {movie["title"]}')
        try:
            search_result = search_movie_in_overseerr(overseerr_url, api_key, movie['title'])
            if search_result:
                # Confirm movie status before requesting
                is_available_to_watch, is_requested = confirm_movie_status(overseerr_url, api_key, search_result['id'])
                if is_available_to_watch:
                    movie_status = f"{idx}/{total_movies} {movie['title']}: ☑️  Already available"
                    print(color_gradient(movie_status, "#aaaaaa", "#00ff00"))
                    logging.info(f'Movie already available: {movie["title"]}')
                    already_available_movies += 1
                elif is_requested:
                    movie_status = f"{idx}/{total_movies} {movie['title']}: 📌  Already requested"
                    print(color_gradient(movie_status, "#aaaaaa", "#ffff00"))
                    logging.info(f'Movie already requested: {movie["title"]}')
                    already_requested_movies += 1
                else:
                    request_status = request_movie_in_overseerr(overseerr_url, api_key, search_result['id'], search_result['mediaType'])
                    if request_status == 'success':
                        movie_status = f"{idx}/{total_movies} {movie['title']}: ✅  Requested"
                        print(color_gradient(movie_status, "#00ff00", "#00aa00"))
                        logging.info(f'Requested movie: {movie["title"]}')
                        added_logger.info(f'Requested: {movie["title"]} (IMDB ID: {movie["imdb_id"]})')
                        requested_movies += 1
                    else:
                        movie_status = f"{idx}/{total_movies} {movie['title']}: ❌  Failed to request"
                        print(color_gradient(movie_status, "#ff0000", "#aa0000"))
                        logging.error(f'Failed to request movie: {movie["title"]}')
                        failed_movies += 1
            else:
                movie_status = f"{idx}/{total_movies} {movie['title']}: ❓  Not found"
                print(color_gradient(movie_status, "#ff0000", "#aa0000"))
                logging.error(f'Movie not found in Overseerr: {movie["title"]}')
                not_found_movies += 1
        except Exception as e:
            movie_status = f"{idx}/{total_movies} {movie['title']}: ❌  Error processing"
            print(color_gradient(movie_status, "#ff0000", "#aa0000"))
            logging.error(f'Error processing movie {movie["title"]}: {e}')
            failed_movies += 1
        time.sleep(1)  # Rate limiting

    display_summary(total_movies, requested_movies, already_requested_movies, already_available_movies, not_found_movies, failed_movies)

if __name__ == "__main__":
    main()
