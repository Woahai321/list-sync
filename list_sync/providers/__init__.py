"""
List provider registration and management.
"""

from typing import Any, Callable, Dict, List

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
        from . import imdb, letterboxd, mdblist, stevenlu, trakt
    except ImportError as e:
        import logging
        logging.warning(f"Could not import all providers: {e}")


# Import providers immediately when this module is loaded
_import_all_providers()
