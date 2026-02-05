"""
Example usage of the Fetcher module.

Demonstrates:
1. Fetching historical data for multiple stocks
2. Fetching current prices
3. Saving to JSON
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from fetcher import FetcherFactory


def main():
    # Create stock fetcher
    fetcher = FetcherFactory.create_fetcher("stock")
    
    # Top 10 stocks
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "V", "JPM"]
    
    print("Fetching historical data (1 year)...")
    results = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        
        # Fetch historical data
        data = fetcher.fetch_historical(symbol, start_date, end_date)
        
        if data:
            results.append(data.to_dict())
            print(f"  ✓ {symbol}: {len(data.prices)} records")
        else:
            print(f"  ✗ {symbol}: Failed")
    
    # Save to JSON
    output_file = Path(__file__).parent / "example_output.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Saved {len(results)} stocks to {output_file}")
    
    # Example: Fetch current price
    print("\nFetching current prices...")
    for symbol in symbols[:3]:  # Just first 3 for demo
        current = fetcher.fetch_current(symbol)
        if current:
            print(f"{symbol}: ${current.close}")


if __name__ == "__main__":
    main()
