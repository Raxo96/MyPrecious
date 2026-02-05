"""
Populate database with real stock price data from fetcher.
"""
import sys
sys.path.append('../fetcher')

from fetcher import FetcherFactory
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_batch

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'portfolio_tracker',
    'user': 'postgres',
    'password': 'postgres'
}

def populate_prices():
    """Fetch and insert real price data for all assets in database."""
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all assets
    cur.execute("SELECT id, symbol FROM assets WHERE is_active = true")
    assets = cur.fetchall()
    
    print(f"Found {len(assets)} assets to fetch")
    
    # Create fetcher
    fetcher = FetcherFactory.create_fetcher("stock")
    
    # Fetch data for each asset (1 year)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    for asset_id, symbol in assets:
        print(f"Fetching {symbol}...")
        
        try:
            data = fetcher.fetch_historical(symbol, start_date, end_date)
            
            if data and data.prices:
                # Prepare batch insert
                values = [
                    (
                        asset_id,
                        p.timestamp,
                        p.open,
                        p.high,
                        p.low,
                        p.close,
                        p.volume,
                        'yahoo_finance'
                    )
                    for p in data.prices
                ]
                
                # Insert prices
                execute_batch(
                    cur,
                    """
                    INSERT INTO asset_prices 
                    (asset_id, timestamp, open, high, low, close, volume, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    values,
                    page_size=1000
                )
                
                conn.commit()
                print(f"  ✓ Inserted {len(values)} price records")
            else:
                print(f"  ✗ No data available")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            conn.rollback()
    
    cur.close()
    conn.close()
    print("\n✓ Database populated with real price data!")


if __name__ == "__main__":
    populate_prices()
