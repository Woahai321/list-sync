#!/bin/bash
# Shell script to start ListSync in Core-Only mode
# This deployment includes only the core synchronization functionality
# No web UI or API server - minimal resource footprint

echo "🚀 Starting ListSync Core-Only Mode..."
echo "📦 This deployment excludes the web UI and API server"
echo "🔧 Using docker-compose.core.yml configuration"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please copy .env.example to .env and configure your settings"
    echo ""
fi

# Check if Docker is running
if ! docker version > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running or not installed"
    echo "   Please start Docker and try again"
    exit 1
fi

# Start the core-only deployment
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.core.yml up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ListSync Core started successfully!"
    echo ""
    echo "📊 Core Status:"
    echo "   • Container: listsync-core"
    echo "   • Mode: Headless sync only"
    echo "   • Web UI: Not available (core mode)"
    echo "   • API Server: Not available (core mode)"
    echo ""
    echo "📝 View logs:"
    echo "   docker-compose -f docker-compose.core.yml logs -f"
    echo ""
    echo "🛑 To stop:"
    echo "   docker-compose -f docker-compose.core.yml down"
    echo "   or run: ./stop-core.sh"
else
    echo ""
    echo "❌ Failed to start ListSync Core"
    echo "   Check the logs above for error details"
fi 