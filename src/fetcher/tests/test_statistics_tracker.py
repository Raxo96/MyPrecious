#!/usr/bin/env python3
"""
Test script for StatisticsTracker component.
Tests basic functionality: connect, record_cycle_start, record_cycle_end, 
get_statistics, persist_statistics.
"""
import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from statistics_tracker import StatisticsTracker


def test_statistics_tracker():
    """Test StatisticsTracker basic functionality."""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    
    print("=" * 60)
    print("Testing StatisticsTracker Component")
    print("=" * 60)
    
    # Initialize StatisticsTracker
    tracker = StatisticsTracker(db_url)
    
    # Test 1: Connect
    print("\n[Test 1] Testing connect()...")
    try:
        tracker.connect()
        print("✓ Connection established successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # Test 2: Record cycle start
    print("\n[Test 2] Testing record_cycle_start()...")
    try:
        cycle_id_1 = tracker.record_cycle_start()
        print(f"✓ Cycle started with ID: {cycle_id_1}")
        
        cycle_id_2 = tracker.record_cycle_start()
        print(f"✓ Second cycle started with ID: {cycle_id_2}")
        
        # Verify IDs are unique
        assert cycle_id_1 != cycle_id_2, "Cycle IDs should be unique"
        print("✓ Cycle IDs are unique")
        
    except Exception as e:
        print(f"✗ Recording cycle start failed: {e}")
        tracker.close()
        return
    
    # Test 3: Record cycle end
    print("\n[Test 3] Testing record_cycle_end()...")
    try:
        # Complete first cycle successfully
        tracker.record_cycle_end(cycle_id_1, success=True, duration=12.5)
        print("✓ First cycle completed successfully (12.5s)")
        
        # Complete second cycle with failure
        tracker.record_cycle_end(cycle_id_2, success=False, duration=8.3)
        print("✓ Second cycle completed with failure (8.3s)")
        
        # Verify counters updated
        assert tracker.total_cycles == 2, "Total cycles should be 2"
        assert tracker.successful_cycles == 1, "Successful cycles should be 1"
        print("✓ Cycle counters updated correctly")
        
    except Exception as e:
        print(f"✗ Recording cycle end failed: {e}")
        tracker.close()
        return
    
    # Test 4: Get statistics
    print("\n[Test 4] Testing get_statistics()...")
    try:
        stats = tracker.get_statistics()
        print("✓ Statistics retrieved successfully")
        print(f"\n  Statistics Summary:")
        print(f"  - Uptime: {stats['uptime_seconds']} seconds")
        print(f"  - Total Cycles: {stats['total_cycles']}")
        print(f"  - Successful Cycles: {stats['successful_cycles']}")
        print(f"  - Failed Cycles: {stats['failed_cycles']}")
        print(f"  - Success Rate: {stats['success_rate']}%")
        print(f"  - Average Cycle Duration: {stats['average_cycle_duration']}s")
        print(f"  - Last Cycle Duration: {stats['last_cycle_duration']}s")
        print(f"  - Assets Tracked: {stats['assets_tracked']}")
        
        # Verify calculations
        assert stats['total_cycles'] == 2, "Total cycles should be 2"
        assert stats['successful_cycles'] == 1, "Successful cycles should be 1"
        assert stats['failed_cycles'] == 1, "Failed cycles should be 1"
        assert stats['success_rate'] == 50.0, "Success rate should be 50%"
        
        # Average should be (12.5 + 8.3) / 2 = 10.4
        expected_avg = round((12.5 + 8.3) / 2, 2)
        assert stats['average_cycle_duration'] == expected_avg, f"Average should be {expected_avg}"
        
        # Last duration should be 8.3
        assert stats['last_cycle_duration'] == 8.3, "Last duration should be 8.3"
        
        print("✓ All calculations are correct")
        
    except Exception as e:
        print(f"✗ Getting statistics failed: {e}")
        tracker.close()
        return
    
    # Test 5: Rolling average with more than 100 cycles
    print("\n[Test 5] Testing rolling average calculation...")
    try:
        # Add 100 more cycles to test rolling window
        for i in range(100):
            cycle_id = tracker.record_cycle_start()
            tracker.record_cycle_end(cycle_id, success=True, duration=10.0)
        
        stats = tracker.get_statistics()
        print(f"✓ Added 100 more cycles")
        print(f"  - Total Cycles: {stats['total_cycles']}")
        print(f"  - Cycle durations tracked: {len(tracker.cycle_durations)}")
        
        # Should only track last 100 durations
        assert len(tracker.cycle_durations) == 100, "Should only track last 100 durations"
        print("✓ Rolling window correctly maintains last 100 durations")
        
        # Average should be close to 10.0 now (since we added 100 cycles of 10.0s)
        assert 9.9 <= stats['average_cycle_duration'] <= 10.1, "Average should be ~10.0"
        print(f"✓ Rolling average calculated correctly: {stats['average_cycle_duration']}s")
        
    except Exception as e:
        print(f"✗ Rolling average test failed: {e}")
        tracker.close()
        return
    
    # Test 6: Persist statistics
    print("\n[Test 6] Testing persist_statistics()...")
    try:
        tracker.persist_statistics()
        print("✓ Statistics persisted to database")
        
        # Verify by querying the database
        cursor = tracker.conn.cursor()
        cursor.execute(
            "SELECT * FROM fetcher_statistics ORDER BY timestamp DESC LIMIT 1"
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f"✓ Statistics record found in database")
            print(f"  - Record ID: {result[0]}")
            print(f"  - Total Cycles: {result[3]}")
            print(f"  - Success Rate: {result[6]}%")
        else:
            print("✗ No statistics record found in database")
        
    except Exception as e:
        print(f"✗ Persisting statistics failed: {e}")
        tracker.close()
        return
    
    # Test 7: Error handling - invalid cycle_id
    print("\n[Test 7] Testing error handling...")
    try:
        # Try to end a cycle that was never started
        try:
            tracker.record_cycle_end("invalid-cycle-id", success=True, duration=5.0)
            print("✗ Should have raised ValueError for invalid cycle_id")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        tracker.close()
        return
    
    # Test 8: Close connection
    print("\n[Test 8] Testing close()...")
    try:
        tracker.close()
        print("✓ Connection closed successfully")
    except Exception as e:
        print(f"✗ Closing connection failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_statistics_tracker()
