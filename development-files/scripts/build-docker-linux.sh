#!/bin/bash

# Build script for Linux environments
# This script ensures clean builds and proper cross-platform compatibility

set -e

echo "🐧 Building ListSync for Linux..."

# Clean any existing Windows-specific artifacts
echo "🧹 Cleaning Windows-specific artifacts..."
find . -name "*.cmd" -type f -delete 2>/dev/null || true
find . -name "*.bat" -type f -delete 2>/dev/null || true

# Remove any existing node_modules to ensure clean Linux build
if [ -d "listsync-web/node_modules" ]; then
    echo "🗑️  Removing existing node_modules for clean build..."
    rm -rf listsync-web/node_modules
fi

# Build the Docker image
echo "🐳 Building Docker image..."
docker compose -f docker-compose.local.yml build --no-cache

echo "✅ Build completed successfully!"
echo ""
echo "To run the application:"
echo "  docker compose -f docker-compose.local.yml up"
echo ""
echo "To run in detached mode:"
echo "  docker compose -f docker-compose.local.yml up -d" 