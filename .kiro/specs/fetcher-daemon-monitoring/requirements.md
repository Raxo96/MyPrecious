# Requirements Document

## Introduction

This specification defines enhancements to the data fetcher module to enable continuous daemon operation with improved monitoring and visibility. The system will provide real-time insights into fetcher operations, automatic portfolio value updates, and a dedicated monitoring interface for tracking fetcher health and activity.

## Glossary

- **Fetcher_Daemon**: The background service that continuously updates stock prices from external data sources
- **Portfolio_Value_Calculator**: The component that recalculates portfolio values based on updated stock prices
- **Monitoring_Dashboard**: The web interface that displays fetcher status, logs, and statistics
- **Update_Cycle**: A single iteration of fetching prices for all tracked assets
- **Price_Update**: The process of retrieving and storing current price data for a single asset
- **Fetcher_API**: The REST API endpoints that provide fetcher status and log data
- **Log_Store**: The persistent storage mechanism for fetcher operational logs
- **Fetcher_Status**: The current operational state of the daemon (running, stopped, error)

## Requirements

### Requirement 1: Daemon Mode Operation

**User Story:** As a system operator, I want the fetcher to run continuously in daemon mode, so that stock prices are kept up-to-date automatically without manual intervention.

#### Acceptance Criteria

1. WHEN the Fetcher_Daemon starts, THE system SHALL enter continuous operation mode
2. WHILE the Fetcher_Daemon is running, THE system SHALL execute Update_Cycles every 10 minutes
3. WHEN an Update_Cycle completes, THE Fetcher_Daemon SHALL log the completion timestamp and status
4. IF an Update_Cycle fails, THEN THE Fetcher_Daemon SHALL log the error and continue operation
5. WHEN the Fetcher_Daemon encounters an error, THE system SHALL not terminate but SHALL retry the next Update_Cycle

### Requirement 2: Automatic Portfolio Value Updates

**User Story:** As a portfolio manager, I want portfolio values to update automatically after price updates, so that I always see current portfolio valuations without manual recalculation.

#### Acceptance Criteria

1. WHEN an Update_Cycle completes successfully, THE Portfolio_Value_Calculator SHALL recalculate all portfolio values
2. WHEN portfolio values are recalculated, THE system SHALL update the portfolio_performance_cache table
3. WHEN the portfolio_performance_cache table is updated, THE system SHALL commit the transaction immediately
4. IF portfolio recalculation fails, THEN THE system SHALL log the error and continue Fetcher_Daemon operation
5. THE Portfolio_Value_Calculator SHALL complete recalculation within 30 seconds of Update_Cycle completion

### Requirement 3: Fetcher Status API

**User Story:** As a frontend developer, I want API endpoints for fetcher status and logs, so that I can display real-time monitoring information to users.

#### Acceptance Criteria

1. THE Fetcher_API SHALL provide an endpoint that returns current Fetcher_Status
2. WHEN the status endpoint is called, THE system SHALL return the daemon state, last update timestamp, and uptime
3. THE Fetcher_API SHALL provide an endpoint that returns recent fetcher logs
4. WHEN the logs endpoint is called, THE system SHALL return logs from the Log_Store with pagination support
5. THE Fetcher_API SHALL provide an endpoint that returns fetcher statistics including total updates, success rate, and average duration
6. WHEN any Fetcher_API endpoint is called, THE system SHALL respond within 500 milliseconds

### Requirement 4: Log Persistence

**User Story:** As a system administrator, I want fetcher logs to be persisted to the database, so that I can review historical fetcher activity and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the Fetcher_Daemon performs any operation, THE system SHALL write log entries to the Log_Store
2. THE Log_Store SHALL persist log entries to the PostgreSQL database
3. WHEN a log entry is created, THE system SHALL include timestamp, log level, message, and operation context
4. THE Log_Store SHALL retain log entries for at least 30 days
5. WHEN log entries exceed 30 days old, THE system SHALL automatically purge them

### Requirement 5: Monitoring Dashboard Interface

**User Story:** As a portfolio manager, I want a monitoring dashboard for the fetcher, so that I can see real-time status, recent activity, and operational statistics.

#### Acceptance Criteria

1. THE Monitoring_Dashboard SHALL be accessible via a "Fetcher" navigation link from the main page
2. WHEN the Monitoring_Dashboard loads, THE system SHALL display current Fetcher_Status
3. WHEN the Monitoring_Dashboard is displayed, THE system SHALL show the last update timestamp
4. THE Monitoring_Dashboard SHALL display the number of assets currently tracked
5. THE Monitoring_Dashboard SHALL show recent Price_Updates with asset name, timestamp, and success status
6. THE Monitoring_Dashboard SHALL display error logs if any errors occurred
7. THE Monitoring_Dashboard SHALL show fetcher statistics including uptime, total updates, success rate, and average update duration
8. WHEN new logs are generated, THE Monitoring_Dashboard SHALL refresh automatically within 15 seconds

### Requirement 6: Price Update Tracking

**User Story:** As a system operator, I want to see which stocks were updated and when, so that I can verify the fetcher is working correctly for all tracked assets.

#### Acceptance Criteria

1. WHEN a Price_Update occurs, THE system SHALL log the asset identifier, timestamp, and result status
2. THE Monitoring_Dashboard SHALL display a list of recent Price_Updates
3. WHEN displaying Price_Updates, THE system SHALL show the asset name, update timestamp, and success or failure status
4. THE Monitoring_Dashboard SHALL display at least the 50 most recent Price_Updates
5. WHEN a Price_Update fails, THE system SHALL log the error message with the Price_Update record

### Requirement 7: Error Handling and Recovery

**User Story:** As a system administrator, I want the fetcher to handle errors gracefully, so that temporary failures don't cause system downtime.

#### Acceptance Criteria

1. WHEN a network error occurs during Price_Update, THE Fetcher_Daemon SHALL log the error and continue with remaining assets
2. WHEN a database error occurs, THE Fetcher_Daemon SHALL log the error and retry the operation once
3. IF an Update_Cycle fails completely, THEN THE Fetcher_Daemon SHALL wait for the next scheduled cycle
4. WHEN an unhandled exception occurs, THE Fetcher_Daemon SHALL log the stack trace and continue operation
5. THE Fetcher_Daemon SHALL not terminate unless explicitly stopped by system signal

### Requirement 8: Fetcher Statistics Calculation

**User Story:** As a system operator, I want to see fetcher performance statistics, so that I can monitor system health and identify performance issues.

#### Acceptance Criteria

1. THE system SHALL track the total number of Update_Cycles performed since daemon start
2. THE system SHALL calculate success rate as successful updates divided by total updates
3. THE system SHALL track the duration of each Update_Cycle
4. THE system SHALL calculate average Update_Cycle duration over the last 100 cycles
5. THE system SHALL calculate daemon uptime as time elapsed since daemon start
6. WHEN statistics are requested via Fetcher_API, THE system SHALL return current calculated values
