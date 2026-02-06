# Requirements Document

## Introduction

This document specifies the requirements for a historical data backfill feature that will populate the database with one year of historical price data for the 500 most popular stocks. This is a one-time bulk operation (or scheduled periodic operation) that will enable the frontend to display historical price charts and performance metrics for these assets without requiring users to manually add them first.

The feature will leverage the existing fetcher infrastructure (fetcher.py, db_loader.py) and database schema (asset_prices table) to fetch and store historical data efficiently while respecting API rate limits.

## Glossary

- **Backfill_System**: The component responsible for fetching and storing historical price data for multiple assets
- **Asset_Catalog**: The list of 500 most popular stocks to be backfilled (e.g., S&P 500 constituents)
- **Historical_Data**: Daily OHLCV (Open, High, Low, Close, Volume) price data for the past 365 days
- **Rate_Limiter**: Component that manages API request throttling to respect data provider quotas
- **Backfill_Queue**: Database table that tracks backfill progress and retry logic
- **Data_Provider**: External API service (Yahoo Finance) that supplies historical price data
- **Fetcher_Infrastructure**: Existing Python modules (fetcher.py, db_loader.py) for data retrieval and storage

## Requirements

### Requirement 1: Asset Catalog Definition

**User Story:** As a system administrator, I want to define a list of 500 popular stocks to backfill, so that the system knows which assets to fetch historical data for.

#### Acceptance Criteria

1. THE Backfill_System SHALL use the S&P 500 index constituents as the Asset_Catalog
2. WHEN the Asset_Catalog is loaded, THE Backfill_System SHALL validate that each symbol is a valid stock ticker format
3. THE Backfill_System SHALL store the Asset_Catalog in a configuration file or database table
4. WHEN a symbol in the Asset_Catalog is invalid or delisted, THE Backfill_System SHALL log a warning and continue with remaining symbols

### Requirement 2: Historical Data Retrieval

**User Story:** As a system administrator, I want to fetch one year of historical price data for each asset, so that users can view historical performance and charts.

#### Acceptance Criteria

1. WHEN fetching Historical_Data for an asset, THE Backfill_System SHALL request daily OHLCV data for the past 365 calendar days from the current date
2. THE Backfill_System SHALL use the existing StockFetcher class from fetcher.py to retrieve data from the Data_Provider
3. WHEN Historical_Data is successfully retrieved, THE Backfill_System SHALL validate that each price record contains a timestamp, close price, and volume
4. IF the Data_Provider returns incomplete data (missing days), THE Backfill_System SHALL store all available records and log the gaps
5. WHEN the Data_Provider returns an error for a specific asset, THE Backfill_System SHALL mark that asset for retry and continue with remaining assets

### Requirement 3: Data Storage

**User Story:** As a system administrator, I want historical data stored in the existing database schema, so that the frontend can immediately access and display the data.

#### Acceptance Criteria

1. THE Backfill_System SHALL use the existing DatabaseLoader class from db_loader.py to store Historical_Data
2. WHEN storing Historical_Data, THE Backfill_System SHALL insert records into the asset_prices table
3. THE Backfill_System SHALL create asset records in the assets table if they do not already exist
4. WHEN a price record already exists for a given asset and timestamp, THE Backfill_System SHALL skip the duplicate record
5. THE Backfill_System SHALL use batch insert operations to optimize database performance
6. WHEN all Historical_Data for an asset is stored, THE Backfill_System SHALL update the tracked_assets table with the last_price_update timestamp

### Requirement 4: Rate Limiting and API Quota Management

**User Story:** As a system administrator, I want the backfill process to respect API rate limits, so that the system does not get blocked or throttled by the data provider.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a minimum delay of 1 second between consecutive API requests to the Data_Provider
2. WHEN the Data_Provider returns a rate limit error (HTTP 429), THE Rate_Limiter SHALL exponentially back off with delays of 5, 10, 20, 40, and 80 seconds
3. THE Backfill_System SHALL track the number of API requests made per hour
4. WHEN the hourly request count exceeds 1800 requests, THE Backfill_System SHALL pause for 60 minutes before resuming
5. THE Rate_Limiter SHALL log all rate limit events with timestamps and retry schedules

### Requirement 5: Progress Tracking and Retry Logic

**User Story:** As a system administrator, I want to track backfill progress and automatically retry failed assets, so that the system can recover from transient failures.

#### Acceptance Criteria

1. THE Backfill_System SHALL use the existing backfill_queue table to track the status of each asset
2. WHEN starting a backfill for an asset, THE Backfill_System SHALL insert a record with status 'pending' into the Backfill_Queue
3. WHEN an asset backfill is in progress, THE Backfill_System SHALL update the status to 'in_progress'
4. WHEN an asset backfill completes successfully, THE Backfill_System SHALL update the status to 'completed' and set the completed_at timestamp
5. WHEN an asset backfill fails, THE Backfill_System SHALL update the status to 'failed' and increment the attempts counter
6. WHEN a rate limit is encountered, THE Backfill_System SHALL update the status to 'rate_limited' and set the retry_after timestamp
7. THE Backfill_System SHALL automatically retry failed assets up to 5 times with exponential backoff
8. WHEN an asset exceeds the maximum retry attempts, THE Backfill_System SHALL mark it as 'failed' permanently and log the error

### Requirement 6: Execution Modes

**User Story:** As a system administrator, I want to run the backfill as either a one-time operation or a scheduled job, so that I can control when and how the backfill executes.

#### Acceptance Criteria

1. THE Backfill_System SHALL support a command-line interface for one-time execution
2. WHEN invoked with a '--once' flag, THE Backfill_System SHALL process all assets in the Asset_Catalog and then exit
3. WHEN invoked with a '--scheduled' flag, THE Backfill_System SHALL run as a daemon and execute backfills at a specified interval
4. THE Backfill_System SHALL accept a '--symbols' parameter to backfill specific assets instead of the entire Asset_Catalog
5. THE Backfill_System SHALL accept a '--days' parameter to specify the number of historical days to fetch (default 365)

### Requirement 7: Monitoring and Logging

**User Story:** As a system administrator, I want detailed logs and progress reports, so that I can monitor the backfill operation and troubleshoot issues.

#### Acceptance Criteria

1. THE Backfill_System SHALL log the start time, end time, and total duration of the backfill operation
2. THE Backfill_System SHALL log progress updates every 10 assets processed
3. WHEN an asset backfill completes, THE Backfill_System SHALL log the symbol, number of records inserted, and time taken
4. WHEN an error occurs, THE Backfill_System SHALL log the error message, asset symbol, and stack trace
5. THE Backfill_System SHALL generate a summary report at the end showing total assets processed, successful, failed, and total records inserted
6. THE Backfill_System SHALL write logs to both console output and the fetcher_logs database table

### Requirement 8: Data Validation and Quality

**User Story:** As a system administrator, I want the backfill system to validate data quality, so that only accurate and complete data is stored in the database.

#### Acceptance Criteria

1. WHEN Historical_Data is retrieved, THE Backfill_System SHALL verify that close prices are positive numbers
2. THE Backfill_System SHALL verify that timestamps are within the requested date range
3. THE Backfill_System SHALL verify that volume values are non-negative integers
4. WHEN OHLC prices are present, THE Backfill_System SHALL verify that high >= low and high >= open and high >= close and low <= open and low <= close
5. WHEN data validation fails for a price record, THE Backfill_System SHALL log the validation error and skip that specific record
6. THE Backfill_System SHALL calculate and log the data completeness percentage (actual records / expected records) for each asset

### Requirement 9: Idempotency and Resume Capability

**User Story:** As a system administrator, I want the backfill to be idempotent and resumable, so that I can safely restart the process without duplicating data or losing progress.

#### Acceptance Criteria

1. WHEN the Backfill_System starts, THE Backfill_System SHALL check the Backfill_Queue for any incomplete backfills
2. THE Backfill_System SHALL resume processing from the last incomplete asset rather than starting from the beginning
3. WHEN an asset already has Historical_Data in the database, THE Backfill_System SHALL skip fetching that asset unless explicitly forced
4. THE Backfill_System SHALL support a '--force' flag to re-fetch and overwrite existing Historical_Data
5. WHEN the Backfill_System is interrupted (SIGINT, SIGTERM), THE Backfill_System SHALL gracefully save progress and exit

### Requirement 10: Integration with Existing Infrastructure

**User Story:** As a developer, I want the backfill system to integrate seamlessly with existing components, so that it requires minimal changes to the current codebase.

#### Acceptance Criteria

1. THE Backfill_System SHALL reuse the existing StockFetcher class without modification
2. THE Backfill_System SHALL reuse the existing DatabaseLoader class without modification
3. THE Backfill_System SHALL use the existing database schema without requiring new tables (except backfill_queue which already exists)
4. THE Backfill_System SHALL be deployable as a standalone Python script or Docker container
5. WHEN the backfill completes, THE frontend SHALL immediately be able to display Historical_Data without requiring code changes
