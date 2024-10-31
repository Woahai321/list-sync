# list_sync/__init__.py

"""
List Sync Package

This package provides tools for synchronizing media lists with Overseerr.
"""

from .config import load_config, save_config
from .database import init_database, save_list_id, load_list_ids, save_sync_result
from .lists import fetch_imdb_list, fetch_trakt_list, display_lists, delete_list, edit_lists
from .overseerr import test_overseerr_api, search_media_in_overseerr, request_media_in_overseerr, request_tv_series_in_overseerr
from .sync import process_media, display_summary
from .utils import color_gradient, custom_input, setup_logging

# You can include any other initial setup code here if needed
