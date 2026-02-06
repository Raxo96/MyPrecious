#!/bin/bash
# Safely restart Portfolio Tracker application

echo "========================================"
echo "  Portfolio Tracker - Safe Restart"
echo "========================================"
echo ""

echo "🔄 Restarting application..."
echo ""

./stop.sh
if [ $? -ne 0 ]; then
    echo "❌ Stop failed!"
    exit 1
fi

echo ""
echo "⏳ Waiting 3 seconds..."
sleep 3

./start.sh
if [ $? -ne 0 ]; then
    echo "❌ Start failed!"
    exit 1
fi

echo ""
echo "✅ Restart complete!"
