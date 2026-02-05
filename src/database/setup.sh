#!/bin/bash
# Setup PostgreSQL database for Portfolio Tracker

set -e

DB_NAME="${DB_NAME:-portfolio_tracker}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Creating database: $DB_NAME"

# Create database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

echo "Running schema..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f schema.sql

echo "Running seed data..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f seed.sql

echo "✓ Database setup complete!"
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
