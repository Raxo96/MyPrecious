#!/usr/bin/env python3
"""
Quick test script for RateLimiter component.
Tests basic functionality without long delays.
"""
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from rate_limiter import RateLimiter


def test_rate_limiter_quick():
    """Test RateLimiter basic functionality (quick version)."""
    
    print("=" * 60)
    print("Testing RateLimiter Component (Quick Tests)")
    print("=" * 60)
    
    # Test 1: Initialization
    print("\n[Test 1] Testing initialization...")
    try:
        limiter = RateLimiter(min_delay_seconds=1.0, hourly_limit=1800)
        print(f"✓ RateLimiter initialized with min_delay=1.0s, hourly_limit=1800")
        assert limiter.min_delay_seconds == 1.0
        assert limiter.hourly_limit == 1800
        assert limiter.last_request_time == 0.0
        assert len(limiter.request_timestamps) == 0
        print("✓ All attributes initialized correctly")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    # Test 2: Minimum delay enforcement
    print("\n[Test 2] Testing minimum delay enforcement...")
    try:
        limiter = RateLimiter(min_delay_seconds=0.2, hourly_limit=1800)
        
        # First request - should not wait
        start_time = time.time()
        limiter.wait_if_needed()
        limiter.record_request()
        first_request_time = time.time() - start_time
        print(f"✓ First request completed in {first_request_time:.3f}s (no delay expected)")
        
        # Second request - should wait ~0.2 seconds
        start_time = time.time()
        limiter.wait_if_needed()
        limiter.record_request()
        second_request_time = time.time() - start_time
        print(f"✓ Second request completed in {second_request_time:.3f}s")
        
        # Verify delay was enforced (allow some tolerance for execution time)
        assert second_request_time >= 0.15, f"Expected delay >= 0.15s, got {second_request_time:.3f}s"
        print(f"✓ Minimum delay of 0.2s was enforced")
        
    except Exception as e:
        print(f"✗ Minimum delay test failed: {e}")
        return False
    
    # Test 3: Request counter accuracy
    print("\n[Test 3] Testing request counter accuracy...")
    try:
        limiter = RateLimiter(min_delay_seconds=0.01, hourly_limit=1800)
        
        # Make 10 requests
        for i in range(10):
            limiter.wait_if_needed()
            limiter.record_request()
        
        count = limiter.get_hourly_count()
        print(f"✓ Made 10 requests, counter shows: {count}")
        assert count == 10, f"Expected count=10, got {count}"
        print("✓ Request counter is accurate")
        
    except Exception as e:
        print(f"✗ Request counter test failed: {e}")
        return False
    
    # Test 4: Exponential backoff calculation (without actual sleep)
    print("\n[Test 4] Testing exponential backoff calculation...")
    try:
        limiter = RateLimiter(min_delay_seconds=1.0, hourly_limit=1800)
        
        expected_delays = [5, 10, 20, 40, 80]
        
        # Test the calculation without actually sleeping
        # We'll monkey-patch time.sleep to avoid waiting
        original_sleep = time.sleep
        sleep_durations = []
        
        def mock_sleep(duration):
            sleep_durations.append(duration)
        
        time.sleep = mock_sleep
        
        try:
            for attempt, expected_delay in enumerate(expected_delays, start=1):
                actual_delay = limiter.handle_rate_limit_error(attempt)
                print(f"  Attempt {attempt}: expected={expected_delay}s, returned={actual_delay}s")
                assert actual_delay == expected_delay, f"Expected {expected_delay}s, got {actual_delay}s"
        finally:
            time.sleep = original_sleep
        
        # Verify all sleeps were called with correct durations
        assert sleep_durations == expected_delays, f"Expected {expected_delays}, got {sleep_durations}"
        print("✓ Exponential backoff sequence is correct: 5, 10, 20, 40, 80 seconds")
        
    except Exception as e:
        print(f"✗ Exponential backoff test failed: {e}")
        return False
    
    # Test 5: Timestamp cleanup
    print("\n[Test 5] Testing timestamp cleanup...")
    try:
        limiter = RateLimiter(min_delay_seconds=0.01, hourly_limit=1800)
        
        # Add some old timestamps manually
        current_time = time.time()
        limiter.request_timestamps = [
            current_time - 7200,  # 2 hours ago (should be removed)
            current_time - 3700,  # 1 hour 1 minute ago (should be removed)
            current_time - 1800,  # 30 minutes ago (should be kept)
            current_time - 60,    # 1 minute ago (should be kept)
        ]
        
        # Trigger cleanup
        limiter._cleanup_old_timestamps(current_time)
        
        print(f"✓ After cleanup: {len(limiter.request_timestamps)} timestamps remain")
        assert len(limiter.request_timestamps) == 2, f"Expected 2 timestamps, got {len(limiter.request_timestamps)}"
        print("✓ Old timestamps (>1 hour) were correctly removed")
        
    except Exception as e:
        print(f"✗ Timestamp cleanup test failed: {e}")
        return False
    
    # Test 6: get_hourly_count method
    print("\n[Test 6] Testing get_hourly_count()...")
    try:
        limiter = RateLimiter(min_delay_seconds=0.01, hourly_limit=1800)
        
        # Initially should be 0
        assert limiter.get_hourly_count() == 0, "Initial count should be 0"
        print("✓ Initial hourly count is 0")
        
        # Add some requests
        for i in range(5):
            limiter.record_request()
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        count = limiter.get_hourly_count()
        assert count == 5, f"Expected count=5, got {count}"
        print(f"✓ After 5 requests, hourly count is {count}")
        
    except Exception as e:
        print(f"✗ get_hourly_count test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_rate_limiter_quick()
    sys.exit(0 if success else 1)
