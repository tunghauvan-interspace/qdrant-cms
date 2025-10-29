#!/bin/bash

echo "====================================="
echo "Qdrant CMS/DMS Health Check"
echo "====================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi
echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi
echo "✅ docker-compose is installed"

# Check if services are running
echo ""
echo "Checking services..."

if docker-compose ps | grep -q "qdrant.*Up"; then
    echo "✅ Qdrant is running"
else
    echo "❌ Qdrant is not running"
fi

if docker-compose ps | grep -q "backend.*Up"; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running"
fi

if docker-compose ps | grep -q "frontend.*Up"; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not running"
fi

# Check endpoints
echo ""
echo "Checking endpoints..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is accessible"
else
    echo "❌ Backend API is not accessible"
fi

if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✅ Qdrant is accessible"
else
    echo "❌ Qdrant is not accessible"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

echo ""
echo "====================================="
echo "Health check complete!"
echo "====================================="
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API Docs: http://localhost:8000/docs"
echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
