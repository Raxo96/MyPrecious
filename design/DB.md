# Database Design - Portfolio Tracker

## Technology
- **DBMS**: PostgreSQL
- **Base currency**: USD
- **Historical data strategy**: On-demand, 1 year before first purchase date per asset

## Table Schema

### 1. users
System users.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. assets
Catalog of all available assets (stocks, crypto, commodities, bonds).
**Note**: Contains metadata only. Price data fetched on-demand when user adds asset to portfolio.

```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('stock', 'crypto', 'commodity', 'bond')),
    exchange VARCHAR(50),
    native_currency VARCHAR(3) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange)
);

CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_search ON assets USING gin(to_tsvector('english', name || ' ' || symbol));
```

### 3. asset_prices
Historical asset price data (partitioned by year).
**Note**: Only contains data for assets in user portfolios, starting 1 year before first purchase.

```sql
CREATE TABLE asset_prices (
    id BIGSERIAL,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(18,8),
    high DECIMAL(18,8),
    low DECIMAL(18,8),
    close DECIMAL(18,8) NOT NULL,
    volume BIGINT,
    source VARCHAR(50),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Partitions for each year (2016-2026+)
CREATE TABLE asset_prices_2016 PARTITION OF asset_prices
    FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
CREATE TABLE asset_prices_2017 PARTITION OF asset_prices
    FOR VALUES FROM ('2017-01-01') TO ('2018-01-01');
-- ... (similarly for remaining years)

CREATE INDEX idx_asset_prices_asset_time ON asset_prices(asset_id, timestamp DESC);
CREATE INDEX idx_asset_prices_latest ON asset_prices(asset_id, timestamp DESC);
```

**Optimization**: For data older than 2 years, store only `close` price (OHLCV → close only).

### 4. exchange_rates
Currency exchange rates to USD (base currency).

```sql
CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_code VARCHAR(3) NOT NULL,
    rate_to_usd DECIMAL(18,8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50),
    UNIQUE(currency_code, timestamp)
);

CREATE INDEX idx_exchange_rates_latest ON exchange_rates(currency_code, timestamp DESC);
```

**Refresh rate**: Hourly.

### 5. portfolios
User portfolios.

```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolios_user ON portfolios(user_id);
```

### 6. portfolio_positions
Current positions in portfolios.

```sql
CREATE TABLE portfolio_positions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    quantity DECIMAL(18,8) NOT NULL,
    average_buy_price DECIMAL(18,8) NOT NULL,
    first_purchase_date DATE NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, asset_id)
);

CREATE INDEX idx_positions_portfolio ON portfolio_positions(portfolio_id);
```

### 7. transactions
History of all transactions.

```sql
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('buy', 'sell')),
    quantity DECIMAL(18,8) NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    fee DECIMAL(18,8) DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    notes TEXT
);

CREATE INDEX idx_transactions_portfolio_date ON transactions(portfolio_id, timestamp DESC);
```

### 8. portfolio_snapshots
Cache of daily portfolio values (snapshot at midnight UTC).

```sql
CREATE TABLE portfolio_snapshots (
    id BIGSERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    total_value_usd DECIMAL(18,2) NOT NULL,
    snapshot_date DATE NOT NULL,
    positions_snapshot JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, snapshot_date)
);

CREATE INDEX idx_snapshots_portfolio_date ON portfolio_snapshots(portfolio_id, snapshot_date DESC);
```

**Refresh rate**: Daily at midnight UTC.

### 9. portfolio_performance_cache
Cache of portfolio performance metrics.

```sql
CREATE TABLE portfolio_performance_cache (
    portfolio_id INTEGER PRIMARY KEY REFERENCES portfolios(id) ON DELETE CASCADE,
    current_value_usd DECIMAL(18,2) NOT NULL,
    total_invested_usd DECIMAL(18,2) NOT NULL,
    total_return_pct DECIMAL(8,4),
    day_change_pct DECIMAL(8,4),
    week_change_pct DECIMAL(8,4),
    month_change_pct DECIMAL(8,4),
    year_change_pct DECIMAL(8,4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Refresh rate**: 
- After each transaction
- Every 15 minutes during trading hours

**Invalidation**: Trigger on `transactions` → invalidates portfolio cache.

## Fetcher Integration Tables

### 10. tracked_assets
Registry of assets currently being monitored by the fetcher service.

```sql
CREATE TABLE tracked_assets (
    asset_id INTEGER PRIMARY KEY REFERENCES assets(id),
    first_tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tracked_at TIMESTAMP,
    tracking_users INTEGER DEFAULT 1,
    last_price_update TIMESTAMP
);

CREATE INDEX idx_tracked_assets_active ON tracked_assets(last_tracked_at) 
WHERE tracking_users > 0;
```

**Purpose**: 
- Reference counter for how many users hold this asset
- Determines which assets the daemon should fetch updates for
- Incremented when user adds asset, decremented when removed

### 11. backfill_queue
Persistent queue for historical data fetching jobs.

```sql
CREATE TABLE backfill_queue (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'in_progress', 'rate_limited', 'completed', 'failed')),
    retry_after TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_backfill_queue_status ON backfill_queue(status, retry_after);
CREATE INDEX idx_backfill_queue_asset ON backfill_queue(asset_id, status);
```

**Purpose**:
- Manages asynchronous historical data fetching
- Handles rate limit retries with exponential backoff
- Persists across service restarts

## Helper Views

### latest_asset_prices
Latest asset prices.

```sql
CREATE VIEW latest_asset_prices AS
SELECT DISTINCT ON (asset_id) *
FROM asset_prices
ORDER BY asset_id, timestamp DESC;
```

### latest_exchange_rates
Latest exchange rates.

```sql
CREATE VIEW latest_exchange_rates AS
SELECT DISTINCT ON (currency_code) *
FROM exchange_rates
ORDER BY currency_code, timestamp DESC;
```

## Cache Strategy

### Refresh Schedule
- **portfolio_performance_cache**: Update after each transaction + every 15 min during trading hours
- **portfolio_snapshots**: Daily snapshot at midnight UTC
- **exchange_rates**: Hourly

### Invalidation
- Trigger on `transactions` → invalidates portfolio cache
- Background job recalculates values using latest prices

## Data Size Estimates

### On-Demand Strategy

**Assumptions**:
- Average user portfolio: 10-20 assets
- 1 year historical data per asset
- Daily quotes (252 trading days/year)
- ~100 bytes per OHLCV record

**Per User**:
- 20 assets × 252 days × 100 bytes = ~500 KB historical data
- Ongoing: 20 assets × 252 days/year × 100 bytes = ~500 KB/year

**System-wide (1000 users)**:
- Unique assets tracked: ~100-200 (overlap between users)
- **asset_prices**: 200 assets × 252 days × 100 bytes = ~5 MB (initial)
- Growth: ~5 MB/year for tracked assets
- **Total**: ~500 MB for 1000 users (vs 250 GB for all assets)

**Savings**: ~99.8% reduction compared to tracking all assets

### Other Tables

- **assets**: ~10,000 symbols × 500 bytes = ~5 MB (metadata catalog)
- **exchange_rates**: ~18 MB (50 currencies × 10 years × 365 days)
- **transactions**: ~100 bytes × transactions (user-dependent)
- **snapshots**: ~1 KB × portfolios × days
- **backfill_queue**: Temporary, cleaned periodically

## Key Design Decisions

1. **On-Demand Data Fetching**: Only fetch price data for assets in user portfolios
2. **Smart Backfill**: Historical data limited to 1 year before first purchase date
3. **Asset Catalog**: Separate metadata catalog (10k+ assets) from price data (100-200 tracked)
4. **Reference Counting**: Track how many users hold each asset via `tracked_assets`
5. **Partitioning**: `asset_prices` partitioned by year for better performance
6. **Normalization**: Separate `assets` table eliminates data duplication
7. **Caching**: Two-layer cache (snapshots + performance) for fast access
8. **Base Currency**: USD as standard, all conversions through `exchange_rates`
9. **History**: Full transaction history + aggregated snapshots
10. **Queue Persistence**: Backfill jobs survive service restarts

## Data Lifecycle

### Asset Addition Flow

1. User creates buy transaction with date, quantity, price
2. Check if asset exists in `tracked_assets`
3. If new:
   - Create backfill job (transaction_date - 1 year to now)
   - Add to `tracked_assets` with counter = 1
4. If existing:
   - Increment `tracking_users` counter
5. Backfill worker fetches historical data asynchronously
6. Daemon starts fetching real-time updates

### Asset Removal Flow

1. User sells entire position (quantity = 0)
2. Decrement `tracking_users` counter in `tracked_assets`
3. If counter reaches 0:
   - Stop real-time updates (remove from daemon tracking)
   - Keep historical data in `asset_prices` (for reference)
4. If counter > 0:
   - Continue tracking (other users still hold it)

## Triggers

### Transaction Trigger

```sql
CREATE OR REPLACE FUNCTION notify_transaction_created()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify fetcher service about new transaction
    PERFORM pg_notify('transaction_created', 
        json_build_object(
            'transaction_id', NEW.id,
            'asset_id', NEW.asset_id,
            'timestamp', NEW.timestamp
        )::text
    );
    
    -- Invalidate portfolio cache
    UPDATE portfolio_performance_cache
    SET last_updated = NOW() - INTERVAL '1 hour'
    WHERE portfolio_id = NEW.portfolio_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_created_trigger
AFTER INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION notify_transaction_created();
```
