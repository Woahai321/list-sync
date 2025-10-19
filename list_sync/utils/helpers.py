"""
Helper utilities shared across the application.
"""

import re
import readline
import logging
import os
from colorama import Style
from seleniumbase import SB


def custom_input(prompt):
    """
    Custom input function that supports better readline functionality.
    
    Args:
        prompt (str): The prompt to display to the user
        
    Returns:
        str: The user's input
    """
    readline.set_startup_hook(lambda: readline.insert_text(''))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def color_gradient(text, start_color, end_color):
    """
    Create a color gradient for the given text.
    
    Args:
        text (str): The text to apply the gradient to
        start_color (str): The starting color in hex format (e.g., "#00aaff")
        end_color (str): The ending color in hex format (e.g., "#00ffaa")
        
    Returns:
        str: The text with ANSI color gradient applied
    """
    def hex_to_rgb(hex_code):
        return tuple(int(hex_code.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)

    gradient_text = ""
    steps = len(text)

    for i, char in enumerate(text):
        ratio = i / steps if steps > 1 else 0
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        gradient_text += f"\033[38;2;{r};{g};{b}m{char}"

    return gradient_text + Style.RESET_ALL


def normalize_title(title: str) -> str:
    """
    Normalize a title for comparison by removing special characters and converting to lowercase.
    
    Args:
        title (str): The title to normalize
        
    Returns:
        str: The normalized title
    """
    # Remove special characters, keeping only alphanumeric and spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    # Convert to lowercase and remove extra spaces
    normalized = ' '.join(normalized.lower().split())
    return normalized


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate fuzzy match similarity between two titles using Levenshtein distance.
    
    Args:
        title1 (str): First title
        title2 (str): Second title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Convert to lowercase for comparison but keep articles
    t1 = title1.lower()
    t2 = title2.lower()
    
    # Calculate Levenshtein distance
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Get the Levenshtein distance
    distance = levenshtein(t1, t2)
    max_length = max(len(t1), len(t2))
    
    # Convert distance to similarity score (0 to 1)
    similarity = 1 - (distance / max_length) if max_length > 0 else 0
    return similarity


def format_time_remaining(seconds):
    """
    Format seconds into hours, minutes, seconds.
    
    Args:
        seconds (float): Number of seconds
        
    Returns:
        str: Formatted time string (e.g., "2h 30m 15s")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{int(hours)}h {int(minutes)}m {int(secs)}s"


def init_selenium_driver():
    """
    Initialize Selenium driver to ensure it's working properly.
    
    Raises:
        Exception: If Selenium driver initialization fails
    """
    logging.info("Initializing Selenium driver...")
    try:
        chrome_options = [
            "--no-sandbox",
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--remote-debugging-port=9222",
            f"--user-data-dir=/tmp/chrome-data-{os.getpid()}"
        ]
        
        with SB(uc=True, 
               headless=True,
               browser='chrome',
               chromium_arg=" ".join(chrome_options),
               xvfb=True) as sb:
            logging.info("Chrome version: " + sb.execute_script("return navigator.userAgent"))
            sb.get("about:blank")
        logging.info("Successfully initialized Selenium driver")
    except Exception as e:
        logging.error(f"Failed to initialize Selenium driver: {str(e)}")
        logging.error(f"Chrome binary path: {os.environ.get('CHROME_BIN')}")
        logging.error(f"ChromeDriver path: {os.environ.get('CHROME_DRIVER_PATH')}")
        raise


def sleep_with_countdown(seconds, overseerr_client, setup_logging_func):
    """
    Sleep with countdown and handle keyboard interrupts for exit or sync.
    
    Args:
        seconds (int): Number of seconds to sleep
        overseerr_client: Overseerr API client (unused but kept for compatibility)
        setup_logging_func: Logging setup function (unused but kept for compatibility)
    """
    import time
    import os
    from .logger import DATA_DIR
    
    # Non-interactive mode (e.g., Docker container)
    try:
        start_time = time.time()
        end_time = start_time + seconds
        
        while time.time() < end_time:
            remaining = end_time - time.time()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            print(f'Next sync in: {hours}h {minutes}m', flush=True)
            
            # Check for interrupt.txt
            if os.path.exists(f"{DATA_DIR}/interrupt.txt"):
                os.remove(f"{DATA_DIR}/interrupt.txt")
                raise KeyboardInterrupt()
                
            time.sleep(60)  # Sleep for 1 minute between updates
            
    except KeyboardInterrupt:
        print("\nExiting automated sync mode...")
        raise


def construct_list_url(list_type: str, list_id: str) -> str:
    """
    Construct the full URL for a list based on its type and ID.
    
    Args:
        list_type (str): Type of list (imdb, trakt, trakt_special, letterboxd, mdblist, stevenlu)
        list_id (str): List ID or URL
        
    Returns:
        str: Full URL for the list
    """
    # If it's already a full URL, return as is
    if list_id.startswith(('http://', 'https://')):
        return list_id
    
    # Construct URLs based on list type
    if list_type.lower() == "imdb":
        # Handle special chart names
        if list_id in ['top', 'boxoffice', 'moviemeter', 'tvmeter']:
            return f"https://www.imdb.com/chart/{list_id}"
        # Handle user watchlist format
        elif list_id.startswith('ur'):
            return f"https://www.imdb.com/user/{list_id}/watchlist"
        # Handle regular list format
        elif list_id.startswith('ls'):
            return f"https://www.imdb.com/list/{list_id}"
        else:
            # Fallback for unknown format
            return f"https://www.imdb.com/list/{list_id}"
    
    elif list_type.lower() in ["trakt", "trakt_special"]:
        # Handle numeric list IDs (regular trakt lists)
        if list_id.isdigit():
            return f"https://trakt.tv/lists/{list_id}"
        # Handle special Trakt lists (shortcuts)
        elif ':' in list_id:
            parts = list_id.split(':')
            if len(parts) == 2:
                list_name, media_type = parts
                if media_type.lower() == 'movies':
                    return f"https://trakt.tv/movies/{list_name}"
                elif media_type.lower() in ['tv', 'shows']:
                    return f"https://trakt.tv/shows/{list_name}"
        # Handle special list names without colon (for trakt_special)
        elif list_type.lower() == "trakt_special":
            # These are the special list identifiers that need to be converted to proper URLs
            special_mappings = {
                # Movies
                'trending:movies': 'https://trakt.tv/movies/trending',
                'popular:movies': 'https://trakt.tv/movies/popular',
                'anticipated:movies': 'https://trakt.tv/movies/anticipated',
                'watched:movies': 'https://trakt.tv/movies/watched',
                'collected:movies': 'https://trakt.tv/movies/collected',
                'recommendations:movies': 'https://trakt.tv/movies/recommendations',
                'boxoffice:movies': 'https://trakt.tv/movies/boxoffice',
                # TV Shows
                'trending:shows': 'https://trakt.tv/shows/trending',
                'popular:shows': 'https://trakt.tv/shows/popular',
                'anticipated:shows': 'https://trakt.tv/shows/anticipated',
                'watched:shows': 'https://trakt.tv/shows/watched',
                'collected:shows': 'https://trakt.tv/shows/collected',
                'recommendations:shows': 'https://trakt.tv/shows/recommendations'
            }
            
            if list_id in special_mappings:
                return special_mappings[list_id]
            
            # If not in mappings, try to construct from the list_id format
            if list_id.startswith(('trending', 'popular', 'anticipated', 'watched', 'collected', 'recommendations', 'boxoffice')):
                parts = list_id.split(':') if ':' in list_id else [list_id, 'movies']  # Default to movies
                if len(parts) == 2:
                    list_name, media_type = parts
                    if media_type.lower() == 'movies':
                        return f"https://trakt.tv/movies/{list_name}"
                    elif media_type.lower() in ['tv', 'shows']:
                        return f"https://trakt.tv/shows/{list_name}"
        
        # Fallback for unknown format
        return f"https://trakt.tv/lists/{list_id}"
    
    elif list_type.lower() == "letterboxd":
        # Handle username/list-slug format
        if '/' in list_id:
            return f"https://letterboxd.com/{list_id}"
        else:
            # Might be a direct list path
            return f"https://letterboxd.com/{list_id}"
    
    elif list_type.lower() == "mdblist":
        # Handle username/listname format
        if '/' in list_id:
            return f"https://mdblist.com/lists/{list_id}"
        else:
            # Fallback for unknown format
            return f"https://mdblist.com/lists/{list_id}"
    
    elif list_type.lower() == "stevenlu":
        # Steven Lu has a user-friendly website
        return "https://movies.stevenlu.com/"
    
    elif list_type.lower() == "tmdb":
        # Handle TMDB list IDs
        if list_id.isdigit():
            return f"https://www.themoviedb.org/list/{list_id}"
        else:
            # If it's already a URL, return as is
            return list_id
    
    elif list_type.lower() == "simkl":
        # Handle Simkl list IDs
        if list_id.isdigit():
            return f"https://simkl.com/5/list/{list_id}"
        else:
            # If it's already a URL, return as is
            return list_id
    
    else:
        # Unknown list type, return the ID as-is
        return list_id
