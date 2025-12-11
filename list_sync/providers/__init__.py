"""
List provider registration and management.
"""

import logging
from typing import Dict, Callable, List, Any


class SyncCancelledException(Exception):
    """Exception raised when sync cancellation is requested."""
    pass


def check_cancellation() -> bool:
    """
    Check if sync cancellation has been requested.
    
    Returns:
        bool: True if cancellation was requested, False otherwise
    """
    try:
        from ..utils.sync_status import get_sync_tracker
        sync_tracker = get_sync_tracker()
        return sync_tracker.is_cancellation_requested()
    except Exception as e:
        logging.warning(f"Error checking cancellation status in provider: {e}")
        return False


def check_and_raise_if_cancelled():
    """
    Check if cancellation was requested and raise SyncCancelledException if so.
    
    Raises:
        SyncCancelledException: If cancellation was requested
    """
    if check_cancellation():
        logging.warning("⚠️ Sync cancellation detected in provider - stopping fetch operation")
        raise SyncCancelledException("Sync cancelled by user")


# Registry to store provider functions by type
PROVIDERS = {}


def register_provider(provider_type: str):
    """
    Decorator to register a provider function.
    
    Args:
        provider_type (str): Type of provider (e.g., 'imdb', 'trakt')
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func):
        PROVIDERS[provider_type] = func
        return func
    return decorator


def get_provider(provider_type: str) -> Callable:
    """
    Get the provider function for a given type.
    
    Args:
        provider_type (str): Type of provider
        
    Returns:
        Callable: Provider function
        
    Raises:
        ValueError: If provider type is not supported
    """
    # Import providers if not already imported
    if not PROVIDERS:
        _import_all_providers()
    
    if provider_type not in PROVIDERS:
        raise ValueError(f"Provider type '{provider_type}' not supported. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[provider_type]


def get_available_providers() -> List[str]:
    """
    Get a list of available provider types.
    
    Returns:
        List[str]: List of available provider types
    """
    # Import providers if not already imported
    if not PROVIDERS:
        _import_all_providers()
    
    return list(PROVIDERS.keys())


def _import_all_providers():
    """Import all providers to register them."""
    try:
        from . import imdb
        from . import trakt
        from . import letterboxd
        from . import mdblist
        from . import stevenlu
        from . import tmdb
        from . import simkl
        from . import tvdb
        from . import anilist
        from . import collections
    except ImportError as e:
        import logging
        logging.warning(f"Could not import all providers: {e}")


# Import providers immediately when this module is loaded
_import_all_providers()
