-- Portfolio Tracker Database Schema
-- PostgreSQL 14+

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets catalog (metadata only, no prices yet)
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

-- Asset prices (partitioned by year)
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

-- Create partitions for years 2016-2027
CREATE TABLE asset_prices_2016 PARTITION OF asset_prices
    FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
CREATE TABLE asset_prices_2017 PARTITION OF asset_prices
    FOR VALUES FROM ('2017-01-01') TO ('2018-01-01');
CREATE TABLE asset_prices_2018 PARTITION OF asset_prices
    FOR VALUES FROM ('2018-01-01') TO ('2019-01-01');
CREATE TABLE asset_prices_2019 PARTITION OF asset_prices
    FOR VALUES FROM ('2019-01-01') TO ('2020-01-01');
CREATE TABLE asset_prices_2020 PARTITION OF asset_prices
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE asset_prices_2021 PARTITION OF asset_prices
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE asset_prices_2022 PARTITION OF asset_prices
    FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE asset_prices_2023 PARTITION OF asset_prices
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE asset_prices_2024 PARTITION OF asset_prices
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE asset_prices_2025 PARTITION OF asset_prices
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE asset_prices_2026 PARTITION OF asset_prices
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE asset_prices_2027 PARTITION OF asset_prices
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');

CREATE INDEX idx_asset_prices_asset_time ON asset_prices(asset_id, timestamp DESC);

-- Exchange rates to USD
CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_code VARCHAR(3) NOT NULL,
    rate_to_usd DECIMAL(18,8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50),
    UNIQUE(currency_code, timestamp)
);

CREATE INDEX idx_exchange_rates_latest ON exchange_rates(currency_code, timestamp DESC);

-- Portfolios
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolios_user ON portfolios(user_id);

-- Portfolio positions (current holdings)
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

-- Transactions history
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

-- Portfolio snapshots (daily cache)
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

-- Portfolio performance cache
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

-- Tracked assets (for fetcher service)
CREATE TABLE tracked_assets (
    asset_id INTEGER PRIMARY KEY REFERENCES assets(id),
    first_tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tracked_at TIMESTAMP,
    tracking_users INTEGER DEFAULT 1,
    last_price_update TIMESTAMP
);

CREATE INDEX idx_tracked_assets_active ON tracked_assets(last_tracked_at) 
WHERE tracking_users > 0;

-- Backfill queue (for fetcher service)
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

-- Helper views
CREATE VIEW latest_asset_prices AS
SELECT DISTINCT ON (asset_id) *
FROM asset_prices
ORDER BY asset_id, timestamp DESC;

CREATE VIEW latest_exchange_rates AS
SELECT DISTINCT ON (currency_code) *
FROM exchange_rates
ORDER BY currency_code, timestamp DESC;

-- Trigger for transaction events (notify fetcher)
CREATE OR REPLACE FUNCTION notify_transaction_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('transaction_created', 
        json_build_object(
            'transaction_id', NEW.id,
            'asset_id', NEW.asset_id,
            'timestamp', NEW.timestamp
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_created_trigger
AFTER INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION notify_transaction_created();
