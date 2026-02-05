import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from typing import List, Optional
from fetcher import AssetData, PriceData


class DatabaseLoader:
    """Loads fetched asset data into PostgreSQL database."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(self.connection_string)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def load_asset_prices(self, asset_data: AssetData) -> int:
        """
        Load price data for an asset into database.
        Returns number of records inserted.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        # Get asset_id from assets table
        asset_id = self._get_or_create_asset(asset_data)
        
        # Prepare batch insert data
        records = [
            (
                asset_id,
                datetime.fromisoformat(price.timestamp),
                price.open,
                price.high,
                price.low,
                price.close,
                price.volume
            )
            for price in asset_data.prices
        ]
        
        # Bulk insert - skip duplicates by checking first
        cursor = self.conn.cursor()
        
        # Get existing timestamps for this asset
        cursor.execute(
            """
            SELECT timestamp FROM asset_prices 
            WHERE asset_id = %s AND timestamp >= %s AND timestamp <= %s
            """,
            (asset_id, 
             datetime.fromisoformat(asset_data.prices[0].timestamp),
             datetime.fromisoformat(asset_data.prices[-1].timestamp))
        )
        existing_timestamps = {row[0] for row in cursor.fetchall()}
        
        # Filter out existing records
        new_records = [
            r for r in records 
            if r[1] not in existing_timestamps
        ]
        
        if new_records:
            execute_batch(
                cursor,
                """
                INSERT INTO asset_prices (asset_id, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                new_records,
                page_size=1000
            )
            inserted = len(new_records)
        else:
            inserted = 0
        
        self.conn.commit()
        cursor.close()
        
        return inserted
    
    def _get_or_create_asset(self, asset_data: AssetData) -> int:
        """Get asset_id or create asset if it doesn't exist."""
        cursor = self.conn.cursor()
        
        # Try to find existing asset
        cursor.execute(
            "SELECT id FROM assets WHERE symbol = %s",
            (asset_data.symbol,)
        )
        result = cursor.fetchone()
        
        if result:
            asset_id = result[0]
        else:
            # Create new asset
            cursor.execute(
                """
                INSERT INTO assets (symbol, name, asset_type, exchange, native_currency)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (asset_data.symbol, asset_data.name, asset_data.asset_type, 
                 asset_data.exchange, asset_data.currency)
            )
            asset_id = cursor.fetchone()[0]
            self.conn.commit()
        
        cursor.close()
        return asset_id
    
    def get_tracked_assets(self) -> List[tuple]:
        """Get list of assets that need price updates (tracking_users > 0)."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT a.symbol, a.asset_type, ta.last_price_update
            FROM tracked_assets ta
            JOIN assets a ON ta.asset_id = a.id
            WHERE ta.tracking_users > 0
            ORDER BY ta.last_price_update ASC NULLS FIRST
            """
        )
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def update_tracked_asset_timestamp(self, symbol: str):
        """Update last_price_update timestamp for a tracked asset."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE tracked_assets
            SET last_price_update = NOW()
            WHERE asset_id = (SELECT id FROM assets WHERE symbol = %s)
            """,
            (symbol,)
        )
        self.conn.commit()
        cursor.close()
