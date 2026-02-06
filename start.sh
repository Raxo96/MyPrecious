#!/bin/bash
# Safely start Portfolio Tracker application

echo "========================================"
echo "  Portfolio Tracker - Safe Startup"
echo "========================================"
echo ""

echo "🚀 Starting all services..."
docker-compose up -d --wait

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Application started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "========================================"
    echo "  Access Points:"
    echo "========================================"
    echo "  Frontend:  http://localhost:5173"
    echo "  API:       http://localhost:8000"
    echo "  Database:  localhost:5432"
    echo "========================================"
else
    echo ""
    echo "❌ Error starting services!"
    echo ""
    echo "🔍 Checking logs..."
    docker-compose logs --tail=50
    exit 1
fi
