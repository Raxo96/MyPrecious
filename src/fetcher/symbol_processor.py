"""
Symbol processor for historical data backfill.

This module implements the SymbolProcessor class which orchestrates the
fetching, validation, and storage of historical price data for a single
stock symbol.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional
import psycopg2
import requests

from fetcher import StockFetcher, AssetData
from db_loader import DatabaseLoader
from rate_limiter import RateLimiter
from data_validator import DataValidator, ValidationResult
from backfill_models import BackfillTask, ProcessingResult
from log_store import log_with_context

logger = logging.getLogger(__name__)


class SymbolProcessor:
    """
    Processes backfill for a single stock symbol.
    
    Orchestrates the complete workflow for fetching and storing historical
    price data for one asset, including:
    - Rate limiting
    - Data fetching
    - Data validation
    - Database storage
    - Error handling
    - Progress tracking
    """
    
    def __init__(
        self,
        fetcher: StockFetcher,
        db_loader: DatabaseLoader,
        rate_limiter: RateLimiter,
        validator: DataValidator
    ):
        """
        Initialize the symbol processor.
        
        Args:
            fetcher: StockFetcher instance for retrieving price data
            db_loader: DatabaseLoader instance for storing data
            rate_limiter: RateLimiter instance for API throttling
            validator: DataValidator instance for data quality checks
        """
        self.fetcher = fetcher
        self.db_loader = db_loader
        self.rate_limiter = rate_limiter
        self.validator = validator
        
        logger.info("SymbolProcessor initialized")
    
    def process(self, task: BackfillTask) -> ProcessingResult:
        """
        Process a single backfill task.
        
        This method orchestrates the complete workflow:
        1. Update queue status to 'in_progress'
        2. Enforce rate limiting
        3. Fetch historical data from API
        4. Validate data quality
        5. Store valid records in database
        6. Update tracked_assets metadata
        7. Update queue status to 'completed' or 'failed'
        8. Return processing statistics
        
        Handles all error types:
        - Network errors (connection failures, timeouts)
        - Rate limit errors (HTTP 429)
        - Validation errors (invalid data)
        - Database errors (connection failures, constraint violations)
        
        Args:
            task: BackfillTask containing symbol and date range
            
        Returns:
            ProcessingResult with status and statistics
        """
        start_time = time.time()
        symbol = task.symbol
        
        log_with_context(
            logger, logging.INFO,
            f"Processing backfill for {symbol} ({task.start_date} to {task.end_date})",
            operation="symbol_processing_start",
            symbol=symbol,
            task_id=task.id,
            asset_id=task.asset_id,
            start_date=str(task.start_date),
            end_date=str(task.end_date)
        )
        
        try:
            # Update status to in_progress (Requirement 5.3)
            self.update_queue_status(task.id, 'in_progress')
            
            # Enforce rate limiting (Requirement 4.1)
            self.rate_limiter.wait_if_needed()
            
            # Fetch historical data (Requirement 2.2)
            start_datetime = datetime.combine(task.start_date, datetime.min.time())
            end_datetime = datetime.combine(task.end_date, datetime.max.time())
            
            asset_data = self.fetcher.fetch_historical(
                symbol,
                start_datetime,
                end_datetime
            )
            
            # Record the API request for rate limiting
            self.rate_limiter.record_request()
            
            # Handle case where fetcher returns None (invalid symbol, network error, etc.)
            if asset_data is None:
                error_msg = f"Failed to fetch data for {symbol} - API returned no data"
                log_with_context(
                    logger, logging.ERROR,
                    error_msg,
                    operation="fetch_failed",
                    symbol=symbol,
                    task_id=task.id,
                    error_type="NoDataReturned"
                )
                
                # Calculate exponential backoff delay for retry (Requirement 5.7, 5.8)
                attempt = task.attempts + 1
                delay = self._calculate_backoff_delay(attempt)
                retry_after = datetime.now() + timedelta(seconds=delay)
                
                self.update_queue_status(task.id, 'failed', error_msg)
                self._update_retry_after(task.id, retry_after)
                
                logger.info(
                    f"Task {task.id} for {symbol} will retry after {delay}s (attempt {attempt}/5)"
                )
                
                duration = time.time() - start_time
                return ProcessingResult(
                    symbol=symbol,
                    success=False,
                    records_inserted=0,
                    records_skipped=0,
                    completeness_pct=0.0,
                    duration_seconds=duration,
                    error_message=error_msg
                )
            
            # Validate and filter price records (Requirements 2.3, 8.1-8.5)
            valid_prices = []
            invalid_count = 0
            
            for price in asset_data.prices:
                validation_result = self.validator.validate_price_record(price)
                
                if validation_result.valid:
                    valid_prices.append(price)
                else:
                    # Log validation errors and skip invalid records (Requirement 8.5)
                    invalid_count += 1
                    log_with_context(
                        logger, logging.WARNING,
                        f"Validation failed for {symbol} at {price.timestamp}: "
                        f"{', '.join(validation_result.errors)}",
                        operation="validation_failed",
                        symbol=symbol,
                        task_id=task.id,
                        timestamp=price.timestamp,
                        errors=validation_result.errors
                    )
            
            # Update asset_data with only valid prices
            asset_data.prices = valid_prices
            
            # Store data in database (Requirements 3.2, 3.4)
            if valid_prices:
                try:
                    records_inserted = self.db_loader.load_asset_prices(asset_data)
                    records_skipped = len(valid_prices) - records_inserted
                    
                    # Update tracked_assets timestamp (Requirement 3.6)
                    self.db_loader.update_tracked_asset_timestamp(symbol)
                    
                    log_with_context(
                        logger, logging.INFO,
                        f"Stored {records_inserted} records for {symbol} "
                        f"({records_skipped} duplicates skipped, {invalid_count} invalid)",
                        operation="storage_complete",
                        symbol=symbol,
                        task_id=task.id,
                        records_inserted=records_inserted,
                        records_skipped=records_skipped,
                        invalid_count=invalid_count
                    )
                except psycopg2.Error as e:
                    # Database error - mark as failed for retry
                    error_msg = f"Database error storing {symbol}: {str(e)}"
                    log_with_context(
                        logger, logging.ERROR,
                        error_msg,
                        operation="database_error",
                        symbol=symbol,
                        task_id=task.id,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        exc_info=True
                    )
                    
                    # Calculate exponential backoff delay for retry (Requirement 5.7, 5.8)
                    attempt = task.attempts + 1
                    delay = self._calculate_backoff_delay(attempt)
                    retry_after = datetime.now() + timedelta(seconds=delay)
                    
                    self.update_queue_status(task.id, 'failed', error_msg)
                    self._update_retry_after(task.id, retry_after)
                    
                    logger.info(
                        f"Task {task.id} for {symbol} will retry after {delay}s (attempt {attempt}/5)"
                    )
                    
                    duration = time.time() - start_time
                    return ProcessingResult(
                        symbol=symbol,
                        success=False,
                        records_inserted=0,
                        records_skipped=0,
                        completeness_pct=0.0,
                        duration_seconds=duration,
                        error_message=error_msg
                    )
            else:
                records_inserted = 0
                records_skipped = 0
                logger.warning(f"No valid records to store for {symbol}")
            
            # Calculate completeness (Requirement 8.6)
            # Expected trading days is approximately 252 per year (365 calendar days)
            # For 365 days, expect ~252 trading days
            days_requested = (task.end_date - task.start_date).days
            expected_trading_days = int(days_requested * 252 / 365)
            completeness_pct = self.validator.calculate_completeness(
                expected_trading_days,
                len(valid_prices)
            )
            
            log_with_context(
                logger, logging.INFO,
                f"Data completeness for {symbol}: {completeness_pct:.1f}% "
                f"({len(valid_prices)}/{expected_trading_days} expected trading days)",
                operation="completeness_calculated",
                symbol=symbol,
                task_id=task.id,
                completeness_pct=completeness_pct,
                actual_records=len(valid_prices),
                expected_records=expected_trading_days
            )
            
            # Update status to completed (Requirement 5.4)
            self.update_queue_status(task.id, 'completed')
            
            duration = time.time() - start_time
            
            log_with_context(
                logger, logging.INFO,
                f"Successfully completed backfill for {symbol} in {duration:.2f}s",
                operation="symbol_processing_complete",
                symbol=symbol,
                task_id=task.id,
                duration_seconds=duration,
                records_inserted=records_inserted,
                completeness_pct=completeness_pct
            )
            
            return ProcessingResult(
                symbol=symbol,
                success=True,
                records_inserted=records_inserted,
                records_skipped=records_skipped + invalid_count,
                completeness_pct=completeness_pct,
                duration_seconds=duration,
                error_message=None
            )
            
        except requests.exceptions.Timeout as e:
            # Network timeout error (Requirement 2.5)
            error_msg = f"Timeout fetching {symbol}: {str(e)}"
            log_with_context(
                logger, logging.ERROR,
                error_msg,
                operation="timeout_error",
                symbol=symbol,
                task_id=task.id,
                error_type="Timeout",
                error_message=str(e)
            )
            
            # Calculate exponential backoff delay for retry (Requirement 5.7, 5.8)
            attempt = task.attempts + 1
            delay = self._calculate_backoff_delay(attempt)
            retry_after = datetime.now() + timedelta(seconds=delay)
            
            self.update_queue_status(task.id, 'failed', error_msg)
            self._update_retry_after(task.id, retry_after)
            
            logger.info(
                f"Task {task.id} for {symbol} will retry after {delay}s (attempt {attempt}/5)"
            )
            
            duration = time.time() - start_time
            return ProcessingResult(
                symbol=symbol,
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=duration,
                error_message=error_msg
            )
            
        except requests.exceptions.RequestException as e:
            # Network error (connection failure, etc.) (Requirement 2.5)
            error_msg = f"Network error fetching {symbol}: {str(e)}"
            log_with_context(
                logger, logging.ERROR,
                error_msg,
                operation="network_error",
                symbol=symbol,
                task_id=task.id,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            # Check if it's a rate limit error (HTTP 429)
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 429:
                    # Rate limit error - use exponential backoff (Requirement 4.2)
                    attempt = task.attempts + 1
                    delay = self.rate_limiter.handle_rate_limit_error(attempt)
                    
                    # Calculate retry_after timestamp
                    retry_after = datetime.now() + timedelta(seconds=delay)
                    
                    # Update status to rate_limited (Requirement 5.6)
                    self.update_queue_status(
                        task.id,
                        'rate_limited',
                        f"Rate limited, retry after {delay}s"
                    )
                    
                    # Update retry_after in database
                    self._update_retry_after(task.id, retry_after)
                    
                    duration = time.time() - start_time
                    return ProcessingResult(
                        symbol=symbol,
                        success=False,
                        records_inserted=0,
                        records_skipped=0,
                        completeness_pct=0.0,
                        duration_seconds=duration,
                        error_message=f"Rate limited (attempt {attempt})"
                    )
            
            # Other network error - mark as failed for retry
            # Calculate exponential backoff delay for retry (Requirement 5.7, 5.8)
            attempt = task.attempts + 1
            delay = self._calculate_backoff_delay(attempt)
            retry_after = datetime.now() + timedelta(seconds=delay)
            
            self.update_queue_status(task.id, 'failed', error_msg)
            self._update_retry_after(task.id, retry_after)
            
            logger.info(
                f"Task {task.id} for {symbol} will retry after {delay}s (attempt {attempt}/5)"
            )
            
            duration = time.time() - start_time
            return ProcessingResult(
                symbol=symbol,
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=duration,
                error_message=error_msg
            )
            
        except Exception as e:
            # Unexpected error - log with stack trace (Requirement 7.4)
            error_msg = f"Unexpected error processing {symbol}: {str(e)}"
            log_with_context(
                logger, logging.ERROR,
                error_msg,
                operation="unexpected_error",
                symbol=symbol,
                task_id=task.id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            
            # Calculate exponential backoff delay for retry (Requirement 5.7, 5.8)
            attempt = task.attempts + 1
            delay = self._calculate_backoff_delay(attempt)
            retry_after = datetime.now() + timedelta(seconds=delay)
            
            self.update_queue_status(task.id, 'failed', error_msg)
            self._update_retry_after(task.id, retry_after)
            
            logger.info(
                f"Task {task.id} for {symbol} will retry after {delay}s (attempt {attempt}/5)"
            )
            
            duration = time.time() - start_time
            return ProcessingResult(
                symbol=symbol,
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=duration,
                error_message=error_msg
            )
    
    def update_queue_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Update backfill_queue table with current status.
        
        Updates the status field and related metadata:
        - Sets status to new value
        - Increments attempts counter for failed/rate_limited status
        - Sets completed_at timestamp for completed status
        - Sets error_message for failed status
        - Updates updated_at timestamp
        
        Args:
            task_id: ID of the backfill task
            status: New status (in_progress, completed, failed, rate_limited)
            error_message: Optional error message for failed tasks
        """
        if not self.db_loader.conn:
            logger.error("Cannot update queue status - database not connected")
            return
        
        try:
            cursor = self.db_loader.conn.cursor()
            
            # Build UPDATE query based on status
            if status == 'completed':
                # Set completed_at timestamp (Requirement 5.4)
                cursor.execute(
                    """
                    UPDATE backfill_queue
                    SET status = %s,
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (status, task_id)
                )
            elif status in ('failed', 'rate_limited'):
                # Increment attempts counter (Requirement 5.5, 5.6)
                cursor.execute(
                    """
                    UPDATE backfill_queue
                    SET status = %s,
                        attempts = attempts + 1,
                        error_message = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (status, error_message, task_id)
                )
            else:
                # For in_progress or other statuses
                cursor.execute(
                    """
                    UPDATE backfill_queue
                    SET status = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (status, task_id)
                )
            
            self.db_loader.conn.commit()
            cursor.close()
            
            logger.debug(f"Updated task {task_id} status to '{status}'")
            
        except psycopg2.Error as e:
            logger.error(
                f"Failed to update queue status for task {task_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - this is a non-critical operation
    
    def _update_retry_after(self, task_id: int, retry_after: datetime):
        """
        Update retry_after timestamp in backfill_queue.
        
        Args:
            task_id: ID of the backfill task
            retry_after: Timestamp when task should be retried
        """
        if not self.db_loader.conn:
            logger.error("Cannot update retry_after - database not connected")
            return
        
        try:
            cursor = self.db_loader.conn.cursor()
            cursor.execute(
                """
                UPDATE backfill_queue
                SET retry_after = %s
                WHERE id = %s
                """,
                (retry_after, task_id)
            )
            self.db_loader.conn.commit()
            cursor.close()
            
            logger.debug(f"Updated task {task_id} retry_after to {retry_after}")
            
        except psycopg2.Error as e:
            logger.error(
                f"Failed to update retry_after for task {task_id}: {str(e)}",
                exc_info=True
            )
    
    def _calculate_backoff_delay(self, attempt: int) -> int:
        """
        Calculate exponential backoff delay for retry attempts.
        
        Uses exponential backoff with base delay of 5 seconds:
        - Attempt 1: 5 seconds
        - Attempt 2: 10 seconds
        - Attempt 3: 20 seconds
        - Attempt 4: 40 seconds
        - Attempt 5: 80 seconds
        
        Args:
            attempt: Current retry attempt number (1-based)
            
        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: 5 * 2^(attempt-1)
        # Attempt 1: 5 * 2^0 = 5
        # Attempt 2: 5 * 2^1 = 10
        # Attempt 3: 5 * 2^2 = 20
        # Attempt 4: 5 * 2^3 = 40
        # Attempt 5: 5 * 2^4 = 80
        base_delay = 5
        delay = base_delay * (2 ** (attempt - 1))
        return delay

