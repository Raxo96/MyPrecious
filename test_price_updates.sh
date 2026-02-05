#!/bin/bash
# Test real-time price updates

echo "=== Real-Time Price Updates Test ==="
echo ""

echo "1. Current tracked assets:"
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT 
    a.symbol,
    ta.tracking_users,
    ta.last_price_update,
    (SELECT COUNT(*) FROM asset_prices WHERE asset_id = a.id) as price_records
FROM tracked_assets ta
JOIN assets a ON ta.asset_id = a.id
WHERE ta.tracking_users > 0
ORDER BY a.symbol;
"

echo ""
echo "2. Latest prices before update:"
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT 
    a.symbol,
    ap.timestamp,
    ap.close as price
FROM assets a
JOIN asset_prices ap ON a.id = ap.asset_id
WHERE a.symbol IN ('NFLX', 'AMD')
  AND ap.timestamp = (
    SELECT MAX(timestamp) 
    FROM asset_prices 
    WHERE asset_id = a.id
  )
ORDER BY a.symbol;
"

echo ""
echo "3. Triggering manual price update..."
cd /local/home/hoskarro/workplace/MyPrecious/src/fetcher
source venv/bin/activate
python test_price_update.py

echo ""
echo "4. Latest prices after update:"
docker exec portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "
SELECT 
    a.symbol,
    ap.timestamp,
    ap.close as price
FROM assets a
JOIN asset_prices ap ON a.id = ap.asset_id
WHERE a.symbol IN ('NFLX', 'AMD')
  AND ap.timestamp = (
    SELECT MAX(timestamp) 
    FROM asset_prices 
    WHERE asset_id = a.id
  )
ORDER BY a.symbol;
"

echo ""
echo "5. Daemon status:"
docker logs portfolio_tracker_fetcher --tail 5

echo ""
echo "=== Test Complete ==="
echo ""
echo "Note: In production, updates happen automatically every 15 minutes"
echo "Next automatic update in: ~15 minutes from daemon start"
