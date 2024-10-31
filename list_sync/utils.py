# list_sync/utils.py

import logging
import readline
import time
from colorama import Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

def color_gradient(text, start_color, end_color):
    """Apply a color gradient to the text."""
    def hex_to_rgb(hex_code):
        return tuple(int(hex_code[i: i + 2], 16) for i in (0, 2, 4))

    start_rgb = hex_to_rgb(start_color.lstrip("#"))
    end_rgb = hex_to_rgb(end_color.lstrip("#"))

    gradient_text = ""
    steps = len(text)

    for i, char in enumerate(text):
        ratio = i / steps
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        gradient_text += f"\033[38;2;{r};{g};{b}m{char}"

    return gradient_text + Style.RESET_ALL

def custom_input(prompt):
    """Provide a custom input function to handle readline startup hook."""
    readline.set_startup_hook(lambda: readline.insert_text(''))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def setup_logging():
    """Set up logging for the application."""
    logging.basicConfig(
        filename="./logs/list_sync.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    added_logger = logging.getLogger("added_items")
    added_logger.setLevel(logging.INFO)
    added_handler = logging.FileHandler("./logs/added.log")
    added_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    added_logger.addHandler(added_handler)
    return added_logger
