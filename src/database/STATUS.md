# Portfolio Tracker - Database

Complete PostgreSQL database implementation based on the design document.

## Structure

```
src/database/
├── schema.sql       # Complete database schema
├── seed.sql         # Test data
├── setup.sh         # Setup script (for local PostgreSQL)
└── README.md        # Documentation

docker-compose.yml   # Docker setup (recommended)
DATABASE_SETUP.md    # Setup guide
```

## Features Implemented

### Tables (11 total)

✅ **Core Tables**
- `users` - User accounts with authentication
- `assets` - Asset catalog with full-text search
- `asset_prices` - Partitioned by year (2016-2027)
- `exchange_rates` - Currency conversion to USD

✅ **Portfolio Tables**
- `portfolios` - User portfolios
- `portfolio_positions` - Current holdings
- `transactions` - Complete transaction history
- `portfolio_snapshots` - Daily value cache
- `portfolio_performance_cache` - Performance metrics

✅ **Fetcher Integration**
- `tracked_assets` - Reference counting for active assets
- `backfill_queue` - Async job queue with retry logic

### Indexes

- Full-text search on asset names/symbols (GIN index)
- Optimized for latest price queries
- Fast portfolio and transaction lookups
- Efficient backfill queue processing

### Views

- `latest_asset_prices` - Most recent price per asset
- `latest_exchange_rates` - Current exchange rates

### Triggers

- `transaction_created_trigger` - PostgreSQL NOTIFY for fetcher service

### Partitioning

`asset_prices` table partitioned by year for:
- Better query performance
- Easier data management
- Scalability

## Quick Start

### Using Docker (Recommended)

```bash
# Start database
docker-compose up -d

# Verify
docker exec -it portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "\dt"
```

### Using Local PostgreSQL

```bash
cd src/database
./setup.sh
```

## Test Data

After setup:
- **User**: test@example.com (password: test123)
- **Assets**: 10 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, BRK-B, V, JPM)
- **Portfolio**: 1 empty portfolio ready for transactions

## Connection

```
postgresql://postgres:postgres@localhost:5432/portfolio_tracker
```

## Design Alignment

This implementation follows the design document (`design/DB.md`):

✅ On-demand data strategy
✅ 1-year backfill approach
✅ Event-driven architecture (pg_notify)
✅ Reference counting for tracked assets
✅ Persistent backfill queue
✅ Performance caching layers
✅ Partitioned price storage

## Next Steps

1. ✅ Database schema created
2. ⏭️ Connect fetcher to database
3. ⏭️ Build API layer
4. ⏭️ Create frontend

## Schema Diagram

```
users
  ↓
portfolios
  ↓
portfolio_positions → assets → asset_prices (partitioned)
  ↓                      ↓
transactions         tracked_assets
  ↓                      ↓
portfolio_snapshots  backfill_queue
  ↓
portfolio_performance_cache
```
