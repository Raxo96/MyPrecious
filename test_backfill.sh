#!/bin/bash
# Test backfill automation

echo "=== Backfill Automation Test ==="
echo ""

# Start daemon in background
echo "1. Starting backfill daemon..."
cd /local/home/hoskarro/workplace/MyPrecious/src/fetcher
source venv/bin/activate
python backfill_daemon.py &
DAEMON_PID=$!
echo "   Daemon started (PID: $DAEMON_PID)"
sleep 2

# Add a new asset (NFLX - Netflix)
echo ""
echo "2. Adding new asset NFLX to database..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
INSERT INTO assets (symbol, name, asset_type, exchange, native_currency)
VALUES ('NFLX', 'Netflix Inc.', 'stock', 'NASDAQ', 'USD')
ON CONFLICT (symbol, exchange) DO NOTHING
RETURNING id, symbol;
" 2>&1 | grep -E "id|symbol|INSERT|^$"

# Get NFLX asset_id
NFLX_ID=$(docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -t -c "SELECT id FROM assets WHERE symbol = 'NFLX';" | xargs)
echo "   NFLX asset_id: $NFLX_ID"

# Create a transaction to trigger the notification
echo ""
echo "3. Creating transaction to trigger backfill..."
curl -s -X POST "http://localhost:8000/api/transactions?portfolio_id=1" \
  -H "Content-Type: application/json" \
  -d "{
    \"asset_id\": $NFLX_ID,
    \"quantity\": 3,
    \"price\": 600.00,
    \"timestamp\": \"2025-02-01T10:00:00\"
  }" | python3 -m json.tool

# Wait for backfill to complete
echo ""
echo "4. Waiting for backfill to complete (10 seconds)..."
sleep 10

# Check if price data was added
echo ""
echo "5. Verifying price data was backfilled..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT 
    a.symbol,
    COUNT(ap.id) as price_records,
    MIN(ap.timestamp) as earliest_date,
    MAX(ap.timestamp) as latest_date
FROM assets a
LEFT JOIN asset_prices ap ON a.id = ap.asset_id
WHERE a.symbol = 'NFLX'
GROUP BY a.symbol;
"

# Check tracked_assets
echo ""
echo "6. Checking tracked_assets table..."
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT 
    a.symbol,
    ta.tracking_users,
    ta.last_price_update
FROM tracked_assets ta
JOIN assets a ON ta.asset_id = a.id
WHERE a.symbol = 'NFLX';
"

# Verify API returns price
echo ""
echo "7. Verifying API returns current price..."
curl -s "http://localhost:8000/api/assets/search?q=NFLX" | python3 -m json.tool

# Stop daemon
echo ""
echo "8. Stopping daemon..."
kill $DAEMON_PID
wait $DAEMON_PID 2>/dev/null

echo ""
echo "=== Test Complete ==="
