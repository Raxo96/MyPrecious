# Fetcher Module

Market data fetching module with clean architecture for the Portfolio Tracker application.

## Architecture

```
fetcher/
├── __init__.py          # Package exports
├── fetcher.py           # Core fetcher classes
├── example.py           # Usage example
└── requirements.txt     # Dependencies
```

## Classes

### BaseFetcher (Abstract)
Base class for all fetchers with required methods:
- `fetch_historical(symbol, start_date, end_date)` - Get historical OHLCV data
- `fetch_current(symbol)` - Get current price
- `validate_symbol(symbol)` - Validate symbol format

### StockFetcher
Fetches stock data from Yahoo Finance API.

### CryptoFetcher
Placeholder for cryptocurrency data (future implementation).

### FetcherFactory
Creates appropriate fetcher based on asset type.

## Usage

```python
from fetcher import FetcherFactory
from datetime import datetime, timedelta

# Create fetcher
fetcher = FetcherFactory.create_fetcher("stock")

# Fetch historical data (1 year)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
data = fetcher.fetch_historical("AAPL", start_date, end_date)

print(f"Symbol: {data.symbol}")
print(f"Name: {data.name}")
print(f"Prices: {len(data.prices)} records")

# Fetch current price
current = fetcher.fetch_current("AAPL")
print(f"Current price: ${current.close}")
```

## Installation

```bash
pip install -r requirements.txt
```

## Docker Deployment

The fetcher runs as a daemon service in Docker Compose with continuous monitoring capabilities.

### Environment Variables

Configure the fetcher daemon using these environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string (e.g., `postgresql://user:pass@host:port/db`) |
| `UPDATE_INTERVAL_MINUTES` | `10` | Interval between price update cycles in minutes |
| `LOG_RETENTION_DAYS` | `30` | Number of days to retain fetcher logs before automatic purging |
| `STATS_PERSIST_INTERVAL` | `300` | Interval in seconds to persist statistics to database |

### Resource Limits

The fetcher service is configured with the following resource constraints:

- **CPU Limit**: 0.5 cores (50% of one CPU)
- **CPU Reservation**: 0.25 cores (25% of one CPU)
- **Memory Limit**: 512MB
- **Memory Reservation**: 256MB

These limits ensure the fetcher operates efficiently without consuming excessive system resources.

### Restart Policy

The fetcher uses `restart: unless-stopped` policy, which means:
- Automatically restarts if the container exits unexpectedly
- Restarts on system reboot (unless manually stopped)
- Does not restart if explicitly stopped by user

### Health Check

The fetcher includes a health check that:
- Verifies database connectivity every 30 seconds
- Allows 40 seconds startup time before first check
- Retries 3 times before marking as unhealthy
- Times out after 10 seconds per check

### Starting the Fetcher

```bash
# Start all services including fetcher
docker-compose up -d

# View fetcher logs
docker-compose logs -f fetcher

# Restart fetcher only
docker-compose restart fetcher

# Stop fetcher
docker-compose stop fetcher
```

## Run Example

```bash
python example.py
```

## Data Models

### PriceData
Single price point with OHLCV data:
- `timestamp` (str): ISO format datetime
- `open` (float): Opening price
- `high` (float): High price
- `low` (float): Low price
- `close` (float): Closing price
- `volume` (int): Trading volume

### AssetData
Asset metadata and price history:
- `symbol` (str): Asset symbol
- `name` (str): Full name
- `asset_type` (str): Type (stock, crypto, etc.)
- `exchange` (str): Exchange name
- `currency` (str): Currency code
- `prices` (List[PriceData]): Historical prices

## Future Enhancements

- [ ] CryptoFetcher implementation (ccxt/CoinGecko)
- [ ] CommodityFetcher (gold, silver, oil)
- [ ] ForexFetcher (currency exchange rates)
- [ ] Rate limiting and retry logic
- [ ] Async/await support
- [ ] Caching layer
