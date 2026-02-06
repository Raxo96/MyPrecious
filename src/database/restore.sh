#!/bin/bash
# Database restore script for Portfolio Tracker

# Configuration
BACKUP_DIR="./backups"
CONTAINER_NAME="portfolio_tracker_db"
DB_NAME="portfolio_tracker"
DB_USER="postgres"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a backup file name"
    echo ""
    echo "Usage: ./restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/*.sql 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will replace all data in the database!"
echo "📁 Backup file: $BACKUP_DIR/$BACKUP_FILE"
echo ""
read -p "Are you sure you want to restore? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo ""
echo "🔄 Restoring database from backup..."

# Restore backup using psql
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"
else
    echo "❌ Restore failed!"
    exit 1
fi
