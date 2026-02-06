# Implementation Plan: Fetcher Daemon Monitoring

## Overview

This implementation plan breaks down the fetcher daemon monitoring feature into discrete coding tasks. The approach follows a layered implementation strategy: database schema first, then core daemon enhancements, API endpoints, and finally the frontend dashboard. Each task builds incrementally to ensure continuous integration and early validation.

## Tasks

- [x] 1. Create database schema for monitoring tables
  - Create migration script for fetcher_logs table with indexes
  - Create migration script for fetcher_statistics table with indexes
  - Create migration script for price_update_log table with indexes
  - Create migration script for portfolio_performance_cache table (if not exists)
  - Run migrations and verify table creation
  - _Requirements: 4.1, 4.2, 8.1_

- [x] 2. Implement LogStore component
  - [x] 2.1 Create LogStore class with database connection management
    - Implement connect() and close() methods
    - Implement log() method to write entries to fetcher_logs table
    - Implement get_recent_logs() with pagination support
    - Implement purge_old_logs() for 30-day retention
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 2.2 Write property test for log pagination correctness
    - **Property 9: Log Pagination Correctness**
    - **Validates: Requirements 3.4**
  
  - [ ]* 2.3 Write property test for log entry persistence
    - **Property 11: Log Entry Persistence**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [ ]* 2.4 Write property test for log retention policy
    - **Property 12: Log Retention Policy**
    - **Validates: Requirements 4.4, 4.5**

- [x] 3. Implement StatisticsTracker component
  - [x] 3.1 Create StatisticsTracker class with metrics tracking
    - Implement record_cycle_start() and record_cycle_end() methods
    - Implement rolling average calculation for last 100 cycles
    - Implement get_statistics() to return current metrics
    - Implement persist_statistics() to save to database
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 3.2 Write property test for cycle counter accuracy
    - **Property 20: Update Cycle Counter Accuracy**
    - **Validates: Requirements 8.1**
  
  - [ ]* 3.3 Write property test for success rate calculation
    - **Property 21: Success Rate Calculation Correctness**
    - **Validates: Requirements 8.2**
  
  - [ ]* 3.4 Write property test for rolling average duration
    - **Property 23: Rolling Average Duration Calculation**
    - **Validates: Requirements 8.4**
  
  - [ ]* 3.5 Write property test for uptime calculation
    - **Property 24: Uptime Calculation Accuracy**
    - **Validates: Requirements 8.5**

- [x] 4. Implement PortfolioValueCalculator component
  - [x] 4.1 Create PortfolioValueCalculator class
    - Implement recalculate_all_portfolios() method
    - Implement _calculate_portfolio_value() for single portfolio
    - Implement _update_cache() to write to portfolio_performance_cache
    - Add error handling with logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 4.2 Write property test for portfolio cache update atomicity
    - **Property 5: Portfolio Cache Update Atomicity**
    - **Validates: Requirements 2.2, 2.3**
  
  - [ ]* 4.3 Write unit tests for portfolio calculation edge cases
    - Test portfolio with no positions
    - Test portfolio with missing price data
    - Test error handling and logging
    - _Requirements: 2.4_

- [x] 5. Checkpoint - Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Enhance BackfillDaemon with monitoring capabilities
  - [x] 6.1 Update BackfillDaemon initialization
    - Add LogStore, StatisticsTracker, and PortfolioValueCalculator instances
    - Update constructor to initialize monitoring components
    - Add start_time tracking for uptime calculation
    - _Requirements: 1.1, 8.5_
  
  - [x] 6.2 Update _price_update_loop to use 10-minute interval
    - Change sleep time from 900 to 600 seconds
    - Add cycle timing tracking
    - Integrate StatisticsTracker for cycle recording
    - _Requirements: 1.2_
  
  - [x] 6.3 Enhance _update_tracked_prices with logging and statistics
    - Add LogStore calls for cycle start and completion
    - Record each asset update to price_update_log table
    - Track cycle duration and success/failure
    - Call _trigger_portfolio_update on successful completion
    - _Requirements: 1.3, 6.1, 6.5_
  
  - [x] 6.4 Implement _trigger_portfolio_update method
    - Call PortfolioValueCalculator.recalculate_all_portfolios()
    - Log portfolio update start and completion
    - Handle errors without stopping daemon
    - _Requirements: 2.1, 2.4_
  
  - [x] 6.5 Enhance error handling throughout daemon
    - Wrap operations in try-except blocks
    - Log all errors with context to LogStore
    - Ensure daemon continues on errors
    - Add retry logic for database errors
    - _Requirements: 1.4, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 6.6 Write property test for daemon error resilience
    - **Property 3: Daemon Error Resilience**
    - **Validates: Requirements 1.4, 1.5, 7.4, 7.5**
  
  - [ ]* 6.7 Write property test for update cycle timing consistency
    - **Property 1: Update Cycle Timing Consistency**
    - **Validates: Requirements 1.2**
  
  - [ ]* 6.8 Write property test for portfolio recalculation trigger
    - **Property 4: Portfolio Recalculation Trigger**
    - **Validates: Requirements 2.1**

- [ ] 7. Checkpoint - Test enhanced daemon functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Fetcher API endpoints
  - [x] 8.1 Add GET /api/fetcher/status endpoint
    - Query daemon state from database or in-memory state
    - Calculate uptime, next update time
    - Return tracked assets count
    - _Requirements: 3.1, 3.2_
  
  - [x] 8.2 Add GET /api/fetcher/logs endpoint
    - Accept limit, offset, and level query parameters
    - Query fetcher_logs table with pagination
    - Return logs with total count
    - _Requirements: 3.3, 3.4_
  
  - [x] 8.3 Add GET /api/fetcher/statistics endpoint
    - Query fetcher_statistics table for latest entry
    - Return all statistics fields
    - _Requirements: 3.5_
  
  - [x] 8.4 Add GET /api/fetcher/recent-updates endpoint
    - Query price_update_log table with limit
    - Join with assets table for symbol and name
    - Return recent updates with success/failure status
    - _Requirements: 6.2, 6.3_
  
  - [ ]* 8.5 Write property test for API response structure completeness
    - **Property 8: API Response Structure Completeness**
    - **Validates: Requirements 3.2**
  
  - [ ]* 8.6 Write property test for API response time performance
    - **Property 10: API Response Time Performance**
    - **Validates: Requirements 3.6**
  
  - [ ]* 8.7 Write unit tests for API endpoints
    - Test each endpoint with valid parameters
    - Test error responses for invalid parameters
    - Test pagination edge cases
    - _Requirements: 3.1, 3.3, 3.5_

- [x] 9. Create Monitoring Dashboard React component
  - [x] 9.1 Create FetcherMonitoring page component
    - Set up component structure with routing
    - Add navigation link in Header component
    - Implement auto-refresh with 15-second interval
    - _Requirements: 5.1, 5.8_
  
  - [x] 9.2 Create StatusCard component
    - Fetch data from /api/fetcher/status
    - Display daemon status with color indicators
    - Show last update timestamp
    - Show next update countdown
    - Display tracked assets count
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 9.3 Create StatisticsCard component
    - Fetch data from /api/fetcher/statistics
    - Display uptime in human-readable format
    - Show total cycles count
    - Display success rate with visual indicator
    - Show average cycle duration
    - _Requirements: 5.7_
  
  - [x] 9.4 Create RecentUpdatesCard component
    - Fetch data from /api/fetcher/recent-updates
    - Display table with symbol, timestamp, price, status
    - Show success/failure indicators
    - Implement scrolling for long lists
    - _Requirements: 5.5, 6.2, 6.3, 6.4_
  
  - [x] 9.5 Create LogsCard component
    - Fetch data from /api/fetcher/logs
    - Display table with timestamp, level, message
    - Add level filter dropdown
    - Show error logs prominently
    - Implement expandable rows for context details
    - _Requirements: 5.6_
  
  - [ ]* 9.6 Write property test for dashboard auto-refresh timing
    - **Property 13: Dashboard Auto-Refresh Timing**
    - **Validates: Requirements 5.8**
  
  - [ ]* 9.7 Write unit tests for dashboard components
    - Test component rendering with mock data
    - Test auto-refresh behavior
    - Test error state handling
    - Test loading states
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 10. Checkpoint - Test full integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Add remaining property-based tests
  - [ ]* 11.1 Write property test for update cycle logging completeness
    - **Property 2: Update Cycle Logging Completeness**
    - **Validates: Requirements 1.3**
  
  - [ ]* 11.2 Write property test for portfolio calculation error isolation
    - **Property 6: Portfolio Calculation Error Isolation**
    - **Validates: Requirements 2.4**
  
  - [ ]* 11.3 Write property test for portfolio recalculation timeliness
    - **Property 7: Portfolio Recalculation Timeliness**
    - **Validates: Requirements 2.5**
  
  - [ ]* 11.4 Write property test for price update audit trail
    - **Property 14: Price Update Audit Trail**
    - **Validates: Requirements 6.1, 6.5**
  
  - [ ]* 11.5 Write property test for price update display completeness
    - **Property 15: Price Update Display Completeness**
    - **Validates: Requirements 6.3**
  
  - [ ]* 11.6 Write property test for recent updates display limit
    - **Property 16: Recent Updates Display Limit**
    - **Validates: Requirements 6.4**
  
  - [ ]* 11.7 Write property test for network error isolation
    - **Property 17: Network Error Isolation**
    - **Validates: Requirements 7.1**
  
  - [ ]* 11.8 Write property test for database error retry logic
    - **Property 18: Database Error Retry Logic**
    - **Validates: Requirements 7.2**
  
  - [ ]* 11.9 Write property test for failed cycle recovery
    - **Property 19: Failed Cycle Recovery**
    - **Validates: Requirements 7.3**
  
  - [ ]* 11.10 Write property test for cycle duration tracking
    - **Property 22: Cycle Duration Tracking**
    - **Validates: Requirements 8.3**
  
  - [ ]* 11.11 Write property test for statistics API consistency
    - **Property 25: Statistics API Consistency**
    - **Validates: Requirements 8.6**

- [x] 12. Update Docker Compose configuration
  - Add environment variables for fetcher configuration
  - Ensure fetcher service has restart policy
  - Configure resource limits
  - Update documentation with new configuration options
  - _Requirements: 1.1_

- [ ] 13. Final checkpoint - End-to-end testing
  - Run full integration test suite
  - Verify daemon starts and runs continuously
  - Verify all API endpoints respond correctly
  - Verify dashboard displays all data correctly
  - Verify error handling and recovery
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: database → components → daemon → API → UI
