#!/bin/bash
# End-to-End Flow Test Script

echo "=== Portfolio Tracker E2E Test ==="
echo ""

echo "1. Testing API Health..."
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

echo "2. Searching for assets (MSFT)..."
curl -s "http://localhost:8000/api/assets/search?q=MSFT" | python3 -m json.tool
echo ""

echo "3. Getting current portfolio state..."
curl -s "http://localhost:8000/api/portfolios/1" | python3 -m json.tool
echo ""

echo "4. Getting current positions..."
curl -s "http://localhost:8000/api/portfolios/1/positions" | python3 -m json.tool
echo ""

echo "5. Adding new transaction (5 shares of MSFT at $400)..."
curl -s -X POST "http://localhost:8000/api/transactions?portfolio_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": 2,
    "quantity": 5,
    "price": 400.00,
    "timestamp": "2025-01-20T10:00:00"
  }' | python3 -m json.tool
echo ""

echo "6. Verifying updated positions..."
curl -s "http://localhost:8000/api/portfolios/1/positions" | python3 -m json.tool
echo ""

echo "7. Verifying updated portfolio value..."
curl -s "http://localhost:8000/api/portfolios/1" | python3 -m json.tool
echo ""

echo "=== Test Complete ==="
echo ""
echo "Frontend available at: http://localhost:5173"
echo "API available at: http://localhost:8000"
echo "Database: postgresql://postgres:postgres@localhost:5432/portfolio_tracker"
