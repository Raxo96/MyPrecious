import requests
import json
from datetime import datetime, timedelta
from pathlib import Path


def fetch_stock_data(symbol: str, days: int = 365) -> dict:
    """Fetch historical data using Yahoo Finance API directly."""
    end_date = int(datetime.now().timestamp())
    start_date = int((datetime.now() - timedelta(days=days)).timestamp())
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "period1": start_date,
        "period2": end_date,
        "interval": "1d"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    
    if "chart" not in data or "result" not in data["chart"]:
        return None
    
    result = data["chart"]["result"][0]
    
    if "timestamp" not in result or "indicators" not in result:
        return None
    
    timestamps = result["timestamp"]
    quotes = result["indicators"]["quote"][0]
    
    # Convert to our format
    prices = []
    for i, ts in enumerate(timestamps):
        if quotes["close"][i] is None:
            continue
            
        prices.append({
            "timestamp": datetime.fromtimestamp(ts).isoformat(),
            "open": round(quotes["open"][i], 2) if quotes["open"][i] else 0,
            "high": round(quotes["high"][i], 2) if quotes["high"][i] else 0,
            "low": round(quotes["low"][i], 2) if quotes["low"][i] else 0,
            "close": round(quotes["close"][i], 2),
            "volume": int(quotes["volume"][i]) if quotes["volume"][i] else 0
        })
    
    # Get metadata
    meta = result.get("meta", {})
    
    return {
        "symbol": symbol,
        "name": meta.get("longName", symbol),
        "asset_type": "stock",
        "exchange": meta.get("exchangeName", "UNKNOWN"),
        "currency": meta.get("currency", "USD"),
        "prices": prices
    }


def main():
    # Top 10 most popular stocks
    symbols = [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "GOOGL", # Alphabet
        "AMZN",  # Amazon
        "NVDA",  # NVIDIA
        "TSLA",  # Tesla
        "META",  # Meta
        "BRK-B", # Berkshire Hathaway
        "V",     # Visa
        "JPM"    # JPMorgan Chase
    ]
    
    print("Fetching data for 10 popular stocks...")
    results = []
    
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        try:
            data = fetch_stock_data(symbol)
            if data and data["prices"]:
                results.append(data)
                print(f"  ✓ {symbol}: {len(data['prices'])} price records")
            else:
                print(f"  ✗ {symbol}: No data")
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {e}")
    
    # Save to JSON
    output_file = Path(__file__).parent / "stock_data.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Saved {len(results)} stocks to {output_file}")
    if results:
        print(f"✓ Total price records: {sum(len(s['prices']) for s in results)}")


if __name__ == "__main__":
    main()
