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
