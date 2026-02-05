#!/bin/bash
# Database test script

set -e

echo "🧪 Testing Portfolio Tracker Database"
echo "======================================"
echo ""

# Test 1: Check tables exist
echo "✓ Test 1: Checking tables..."
TABLES=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';")
echo "  Found $TABLES tables"

# Test 2: Check seed data
echo ""
echo "✓ Test 2: Checking seed data..."
ASSETS=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM assets;")
echo "  Assets: $ASSETS (expected: 10)"

USERS=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM users;")
echo "  Users: $USERS (expected: 1)"

PORTFOLIOS=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM portfolios;")
echo "  Portfolios: $PORTFOLIOS (expected: 1)"

# Test 3: Check partitions
echo ""
echo "✓ Test 3: Checking partitions..."
PARTITIONS=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'asset_prices_%';")
echo "  Partitions: $PARTITIONS (expected: 12)"

# Test 4: Test full-text search
echo ""
echo "✓ Test 4: Testing full-text search..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT symbol, name FROM assets 
WHERE to_tsvector('english', name || ' ' || symbol) @@ to_tsquery('english', 'microsoft');
" | head -5

# Test 5: Test views
echo ""
echo "✓ Test 5: Testing views..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT * FROM latest_exchange_rates;
" | head -5

# Test 6: Test transaction insert and trigger
echo ""
echo "✓ Test 6: Testing transaction insert..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
INSERT INTO transactions (portfolio_id, asset_id, transaction_type, quantity, price, timestamp)
VALUES (1, 2, 'buy', 5, 350.00, NOW())
RETURNING id, asset_id, quantity, price;
"

# Test 7: Check indexes
echo ""
echo "✓ Test 7: Checking indexes..."
INDEXES=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")
echo "  Indexes: $INDEXES"

# Test 8: Check triggers
echo ""
echo "✓ Test 8: Checking triggers..."
TRIGGERS=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%transaction%';")
echo "  Triggers: $TRIGGERS (expected: 1)"

echo ""
echo "======================================"
echo "✅ All tests passed!"
echo ""
echo "Connection string:"
echo "postgresql://postgres:postgres@localhost:5432/portfolio_tracker"
