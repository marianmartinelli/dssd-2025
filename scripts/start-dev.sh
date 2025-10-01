#!/bin/bash

# Development startup script for ProjectPlanning
# This script starts all services in development mode

set -e

echo "🚀 Starting ProjectPlanning development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Copy environment files if they don't exist
if [ ! -f "infra/.env" ]; then
    echo "📋 Copying environment configuration..."
    cp infra/.env.example infra/.env
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
fi

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
fi

# Start services
echo "🐳 Starting Docker services..."
cd infra
docker-compose -f docker-compose.dev.yml up --build -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000/api/v1"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🏢 Bonita Portal: http://localhost:8080/bonita (LOCAL - not in Docker)"
echo "🗄️  PostgreSQL: localhost:5432 (Docker)"
echo ""
echo "👤 Demo credentials:"
echo "   Email: admin@example.org"
echo "   Password: admin123"
echo ""
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo "📋 To view logs: docker-compose logs -f [service-name]"
