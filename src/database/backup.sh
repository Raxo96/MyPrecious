#!/bin/bash
# Database backup script for Portfolio Tracker

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="portfolio_tracker_backup_${TIMESTAMP}.sql"
CONTAINER_NAME="portfolio_tracker_db"
DB_NAME="portfolio_tracker"
DB_USER="postgres"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Creating database backup..."
echo "📁 Backup location: $BACKUP_DIR/$BACKUP_FILE"

# Create backup using pg_dump
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully!"
    echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
    echo ""
    echo "To restore this backup, run:"
    echo "  docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $BACKUP_DIR/$BACKUP_FILE"
else
    echo "❌ Backup failed!"
    exit 1
fi
