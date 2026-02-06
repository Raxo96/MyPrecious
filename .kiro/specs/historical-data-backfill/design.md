# Design Document: Historical Data Backfill

## Overview

The Historical Data Backfill feature is a batch processing system that fetches and stores one year of historical price data for 500 popular stocks (S&P 500 constituents). The system is designed to be idempotent, resumable, and respectful of API rate limits.

The backfill system will:
- Load a list of S&P 500 stock symbols from a configuration file
- Fetch 365 days of historical OHLCV data for each symbol using the existing StockFetcher
- Store the data in the asset_prices table using the existing DatabaseLoader
- Track progress in the backfill_queue table for resumability
- Implement rate limiting to avoid API throttling
- Provide detailed logging and progress reporting

The system will be implemented as a standalone Python script that can be run as a one-time operation or scheduled periodically. It will integrate seamlessly with the existing fetcher infrastructure without requiring modifications to core components.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Backfill Orchestrator                     │
│  - Load S&P 500 symbols from config                         │
│  - Manage backfill queue                                     │
│  - Coordinate rate limiting                                  │
│  - Generate progress reports                                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────┬──────────────┐
             ▼              ▼              ▼              ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Symbol 1  │  │  Symbol 2  │  │  Symbol 3  │  │  Symbol N  │
    │  Processor │  │  Processor │  │  Processor │  │  Processor │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │               │
          ▼               ▼               ▼               ▼
    ┌──────────────────────────────────────────────────────────┐
    │              Rate Limiter (Shared)                        │
    │  - Enforce 1 second delay between requests               │
    │  - Track hourly request count                            │
    │  - Implement exponential backoff on 429 errors           │
    └────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │         Existing StockFetcher (fetcher.py)               │
    │  - fetch_historical(symbol, start_date, end_date)        │
    └────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │         Yahoo Finance API                                 │
    └────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │      Existing DatabaseLoader (db_loader.py)              │
    │  - load_asset_prices(asset_data)                         │
    │  - _get_or_create_asset(asset_data)                      │
    └────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │         PostgreSQL Database                               │
    │  - assets table                                           │
    │  - asset_prices table (partitioned)                       │
    │  - backfill_queue table                                   │
    │  - tracked_assets table                                   │
    └──────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Backfill Orchestrator**:
- Entry point for the backfill operation
- Loads S&P 500 symbols from configuration
- Initializes database connection and fetcher
- Manages the backfill queue (pending, in_progress, completed, failed)
- Coordinates sequential processing of symbols
- Generates summary reports

**Symbol Processor**:
- Processes a single stock symbol
- Validates symbol format
- Fetches historical data via StockFetcher
- Validates data quality
- Stores data via DatabaseLoader
- Updates backfill_queue status
- Handles errors and retries

**Rate Limiter**:
- Enforces minimum 1-second delay between API requests
- Tracks hourly request count (limit: 1800/hour based on conservative estimates)
- Implements exponential backoff on rate limit errors (HTTP 429)
- Pauses processing when hourly limit is reached
- Logs all rate limit events

**Data Validator**:
- Validates price data quality (positive prices, valid timestamps, OHLC consistency)
- Calculates data completeness percentage
- Logs validation errors

## Components and Interfaces

### 1. BackfillOrchestrator Class

```python
class BackfillOrchestrator:
    """
    Main orchestrator for the historical data backfill process.
    """
    
    def __init__(self, db_connection_string: str, config_path: str):
        """
        Initialize the orchestrator.
        
        Args:
            db_connection_string: PostgreSQL connection string
            config_path: Path to S&P 500 symbols configuration file
        """
        pass
    
    def load_symbols(self) -> List[str]:
        """
        Load S&P 500 symbols from configuration file.
        
        Returns:
            List of stock symbols
        """
        pass
    
    def initialize_queue(self, symbols: List[str], days: int = 365):
        """
        Initialize backfill_queue table with pending entries for each symbol.
        
        Args:
            symbols: List of stock symbols to backfill
            days: Number of historical days to fetch (default 365)
        """
        pass
    
    def get_pending_backfills(self) -> List[BackfillTask]:
        """
        Retrieve pending and failed backfills from queue.
        
        Returns:
            List of BackfillTask objects ready for processing
        """
        pass
    
    def run(self, force: bool = False):
        """
        Execute the backfill operation.
        
        Args:
            force: If True, re-fetch data even if it already exists
        """
        pass
    
    def generate_report(self) -> BackfillReport:
        """
        Generate summary report of backfill operation.
        
        Returns:
            BackfillReport with statistics
        """
        pass
```

### 2. SymbolProcessor Class

```python
class SymbolProcessor:
    """
    Processes backfill for a single stock symbol.
    """
    
    def __init__(self, fetcher: StockFetcher, db_loader: DatabaseLoader, 
                 rate_limiter: RateLimiter, validator: DataValidator):
        """
        Initialize the processor.
        
        Args:
            fetcher: StockFetcher instance
            db_loader: DatabaseLoader instance
            rate_limiter: RateLimiter instance
            validator: DataValidator instance
        """
        pass
    
    def process(self, task: BackfillTask) -> ProcessingResult:
        """
        Process a single backfill task.
        
        Args:
            task: BackfillTask containing symbol and date range
            
        Returns:
            ProcessingResult with status and statistics
        """
        pass
    
    def update_queue_status(self, task_id: int, status: str, 
                           error_message: str = None):
        """
        Update backfill_queue table with current status.
        
        Args:
            task_id: ID of the backfill task
            status: New status (in_progress, completed, failed, rate_limited)
            error_message: Optional error message for failed tasks
        """
        pass
```

### 3. RateLimiter Class

```python
class RateLimiter:
    """
    Manages API rate limiting to prevent throttling.
    """
    
    def __init__(self, min_delay_seconds: float = 1.0, 
                 hourly_limit: int = 1800):
        """
        Initialize the rate limiter.
        
        Args:
            min_delay_seconds: Minimum delay between requests (default 1.0)
            hourly_limit: Maximum requests per hour (default 1800)
        """
        pass
    
    def wait_if_needed(self):
        """
        Block execution if rate limit would be exceeded.
        Enforces minimum delay and hourly limit.
        """
        pass
    
    def record_request(self):
        """
        Record that a request was made.
        Updates internal counters for rate limiting.
        """
        pass
    
    def handle_rate_limit_error(self, attempt: int) -> int:
        """
        Handle HTTP 429 rate limit error with exponential backoff.
        
        Args:
            attempt: Current retry attempt number
            
        Returns:
            Delay in seconds before next retry
        """
        pass
    
    def get_hourly_count(self) -> int:
        """
        Get number of requests made in the current hour.
        
        Returns:
            Request count
        """
        pass
```

### 4. DataValidator Class

```python
class DataValidator:
    """
    Validates quality of fetched price data.
    """
    
    def validate_price_record(self, price: PriceData) -> ValidationResult:
        """
        Validate a single price record.
        
        Args:
            price: PriceData object to validate
            
        Returns:
            ValidationResult indicating pass/fail and any errors
        """
        pass
    
    def validate_ohlc_consistency(self, price: PriceData) -> bool:
        """
        Validate OHLC price consistency (high >= low, etc.).
        
        Args:
            price: PriceData object to validate
            
        Returns:
            True if consistent, False otherwise
        """
        pass
    
    def calculate_completeness(self, expected_days: int, 
                              actual_records: int) -> float:
        """
        Calculate data completeness percentage.
        
        Args:
            expected_days: Expected number of trading days
            actual_records: Actual number of records received
            
        Returns:
            Completeness percentage (0-100)
        """
        pass
```

### 5. Data Models

```python
@dataclass
class BackfillTask:
    """Represents a backfill task from the queue."""
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
    """Result of processing a single symbol."""
    symbol: str
    success: bool
    records_inserted: int
    records_skipped: int
    completeness_pct: float
    duration_seconds: float
    error_message: Optional[str]

@dataclass
class BackfillReport:
    """Summary report of backfill operation."""
    total_symbols: int
    successful: int
    failed: int
    total_records_inserted: int
    total_duration_seconds: float
    start_time: datetime
    end_time: datetime
    failed_symbols: List[str]

@dataclass
class ValidationResult:
    """Result of data validation."""
    valid: bool
    errors: List[str]
```

## Data Models

### S&P 500 Configuration File

The S&P 500 symbols will be stored in a JSON configuration file:

```json
{
  "name": "S&P 500",
  "last_updated": "2025-02-01",
  "symbols": [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK",
    "ABBV", "PEP", "COST", "AVGO", "KO", "ADBE", "WMT", "MCD", "CSCO",
    "ACN", "LIN", "TMO", "ABT", "DHR", "NFLX", "VZ", "NKE", "CRM",
    "CMCSA", "TXN", "PM", "NEE", "DIS", "UPS", "RTX", "ORCL", "INTC",
    "AMD", "HON", "QCOM", "INTU", "LOW", "SPGI", "UNP", "IBM", "CAT",
    "BA", "GE", "AMGN", "AMAT", "ELV", "PLD", "SBUX", "DE", "BKNG",
    "GILD", "ADP", "TJX", "MDLZ", "ADI", "LMT", "SYK", "VRTX", "MMC",
    "CI", "BLK", "ISRG", "AMT", "REGN", "CVS", "ZTS", "PGR", "C",
    "MO", "CB", "SO", "DUK", "SCHW", "BSX", "ETN", "EOG", "BDX",
    "LRCX", "HCA", "PNC", "ITW", "USB", "AON", "CL", "SLB", "APD",
    "EQIX", "CME", "NOC", "WM", "ICE", "FI", "GD", "NSC", "MCO",
    "PYPL", "EMR", "TGT", "CCI", "SHW", "FCX", "MAR", "PSA", "GM",
    "KLAC", "MSI", "AJG", "MCK", "APH", "ORLY", "ADSK", "TT", "NXPI",
    "ROP", "PCAR", "SNPS", "AZO", "CDNS", "MCHP", "FTNT", "PAYX", "AFL",
    "ROST", "AIG", "TRV", "CARR", "KMB", "AEP", "MSCI", "O", "WELL",
    "CPRT", "CTAS", "MNST", "HLT", "TEL", "CHTR", "FAST", "CMG", "KMI",
    "ODFL", "SRE", "ALL", "CTSH", "VRSK", "GWW", "EA", "PRU", "YUM",
    "BK", "KHC", "IQV", "IDXX", "EW", "DXCM", "DD", "A", "OTIS",
    "HES", "CTVA", "CBRE", "GIS", "EXC", "GEHC", "ANSS", "XEL", "KR",
    "BIIB", "ACGL", "VICI", "TROW", "RMD", "FANG", "IT", "ED", "WEC",
    "KEYS", "VMC", "ROK", "MPWR", "MTD", "DOV", "PPG", "SBAC", "MLM",
    "DHI", "APTV", "EBAY", "FITB", "CSGP", "AWK", "NDAQ", "TTWO", "WTW",
    "GLW", "STZ", "TSCO", "EXR", "DLTR", "HBAN", "HPQ", "IFF", "LH",
    "ALGN", "NTRS", "MTB", "BALL", "LYB", "FTV", "WBD", "HOLX", "TDY",
    "EXPE", "AVB", "ZBRA", "STT", "INVH", "EQR", "CINF", "TYL", "DTE",
    "AEE", "HUBB", "LDOS", "TRMB", "AKAM", "EXPD", "VRSN", "JBHT", "SYY",
    "SWKS", "POOL", "CBOE", "ULTA", "EPAM", "J", "NTAP", "DGX", "LUV",
    "BLDR", "JKHY", "NDSN", "CHRW", "PAYC", "FFIV", "MKTX", "HSIC", "INCY",
    "TECH", "FOXA", "ENPH", "QRVO", "GNRC", "NWSA", "BBWI", "ETSY", "MTCH",
    "WYNN", "PARA", "NWS", "FOX", "DISH", "PENN", "NCLH", "HAS", "RL",
    "UAA", "UA", "IPGP", "XRAY", "PNW", "CMS", "ES", "FE", "CNP",
    "NI", "LNT", "EVRG", "AES", "PEG", "WEC", "DRI", "HST", "WHR",
    "TPR", "VFC", "NWL", "HBI", "PVH", "GPS", "AAP", "KSS", "M",
    "JWN", "BBBY", "EXPR", "ANF", "AEO", "URBN", "ROST", "TJX", "BURL",
    "FIVE", "OLLI", "DKS", "FL", "HIBB", "ASO", "BGFV", "GES", "SCVL",
    "BOOT", "SHOO", "WWW", "TLYS", "ZUMZ", "PLCE", "PSMT", "CTRN", "DXLG",
    "TLRD", "GIII", "LAKE", "UNFI", "IMKTA", "NGVC", "VLGEA", "SPTN", "RICK",
    "RUTH", "TXRH", "BLMN", "CAKE", "EAT", "DENN", "BJRI", "PZZA", "NDLS",
    "SONC", "JACK", "WING", "LOCO", "HAFC", "PBPB", "KRUS", "RRGB", "DFRG",
    "FCCG", "GOOD", "SASR", "RAVE", "ARKR", "PLAY", "PLYA", "CNNE", "DESP",
    "DMRC", "BROS", "CAVA", "SHAK", "RRGB", "DFRG", "FCCG", "GOOD", "SASR"
  ]
}
```

Note: The actual S&P 500 list should be obtained from a reliable source like [Wikipedia](https://en.wikipedia.org/wiki/List_of_S&P_500_companies) or a financial data provider. The list above is illustrative and may not reflect the current S&P 500 composition.

### Database Schema Usage

The backfill system will use the existing database schema:

**assets table**: Stores asset metadata (symbol, name, type, exchange, currency)
**asset_prices table**: Stores OHLCV price data (partitioned by year)
**backfill_queue table**: Tracks backfill progress and retry logic
**tracked_assets table**: Marks assets as tracked for future price updates

The backfill_queue table structure (already exists):
```sql
CREATE TABLE backfill_queue (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    retry_after TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

## Error Handling

### Error Categories and Handling Strategies

**1. Network Errors (Connection failures, timeouts)**
- Strategy: Retry with exponential backoff
- Max retries: 5 attempts
- Backoff: 5, 10, 20, 40, 80 seconds
- Log error and continue with next symbol

**2. Rate Limit Errors (HTTP 429)**
- Strategy: Exponential backoff with longer delays
- Update backfill_queue status to 'rate_limited'
- Set retry_after timestamp
- Pause processing until retry_after time
- Log rate limit event

**3. Invalid Symbol Errors (Symbol not found, delisted)**
- Strategy: Log warning and mark as failed
- Do not retry
- Continue with next symbol
- Include in failed_symbols list in report

**4. Data Validation Errors (Invalid prices, missing data)**
- Strategy: Log validation errors
- Store valid records, skip invalid ones
- Mark task as completed with warnings
- Include validation statistics in report

**5. Database Errors (Connection failures, constraint violations)**
- Strategy: Retry database operation
- If persistent, mark task as failed
- Log error with full stack trace
- Halt processing if database is unavailable

**6. Configuration Errors (Missing config file, invalid format)**
- Strategy: Fail fast at startup
- Log error and exit with non-zero code
- Do not attempt processing

### Error Recovery

The system implements several recovery mechanisms:

**Queue-based Recovery**: All tasks are tracked in backfill_queue, allowing the system to resume from the last incomplete task after a crash or interruption.

**Graceful Shutdown**: On SIGINT or SIGTERM, the system saves the current state to the database and exits cleanly.

**Idempotency**: The system checks for existing data before fetching, preventing duplicate records. The DatabaseLoader already implements duplicate detection.

**Retry Logic**: Failed tasks are automatically retried up to 5 times with exponential backoff. After max retries, tasks are marked as permanently failed.

## Testing Strategy

The testing strategy for the historical data backfill feature will employ both unit testing and property-based testing to ensure correctness, reliability, and robustness.

### Unit Testing

Unit tests will focus on:

**1. Component Behavior**
- BackfillOrchestrator initialization and configuration loading
- SymbolProcessor processing logic for single symbols
- RateLimiter delay enforcement and hourly limit tracking
- DataValidator validation rules for price data

**2. Edge Cases**
- Empty symbol list
- Invalid symbol formats
- Missing configuration file
- Database connection failures
- Malformed API responses

**3. Integration Points**
- Interaction with existing StockFetcher
- Interaction with existing DatabaseLoader
- Database queue operations (insert, update, query)

**4. Error Handling**
- Network timeout handling
- Rate limit error handling (HTTP 429)
- Invalid symbol handling
- Data validation failures

### Property-Based Testing

Property-based tests will verify universal properties across many generated inputs. Each test will run a minimum of 100 iterations with randomized inputs.

The property-based testing library for Python will be **Hypothesis**, which is the standard for property-based testing in Python and integrates well with pytest.

Each property test will be tagged with a comment referencing the design document property:
```python
# Feature: historical-data-backfill, Property 1: Rate limiter enforces minimum delay
```

### Test Configuration

- **Test Framework**: pytest
- **Property Testing Library**: Hypothesis
- **Minimum Iterations**: 100 per property test
- **Coverage Target**: 80% code coverage for new components
- **Integration Tests**: Test against a test database with sample data

### Test Data

- **Mock API Responses**: Use recorded Yahoo Finance responses for deterministic testing
- **Test Database**: Separate PostgreSQL database with test schema
- **Sample Symbols**: Small subset of 10 symbols for fast test execution
- **Generated Data**: Use Hypothesis to generate random price data, dates, and symbols


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Symbol Validation Consistency

*For any* string input, the symbol validation function should consistently identify valid stock ticker formats (1-5 uppercase letters, optionally with a dash) and reject all other formats.

**Validates: Requirements 1.2**

### Property 2: Error Isolation

*For any* list of symbols containing both valid and invalid symbols, processing should continue through all symbols, logging warnings for invalid ones, without halting execution.

**Validates: Requirements 1.4, 2.5**

### Property 3: Date Range Calculation

*For any* current date, when calculating the historical data date range, the start date should be exactly 365 days before the end date.

**Validates: Requirements 2.1**

### Property 4: Required Field Validation

*For any* price record, validation should verify that timestamp, close price, and volume fields are present and non-null.

**Validates: Requirements 2.3**

### Property 5: Incomplete Data Handling

*For any* dataset with missing days (gaps in the date sequence), all valid records should be stored in the database, and the gaps should be logged.

**Validates: Requirements 2.4**

### Property 6: Asset Creation Idempotency

*For any* symbol, after processing completes, an asset record should exist in the assets table, regardless of whether it existed before processing.

**Validates: Requirements 3.3**

### Property 7: Duplicate Prevention

*For any* asset and date range, processing the same data twice should result in the same number of records in the database (no duplicates created).

**Validates: Requirements 3.4**

### Property 8: Tracking Metadata Update

*For any* successfully processed asset, the tracked_assets table should contain an entry with a last_price_update timestamp within the last minute.

**Validates: Requirements 3.6**

### Property 9: Rate Limiter Minimum Delay

*For any* sequence of API requests, the time elapsed between consecutive requests should be greater than or equal to 1 second.

**Validates: Requirements 4.1**

### Property 10: Request Counter Accuracy

*For any* number N of API requests made, the rate limiter's hourly request counter should equal N.

**Validates: Requirements 4.3**

### Property 11: Rate Limit Event Logging

*For any* rate limit event (HTTP 429 or hourly limit exceeded), a log entry should be created containing the timestamp and retry schedule.

**Validates: Requirements 4.5**

### Property 12: Queue State Machine Transitions

*For any* backfill task, the status transitions should follow the valid state machine: pending → in_progress → (completed | failed | rate_limited), with appropriate metadata updates (completed_at timestamp for completed, attempts increment for failed, retry_after timestamp for rate_limited).

**Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 13: Retry Limit Enforcement

*For any* failing asset, the system should retry up to 5 times with exponential backoff, and after the 5th failure, mark the asset as permanently failed without further retries.

**Validates: Requirements 5.7, 5.8**

### Property 14: Operation Logging Completeness

*For any* backfill operation, the logs should contain start time, end time, total duration, and for each processed asset, the symbol, record count, and processing time.

**Validates: Requirements 7.1, 7.3**

### Property 15: Progress Logging Frequency

*For any* backfill processing N assets where N >= 10, the system should generate at least floor(N/10) progress log entries.

**Validates: Requirements 7.2**

### Property 16: Error Logging Completeness

*For any* error that occurs during processing, a log entry should be created containing the error message, affected asset symbol, and stack trace.

**Validates: Requirements 7.4**

### Property 17: Summary Report Accuracy

*For any* completed backfill operation, the summary report should contain accurate counts: total_symbols = successful + failed, and total_records_inserted should equal the sum of records inserted for all successful assets.

**Validates: Requirements 7.5**

### Property 18: Dual Logging

*For any* log message generated during backfill, the message should appear in both console output and the fetcher_logs database table.

**Validates: Requirements 7.6**

### Property 19: Price Data Validation

*For any* price record, validation should verify that: close price > 0, timestamp is within the requested date range, volume >= 0, and if OHLC values are present, high >= low and high >= open and high >= close and low <= open and low <= close.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 20: Validation Error Handling

*For any* price record that fails validation, the record should be skipped (not stored), and a validation error should be logged with details of the failure.

**Validates: Requirements 8.5**

### Property 21: Completeness Calculation

*For any* asset with E expected trading days and A actual records received, the completeness percentage should be calculated as (A / E) * 100 and logged.

**Validates: Requirements 8.6**

### Property 22: Resume from Incomplete

*For any* backfill operation that is interrupted, when restarted, the system should identify all incomplete tasks (status != 'completed') from the backfill_queue and process them.

**Validates: Requirements 9.1, 9.2**

### Property 23: Skip Existing Data

*For any* asset that already has historical data in the database for the requested date range, the system should skip fetching that asset unless the --force flag is provided.

**Validates: Requirements 9.3**
