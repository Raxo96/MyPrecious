#!/usr/bin/env python3
"""
Backfill daemon that listens for new transactions and automatically
fetches historical price data for new assets. Also periodically updates
prices for tracked assets every 15 minutes.
"""
import psycopg2
import psycopg2.extensions
import json
import time
import threading
from datetime import datetime, timedelta
from fetcher import FetcherFactory
from db_loader import DatabaseLoader


class BackfillDaemon:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.loader = DatabaseLoader(db_url)
        self.loader.connect()
        self.running = True
        
    def listen(self):
        """Listen for transaction notifications and trigger backfills."""
        conn = psycopg2.connect(self.db_url)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("LISTEN transaction_created;")
        
        print("🎧 Backfill daemon listening for new transactions...", flush=True)
        
        # Start price update thread
        update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
        update_thread.start()
        print("⏰ Price update scheduler started (15 min interval)", flush=True)
        
        try:
            while self.running:
                if conn.poll() == psycopg2.extensions.POLL_OK:
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        self._handle_notification(notify.payload)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...", flush=True)
            self.running = False
        finally:
            cursor.close()
            conn.close()
            self.loader.close()
    
    def _price_update_loop(self):
        """Periodically update prices for tracked assets."""
        while self.running:
            time.sleep(900)  # 15 minutes
            if not self.running:
                break
            self._update_tracked_prices()
    
    def _update_tracked_prices(self):
        """Update current prices for all tracked assets."""
        try:
            tracked = self.loader.get_tracked_assets()
            if not tracked:
                return
            
            print(f"🔄 Updating prices for {len(tracked)} tracked assets...", flush=True)
            
            for symbol, asset_type, last_update in tracked:
                try:
                    fetcher = FetcherFactory.create_fetcher(asset_type)
                    price_data = fetcher.fetch_current(symbol)
                    
                    if price_data:
                        # Get asset_id
                        cursor = self.loader.conn.cursor()
                        cursor.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                        asset_id = cursor.fetchone()[0]
                        
                        # Insert current price
                        cursor.execute(
                            """
                            INSERT INTO asset_prices (asset_id, timestamp, open, high, low, close, volume)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (asset_id, datetime.fromisoformat(price_data.timestamp),
                             price_data.open, price_data.high, price_data.low,
                             price_data.close, price_data.volume)
                        )
                        self.loader.conn.commit()
                        cursor.close()
                        
                        self.loader.update_tracked_asset_timestamp(symbol)
                        print(f"  ✓ {symbol}: ${price_data.close}", flush=True)
                    
                except Exception as e:
                    print(f"  ✗ {symbol}: {e}", flush=True)
            
            print(f"✅ Price update complete", flush=True)
            
        except Exception as e:
            print(f"❌ Error updating prices: {e}", flush=True)
    
    def _handle_notification(self, payload: str):
        """Handle transaction notification and backfill if needed."""
        try:
            data = json.loads(payload)
            asset_id = data['asset_id']
            
            # Check if asset needs backfill
            if self._needs_backfill(asset_id):
                print(f"📥 New asset detected (ID: {asset_id}), starting backfill...", flush=True)
                self._backfill_asset(asset_id)
            
        except Exception as e:
            print(f"❌ Error handling notification: {e}", flush=True)
    
    def _needs_backfill(self, asset_id: int) -> bool:
        """Check if asset has no price data."""
        cursor = self.loader.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM asset_prices WHERE asset_id = %s",
            (asset_id,)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count == 0
    
    def _backfill_asset(self, asset_id: int):
        """Fetch 1 year of historical data for asset."""
        cursor = self.loader.conn.cursor()
        cursor.execute(
            "SELECT symbol, asset_type FROM assets WHERE id = %s",
            (asset_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return
        
        symbol, asset_type = result
        
        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        try:
            fetcher = FetcherFactory.create_fetcher(asset_type)
            asset_data = fetcher.fetch_historical(symbol, start_date, end_date)
            
            if asset_data:
                inserted = self.loader.load_asset_prices(asset_data)
                print(f"✅ Backfilled {symbol}: {inserted} records", flush=True)
                
                # Add to tracked_assets
                cursor = self.loader.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO tracked_assets (asset_id, last_price_update)
                    VALUES (%s, NOW())
                    ON CONFLICT (asset_id) DO UPDATE
                    SET tracking_users = tracked_assets.tracking_users + 1,
                        last_price_update = NOW()
                    """,
                    (asset_id,)
                )
                self.loader.conn.commit()
                cursor.close()
            else:
                print(f"❌ Failed to fetch data for {symbol}", flush=True)
                
        except Exception as e:
            print(f"❌ Error backfilling {symbol}: {e}", flush=True)


def main():
    import os
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    daemon = BackfillDaemon(db_url)
    daemon.listen()


if __name__ == "__main__":
    main()
