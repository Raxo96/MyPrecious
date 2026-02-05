#!/usr/bin/env python3
"""
Populate database with historical price data for seeded stocks.
"""
from datetime import datetime, timedelta
from fetcher import FetcherFactory
from db_loader import DatabaseLoader


def main():
    # Database connection
    db_url = "postgresql://postgres:postgres@localhost:5432/portfolio_tracker"
    loader = DatabaseLoader(db_url)
    loader.connect()
    
    # Stocks from seed.sql
    stocks = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "TSLA", "META", "BRK-B", "V", "JPM"
    ]
    
    # Fetch 1 year of historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    fetcher = FetcherFactory.create_fetcher("stock")
    
    total_inserted = 0
    
    for symbol in stocks:
        print(f"Fetching {symbol}...", end=" ", flush=True)
        
        asset_data = fetcher.fetch_historical(symbol, start_date, end_date)
        
        if asset_data:
            inserted = loader.load_asset_prices(asset_data)
            total_inserted += inserted
            print(f"✓ {inserted} records")
            
            # Update tracked_assets timestamp
            loader.update_tracked_asset_timestamp(symbol)
        else:
            print("✗ Failed")
    
    loader.close()
    
    print(f"\nTotal records inserted: {total_inserted}")


if __name__ == "__main__":
    main()
