"""
Data models for the historical data backfill system.

This module defines the core data structures used throughout the backfill
process for tracking tasks, results, and reports.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional


@dataclass
class BackfillTask:
    """
    Represents a backfill task from the queue.
    
    Tracks the state of a single asset's historical data backfill operation,
    including retry logic and scheduling information.
    
    Attributes:
        id: Unique identifier for the task
        asset_id: Foreign key to assets table (None if asset not yet created)
        symbol: Stock ticker symbol (e.g., 'AAPL')
        start_date: Beginning of historical data range
        end_date: End of historical data range
        status: Current task status (pending, in_progress, completed, failed, rate_limited)
        attempts: Number of processing attempts made
        retry_after: Timestamp when task should be retried (for rate-limited tasks)
    """
    id: int
    asset_id: Optional[int]
    symbol: str
    start_date: date
    end_date: date
    status: str
    attempts: int
    retry_after: Optional[datetime]


@dataclass
class ProcessingResult:
    """
    Result of processing a single symbol.
    
    Contains statistics and outcome information for a completed backfill
    operation on one asset.
    
    Attributes:
        symbol: Stock ticker symbol that was processed
        success: Whether the processing completed successfully
        records_inserted: Number of price records inserted into database
        records_skipped: Number of duplicate/invalid records skipped
        completeness_pct: Data completeness percentage (0-100)
        duration_seconds: Time taken to process this symbol
        error_message: Error details if processing failed (None if successful)
    """
    symbol: str
    success: bool
    records_inserted: int
    records_skipped: int
    completeness_pct: float
    duration_seconds: float
    error_message: Optional[str]


@dataclass
class BackfillReport:
    """
    Summary report of backfill operation.
    
    Provides aggregate statistics for an entire backfill run across
    multiple assets.
    
    Attributes:
        total_symbols: Total number of symbols processed
        successful: Number of successfully completed symbols
        failed: Number of failed symbols
        total_records_inserted: Total price records inserted across all symbols
        total_duration_seconds: Total time taken for entire backfill operation
        start_time: When the backfill operation started
        end_time: When the backfill operation completed
        failed_symbols: List of symbols that failed processing
    """
    total_symbols: int
    successful: int
    failed: int
    total_records_inserted: int
    total_duration_seconds: float
    start_time: datetime
    end_time: datetime
    failed_symbols: List[str]
