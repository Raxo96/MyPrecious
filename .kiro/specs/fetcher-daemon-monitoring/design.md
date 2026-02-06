# Design Document: Fetcher Daemon Monitoring

## Overview

This design enhances the existing backfill daemon to provide continuous monitoring, improved update frequency, and automatic portfolio value recalculation. The system will expose real-time operational data through REST APIs and present it via a dedicated monitoring dashboard in the React frontend.

The design follows a layered architecture:
- **Daemon Layer**: Enhanced BackfillDaemon with logging and statistics tracking
- **Storage Layer**: New database tables for logs and statistics
- **API Layer**: FastAPI endpoints for fetcher status, logs, and statistics
- **UI Layer**: React monitoring dashboard with real-time updates

## Architecture

### System Components

```mermaid
graph TB
    subgraph "Daemon Layer"
        BD[BackfillDaemon]
        PU[PriceUpdater]
        PVC[PortfolioValueCalculator]
        LS[LogStore]
        ST[StatisticsTracker]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        FL[fetcher_logs]
        FS[fetcher_statistics]
        PP[portfolio_performance_cache]
    end
    
    subgraph "API Layer"
        FA[FetcherAPI]
        EP1[/api/fetcher/status]
        EP2[/api/fetcher/logs]
        EP3[/api/fetcher/statistics]
    end
    
    subgraph "UI Layer"
        MD[MonitoringDashboard]
        SC[StatusCard]
        LC[LogsCard]
        StC[StatisticsCard]
    end
    
    BD --> PU
    PU --> PVC
    BD --> LS
    BD --> ST
    
    LS --> FL
    ST --> FS
    PVC --> PP
    
    FA --> EP1
    FA --> EP2
    FA --> EP3
    
    EP1 --> DB
    EP2 --> DB
    EP3 --> DB
    
    MD --> SC
    MD --> LC
    MD --> StC
    
    SC --> EP1
    LC --> EP2
    StC --> EP3
```

### Data Flow

1. **Price Update Cycle**:
   - Timer triggers every 10 minutes
   - PriceUpdater fetches prices for all tracked assets
   - Each update logged to fetcher_logs table
   - Statistics updated in fetcher_statistics table
   - On successful cycle completion, trigger PortfolioValueCalculator

2. **Portfolio Value Update**:
   - PortfolioValueCalculator queries all portfolios
   - Recalculates values using latest prices
   - Updates portfolio_performance_cache table
   - Logs completion status

3. **Monitoring Data Flow**:
   - Frontend polls /api/fetcher/status every 15 seconds
   - Frontend fetches logs from /api/fetcher/logs with pagination
   - Frontend displays statistics from /api/fetcher/statistics
   - Real-time updates reflected in dashboard

## Components and Interfaces

### 1. Enhanced BackfillDaemon

**Responsibilities**:
- Manage daemon lifecycle (start, stop, error recovery)
- Coordinate price update cycles every 10 minutes
- Trigger portfolio value recalculation after successful updates
- Log all operations to database
- Track and persist statistics

**Key Methods**:

```python
class BackfillDaemon:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.loader = DatabaseLoader(db_url)
        self.log_store = LogStore(db_url)
        self.stats_tracker = StatisticsTracker(db_url)
        self.portfolio_calculator = PortfolioValueCalculator(db_url)
        self.running = True
        self.start_time = datetime.now()
    
    def listen(self) -> None:
        """Main daemon loop with LISTEN/NOTIFY and periodic updates."""
        pass
    
    def _price_update_loop(self) -> None:
        """Execute price updates every 10 minutes."""
        pass
    
    def _update_tracked_prices(self) -> None:
        """Update prices for all tracked assets with logging."""
        pass
    
    def _trigger_portfolio_update(self) -> None:
        """Trigger portfolio value recalculation."""
        pass
    
    def _handle_error(self, error: Exception, context: str) -> None:
        """Log error and continue operation."""
        pass
```

### 2. LogStore

**Responsibilities**:
- Persist log entries to database
- Provide query interface for retrieving logs
- Manage log retention (30-day automatic purge)

**Interface**:

```python
class LogStore:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
    
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    def log(self, level: str, message: str, context: dict = None) -> None:
        """Write log entry to database."""
        pass
    
    def get_recent_logs(self, limit: int = 100, offset: int = 0, 
                       level: str = None) -> List[dict]:
        """Retrieve recent logs with pagination."""
        pass
    
    def purge_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days."""
        pass
```

### 3. StatisticsTracker

**Responsibilities**:
- Track update cycle metrics (count, duration, success rate)
- Calculate daemon uptime
- Persist statistics to database
- Provide aggregated statistics

**Interface**:

```python
class StatisticsTracker:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self.cycle_durations = []  # Last 100 cycle durations
        self.total_cycles = 0
        self.successful_cycles = 0
        self.start_time = datetime.now()
    
    def record_cycle_start(self) -> str:
        """Record start of update cycle, return cycle_id."""
        pass
    
    def record_cycle_end(self, cycle_id: str, success: bool, 
                        duration: float) -> None:
        """Record completion of update cycle."""
        pass
    
    def get_statistics(self) -> dict:
        """Get current statistics summary."""
        pass
    
    def persist_statistics(self) -> None:
        """Save current statistics to database."""
        pass
```

### 4. PortfolioValueCalculator

**Responsibilities**:
- Recalculate portfolio values using latest prices
- Update portfolio_performance_cache table
- Log calculation results

**Interface**:

```python
class PortfolioValueCalculator:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
    
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    def recalculate_all_portfolios(self) -> dict:
        """Recalculate values for all portfolios."""
        pass
    
    def _calculate_portfolio_value(self, portfolio_id: int) -> float:
        """Calculate current value for a single portfolio."""
        pass
    
    def _update_cache(self, portfolio_id: int, value: float) -> None:
        """Update portfolio_performance_cache table."""
        pass
```

### 5. Fetcher API Endpoints

**Endpoint: GET /api/fetcher/status**

Returns current daemon status and basic information.

Request: None

Response:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "last_update": "2024-01-15T10:30:00Z",
  "next_update_in_seconds": 420,
  "tracked_assets_count": 25,
  "update_interval_minutes": 10
}
```

**Endpoint: GET /api/fetcher/logs**

Returns recent fetcher logs with pagination.

Request Parameters:
- `limit` (optional, default=100): Number of logs to return
- `offset` (optional, default=0): Pagination offset
- `level` (optional): Filter by log level (INFO, WARNING, ERROR)

Response:
```json
{
  "logs": [
    {
      "id": 123,
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "INFO",
      "message": "Price update complete",
      "context": {
        "assets_updated": 25,
        "duration_seconds": 12.5
      }
    }
  ],
  "total": 500,
  "limit": 100,
  "offset": 0
}
```

**Endpoint: GET /api/fetcher/statistics**

Returns fetcher performance statistics.

Request: None

Response:
```json
{
  "uptime_seconds": 86400,
  "total_cycles": 144,
  "successful_cycles": 142,
  "failed_cycles": 2,
  "success_rate": 98.6,
  "average_cycle_duration_seconds": 15.3,
  "last_cycle_duration_seconds": 14.8,
  "assets_tracked": 25
}
```

**Endpoint: GET /api/fetcher/recent-updates**

Returns recent price updates per asset.

Request Parameters:
- `limit` (optional, default=50): Number of updates to return

Response:
```json
{
  "updates": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "timestamp": "2024-01-15T10:30:00Z",
      "price": 185.50,
      "success": true,
      "error": null
    },
    {
      "symbol": "GOOGL",
      "name": "Alphabet Inc.",
      "timestamp": "2024-01-15T10:30:05Z",
      "price": 0.0,
      "success": false,
      "error": "Network timeout"
    }
  ]
}
```

### 6. Monitoring Dashboard (React)

**Component Structure**:

```
MonitoringDashboard
├── StatusCard
│   ├── DaemonStatus (running/stopped/error indicator)
│   ├── LastUpdateTime
│   ├── NextUpdateCountdown
│   └── TrackedAssetsCount
├── StatisticsCard
│   ├── UptimeDisplay
│   ├── TotalCyclesCount
│   ├── SuccessRateChart
│   └── AverageDurationDisplay
├── RecentUpdatesCard
│   └── UpdatesTable (symbol, time, price, status)
└── LogsCard
    └── LogsTable (timestamp, level, message)
```

**Key Features**:
- Auto-refresh every 15 seconds
- Color-coded status indicators (green=running, red=error, gray=stopped)
- Expandable log entries to show context details
- Filterable logs by level
- Responsive design for mobile viewing

## Data Models

### Database Schema Changes

**New Table: fetcher_logs**

```sql
CREATE TABLE fetcher_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,  -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    context JSONB,  -- Additional structured data
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fetcher_logs_timestamp ON fetcher_logs(timestamp DESC);
CREATE INDEX idx_fetcher_logs_level ON fetcher_logs(level);
```

**New Table: fetcher_statistics**

```sql
CREATE TABLE fetcher_statistics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    uptime_seconds INTEGER NOT NULL,
    total_cycles INTEGER NOT NULL,
    successful_cycles INTEGER NOT NULL,
    failed_cycles INTEGER NOT NULL,
    success_rate DECIMAL(5,2) NOT NULL,
    average_cycle_duration DECIMAL(10,2) NOT NULL,
    assets_tracked INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fetcher_statistics_timestamp ON fetcher_statistics(timestamp DESC);
```

**New Table: price_update_log**

```sql
CREATE TABLE price_update_log (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    price DECIMAL(20,8),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_price_update_log_timestamp ON price_update_log(timestamp DESC);
CREATE INDEX idx_price_update_log_asset ON price_update_log(asset_id);
```

**Modified Table: portfolio_performance_cache**

```sql
-- Assuming this table exists or needs to be created
CREATE TABLE IF NOT EXISTS portfolio_performance_cache (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    total_value DECIMAL(20,2) NOT NULL,
    total_cost DECIMAL(20,2) NOT NULL,
    profit_loss DECIMAL(20,2) NOT NULL,
    profit_loss_pct DECIMAL(10,2) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(portfolio_id, timestamp)
);

CREATE INDEX idx_portfolio_cache_portfolio ON portfolio_performance_cache(portfolio_id);
CREATE INDEX idx_portfolio_cache_timestamp ON portfolio_performance_cache(timestamp DESC);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Update Cycle Timing Consistency
*For any* running period of the Fetcher_Daemon, update cycles should be triggered at 10-minute intervals with no more than 5 seconds of drift.
**Validates: Requirements 1.2**

### Property 2: Update Cycle Logging Completeness
*For any* completed update cycle (successful or failed), a log entry must be created containing the completion timestamp and status.
**Validates: Requirements 1.3**

### Property 3: Daemon Error Resilience
*For any* error encountered during operation (network, database, or unexpected exceptions), the Fetcher_Daemon should log the error with context and continue operation without terminating.
**Validates: Requirements 1.4, 1.5, 7.4, 7.5**

### Property 4: Portfolio Recalculation Trigger
*For any* successfully completed update cycle, the Portfolio_Value_Calculator should be triggered to recalculate all portfolio values.
**Validates: Requirements 2.1**

### Property 5: Portfolio Cache Update Atomicity
*For any* portfolio recalculation, the portfolio_performance_cache table should be updated and the transaction committed immediately as a single atomic operation.
**Validates: Requirements 2.2, 2.3**

### Property 6: Portfolio Calculation Error Isolation
*For any* portfolio recalculation failure, the error should be logged and the Fetcher_Daemon should continue its normal operation cycle.
**Validates: Requirements 2.4**

### Property 7: Portfolio Recalculation Timeliness
*For any* successful update cycle, portfolio recalculation should complete within 30 seconds of the cycle completion.
**Validates: Requirements 2.5**

### Property 8: API Response Structure Completeness
*For any* call to the status endpoint, the response should contain daemon state, last update timestamp, and uptime fields.
**Validates: Requirements 3.2**

### Property 9: Log Pagination Correctness
*For any* pagination parameters (limit, offset) provided to the logs endpoint, the returned logs should be the correct subset from the Log_Store ordered by timestamp descending.
**Validates: Requirements 3.4**

### Property 10: API Response Time Performance
*For any* Fetcher_API endpoint call, the response should be returned within 500 milliseconds.
**Validates: Requirements 3.6**

### Property 11: Log Entry Persistence
*For any* daemon operation, a log entry should be written to the Log_Store and persisted to the PostgreSQL database with timestamp, log level, message, and operation context.
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 12: Log Retention Policy
*For any* log entry, it should be retained for at least 30 days, and entries older than 30 days should be automatically purged.
**Validates: Requirements 4.4, 4.5**

### Property 13: Dashboard Auto-Refresh Timing
*For any* period when the Monitoring_Dashboard is displayed, it should poll for new data at intervals of 15 seconds or less.
**Validates: Requirements 5.8**

### Property 14: Price Update Audit Trail
*For any* price update (successful or failed), a log entry should be created containing the asset identifier, timestamp, result status, and error message (if failed).
**Validates: Requirements 6.1, 6.5**

### Property 15: Price Update Display Completeness
*For any* price update displayed in the Monitoring_Dashboard, it should show the asset name, update timestamp, and success or failure status.
**Validates: Requirements 6.3**

### Property 16: Recent Updates Display Limit
*For any* state where more than 50 price updates exist, the Monitoring_Dashboard should display at least the 50 most recent updates.
**Validates: Requirements 6.4**

### Property 17: Network Error Isolation
*For any* network error during a price update for one asset, the Fetcher_Daemon should log the error and continue processing the remaining assets in the update cycle.
**Validates: Requirements 7.1**

### Property 18: Database Error Retry Logic
*For any* database error during an operation, the Fetcher_Daemon should log the error, retry the operation exactly once, and continue regardless of retry outcome.
**Validates: Requirements 7.2**

### Property 19: Failed Cycle Recovery
*For any* completely failed update cycle, the Fetcher_Daemon should wait for the next scheduled cycle time before attempting another update.
**Validates: Requirements 7.3**

### Property 20: Update Cycle Counter Accuracy
*For any* sequence of update cycles, the total_cycles counter should equal the number of cycles executed since daemon start.
**Validates: Requirements 8.1**

### Property 21: Success Rate Calculation Correctness
*For any* set of successful and total update cycles, the success rate should equal (successful_cycles / total_cycles) * 100, rounded to two decimal places.
**Validates: Requirements 8.2**

### Property 22: Cycle Duration Tracking
*For any* update cycle, the duration from start to completion should be recorded and stored.
**Validates: Requirements 8.3**

### Property 23: Rolling Average Duration Calculation
*For any* sequence of cycle durations, the average duration should be calculated over the most recent 100 cycles (or all cycles if fewer than 100 have been executed).
**Validates: Requirements 8.4**

### Property 24: Uptime Calculation Accuracy
*For any* point in time after daemon start, the uptime should equal the elapsed time since the daemon start timestamp.
**Validates: Requirements 8.5**

### Property 25: Statistics API Consistency
*For any* request to the statistics endpoint, the returned values should match the current calculated statistics state at the time of the request.
**Validates: Requirements 8.6**

## Error Handling

### Error Categories and Responses

1. **Network Errors** (API timeouts, connection failures)
   - Log error with asset symbol and error message
   - Continue with next asset in update cycle
   - Do not retry immediately (wait for next cycle)
   - Track failure in statistics

2. **Database Errors** (connection loss, constraint violations)
   - Log error with operation context
   - Retry operation once after 1-second delay
   - If retry fails, log and continue
   - Track failure in statistics

3. **Data Validation Errors** (invalid price data, missing fields)
   - Log error with asset symbol and validation details
   - Skip the invalid data point
   - Continue with next asset
   - Track failure in statistics

4. **Unhandled Exceptions** (unexpected errors)
   - Log full stack trace with context
   - Continue daemon operation
   - Send error-level log to monitoring
   - Track failure in statistics

### Error Recovery Strategies

**Daemon-Level Recovery**:
- Never terminate on errors (except SIGTERM/SIGINT)
- Maintain error counter per cycle
- If error rate exceeds 50% in a cycle, log warning but continue
- Reset error counters at start of each cycle

**Database Connection Recovery**:
- Detect connection loss via exception handling
- Attempt reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Log each reconnection attempt
- Continue operation once reconnected

**API Rate Limiting**:
- Implement 1-second delay between asset price fetches
- If rate limit error received, wait 60 seconds before continuing
- Log rate limit events
- Track rate limit occurrences in statistics

## Testing Strategy

### Unit Testing Approach

Unit tests will focus on specific components and edge cases:

**LogStore Tests**:
- Test log entry creation with all required fields
- Test pagination with various limit/offset combinations
- Test log level filtering
- Test purge operation for old logs
- Test database connection handling

**StatisticsTracker Tests**:
- Test cycle counter increments
- Test success rate calculation with various ratios
- Test rolling average with < 100 and >= 100 cycles
- Test uptime calculation
- Test statistics persistence

**PortfolioValueCalculator Tests**:
- Test single portfolio calculation
- Test multiple portfolios calculation
- Test cache update and commit
- Test error handling when portfolio has no positions
- Test calculation with missing price data

**API Endpoint Tests**:
- Test each endpoint returns correct status codes
- Test response schema validation
- Test pagination parameters
- Test error responses for invalid requests
- Test response time requirements

### Property-Based Testing Approach

Property tests will verify universal correctness properties across randomized inputs. Each test should run a minimum of 100 iterations.

**Test Configuration**:
- Use `pytest` with `hypothesis` library for Python components
- Use `jest` with `fast-check` library for React components
- Minimum 100 iterations per property test
- Tag each test with feature name and property number

**Property Test Examples**:

**Property 9: Log Pagination Correctness**
```python
@given(
    total_logs=st.integers(min_value=0, max_value=1000),
    limit=st.integers(min_value=1, max_value=100),
    offset=st.integers(min_value=0, max_value=500)
)
def test_log_pagination_correctness(total_logs, limit, offset):
    """
    Feature: fetcher-daemon-monitoring, Property 9
    For any pagination parameters, returned logs should be correct subset
    """
    # Setup: Create total_logs entries in database
    # Execute: Call logs endpoint with limit and offset
    # Assert: Returned logs match expected slice [offset:offset+limit]
    # Assert: Total count matches total_logs
```

**Property 21: Success Rate Calculation**
```python
@given(
    successful=st.integers(min_value=0, max_value=1000),
    total=st.integers(min_value=1, max_value=1000)
)
def test_success_rate_calculation(successful, total):
    """
    Feature: fetcher-daemon-monitoring, Property 21
    For any successful/total counts, success rate should be correctly calculated
    """
    assume(successful <= total)
    expected = round((successful / total) * 100, 2)
    # Execute: Calculate success rate
    # Assert: Result equals expected value
```

**Property 23: Rolling Average Duration**
```python
@given(
    durations=st.lists(
        st.floats(min_value=1.0, max_value=300.0),
        min_size=1,
        max_size=200
    )
)
def test_rolling_average_duration(durations):
    """
    Feature: fetcher-daemon-monitoring, Property 23
    For any sequence of durations, average should be over last 100 cycles
    """
    # Execute: Calculate rolling average
    # Assert: If len <= 100, average of all durations
    # Assert: If len > 100, average of last 100 durations
```

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Full Update Cycle Test**:
   - Start daemon
   - Wait for update cycle
   - Verify prices updated in database
   - Verify portfolio cache updated
   - Verify logs created
   - Verify statistics updated

2. **API Integration Test**:
   - Trigger update cycle
   - Call all API endpoints
   - Verify response data matches database state
   - Verify response times meet requirements

3. **Dashboard Integration Test**:
   - Render dashboard component
   - Verify API calls made
   - Verify data displayed correctly
   - Verify auto-refresh behavior
   - Verify error states handled

4. **Error Recovery Test**:
   - Inject network errors
   - Verify daemon continues
   - Verify errors logged
   - Verify statistics reflect failures
   - Verify next cycle executes normally

### Test Data Management

**Database Fixtures**:
- Create test database with sample portfolios
- Seed with tracked assets (10-20 assets)
- Create historical price data for testing
- Reset database state between tests

**Mock External APIs**:
- Mock Yahoo Finance API responses
- Simulate various response scenarios (success, timeout, invalid data)
- Control timing for testing intervals

**Time Mocking**:
- Use `freezegun` for Python time mocking
- Mock time advancement for testing intervals
- Test cycle timing without waiting real time

## Implementation Notes

### Configuration

The daemon should accept configuration via environment variables:

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
UPDATE_INTERVAL_MINUTES=10  # Default: 10
LOG_RETENTION_DAYS=30       # Default: 30
STATS_PERSIST_INTERVAL=300  # Seconds, default: 5 minutes
API_PORT=8000               # Default: 8000
```

### Deployment Considerations

**Docker Compose Updates**:
- Add fetcher service with restart policy
- Ensure database migrations run before fetcher starts
- Configure logging to stdout for container logs
- Set resource limits (memory, CPU)

**Database Migrations**:
- Create migration scripts for new tables
- Add indexes for query performance
- Consider partitioning for fetcher_logs table if high volume

**Monitoring and Alerting**:
- Expose health check endpoint for container orchestration
- Log critical errors to stderr for alerting
- Consider adding Prometheus metrics endpoint

### Performance Considerations

**Database Query Optimization**:
- Use connection pooling for API endpoints
- Add appropriate indexes on timestamp columns
- Consider materialized views for statistics queries
- Batch insert operations where possible

**API Response Caching**:
- Cache statistics for 10 seconds (update interval)
- Cache status for 5 seconds
- Use ETags for conditional requests

**Frontend Optimization**:
- Implement virtual scrolling for large log lists
- Debounce auto-refresh to prevent excessive requests
- Use React.memo for expensive components
- Lazy load dashboard components

### Security Considerations

**API Security**:
- Add authentication middleware (if not already present)
- Rate limit API endpoints to prevent abuse
- Validate all input parameters
- Sanitize log messages to prevent injection

**Database Security**:
- Use parameterized queries (already implemented)
- Limit database user permissions
- Encrypt sensitive data in logs (if any)
- Regular security audits of dependencies

## Future Enhancements

1. **WebSocket Support**: Real-time log streaming instead of polling
2. **Advanced Filtering**: Filter logs by date range, asset, operation type
3. **Export Functionality**: Export logs and statistics to CSV/JSON
4. **Alert Configuration**: User-configurable alerts for error thresholds
5. **Historical Statistics**: Long-term statistics storage and trending
6. **Multi-Daemon Support**: Monitor multiple fetcher instances
7. **Performance Profiling**: Detailed timing breakdown per asset fetch
8. **Retry Configuration**: Configurable retry policies per error type
