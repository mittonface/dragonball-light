#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Move to the parent directory where docker-compose.yml should be
cd "$(dirname "$0")/.."

# Copy docker-compose.yml from server directory if it exists there
if [ -f "server/docker-compose.yml" ] && [ ! -f "docker-compose.yml" ]; then
    echo "📋 Moving docker-compose.yml to project root..."
    cp server/docker-compose.yml .
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Create external network if it doesn't exist
echo "🔗 Creating Docker network..."
docker network create proxy-network 2>/dev/null || true

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --timeout 30

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Health check
echo "🏥 Running health check..."
if curl -f -s --max-time 10 http://localhost:5005/api/status >/dev/null 2>&1; then
    echo "✅ Service is healthy and responding!"
else
    echo "❌ Health check failed!"
    echo "📋 Container logs:"
    docker-compose logs --tail=30
    exit 1
fi

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your application should be accessible at:"
echo "   Local: http://localhost:5005"
echo "   Remote: https://dragonball.mittn.ca"
echo "   Health check: http://localhost:5005/api/status"