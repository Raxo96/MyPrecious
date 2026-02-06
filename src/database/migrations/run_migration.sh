#!/bin/bash
# Migration Runner Script
# Runs database migrations and verifies table creation

set -e  # Exit on error

# Configuration
DB_NAME="${DB_NAME:-portfolio_tracker}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "Running Fetcher Monitoring Migration"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""

# Run the migration
echo "Applying migration 001_add_monitoring_tables.sql..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f 001_add_monitoring_tables.sql

if [ $? -eq 0 ]; then
    echo "✓ Migration applied successfully"
    echo ""
else
    echo "✗ Migration failed"
    exit 1
fi

# Verify table creation
echo "=========================================="
echo "Verifying Table Creation"
echo "=========================================="

# Check fetcher_logs table
echo -n "Checking fetcher_logs table... "
RESULT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fetcher_logs';")
if [ "$RESULT" -eq 1 ]; then
    echo "✓ EXISTS"
else
    echo "✗ NOT FOUND"
    exit 1
fi

# Check fetcher_statistics table
echo -n "Checking fetcher_statistics table... "
RESULT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fetcher_statistics';")
if [ "$RESULT" -eq 1 ]; then
    echo "✓ EXISTS"
else
    echo "✗ NOT FOUND"
    exit 1
fi

# Check price_update_log table
echo -n "Checking price_update_log table... "
RESULT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'price_update_log';")
if [ "$RESULT" -eq 1 ]; then
    echo "✓ EXISTS"
else
    echo "✗ NOT FOUND"
    exit 1
fi

# Check portfolio_performance_cache table
echo -n "Checking portfolio_performance_cache table... "
RESULT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'portfolio_performance_cache';")
if [ "$RESULT" -eq 1 ]; then
    echo "✓ EXISTS"
else
    echo "✗ NOT FOUND"
    exit 1
fi

echo ""
echo "=========================================="
echo "Verifying Indexes"
echo "=========================================="

# Check indexes on fetcher_logs
echo "Indexes on fetcher_logs:"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT indexname FROM pg_indexes WHERE tablename = 'fetcher_logs' ORDER BY indexname;"

# Check indexes on fetcher_statistics
echo "Indexes on fetcher_statistics:"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT indexname FROM pg_indexes WHERE tablename = 'fetcher_statistics' ORDER BY indexname;"

# Check indexes on price_update_log
echo "Indexes on price_update_log:"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT indexname FROM pg_indexes WHERE tablename = 'price_update_log' ORDER BY indexname;"

echo ""
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="
echo "All monitoring tables created successfully."
echo ""
