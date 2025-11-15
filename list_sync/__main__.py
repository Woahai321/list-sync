"""
Entry point for running ListSync as a module.
Allows the package to be run with: python -m list_sync
"""

import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from .main import main

if __name__ == "__main__":
    main() 