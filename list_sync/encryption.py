"""
Encryption utilities for securing sensitive configuration data.
Uses Fernet symmetric encryption from cryptography library.
"""

import os
import logging
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Path to persistent encryption key file (in mounted volume)
ENCRYPTION_KEY_FILE = Path("/usr/src/app/data/.encryption_key")

# Cache the key in memory to avoid repeated file reads
_cached_key = None


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key for securing sensitive settings.
    
    Key is automatically generated on first run and saved to a persistent file
    in the data directory. This ensures the same key is used across container
    restarts without requiring manual configuration.
    
    Priority:
    1. Cached key in memory (performance)
    2. Key file in data directory (persistent)
    3. ENCRYPTION_KEY environment variable (override/backup)
    4. Generate new key and save to file (first run)
    
    Returns:
        bytes: Fernet-compatible encryption key
    """
    global _cached_key
    
    # Return cached key if available
    if _cached_key:
        return _cached_key
    
    # Try to load from persistent file first
    if ENCRYPTION_KEY_FILE.exists():
        try:
            key_bytes = ENCRYPTION_KEY_FILE.read_bytes().strip()
            # Validate it's a proper Fernet key
            Fernet(key_bytes)
            _cached_key = key_bytes
            logger.info("Loaded encryption key from persistent storage")
            return _cached_key
        except Exception as e:
            logger.error(f"Failed to load encryption key from file: {e}")
            # Continue to next method
    
    # Check environment variable as backup/override
    env_key = os.getenv('ENCRYPTION_KEY')
    if env_key:
        try:
            key_bytes = env_key.encode() if isinstance(env_key, str) else env_key
            Fernet(key_bytes)  # Validate
            _cached_key = key_bytes
            logger.info("Using encryption key from environment variable")
            return _cached_key
        except Exception as e:
            logger.warning(f"Invalid ENCRYPTION_KEY in environment: {e}")
    
    # Generate a new key and save it
    logger.info("No encryption key found. Generating new key...")
    new_key = Fernet.generate_key()
    
    # Ensure data directory exists
    ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file with restricted permissions
    try:
        ENCRYPTION_KEY_FILE.write_bytes(new_key)
        # Set file permissions to 600 (owner read/write only)
        ENCRYPTION_KEY_FILE.chmod(0o600)
        logger.info(f"✅ Generated and saved new encryption key to {ENCRYPTION_KEY_FILE}")
        _cached_key = new_key
        return _cached_key
    except Exception as e:
        logger.error(f"Failed to save encryption key to file: {e}")
        logger.warning("Using in-memory encryption key (will not persist)")
        _cached_key = new_key
        return _cached_key


def encrypt_value(value: str, key: bytes = None) -> str:
    """
    Encrypt a string value using Fernet symmetric encryption.
    
    Args:
        value: Plain text value to encrypt
        key: Encryption key (uses default if None)
    
    Returns:
        str: Base64-encoded encrypted value
    """
    if not value:
        return ""
    
    if key is None:
        key = get_encryption_key()
    
    try:
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(value.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_value(encrypted_value: str, key: bytes = None) -> str:
    """
    Decrypt an encrypted string value.
    
    Args:
        encrypted_value: Base64-encoded encrypted value
        key: Encryption key (uses default if None)
    
    Returns:
        str: Decrypted plain text value
    """
    if not encrypted_value:
        return ""
    
    if key is None:
        key = get_encryption_key()
    
    try:
        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(encrypted_value.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        # Return empty string if decryption fails
        # This could happen if key changed
        logger.warning("Failed to decrypt value - encryption key may have changed")
        return ""


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Mask a sensitive value, showing only last N characters.
    
    Args:
        value: Value to mask
        show_chars: Number of characters to show at end
    
    Returns:
        str: Masked value (e.g., "****abc123")
    """
    if not value:
        return ""
    
    if len(value) <= show_chars:
        return "*" * len(value)
    
    return "*" * (len(value) - show_chars) + value[-show_chars:]


# List of sensitive configuration keys that should be encrypted
SENSITIVE_KEYS = {
    'overseerr_api_key',
    'trakt_client_id',
    'discord_webhook',
    'tmdb_key',
}


def should_encrypt(key: str) -> bool:
    """
    Check if a configuration key should be encrypted.
    
    Args:
        key: Configuration key name
    
    Returns:
        bool: True if key should be encrypted
    """
    return key.lower() in SENSITIVE_KEYS

