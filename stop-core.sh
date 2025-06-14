#!/bin/bash 
# Shell script to stop ListSync Core-Only mode

echo "🛑 Stopping ListSync Core-Only Mode..."
echo ""

# Stop the core-only deployment
docker-compose -f docker-compose.core.yml down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ListSync Core stopped successfully!"
    echo ""
    echo "🔄 To restart:"
    echo "   ./start-core.sh"
else
    echo ""
    echo "❌ Error stopping ListSync Core"
    echo "   Check Docker status and try again"
fi 