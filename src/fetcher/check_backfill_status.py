#!/usr/bin/env python3
"""
Quick status check for the backfill operation.

This script provides a snapshot of the current backfill progress.
"""

import psycopg2
import os
from datetime import datetime


def check_status():
    """Check and display backfill status."""
    
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/portfolio_tracker'
    )
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("BACKFILL STATUS CHECK")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Queue status
        print("Backfill Queue Status:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM backfill_queue
            GROUP BY status
            ORDER BY status
        """)
        
        total_tasks = 0
        completed = 0
        for status, count in cursor.fetchall():
            print(f"  {status:15s}: {count:4d}")
            total_tasks += count
            if status == 'completed':
                completed = count
        
        if total_tasks > 0:
            progress_pct = (completed / total_tasks) * 100
            print(f"\n  Progress: {completed}/{total_tasks} ({progress_pct:.1f}%)")
        print()
        
        # Asset data
        print("Asset Data:")
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT asset_id) as assets_with_data,
                COUNT(*) as total_records,
                MIN(timestamp::date) as earliest_date,
                MAX(timestamp::date) as latest_date
            FROM asset_prices
        """)
        
        row = cursor.fetchone()
        if row:
            assets, records, earliest, latest = row
            print(f"  Assets with data: {assets}")
            print(f"  Total records:    {records:,}")
            if earliest and latest:
                print(f"  Date range:       {earliest} to {latest}")
        print()
        
        # Recent activity
        print("Recent Activity (last 10 completed):")
        cursor.execute("""
            SELECT 
                a.symbol,
                bq.completed_at,
                (SELECT COUNT(*) FROM asset_prices WHERE asset_id = a.id) as record_count
            FROM backfill_queue bq
            JOIN assets a ON bq.asset_id = a.id
            WHERE bq.status = 'completed'
            ORDER BY bq.completed_at DESC
            LIMIT 10
        """)
        
        for symbol, completed_at, record_count in cursor.fetchall():
            time_str = completed_at.strftime('%H:%M:%S') if completed_at else 'N/A'
            print(f"  {symbol:6s} - {time_str} - {record_count:3d} records")
        print()
        
        # Failed tasks
        cursor.execute("""
            SELECT COUNT(*) FROM backfill_queue WHERE status = 'failed'
        """)
        failed_count = cursor.fetchone()[0]
        
        if failed_count > 0:
            print(f"Failed Tasks: {failed_count}")
            cursor.execute("""
                SELECT 
                    a.symbol,
                    bq.attempts,
                    bq.error_message
                FROM backfill_queue bq
                JOIN assets a ON bq.asset_id = a.id
                WHERE bq.status = 'failed'
                ORDER BY bq.updated_at DESC
                LIMIT 5
            """)
            
            for symbol, attempts, error in cursor.fetchall():
                error_short = error[:50] + '...' if error and len(error) > 50 else error
                print(f"  {symbol:6s} - {attempts} attempts - {error_short}")
            print()
        
        # Estimated completion
        cursor.execute("""
            SELECT COUNT(*) FROM backfill_queue 
            WHERE status IN ('pending', 'failed', 'rate_limited')
        """)
        remaining = cursor.fetchone()[0]
        
        if remaining > 0:
            est_minutes = remaining * 2 / 60  # 2 seconds per symbol average
            print(f"Estimated time remaining: {est_minutes:.1f} minutes ({remaining} tasks)")
        else:
            print("✓ Backfill complete!")
        
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking status: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(check_status())
