#!/bin/bash

echo "🐳 Testing ListSync Docker Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating a minimal example...${NC}"
    cat > .env << 'EOF'
# Minimal configuration for testing
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=test-key
OVERSEERR_USER_ID=1
SYNC_INTERVAL=24
AUTOMATED_MODE=true
TRAKT_LISTS=popular-movies
EOF
    echo -e "${GREEN}✅ Created .env file with test configuration${NC}"
fi

# Build the application
echo ""
echo "🔨 Building ListSync application..."
if docker-compose -f docker-compose.local.yml build; then
    echo -e "${GREEN}✅ Build completed successfully${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Start the application
echo ""
echo "🚀 Starting ListSync application..."
if docker-compose -f docker-compose.local.yml up -d; then
    echo -e "${GREEN}✅ Application started${NC}"
else
    echo -e "${RED}❌ Failed to start application${NC}"
    exit 1
fi

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

# Test API health
if wait_for_service "http://localhost:4222/api/system/health" "API Backend"; then
    echo "🔗 API Documentation: http://localhost:4222/docs"
else
    echo -e "${RED}❌ API Backend failed to start${NC}"
    docker-compose -f docker-compose.local.yml logs listsync-app
    exit 1
fi

# Test Frontend
if wait_for_service "http://localhost:3222" "Frontend Dashboard"; then
    echo "🎨 Dashboard: http://localhost:3222"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    docker-compose -f docker-compose.local.yml logs listsync-app
    exit 1
fi

# Check container health
echo ""
echo "🏥 Checking container health..."
if docker-compose -f docker-compose.local.yml ps | grep -q "healthy"; then
    echo -e "${GREEN}✅ Container is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Container health check pending...${NC}"
fi

# Show supervisor status
echo ""
echo "📊 Checking service status..."
docker exec listsync-complete supervisorctl status

# Test API endpoints
echo ""
echo "🧪 Testing API endpoints..."

# Health check
if curl -f -s "http://localhost:4222/api/system/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check endpoint working${NC}"
else
    echo -e "${RED}❌ Health check endpoint failed${NC}"
fi

# Stats endpoint
if curl -f -s "http://localhost:4222/api/stats/sync" > /dev/null; then
    echo -e "${GREEN}✅ Stats endpoint working${NC}"
else
    echo -e "${RED}❌ Stats endpoint failed${NC}"
fi

echo ""
echo "🎉 Test completed!"
echo "================================"
echo "📊 Dashboard: http://localhost:3222"
echo "🔗 API Docs:  http://localhost:4222/docs"
echo "❤️  Health:   http://localhost:4222/api/system/health"
echo ""
echo "To stop the application:"
echo "docker-compose -f docker-compose.local.yml down"
echo ""
echo "To view logs:"
echo "docker-compose -f docker-compose.local.yml logs -f" 