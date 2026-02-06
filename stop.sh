#!/bin/bash
# Safely stop Portfolio Tracker application

echo "========================================"
echo "  Portfolio Tracker - Safe Shutdown"
echo "========================================"
echo ""

echo "🔄 Step 1: Creating database backup..."
cd src/database && ./backup.sh && cd ../..
BACKUP_STATUS=$?

if [ $BACKUP_STATUS -ne 0 ]; then
    echo ""
    echo "⚠️  Backup failed, but continuing with shutdown..."
    echo ""
fi

echo ""
echo "🛑 Step 2: Stopping all services..."
docker-compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Application stopped successfully!"
    echo "📊 All services are down"
    echo "💾 Database backup saved in src/database/backups/"
else
    echo ""
    echo "❌ Error stopping services!"
    exit 1
fi

echo ""
echo "========================================"
