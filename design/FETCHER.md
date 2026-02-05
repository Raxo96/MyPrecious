# Data Fetcher Module - Design Document

## Overview

Python-based service responsible for fetching and maintaining asset price data from external sources. Operates in two modes: on-demand historical backfill and continuous real-time tracking.

## Core Principles

1. **On-Demand Data Collection**: Fetch data only for assets actively held in user portfolios
2. **Smart Backfill**: Historical data limited to 1 year before first purchase date
3. **Rate Limit Resilience**: Automatic retry with exponential backoff when API limits are hit
4. **Event-Driven**: Triggered by portfolio transaction events
5. **Free APIs Only**: No paid data sources required

## Technology Stack

### Core Framework
- **Python 3.11+**: Main language
- **SQLAlchemy 2.0**: ORM with async support
- **Pydantic**: Data validation and settings management
- **asyncio + aiohttp**: Async HTTP operations

### Scheduling & Queue
- **APScheduler**: Job scheduling for daemon mode
- **PostgreSQL**: Persistent job queue (backfill_queue table)

### Data Sources
- **yfinance**: Stock market data (Yahoo Finance)
- **ccxt**: Cryptocurrency exchanges (unified API)
- **CoinGecko API**: Crypto metadata and fallback prices
- **pandas**: Data manipulation and cleaning

### Infrastructure
- **python-dotenv**: Configuration management
- **structlog**: Structured logging
- **tenacity**: Retry logic and error handling
- **aiohttp**: Async HTTP client with connection pooling

## Architecture

### Component Structure

```
fetcher/
├── core/
│   ├── orchestrator.py       # Event handler and workflow coordinator
│   ├── backfill_worker.py    # Background worker for historical data
│   ├── daemon_scheduler.py   # Real-time price updates
│   └── database.py           # DB session and connection management
├── fetchers/
│   ├── base_fetcher.py       # Abstract base class
│   ├── stock_fetcher.py      # Stock market implementation
│   ├── crypto_fetcher.py     # Cryptocurrency implementation
│   ├── commodity_fetcher.py  # Commodities implementation
│   └── forex_fetcher.py      # Currency exchange rates
├── strategies/
│   ├── yahoo_strategy.py     # Yahoo Finance data source
│   ├── binance_strategy.py   # Binance exchange
│   └── coingecko_strategy.py # CoinGecko API
├── models/
│   ├── asset.py              # SQLAlchemy models
│   ├── price.py
│   └── backfill_queue.py
└── utils/
    ├── rate_limiter.py       # Token bucket rate limiter
    └── validators.py         # Data validation utilities
```

### Design Patterns

- **Abstract Factory**: Create appropriate fetcher based on asset type
- **Strategy Pattern**: Pluggable data source implementations
- **Observer Pattern**: React to portfolio transaction events
- **Queue Pattern**: Persistent job queue for backfill operations

## Operating Modes

### Mode 1: Historical Backfill (On-Demand)

**Trigger**: User creates buy transaction

**Process**:
1. Receive transaction event (asset_id, transaction_date, quantity, price)
2. Check if asset already tracked
3. If new asset:
   - Calculate backfill range: `transaction_date - 1 year` to `now`
   - Create backfill job in queue
   - Add asset to tracked_assets table
4. If existing asset:
   - Increment tracking counter
   - Skip backfill (data already exists)

**Execution**:
- Background worker processes queue asynchronously
- User doesn't wait for completion
- Transaction recorded immediately

### Mode 2: Real-Time Daemon

**Trigger**: Scheduled interval (default: 15 minutes)

**Process**:
1. Query tracked_assets table for active assets
2. Group by asset type (stocks, crypto, commodities)
3. Batch fetch current prices for each group
4. Update asset_prices table
5. Update portfolio_performance_cache

**Trading Hours Awareness**:
- Stocks: Only during market hours (configurable by exchange)
- Crypto: 24/7
- Commodities: Exchange-specific hours

## Data Flow

### Asset Addition Flow

```
User creates transaction
    ↓
API validates transaction
    ↓
Transaction saved to DB
    ↓
Event published to fetcher
    ↓
Orchestrator receives event
    ↓
Check if asset tracked
    ↓
[New Asset]                    [Existing Asset]
    ↓                               ↓
Create backfill job          Increment counter
    ↓                               ↓
Add to tracked_assets        Continue tracking
    ↓
Background worker picks job
    ↓
Fetch historical data (1 year)
    ↓
Handle rate limits (retry if needed)
    ↓
Bulk insert to asset_prices
    ↓
Mark job completed
```

### Rate Limit Handling Flow

```
Backfill worker fetches data
    ↓
API returns 429 (Rate Limited)
    ↓
Extract retry-after duration
    ↓
Update job status to 'rate_limited'
    ↓
Set retry_after timestamp
    ↓
Worker continues with other jobs
    ↓
After cooldown period
    ↓
Job becomes eligible again
    ↓
Worker retries automatically
```

## Database Schema Extensions

### backfill_queue
Persistent queue for historical data fetching jobs.

```sql
- id (PK)
- asset_id (FK -> assets)
- start_date (DATE)
- end_date (DATE)
- status (ENUM: pending, in_progress, rate_limited, completed, failed)
- retry_after (TIMESTAMP)
- attempts (INTEGER)
- max_attempts (INTEGER, default: 5)
- error_message (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- completed_at (TIMESTAMP)
```

**Indexes**:
- `(status, retry_after)` - Find jobs ready to process
- `(asset_id, status)` - Check asset backfill status

### tracked_assets
Registry of assets currently being monitored.

```sql
- asset_id (PK, FK -> assets)
- first_tracked_at (TIMESTAMP)
- last_tracked_at (TIMESTAMP)
- tracking_users (INTEGER) - Reference counter
- last_price_update (TIMESTAMP)
```

**Indexes**:
- `(last_tracked_at) WHERE tracking_users > 0` - Active assets only

## Rate Limiting Strategy

### Per-Source Limits

- **Yahoo Finance**: 2000 requests/hour (~33/min)
- **CCXT (Binance)**: 1200 requests/minute
- **CoinGecko**: 50 requests/minute (free tier)

### Implementation

- **Token Bucket Algorithm**: Track requests in sliding 1-minute window
- **Automatic Throttling**: Sleep when approaching limit
- **Graceful Degradation**: Queue jobs when rate limited
- **Exponential Backoff**: 5min → 10min → 20min → 40min on retries

### Error Handling

- Detect rate limit from HTTP 429 status
- Parse `Retry-After` header if available
- Default to 5-minute cooldown if not specified
- Maximum 5 retry attempts before marking as failed

## Asset Catalog Management

### Initial Seed

**One-time operation** to populate assets table with available symbols:

- **Stocks**: NYSE, NASDAQ, major international exchanges (~8,000 symbols)
- **Crypto**: Top 500 by market cap from CoinGecko
- **Commodities**: Predefined list (GOLD, SILVER, OIL, NATURAL_GAS, etc.)
- **Bonds**: Major treasury ETFs and bond funds

**Data stored**: symbol, name, type, exchange, currency (metadata only, no prices)

### Periodic Updates

**Weekly refresh** to add new listings and delist inactive symbols:
- Add new IPOs and crypto listings
- Mark delisted assets as inactive
- Update metadata (name changes, etc.)

## Configuration

### Environment Variables

```
# Database
DATABASE_URL=postgresql://...

# Daemon Settings
FETCH_INTERVAL_MINUTES=15
TRADING_HOURS_ONLY=true

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=30
BACKFILL_BATCH_SIZE=10

# Retry Settings
MAX_BACKFILL_ATTEMPTS=5
RETRY_EXPONENTIAL_BASE=5  # minutes

# Data Sources
COINGECKO_API_KEY=optional
```

## Monitoring & Observability

### Metrics to Track

- Backfill queue size by status
- Average backfill completion time
- Rate limit hit frequency
- Failed jobs count
- Active tracked assets count
- API response times

### Logging

- Structured JSON logs (structlog)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include: asset_id, job_id, source, duration, error details

### Health Checks

- `/health`: Service alive
- `/health/queue`: Backfill queue status
- `/health/sources`: Data source availability

## Scalability Considerations

### Current Design (MVP)

- Single worker process
- Sequential job processing
- ~100-500 tracked assets
- ~10,000 API calls/day

### Future Scaling (if needed)

- Multiple worker processes
- Distributed queue (Redis/RabbitMQ)
- Parallel job processing
- Caching layer (Redis)
- CDN for static asset metadata

## Data Quality

### Validation Rules

- Price must be positive
- Volume must be non-negative
- Timestamp must be in the past
- OHLC relationship: low ≤ open, close ≤ high

### Anomaly Detection

- Detect price spikes >50% in single day (flag for review)
- Identify gaps in historical data
- Validate against multiple sources when available

### Gap Handling

- Detect missing dates in historical data
- Attempt to fetch missing data
- Mark gaps in metadata for transparency

## Security

### API Key Management

- Store in environment variables (never in code)
- Rotate keys periodically
- Use separate keys for dev/staging/prod

### Data Validation

- Sanitize all external data before DB insertion
- Validate symbol format before API calls
- Prevent SQL injection (use parameterized queries)

## Error Recovery

### Failure Scenarios

1. **API Unavailable**: Retry with exponential backoff
2. **Rate Limited**: Queue job with retry_after timestamp
3. **Invalid Data**: Log error, skip record, continue processing
4. **Database Error**: Rollback transaction, retry job
5. **Network Timeout**: Retry with increased timeout

### Graceful Degradation

- Continue processing other assets if one fails
- Use cached data if fresh data unavailable
- Alert on repeated failures

## Performance Optimization

### Database

- Bulk inserts for historical data (batch of 1000 records)
- Connection pooling (SQLAlchemy)
- Prepared statements for repeated queries
- Partition asset_prices by year

### API Calls

- Batch requests where supported
- Reuse HTTP connections (aiohttp session)
- Compress responses when available
- Cache asset metadata locally

### Memory

- Stream large datasets (don't load all in memory)
- Process in chunks
- Clean up completed jobs periodically

## Testing Strategy

### Unit Tests

- Fetcher implementations
- Rate limiter logic
- Data validators
- Retry mechanisms

### Integration Tests

- Database operations
- API mocking (responses.py)
- Queue processing
- Event handling

### End-to-End Tests

- Full backfill workflow
- Rate limit simulation
- Daemon scheduling
- Error recovery

## Deployment

### Requirements

- Python 3.11+
- PostgreSQL 14+
- 512MB RAM minimum
- Network access to data sources

### Running

**Backfill Worker**:
```bash
python main.py worker
```

**Daemon**:
```bash
python main.py daemon --interval 15
```

**Asset Catalog Seed**:
```bash
python main.py seed-catalog
```

## Future Enhancements

1. **Multiple Data Sources**: Fallback to secondary source if primary fails
2. **Real-Time WebSockets**: For crypto prices (sub-second updates)
3. **Machine Learning**: Predict optimal fetch times to avoid rate limits
4. **Data Compression**: Archive old price data to reduce storage
5. **API Gateway**: Centralized rate limiting across multiple services
