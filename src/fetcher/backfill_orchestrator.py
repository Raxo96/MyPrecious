"""
Backfill orchestrator for historical data backfill.

This module implements the BackfillOrchestrator class which coordinates
the entire backfill process for fetching and storing historical price data
for multiple stock symbols.
"""

import json
import logging
import re
import signal
import sys
import psycopg2
from datetime import datetime, date, timedelta
from typing import List, Optional
from pathlib import Path

from fetcher import StockFetcher
from db_loader import DatabaseLoader
from rate_limiter import RateLimiter
from data_validator import DataValidator
from symbol_processor import SymbolProcessor
from backfill_models import BackfillTask, BackfillReport, ProcessingResult
from log_store import log_with_context

logger = logging.getLogger(__name__)


class BackfillOrchestrator:
    """
    Main orchestrator for the historical data backfill process.
    
    Coordinates the entire backfill workflow:
    - Loading S&P 500 symbols from configuration
    - Initializing the backfill queue
    - Processing symbols sequentially
    - Managing rate limiting
    - Generating summary reports
    - Handling resume capability
    """
    
    def __init__(self, db_connection_string: str, config_path: str):
        """
        Initialize the orchestrator.
        
        Args:
            db_connection_string: PostgreSQL connection string
            config_path: Path to S&P 500 symbols configuration file
        """
        self.db_connection_string = db_connection_string
        self.config_path = config_path
        
        # Initialize components
        self.db_loader = DatabaseLoader(db_connection_string)
        self.fetcher = StockFetcher()
        self.rate_limiter = RateLimiter(min_delay_seconds=1.0, hourly_limit=1800)
        self.validator = DataValidator()
        self.symbol_processor = SymbolProcessor(
            self.fetcher,
            self.db_loader,
            self.rate_limiter,
            self.validator
        )
        
        # Statistics tracking
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.processing_results: List[ProcessingResult] = []
        
        # Graceful shutdown flag
        self.shutdown_requested = False
        
        # Register signal handlers for graceful shutdown (Requirement 9.5)
        self._register_signal_handlers()
        
        logger.info(
            f"BackfillOrchestrator initialized with config: {config_path}"
        )
    
    def _register_signal_handlers(self):
        """
        Register signal handlers for graceful shutdown.
        
        Registers handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
        to enable graceful shutdown with progress saving.
        
        Note: SIGTERM is not available on Windows, so we only register it
        on Unix-like systems.
        """
        # Register SIGINT handler (Ctrl+C) - available on all platforms
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        logger.debug("Registered SIGINT handler for graceful shutdown")
        
        # Register SIGTERM handler (kill command) - Unix only
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
            logger.debug("Registered SIGTERM handler for graceful shutdown")
    
    def _handle_shutdown_signal(self, signum, frame):
        """
        Handle shutdown signals (SIGINT, SIGTERM).
        
        Sets the shutdown_requested flag to trigger graceful shutdown.
        The main processing loop will check this flag and exit cleanly.
        
        Args:
            signum: Signal number
            frame: Current stack frame (unused)
        """
        signal_name = signal.Signals(signum).name
        logger.warning(
            f"Received {signal_name} signal - initiating graceful shutdown..."
        )
        self.shutdown_requested = True
    
    def load_symbols(self) -> List[str]:
        """
        Load S&P 500 symbols from configuration file.
        
        Reads the JSON configuration file and extracts the list of stock symbols.
        Validates that each symbol matches the expected ticker format.
        
        Returns:
            List of stock symbols
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid or missing required fields
        """
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        
        if 'symbols' not in config:
            raise ValueError("Config file missing 'symbols' field")
        
        symbols = config['symbols']
        
        if not isinstance(symbols, list):
            raise ValueError("'symbols' field must be a list")
        
        if not symbols:
            raise ValueError("'symbols' list is empty")
        
        # Validate symbol formats (Requirement 1.2)
        valid_symbols = []
        for symbol in symbols:
            if self._validate_symbol(symbol):
                valid_symbols.append(symbol)
            else:
                logger.warning(
                    f"Invalid symbol format: {symbol} - skipping"
                )
        
        logger.info(
            f"Loaded {len(valid_symbols)} valid symbols from {self.config_path} "
            f"({len(symbols) - len(valid_symbols)} invalid symbols skipped)"
        )
        
        return valid_symbols
    
    def _validate_symbol(self, symbol: str) -> bool:
        """
        Validate stock ticker symbol format.
        
        Valid formats:
        - 1-5 uppercase letters (e.g., AAPL, MSFT)
        - Optionally with a dot and 1-2 letters (e.g., BRK.B)
        
        Args:
            symbol: Stock ticker symbol to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Pattern: 1-5 uppercase letters, optionally followed by dot and 1-2 letters
        pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
        return bool(re.match(pattern, symbol))

    
    def initialize_queue(self, symbols: List[str], days: int = 365):
        """
        Initialize backfill_queue table with pending entries for each symbol.
        
        Creates a backfill task for each symbol with the specified date range.
        If a symbol already has a pending or completed task, it will be skipped
        unless force mode is enabled.
        
        Args:
            symbols: List of stock symbols to backfill
            days: Number of historical days to fetch (default 365)
            
        Raises:
            RuntimeError: If database connection fails
        """
        if not self.db_loader.conn:
            raise RuntimeError("Database not connected")
        
        # Calculate date range (Requirement 2.1)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        logger.info(
            f"Initializing backfill queue for {len(symbols)} symbols "
            f"({start_date} to {end_date})"
        )
        
        cursor = self.db_loader.conn.cursor()
        tasks_created = 0
        tasks_skipped = 0
        
        for symbol in symbols:
            try:
                # Get or create asset (Requirement 3.3)
                cursor.execute(
                    "SELECT id FROM assets WHERE symbol = %s",
                    (symbol,)
                )
                result = cursor.fetchone()
                
                if result:
                    asset_id = result[0]
                else:
                    # Create placeholder asset (will be updated with full metadata during processing)
                    cursor.execute(
                        """
                        INSERT INTO assets (symbol, name, asset_type, exchange, native_currency)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (symbol, symbol, 'stock', 'UNKNOWN', 'USD')
                    )
                    asset_id = cursor.fetchone()[0]
                    logger.debug(f"Created placeholder asset for {symbol} (id={asset_id})")
                
                # Check if task already exists for this asset and date range
                cursor.execute(
                    """
                    SELECT id, status FROM backfill_queue
                    WHERE asset_id = %s
                    AND start_date = %s
                    AND end_date = %s
                    """,
                    (asset_id, start_date, end_date)
                )
                existing_task = cursor.fetchone()
                
                if existing_task:
                    task_id, status = existing_task
                    logger.debug(
                        f"Task already exists for {symbol} (id={task_id}, status={status}) - skipping"
                    )
                    tasks_skipped += 1
                    continue
                
                # Insert new task (Requirement 5.2)
                cursor.execute(
                    """
                    INSERT INTO backfill_queue (asset_id, start_date, end_date, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (asset_id, start_date, end_date, 'pending')
                )
                tasks_created += 1
                
            except psycopg2.Error as e:
                logger.error(
                    f"Failed to initialize task for {symbol}: {str(e)}",
                    exc_info=True
                )
                # Continue with next symbol (Requirement 1.4)
                continue
        
        self.db_loader.conn.commit()
        cursor.close()
        
        logger.info(
            f"Queue initialization complete: {tasks_created} tasks created, "
            f"{tasks_skipped} tasks skipped (already exist)"
        )
    
    def get_pending_backfills(self) -> List[BackfillTask]:
        """
        Retrieve pending and failed backfills from queue.
        
        Queries the backfill_queue table for tasks that need processing:
        - Status is 'pending' or 'failed' (with attempts < max_attempts)
        - Status is 'rate_limited' and retry_after time has passed
        
        Returns:
            List of BackfillTask objects ready for processing
            
        Raises:
            RuntimeError: If database connection fails
        """
        if not self.db_loader.conn:
            raise RuntimeError("Database not connected")
        
        cursor = self.db_loader.conn.cursor()
        
        # Query for pending tasks (Requirements 5.1, 9.1, 9.2)
        cursor.execute(
            """
            SELECT 
                bq.id,
                bq.asset_id,
                a.symbol,
                bq.start_date,
                bq.end_date,
                bq.status,
                bq.attempts,
                bq.retry_after
            FROM backfill_queue bq
            JOIN assets a ON bq.asset_id = a.id
            WHERE 
                (bq.status = 'pending')
                OR (bq.status = 'failed' AND bq.attempts < bq.max_attempts)
                OR (bq.status = 'rate_limited' AND (bq.retry_after IS NULL OR bq.retry_after <= NOW()))
            ORDER BY bq.created_at ASC
            """
        )
        
        rows = cursor.fetchall()
        cursor.close()
        
        tasks = [
            BackfillTask(
                id=row[0],
                asset_id=row[1],
                symbol=row[2],
                start_date=row[3],
                end_date=row[4],
                status=row[5],
                attempts=row[6],
                retry_after=row[7]
            )
            for row in rows
        ]
        
        logger.info(f"Found {len(tasks)} pending backfill tasks")
        
        return tasks

    
    def run(self, force: bool = False, days: int = 365):
        """
        Execute the backfill operation.
        
        Orchestrates the complete backfill workflow:
        1. Connect to database
        2. Load symbols from configuration
        3. Initialize backfill queue (if needed)
        4. Get pending tasks
        5. Process each task sequentially
        6. Generate and log summary report
        7. Close database connection
        
        Args:
            force: If True, re-fetch data even if it already exists
            days: Number of historical days to fetch (default 365)
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
            RuntimeError: If database connection fails
        """
        # Record start time (Requirement 7.1)
        self.start_time = datetime.now()
        log_with_context(
            logger, logging.INFO,
            f"Starting backfill operation at {self.start_time.isoformat()}",
            operation="backfill_start",
            start_time=self.start_time.isoformat(),
            force=force
        )
        
        try:
            # Connect to database
            logger.info("Connecting to database...")
            self.db_loader.connect()
            logger.info("Database connected")
            
            # Load symbols from configuration
            logger.info(f"Loading symbols from {self.config_path}...")
            symbols = self.load_symbols()
            
            # Initialize queue if needed
            logger.info("Initializing backfill queue...")
            self.initialize_queue(symbols, days=days)
            
            # Get pending tasks (Requirement 9.1, 9.2)
            logger.info("Retrieving pending backfill tasks...")
            tasks = self.get_pending_backfills()
            
            if not tasks:
                logger.info("No pending tasks found - backfill complete")
                self.end_time = datetime.now()
                return
            
            # Check if we should skip existing data (Requirement 9.3)
            if not force:
                tasks = self._filter_tasks_with_existing_data(tasks)
                if not tasks:
                    logger.info(
                        "All tasks have existing data - use --force to re-fetch"
                    )
                    self.end_time = datetime.now()
                    return
            
            logger.info(f"Processing {len(tasks)} backfill tasks...")
            
            # Process each task sequentially
            processed_count = 0
            for task in tasks:
                # Check for shutdown signal (Requirement 9.5)
                if self.shutdown_requested:
                    logger.warning(
                        f"Shutdown requested - stopping after {processed_count}/{len(tasks)} tasks processed"
                    )
                    self._save_shutdown_progress(processed_count, len(tasks))
                    break
                
                # Check if task has exceeded max retry attempts (Requirement 5.7, 5.8)
                if task.attempts >= 5:
                    logger.warning(
                        f"Task {task.id} for {task.symbol} has exceeded max retry attempts "
                        f"({task.attempts}/5) - marking as permanently failed"
                    )
                    self._mark_permanently_failed(task.id, task.symbol)
                    
                    # Create a failed result for reporting
                    result = ProcessingResult(
                        symbol=task.symbol,
                        success=False,
                        records_inserted=0,
                        records_skipped=0,
                        completeness_pct=0.0,
                        duration_seconds=0.0,
                        error_message=f"Exceeded maximum retry attempts ({task.attempts}/5)"
                    )
                    self.processing_results.append(result)
                    processed_count += 1
                    continue
                
                # Process the task
                result = self.symbol_processor.process(task)
                self.processing_results.append(result)
                
                processed_count += 1
                
                # Log progress every 10 assets (Requirement 7.2)
                if processed_count % 10 == 0:
                    log_with_context(
                        logger, logging.INFO,
                        f"Progress: {processed_count}/{len(tasks)} tasks processed "
                        f"({processed_count * 100 // len(tasks)}%)",
                        operation="progress_update",
                        tasks_processed=processed_count,
                        total_tasks=len(tasks),
                        progress_pct=processed_count * 100 // len(tasks)
                    )
            
            # Record end time (Requirement 7.1)
            self.end_time = datetime.now()
            duration_seconds = (self.end_time - self.start_time).total_seconds()
            log_with_context(
                logger, logging.INFO,
                f"Backfill operation completed at {self.end_time.isoformat()}",
                operation="backfill_complete",
                end_time=self.end_time.isoformat(),
                duration_seconds=duration_seconds,
                tasks_processed=processed_count
            )
            
            # Generate and log summary report (Requirement 7.5)
            report = self.generate_report()
            self._log_report(report)
            
        except Exception as e:
            # Log error with stack trace (Requirement 7.4)
            log_with_context(
                logger, logging.ERROR,
                f"Backfill operation failed: {str(e)}",
                operation="backfill_error",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise
        
        finally:
            # Always close database connection
            if self.db_loader.conn:
                logger.info("Closing database connection...")
                self.db_loader.close()
                logger.info("Database connection closed")
            
            # Exit with appropriate status code (Requirement 9.5)
            if self.shutdown_requested:
                logger.info("Exiting with status code 130 (interrupted by signal)")
                sys.exit(130)  # Standard exit code for SIGINT
    
    def _save_shutdown_progress(self, processed_count: int, total_tasks: int):
        """
        Save progress to database before graceful shutdown.
        
        Logs the current progress and generates a partial summary report
        before exiting. All task statuses have already been saved to the
        database during processing, so this just logs the final state.
        
        Args:
            processed_count: Number of tasks processed before shutdown
            total_tasks: Total number of tasks that were queued
        """
        # Record end time
        self.end_time = datetime.now()
        
        # Log shutdown progress
        log_with_context(
            logger, logging.WARNING,
            f"Graceful shutdown: processed {processed_count}/{total_tasks} tasks",
            operation="graceful_shutdown",
            tasks_processed=processed_count,
            total_tasks=total_tasks,
            tasks_remaining=total_tasks - processed_count
        )
        
        # Generate partial report if we processed any tasks
        if self.processing_results:
            report = self.generate_report()
            logger.info("Partial backfill report before shutdown:")
            self._log_report(report)
        
        logger.info(
            f"Progress saved to database. Remaining {total_tasks - processed_count} "
            f"tasks can be resumed by running the backfill again."
        )
    
    def _filter_tasks_with_existing_data(self, tasks: List[BackfillTask]) -> List[BackfillTask]:
        """
        Filter out tasks that already have data in the database.
        
        Checks if each asset already has price data for the requested date range.
        Tasks with existing data are skipped unless force mode is enabled.
        
        Args:
            tasks: List of BackfillTask objects
            
        Returns:
            Filtered list of tasks without existing data
        """
        if not self.db_loader.conn:
            return tasks
        
        filtered_tasks = []
        cursor = self.db_loader.conn.cursor()
        
        for task in tasks:
            # Check if asset has any price data in the date range
            cursor.execute(
                """
                SELECT COUNT(*) FROM asset_prices
                WHERE asset_id = %s
                AND timestamp >= %s
                AND timestamp <= %s
                """,
                (task.asset_id, task.start_date, task.end_date)
            )
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.debug(
                    f"Skipping {task.symbol} - already has {count} price records"
                )
            else:
                filtered_tasks.append(task)
        
        cursor.close()
        
        logger.info(
            f"Filtered {len(tasks) - len(filtered_tasks)} tasks with existing data"
        )
        
        return filtered_tasks
    
    def update_queue_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None,
        retry_after: Optional[datetime] = None,
        increment_attempts: bool = False
    ):
        """
        Update backfill_queue table with current status.
        
        Updates the status of a backfill task and optionally sets error message,
        retry_after timestamp, and increments the attempts counter.
        
        Args:
            task_id: ID of the backfill task
            status: New status (pending, in_progress, completed, failed, rate_limited)
            error_message: Optional error message for failed tasks
            retry_after: Optional timestamp for when to retry rate-limited tasks
            increment_attempts: If True, increment the attempts counter
            
        Raises:
            RuntimeError: If database connection fails
        """
        if not self.db_loader.conn:
            raise RuntimeError("Database not connected")
        
        try:
            cursor = self.db_loader.conn.cursor()
            
            # Build dynamic UPDATE query based on parameters
            update_fields = ["status = %s", "updated_at = NOW()"]
            params = [status]
            
            if error_message is not None:
                update_fields.append("error_message = %s")
                params.append(error_message)
            
            if retry_after is not None:
                update_fields.append("retry_after = %s")
                params.append(retry_after)
            
            if increment_attempts:
                update_fields.append("attempts = attempts + 1")
            
            if status == 'completed':
                update_fields.append("completed_at = NOW()")
            
            query = f"""
                UPDATE backfill_queue
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            params.append(task_id)
            
            cursor.execute(query, params)
            self.db_loader.conn.commit()
            cursor.close()
            
            logger.debug(
                f"Updated task {task_id} status to '{status}'"
            )
            
        except psycopg2.Error as e:
            logger.error(
                f"Failed to update task {task_id} status: {str(e)}",
                exc_info=True
            )
            raise
    
    def update_tracked_asset(self, asset_id: int, symbol: str):
        """
        Update or insert tracked_assets entry for an asset.
        
        Creates a new tracked_assets entry if one doesn't exist, or updates
        the last_price_update timestamp if it does. This marks the asset as
        actively tracked for future price updates.
        
        Args:
            asset_id: ID of the asset
            symbol: Stock symbol for logging
            
        Raises:
            RuntimeError: If database connection fails
        """
        if not self.db_loader.conn:
            raise RuntimeError("Database not connected")
        
        try:
            cursor = self.db_loader.conn.cursor()
            
            # Use INSERT ... ON CONFLICT to handle both insert and update cases
            cursor.execute(
                """
                INSERT INTO tracked_assets (asset_id, last_price_update, last_tracked_at)
                VALUES (%s, NOW(), NOW())
                ON CONFLICT (asset_id) 
                DO UPDATE SET 
                    last_price_update = NOW(),
                    last_tracked_at = NOW()
                """,
                (asset_id,)
            )
            
            self.db_loader.conn.commit()
            cursor.close()
            
            logger.debug(
                f"Updated tracked_assets entry for {symbol} (asset_id={asset_id})"
            )
            
        except psycopg2.Error as e:
            logger.error(
                f"Failed to update tracked_assets for {symbol}: {str(e)}",
                exc_info=True
            )
            raise
    
    def _mark_permanently_failed(self, task_id: int, symbol: str):
        """
        Mark a task as permanently failed after exceeding max retry attempts.
        
        Updates the backfill_queue status to 'failed' with a permanent failure
        indicator. This prevents the task from being retried again.
        
        Args:
            task_id: ID of the backfill task
            symbol: Stock symbol for logging
        """
        try:
            self.update_queue_status(
                task_id=task_id,
                status='failed',
                error_message=f"Permanently failed: exceeded maximum retry attempts (5)"
            )
            
            logger.info(
                f"Marked task {task_id} for {symbol} as permanently failed"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to mark task {task_id} as permanently failed: {str(e)}",
                exc_info=True
            )
    
    def generate_report(self) -> BackfillReport:
        """
        Generate summary report of backfill operation.
        
        Aggregates statistics from all processing results:
        - Total symbols processed
        - Successful vs failed counts
        - Total records inserted
        - Total duration
        - List of failed symbols
        
        Returns:
            BackfillReport with statistics
        """
        if not self.processing_results:
            # No results yet - return empty report
            return BackfillReport(
                total_symbols=0,
                successful=0,
                failed=0,
                total_records_inserted=0,
                total_duration_seconds=0.0,
                start_time=self.start_time or datetime.now(),
                end_time=self.end_time or datetime.now(),
                failed_symbols=[]
            )
        
        # Calculate statistics (Requirement 7.5)
        total_symbols = len(self.processing_results)
        successful = sum(1 for r in self.processing_results if r.success)
        failed = sum(1 for r in self.processing_results if not r.success)
        total_records_inserted = sum(
            r.records_inserted for r in self.processing_results
        )
        
        # Calculate total duration
        if self.start_time and self.end_time:
            total_duration_seconds = (self.end_time - self.start_time).total_seconds()
        else:
            total_duration_seconds = sum(
                r.duration_seconds for r in self.processing_results
            )
        
        # Collect failed symbols
        failed_symbols = [
            r.symbol for r in self.processing_results if not r.success
        ]
        
        return BackfillReport(
            total_symbols=total_symbols,
            successful=successful,
            failed=failed,
            total_records_inserted=total_records_inserted,
            total_duration_seconds=total_duration_seconds,
            start_time=self.start_time or datetime.now(),
            end_time=self.end_time or datetime.now(),
            failed_symbols=failed_symbols
        )
    
    def _log_report(self, report: BackfillReport):
        """
        Log summary report to console and database.
        
        Formats and logs the backfill summary report with all statistics.
        
        Args:
            report: BackfillReport to log
        """
        # Format duration
        duration_minutes = report.total_duration_seconds / 60
        
        # Log summary (Requirement 7.5, 7.6)
        logger.info("=" * 60)
        logger.info("BACKFILL SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"Start Time:          {report.start_time.isoformat()}")
        logger.info(f"End Time:            {report.end_time.isoformat()}")
        logger.info(f"Total Duration:      {duration_minutes:.1f} minutes")
        logger.info(f"Total Symbols:       {report.total_symbols}")
        logger.info(f"Successful:          {report.successful}")
        logger.info(f"Failed:              {report.failed}")
        logger.info(f"Total Records:       {report.total_records_inserted}")
        
        if report.failed_symbols:
            logger.info(f"Failed Symbols:      {', '.join(report.failed_symbols[:10])}")
            if len(report.failed_symbols) > 10:
                logger.info(f"                     ... and {len(report.failed_symbols) - 10} more")
        
        logger.info("=" * 60)
