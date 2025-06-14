"""
Logging utilities for the ListSync application.
"""

import logging
import os

# Define paths for data directory
DATA_DIR = "./data"

def ensure_data_directory_exists():
    """Ensure the data directory exists for logs and configuration files."""
    os.makedirs(DATA_DIR, exist_ok=True)

def setup_logging():
    """
    Set up logging with file and console handlers.
    
    Returns:
        logging.Logger: Logger for added items
    """
    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # Set up file handler for general logging (DEBUG and above)
    file_handler = logging.FileHandler(os.path.join(DATA_DIR, "list_sync.log"), mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Create a custom filter to block non-colored output
    class ColoredOutputFilter(logging.Filter):
        def filter(self, record):
            # Only allow ERROR level messages that are explicitly marked for console
            return False  # Block all logging to console
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ColoredOutputFilter())
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set up separate logger for added items
    added_logger = logging.getLogger("added_items")
    added_logger.setLevel(logging.INFO)
    added_handler = logging.FileHandler(os.path.join(DATA_DIR, "added.log"), mode='a')
    added_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    added_logger.addHandler(added_handler)
    
    # Prevent added_logger from propagating to root logger
    added_logger.propagate = False
    
    selenium_logger = logging.getLogger('selenium')
    selenium_logger.setLevel(logging.INFO)
    selenium_logger.propagate = False
    
    # Disable urllib3 logging to console
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.INFO)
    urllib3_logger.propagate = False
    
    return added_logger 