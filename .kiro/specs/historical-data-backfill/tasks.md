# Implementation Plan: Historical Data Backfill

## Overview

This implementation plan breaks down the historical data backfill feature into discrete coding tasks. The feature will be implemented as a standalone Python script that leverages existing infrastructure (StockFetcher, DatabaseLoader) to fetch and store one year of historical price data for 500 stocks.

The implementation follows a bottom-up approach: building core components first (rate limiter, validator), then the processing logic (symbol processor), then the orchestration layer, and finally the CLI interface and integration.

## Tasks

- [ ] 1. Create S&P 500 configuration file
  - Create `src/fetcher/sp500_symbols.json` with 500 stock symbols
  - Use a reliable source (Wikipedia or financial data provider) for the current S&P 500 list
  - Include metadata: name, last_updated date
  - _Requirements: 1.1, 1.3_

- [ ] 2. Implement RateLimiter class
  - [ ] 2.1 Create `src/fetcher/rate_limiter.py` with RateLimiter class
    - Implement `__init__` with min_delay_seconds and hourly_limit parameters
    - Implement `wait_if_needed()` to enforce minimum delay and hourly limit
    - Implement `record_request()` to track request timestamps
    - Implement `handle_rate_limit_error(attempt)` with exponential backoff
    - Implement `get_hourly_count()` to return current hour's request count
    - Use `time.time()` for timestamp tracking
    - Use `time.sleep()` for delays
    - _Requirements: 4.1, 4.2, 4.3, 4.5_
  
  - [ ]* 2.2 Write property test for rate limiter minimum delay
    - **Property 9: Rate Limiter Minimum Delay**
    - **Validates: Requirements 4.1**
    - Generate random sequences of requests
    - Verify time between consecutive requests >= 1 second
  
  - [ ]* 2.3 Write unit test for exponential backoff sequence
    - Test that backoff delays are 5, 10, 20, 40, 80 seconds for attempts 1-5
    - _Requirements: 4.2_
  
  - [ ]* 2.4 Write property test for request counter accuracy
    - **Property 10: Request Counter Accuracy**
    - **Validates: Requirements 4.3**
    - Generate random number of requests
    - Verify counter equals number of requests made

- [ ] 3. Implement DataValidator class
  - [ ] 3.1 Create `src/fetcher/data_validator.py` with DataValidator class
    - Implement `validate_price_record(price)` to check required fields and value constraints
    - Implement `validate_ohlc_consistency(price)` to verify OHLC relationships
    - Implement `calculate_completeness(expected_days, actual_records)` to compute percentage
    - Return ValidationResult dataclass with valid flag and error list
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_
  
  - [ ]* 3.2 Write property test for price data validation
    - **Property 19: Price Data Validation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    - Generate random price records with various invalid values
    - Verify validation correctly identifies all constraint violations
  
  - [ ]* 3.3 Write property test for completeness calculation
    - **Property 21: Completeness Calculation**
    - **Validates: Requirements 8.6**
    - Generate random expected/actual counts
    - Verify percentage calculation is accurate

- [ ] 4. Implement data models
  - [ ] 4.1 Create `src/fetcher/backfill_models.py` with dataclasses
    - Define BackfillTask dataclass (id, asset_id, symbol, start_date, end_date, status, attempts, retry_after)
    - Define ProcessingResult dataclass (symbol, success, records_inserted, records_skipped, completeness_pct, duration_seconds, error_message)
    - Define BackfillReport dataclass (total_symbols, successful, failed, total_records_inserted, total_duration_seconds, start_time, end_time, failed_symbols)
    - Define ValidationResult dataclass (valid, errors)
    - _Requirements: All (data structures)_

- [ ] 5. Implement SymbolProcessor class
  - [ ] 5.1 Create `src/fetcher/symbol_processor.py` with SymbolProcessor class
    - Implement `__init__` accepting fetcher, db_loader, rate_limiter, validator
    - Implement `process(task)` to orchestrate fetching, validation, and storage for one symbol
    - Implement `update_queue_status(task_id, status, error_message)` to update backfill_queue table
    - Handle all error types (network, rate limit, validation, database)
    - Calculate and return ProcessingResult with statistics
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 3.2, 3.4, 5.3, 5.4, 5.5, 5.6, 8.5_
  
  - [ ]* 5.2 Write property test for error isolation
    - **Property 2: Error Isolation**
    - **Validates: Requirements 1.4, 2.5**
    - Generate list with mix of valid and invalid symbols
    - Verify processing continues through all symbols
  
  - [ ]* 5.3 Write property test for validation error handling
    - **Property 20: Validation Error Handling**
    - **Validates: Requirements 8.5**
    - Generate price records with validation errors
    - Verify invalid records are skipped and logged
  
  - [ ]* 5.4 Write property test for queue state transitions
    - **Property 12: Queue State Machine Transitions**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6**
    - Generate random processing outcomes (success, failure, rate limit)
    - Verify status transitions follow state machine rules

- [ ] 6. Checkpoint - Ensure core components work
  - Ensure all tests pass for RateLimiter, DataValidator, and SymbolProcessor
  - Ask the user if questions arise

- [ ] 7. Implement BackfillOrchestrator class
  - [ ] 7.1 Create `src/fetcher/backfill_orchestrator.py` with BackfillOrchestrator class
    - Implement `__init__` with db_connection_string and config_path
    - Implement `load_symbols()` to read S&P 500 symbols from JSON config
    - Implement `initialize_queue(symbols, days)` to populate backfill_queue table
    - Implement `get_pending_backfills()` to query incomplete tasks from queue
    - Implement `run(force)` to orchestrate the entire backfill process
    - Implement `generate_report()` to create BackfillReport with statistics
    - Add logging for start/end times, progress updates, and errors
    - _Requirements: 1.2, 5.1, 5.2, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3_
  
  - [ ]* 7.2 Write property test for symbol validation consistency
    - **Property 1: Symbol Validation Consistency**
    - **Validates: Requirements 1.2**
    - Generate random strings (valid and invalid ticker formats)
    - Verify validation correctly identifies valid formats
  
  - [ ]* 7.3 Write property test for date range calculation
    - **Property 3: Date Range Calculation**
    - **Validates: Requirements 2.1**
    - Generate random current dates
    - Verify start_date is exactly 365 days before end_date
  
  - [ ]* 7.4 Write property test for duplicate prevention
    - **Property 7: Duplicate Prevention**
    - **Validates: Requirements 3.4**
    - Process same data twice
    - Verify record count remains the same
  
  - [ ]* 7.5 Write property test for progress logging frequency
    - **Property 15: Progress Logging Frequency**
    - **Validates: Requirements 7.2**
    - Process N assets where N >= 10
    - Verify at least floor(N/10) progress logs generated
  
  - [ ]* 7.6 Write property test for summary report accuracy
    - **Property 17: Summary Report Accuracy**
    - **Validates: Requirements 7.5**
    - Process mix of successful and failed assets
    - Verify report counts are accurate

- [ ] 8. Implement retry logic
  - [ ] 8.1 Add retry logic to BackfillOrchestrator
    - Implement exponential backoff for failed tasks
    - Track attempts counter in backfill_queue
    - Mark tasks as permanently failed after 5 attempts
    - Set retry_after timestamps for rate-limited tasks
    - _Requirements: 5.7, 5.8_
  
  - [ ]* 8.2 Write property test for retry limit enforcement
    - **Property 13: Retry Limit Enforcement**
    - **Validates: Requirements 5.7, 5.8**
    - Simulate failing asset
    - Verify retries up to 5 times then marks as permanently failed

- [ ] 9. Implement database integration
  - [ ] 9.1 Add database methods to BackfillOrchestrator
    - Implement queue initialization (INSERT INTO backfill_queue)
    - Implement queue status updates (UPDATE backfill_queue)
    - Implement pending task queries (SELECT FROM backfill_queue WHERE status IN ...)
    - Implement tracked_assets updates (INSERT/UPDATE tracked_assets)
    - Use existing DatabaseLoader for asset and price data
    - _Requirements: 3.1, 3.2, 3.3, 3.6, 5.1_
  
  - [ ]* 9.2 Write property test for asset creation idempotency
    - **Property 6: Asset Creation Idempotency**
    - **Validates: Requirements 3.3**
    - Process symbol that may or may not exist in database
    - Verify asset record exists after processing
  
  - [ ]* 9.3 Write property test for tracking metadata update
    - **Property 8: Tracking Metadata Update**
    - **Validates: Requirements 3.6**
    - Process asset successfully
    - Verify tracked_assets entry has recent last_price_update timestamp

- [ ] 10. Implement logging infrastructure
  - [ ] 10.1 Add logging to all components
    - Configure Python logging with console and database handlers
    - Create database handler to write to fetcher_logs table
    - Add structured logging with context (symbol, task_id, etc.)
    - Log all required information per requirements
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 10.2 Write property test for dual logging
    - **Property 18: Dual Logging**
    - **Validates: Requirements 7.6**
    - Generate log messages
    - Verify messages appear in both console and database
  
  - [ ]* 10.3 Write property test for error logging completeness
    - **Property 16: Error Logging Completeness**
    - **Validates: Requirements 7.4**
    - Trigger various errors
    - Verify logs contain error message, symbol, and stack trace

- [ ] 11. Checkpoint - Ensure orchestration works end-to-end
  - Ensure all tests pass for BackfillOrchestrator
  - Test with a small subset of symbols (5-10) against test database
  - Ask the user if questions arise

- [ ] 12. Implement CLI interface
  - [ ] 12.1 Create `src/fetcher/backfill_cli.py` with command-line interface
    - Use argparse for CLI argument parsing
    - Add --once flag for one-time execution
    - Add --scheduled flag for daemon mode (optional, may defer)
    - Add --symbols parameter to specify specific symbols
    - Add --days parameter to specify historical days (default 365)
    - Add --force flag to re-fetch existing data
    - Add --config parameter to specify config file path
    - Add --db parameter to specify database connection string
    - Wire up to BackfillOrchestrator
    - _Requirements: 6.1, 6.2, 6.4, 6.5, 9.4_
  
  - [ ]* 12.2 Write unit tests for CLI parameter handling
    - Test --symbols parameter filters to specified symbols
    - Test --days parameter sets correct date range
    - Test --force parameter enables re-fetching
    - _Requirements: 6.4, 6.5, 9.4_

- [ ] 13. Implement resume capability
  - [ ] 13.1 Add resume logic to BackfillOrchestrator
    - On startup, query backfill_queue for incomplete tasks
    - Resume from last incomplete task
    - Skip assets with existing data unless --force is used
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ]* 13.2 Write property test for resume from incomplete
    - **Property 22: Resume from Incomplete**
    - **Validates: Requirements 9.1, 9.2**
    - Simulate interrupted backfill
    - Verify restart identifies and processes incomplete tasks
  
  - [ ]* 13.3 Write property test for skip existing data
    - **Property 23: Skip Existing Data**
    - **Validates: Requirements 9.3**
    - Process asset with existing data
    - Verify asset is skipped unless --force is provided

- [ ] 14. Add signal handling for graceful shutdown
  - [ ] 14.1 Implement signal handlers in BackfillOrchestrator
    - Register handlers for SIGINT and SIGTERM
    - On signal, save current progress to database
    - Exit cleanly with appropriate status code
    - _Requirements: 9.5_

- [ ] 15. Create Docker integration
  - [ ] 15.1 Create Dockerfile for backfill script
    - Base on Python 3.11 image
    - Install dependencies (psycopg2, requests)
    - Copy backfill scripts and config
    - Set entrypoint to backfill_cli.py
    - _Requirements: 10.4_
  
  - [ ] 15.2 Update docker-compose.yml
    - Add backfill service (optional, for scheduled runs)
    - Configure environment variables for database connection
    - Mount config file as volume
    - _Requirements: 10.4_

- [ ] 16. Create documentation and usage guide
  - [ ] 16.1 Create `src/fetcher/BACKFILL_README.md`
    - Document usage examples for all CLI flags
    - Document expected runtime (500 symbols * 2 seconds = ~17 minutes)
    - Document rate limiting behavior
    - Document error handling and retry logic
    - Document how to monitor progress
    - Include troubleshooting section
    - _Requirements: All (documentation)_

- [ ] 17. Integration testing
  - [ ]* 17.1 Write integration test for full backfill workflow
    - Test with small subset of real symbols (5-10)
    - Verify data is correctly stored in database
    - Verify frontend can display the data
    - Test resume capability
    - Test error handling with invalid symbols
    - _Requirements: 10.5_

- [ ] 18. Final checkpoint - End-to-end validation
  - Run full backfill with 500 symbols in test environment
  - Verify all data is stored correctly
  - Verify frontend displays historical data
  - Verify logs and reports are generated
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation reuses existing StockFetcher and DatabaseLoader without modification
- Expected runtime for 500 symbols: ~17 minutes (with 2-second average per symbol including rate limiting)
