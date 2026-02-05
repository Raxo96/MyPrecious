# Database Setup Guide

## Option 1: Docker (Recommended)

### Start Database

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL 14 in a container
- Automatically run schema.sql and seed.sql
- Expose on localhost:5432

### Stop Database

```bash
docker-compose down
```

### Connect to Database

```bash
docker exec -it portfolio_tracker_db psql -U postgres -d portfolio_tracker
```

Or use any PostgreSQL client:
```
Host: localhost
Port: 5432
Database: portfolio_tracker
User: postgres
Password: postgres
```

## Option 2: Local PostgreSQL

If you have PostgreSQL installed locally:

```bash
cd src/database
./setup.sh
```

## Verify Setup

```bash
# Using docker
docker exec -it portfolio_tracker_db psql -U postgres -d portfolio_tracker -c "\dt"

# Or using local psql
psql -h localhost -U postgres -d portfolio_tracker -c "\dt"
```

You should see all tables listed:
- users
- assets
- asset_prices (and partitions)
- portfolios
- transactions
- etc.

## Test Data

After setup, you'll have:
- 1 test user (test@example.com)
- 10 stock assets (AAPL, MSFT, GOOGL, etc.)
- 1 empty portfolio

## Connection String

```
postgresql://postgres:postgres@localhost:5432/portfolio_tracker
```
