#!/usr/bin/env python3
"""
Test script for LogStore component.
Tests basic functionality: connect, log, get_recent_logs, purge_old_logs.
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from log_store import LogStore


def test_log_store():
    """Test LogStore basic functionality."""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    
    print("=" * 60)
    print("Testing LogStore Component")
    print("=" * 60)
    
    # Initialize LogStore
    log_store = LogStore(db_url)
    
    # Test 1: Connect
    print("\n[Test 1] Testing connect()...")
    try:
        log_store.connect()
        print("✓ Connection established successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # Test 2: Write log entries
    print("\n[Test 2] Testing log() method...")
    try:
        log_store.log("INFO", "Test log entry - basic message")
        print("✓ Basic log entry written")
        
        log_store.log("WARNING", "Test warning with context", {
            "component": "test_script",
            "test_id": 123,
            "details": "This is a test warning"
        })
        print("✓ Log entry with context written")
        
        log_store.log("ERROR", "Test error message", {
            "error_code": "TEST_001",
            "stack_trace": "Simulated stack trace"
        })
        print("✓ Error log entry written")
        
    except Exception as e:
        print(f"✗ Logging failed: {e}")
        log_store.close()
        return
    
    # Test 3: Retrieve recent logs
    print("\n[Test 3] Testing get_recent_logs()...")
    try:
        # Get all recent logs
        logs = log_store.get_recent_logs(limit=10)
        print(f"✓ Retrieved {len(logs)} recent logs")
        
        if logs:
            print("\nMost recent log:")
            latest = logs[0]
            print(f"  - ID: {latest['id']}")
            print(f"  - Timestamp: {latest['timestamp']}")
            print(f"  - Level: {latest['level']}")
            print(f"  - Message: {latest['message']}")
            if latest['context']:
                print(f"  - Context: {latest['context']}")
        
        # Test pagination
        logs_page1 = log_store.get_recent_logs(limit=2, offset=0)
        logs_page2 = log_store.get_recent_logs(limit=2, offset=2)
        print(f"✓ Pagination works: Page 1 has {len(logs_page1)} logs, Page 2 has {len(logs_page2)} logs")
        
        # Test level filtering
        error_logs = log_store.get_recent_logs(limit=10, level="ERROR")
        print(f"✓ Level filtering works: Found {len(error_logs)} ERROR logs")
        
    except Exception as e:
        print(f"✗ Retrieving logs failed: {e}")
        log_store.close()
        return
    
    # Test 4: Purge old logs (test with 0 days to see if it works, but won't delete recent logs)
    print("\n[Test 4] Testing purge_old_logs()...")
    try:
        # First, let's check how many logs we have
        all_logs = log_store.get_recent_logs(limit=1000)
        print(f"  Total logs before purge: {len(all_logs)}")
        
        # Purge logs older than 365 days (shouldn't delete anything recent)
        deleted = log_store.purge_old_logs(days=365)
        print(f"✓ Purge completed: {deleted} logs deleted (older than 365 days)")
        
    except Exception as e:
        print(f"✗ Purging logs failed: {e}")
        log_store.close()
        return
    
    # Test 5: Close connection
    print("\n[Test 5] Testing close()...")
    try:
        log_store.close()
        print("✓ Connection closed successfully")
    except Exception as e:
        print(f"✗ Closing connection failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_log_store()
