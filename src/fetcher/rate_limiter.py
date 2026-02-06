"""
Rate limiter for API requests to prevent throttling.

This module implements rate limiting to respect API quotas and prevent
the application from being blocked by data providers.
"""

import time
import logging
from typing import List
from log_store import log_with_context

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Manages API rate limiting to prevent throttling.
    
    Enforces:
    - Minimum delay between consecutive requests
    - Maximum requests per hour limit
    - Exponential backoff on rate limit errors
    """
    
    def __init__(self, min_delay_seconds: float = 1.0, hourly_limit: int = 1800):
        """
        Initialize the rate limiter.
        
        Args:
            min_delay_seconds: Minimum delay between requests (default 1.0)
            hourly_limit: Maximum requests per hour (default 1800)
        """
        self.min_delay_seconds = min_delay_seconds
        self.hourly_limit = hourly_limit
        self.last_request_time: float = 0.0
        self.request_timestamps: List[float] = []
        
        logger.info(
            f"RateLimiter initialized: min_delay={min_delay_seconds}s, "
            f"hourly_limit={hourly_limit}"
        )
    
    def wait_if_needed(self):
        """
        Block execution if rate limit would be exceeded.
        
        Enforces:
        1. Minimum delay between consecutive requests
        2. Hourly request limit (pauses for 60 minutes if exceeded)
        """
        current_time = time.time()
        
        # Enforce minimum delay between requests
        if self.last_request_time > 0:
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_delay_seconds:
                sleep_time = self.min_delay_seconds - time_since_last_request
                logger.debug(f"Enforcing minimum delay: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                current_time = time.time()
        
        # Check hourly limit
        self._cleanup_old_timestamps(current_time)
        
        if len(self.request_timestamps) >= self.hourly_limit:
            # Calculate how long to wait until the oldest request is > 1 hour old
            oldest_timestamp = self.request_timestamps[0]
            time_until_reset = 3600 - (current_time - oldest_timestamp)
            
            if time_until_reset > 0:
                log_with_context(
                    logger, logging.WARNING,
                    f"Hourly limit of {self.hourly_limit} requests reached. "
                    f"Pausing for {time_until_reset:.0f} seconds.",
                    operation="rate_limit_pause",
                    hourly_limit=self.hourly_limit,
                    pause_seconds=time_until_reset,
                    current_count=len(self.request_timestamps)
                )
                time.sleep(time_until_reset)
                current_time = time.time()
                self._cleanup_old_timestamps(current_time)
    
    def record_request(self):
        """
        Record that a request was made.
        
        Updates internal counters for rate limiting.
        Should be called immediately after making an API request.
        """
        current_time = time.time()
        self.last_request_time = current_time
        self.request_timestamps.append(current_time)
        
        # Clean up old timestamps to prevent unbounded growth
        self._cleanup_old_timestamps(current_time)
        
        logger.debug(
            f"Request recorded. Hourly count: {len(self.request_timestamps)}/{self.hourly_limit}"
        )
    
    def handle_rate_limit_error(self, attempt: int) -> int:
        """
        Handle HTTP 429 rate limit error with exponential backoff.
        
        Backoff sequence: 5, 10, 20, 40, 80 seconds for attempts 1-5.
        
        Args:
            attempt: Current retry attempt number (1-based)
            
        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: 5 * 2^(attempt-1)
        # attempt 1: 5s, attempt 2: 10s, attempt 3: 20s, attempt 4: 40s, attempt 5: 80s
        delay = 5 * (2 ** (attempt - 1))
        
        log_with_context(
            logger, logging.WARNING,
            f"Rate limit error encountered (attempt {attempt}). "
            f"Backing off for {delay} seconds.",
            operation="rate_limit_backoff",
            attempt=attempt,
            delay_seconds=delay
        )
        
        time.sleep(delay)
        return delay
    
    def get_hourly_count(self) -> int:
        """
        Get number of requests made in the current hour.
        
        Returns:
            Request count for the current hour
        """
        current_time = time.time()
        self._cleanup_old_timestamps(current_time)
        return len(self.request_timestamps)
    
    def _cleanup_old_timestamps(self, current_time: float):
        """
        Remove timestamps older than 1 hour.
        
        Args:
            current_time: Current timestamp to compare against
        """
        # Remove timestamps older than 1 hour (3600 seconds)
        cutoff_time = current_time - 3600
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > cutoff_time
        ]
