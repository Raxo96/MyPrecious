# Minimal Fetcher

Fetches historical data (1 year) for 10 popular stocks and saves to JSON.

## Setup

```bash
cd src/fetcher
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Output

Creates `stock_data.json` with:
- Symbol, name, exchange, currency
- 1 year of daily OHLCV data per stock

## Stocks Fetched

1. AAPL - Apple
2. MSFT - Microsoft
3. GOOGL - Alphabet
4. AMZN - Amazon
5. NVDA - NVIDIA
6. TSLA - Tesla
7. META - Meta
8. BRK-B - Berkshire Hathaway
9. V - Visa
10. JPM - JPMorgan Chase
