#!/usr/bin/env python3
"""
Manually trigger price update for testing (simulates 15-min timer).
"""
import os
import sys
sys.path.insert(0, '/local/home/hoskarro/workplace/MyPrecious/src/fetcher')

from backfill_daemon import BackfillDaemon

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
daemon = BackfillDaemon(db_url)
daemon.loader.connect()

print("Triggering manual price update...")
daemon._update_tracked_prices()

daemon.loader.close()
print("Done!")
