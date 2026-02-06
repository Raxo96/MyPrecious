#!/usr/bin/env python3
"""
Manually trigger price update for testing (simulates 15-min timer).
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from backfill_daemon import BackfillDaemon

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
daemon = BackfillDaemon(db_url)
daemon.loader.connect()

print("Triggering manual price update...")
daemon._update_tracked_prices()

daemon.loader.close()
print("Done!")
