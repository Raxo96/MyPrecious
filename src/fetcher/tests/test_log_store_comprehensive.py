#!/usr/bin/env python3
"""
Comprehensive test for LogStore component.
Validates all requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from log_store import LogStore


def test_requirement_4_1_4_2_4_3():
    """
    Test Requirements 4.1, 4.2, 4.3:
    - Log entries written to database
    - Persisted to PostgreSQL
    - Include timestamp, level, message, and context
    """
    print("\n" + "=" * 60)
    print("Testing Requirements 4.1, 4.2, 4.3")
    print("Log Entry Persistence with Complete Fields")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    log_store = LogStore(db_url)
    log_store.connect()
    
    # Write a log entry with all fields
    test_context = {
        "operation": "price_update",
        "asset_count": 25,
        "duration_seconds": 12.5
    }
    
    log_store.log("INFO", "Test log for requirements validation", test_context)
    
    # Retrieve and verify
    logs = log_store.get_recent_logs(limit=1)
    assert len(logs) > 0, "No logs retrieved"
    
    latest = logs[0]
    print(f"\n✓ Log entry persisted to PostgreSQL")
    print(f"  - Has timestamp: {latest['timestamp'] is not None}")
    print(f"  - Has level: {latest['level'] == 'INFO'}")
    print(f"  - Has message: {latest['message'] == 'Test log for requirements validation'}")
    print(f"  - Has context: {latest['context'] == test_context}")
    
    assert latest['timestamp'] is not None, "Missing timestamp"
    assert latest['level'] == 'INFO', "Incorrect level"
    assert latest['message'] == 'Test log for requirements validation', "Incorrect message"
    assert latest['context'] == test_context, "Incorrect context"
    
    log_store.close()
    print("\n✓ Requirements 4.1, 4.2, 4.3 validated successfully")


def test_requirement_4_4():
    """
    Test Requirement 4.4:
    - Log entries retained for at least 30 days
    """
    print("\n" + "=" * 60)
    print("Testing Requirement 4.4")
    print("Log Retention for 30 Days")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    log_store = LogStore(db_url)
    log_store.connect()
    
    # Create a test log
    log_store.log("INFO", "Test log for 30-day retention")
    
    # Verify it exists
    logs_before = log_store.get_recent_logs(limit=1)
    assert len(logs_before) > 0, "Log not created"
    
    # Try to purge with 30-day retention (should not delete recent logs)
    deleted = log_store.purge_old_logs(days=30)
    
    # Verify log still exists
    logs_after = log_store.get_recent_logs(limit=1)
    assert len(logs_after) > 0, "Log was incorrectly deleted"
    
    print(f"\n✓ Recent logs retained (not deleted by 30-day purge)")
    print(f"  - Logs before purge: {len(logs_before)}")
    print(f"  - Logs deleted: {deleted}")
    print(f"  - Logs after purge: {len(logs_after)}")
    
    log_store.close()
    print("\n✓ Requirement 4.4 validated successfully")


def test_requirement_4_5():
    """
    Test Requirement 4.5:
    - Logs older than 30 days automatically purged
    """
    print("\n" + "=" * 60)
    print("Testing Requirement 4.5")
    print("Automatic Purge of Old Logs")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    log_store = LogStore(db_url)
    log_store.connect()
    
    # Manually insert an old log entry (simulate 31 days old)
    cursor = log_store.conn.cursor()
    old_timestamp = datetime.now() - timedelta(days=31)
    cursor.execute(
        """
        INSERT INTO fetcher_logs (timestamp, level, message, context)
        VALUES (%s, 'INFO', 'Old test log for purge test', NULL)
        RETURNING id
        """,
        (old_timestamp,)
    )
    old_log_id = cursor.fetchone()[0]
    log_store.conn.commit()
    cursor.close()
    
    print(f"\n✓ Created test log with timestamp 31 days ago (ID: {old_log_id})")
    
    # Purge logs older than 30 days
    deleted = log_store.purge_old_logs(days=30)
    
    print(f"✓ Purge executed: {deleted} logs deleted")
    assert deleted >= 1, "Old log was not deleted"
    
    # Verify the old log is gone
    cursor = log_store.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fetcher_logs WHERE id = %s", (old_log_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    
    assert count == 0, "Old log still exists after purge"
    print(f"✓ Old log (ID: {old_log_id}) successfully purged")
    
    log_store.close()
    print("\n✓ Requirement 4.5 validated successfully")


def test_pagination():
    """Test pagination functionality (Requirement 3.4 related)."""
    print("\n" + "=" * 60)
    print("Testing Pagination Functionality")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    log_store = LogStore(db_url)
    log_store.connect()
    
    # Create multiple log entries
    for i in range(10):
        log_store.log("INFO", f"Pagination test log {i}")
    
    # Test pagination
    page1 = log_store.get_recent_logs(limit=3, offset=0)
    page2 = log_store.get_recent_logs(limit=3, offset=3)
    page3 = log_store.get_recent_logs(limit=3, offset=6)
    
    print(f"\n✓ Page 1 (limit=3, offset=0): {len(page1)} logs")
    print(f"✓ Page 2 (limit=3, offset=3): {len(page2)} logs")
    print(f"✓ Page 3 (limit=3, offset=6): {len(page3)} logs")
    
    # Verify no overlap
    page1_ids = {log['id'] for log in page1}
    page2_ids = {log['id'] for log in page2}
    page3_ids = {log['id'] for log in page3}
    
    assert len(page1_ids & page2_ids) == 0, "Page 1 and 2 have overlapping logs"
    assert len(page2_ids & page3_ids) == 0, "Page 2 and 3 have overlapping logs"
    
    print(f"✓ No overlapping logs between pages")
    
    log_store.close()
    print("\n✓ Pagination validated successfully")


def test_level_filtering():
    """Test log level filtering."""
    print("\n" + "=" * 60)
    print("Testing Log Level Filtering")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    log_store = LogStore(db_url)
    log_store.connect()
    
    # Create logs with different levels
    log_store.log("DEBUG", "Debug message")
    log_store.log("INFO", "Info message")
    log_store.log("WARNING", "Warning message")
    log_store.log("ERROR", "Error message")
    log_store.log("CRITICAL", "Critical message")
    
    # Test filtering
    error_logs = log_store.get_recent_logs(limit=100, level="ERROR")
    warning_logs = log_store.get_recent_logs(limit=100, level="WARNING")
    
    print(f"\n✓ ERROR logs: {len(error_logs)}")
    print(f"✓ WARNING logs: {len(warning_logs)}")
    
    # Verify all returned logs have correct level
    for log in error_logs:
        assert log['level'] == 'ERROR', f"Found non-ERROR log: {log['level']}"
    
    for log in warning_logs:
        assert log['level'] == 'WARNING', f"Found non-WARNING log: {log['level']}"
    
    print(f"✓ All filtered logs have correct level")
    
    log_store.close()
    print("\n✓ Level filtering validated successfully")


def main():
    """Run all comprehensive tests."""
    print("\n" + "=" * 70)
    print(" COMPREHENSIVE LOGSTORE VALIDATION")
    print("=" * 70)
    
    try:
        test_requirement_4_1_4_2_4_3()
        test_requirement_4_4()
        test_requirement_4_5()
        test_pagination()
        test_level_filtering()
        
        print("\n" + "=" * 70)
        print(" ALL REQUIREMENTS VALIDATED SUCCESSFULLY!")
        print("=" * 70)
        print("\nValidated Requirements:")
        print("  ✓ 4.1 - Log entries written to database")
        print("  ✓ 4.2 - Logs persisted to PostgreSQL")
        print("  ✓ 4.3 - Logs include timestamp, level, message, context")
        print("  ✓ 4.4 - Logs retained for at least 30 days")
        print("  ✓ 4.5 - Logs older than 30 days automatically purged")
        print("  ✓ 3.4 - Pagination support (related)")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
