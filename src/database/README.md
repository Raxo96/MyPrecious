# Database Setup

PostgreSQL database schema for Portfolio Tracker application.

## Files

- `schema.sql` - Complete database schema with all tables, indexes, and triggers
- `seed.sql` - Sample data for testing (test user, 10 stocks, test portfolio)
- `setup.sh` - Automated setup script

## Quick Start

### Prerequisites

- PostgreSQL 14+ installed and running
- `psql` command-line tool available

### Setup Database

```bash
cd src/database

# Default setup (localhost, postgres user)
./setup.sh

# Custom configuration
DB_NAME=mydb DB_USER=myuser DB_HOST=localhost ./setup.sh
```

### Manual Setup

```bash
# Create database
createdb portfolio_tracker

# Run schema
psql -d portfolio_tracker -f schema.sql

# Load seed data
psql -d portfolio_tracker -f seed.sql
```

## Schema Overview

### Core Tables

- **users** - User accounts
- **assets** - Asset catalog (stocks, crypto, etc.)
- **asset_prices** - Historical OHLCV data (partitioned by year)
- **exchange_rates** - Currency exchange rates to USD

### Portfolio Tables

- **portfolios** - User portfolios
- **portfolio_positions** - Current holdings
- **transactions** - Transaction history
- **portfolio_snapshots** - Daily value snapshots
- **portfolio_performance_cache** - Performance metrics cache

### Fetcher Tables

- **tracked_assets** - Assets being monitored
- **backfill_queue** - Historical data fetch jobs

## Key Features

### Partitioning

`asset_prices` table is partitioned by year (2016-2027) for better performance.

### Indexes

- Full-text search on asset names/symbols
- Optimized queries for latest prices
- Fast portfolio lookups

### Triggers

- `transaction_created_trigger` - Notifies fetcher service via PostgreSQL LISTEN/NOTIFY

## Test Data

After running seed.sql:

- **User**: test@example.com / test123
- **Assets**: 10 popular stocks (AAPL, MSFT, GOOGL, etc.)
- **Portfolio**: Empty portfolio ready for transactions

## Connection String

```
postgresql://postgres@localhost:5432/portfolio_tracker
```

## Verify Setup

```bash
psql -d portfolio_tracker -c "\dt"  # List tables
psql -d portfolio_tracker -c "SELECT * FROM assets;"  # View assets
```
