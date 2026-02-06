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
from log_store import LogStore
from statistics_tracker import StatisticsTracker
from portfolio_value_calculator import PortfolioValueCalculator


class BackfillDaemon:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.loader = DatabaseLoader(db_url)
        self.loader.connect()
        self.running = True
        
        # Initialize monitoring components
        self.log_store = LogStore(db_url)
        self.log_store.connect()
        
        self.stats_tracker = StatisticsTracker(db_url)
        self.stats_tracker.connect()
        
        self.portfolio_calculator = PortfolioValueCalculator(db_url, log_store=self.log_store)
        self.portfolio_calculator.connect()
        
        # Track daemon start time for uptime calculation
        self.start_time = datetime.now()
        
    def listen(self):
        """Listen for transaction notifications and trigger backfills."""
        conn = None
        cursor = None
        
        try:
            conn = psycopg2.connect(self.db_url)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute("LISTEN transaction_created;")
            cursor.execute("LISTEN price_update_trigger;")  # Listen for manual triggers
            
            print("🎧 Backfill daemon listening for new transactions...", flush=True)
            self.log_store.log('INFO', 'Backfill daemon started')
            
            # Persist initial statistics on startup
            try:
                self.stats_tracker.persist_statistics()
                print("📊 Initial statistics persisted", flush=True)
            except Exception as persist_error:
                print(f"⚠️  Failed to persist initial statistics: {persist_error}", flush=True)
                self.log_store.log(
                    'WARNING',
                    'Failed to persist initial statistics',
                    {'error': str(persist_error)}
                )
            
            # Start price update thread
            update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
            update_thread.start()
            print("⏰ Price update scheduler started (10 min interval)", flush=True)
            self.log_store.log('INFO', 'Price update scheduler started', {'interval_minutes': 10})
            
            # Start statistics persistence thread
            stats_thread = threading.Thread(target=self._statistics_persistence_loop, daemon=True)
            stats_thread.start()
            print("📊 Statistics persistence scheduler started (5 min interval)", flush=True)
            self.log_store.log('INFO', 'Statistics persistence scheduler started', {'interval_minutes': 5})
            
            try:
                while self.running:
                    try:
                        if conn.poll() == psycopg2.extensions.POLL_OK:
                            while conn.notifies:
                                notify = conn.notifies.pop(0)
                                print(f"📬 Received notification on channel: {notify.channel}", flush=True)
                                if notify.channel == 'transaction_created':
                                    self._handle_notification(notify.payload)
                                elif notify.channel == 'price_update_trigger':
                                    self._handle_manual_trigger(notify.payload)
                        time.sleep(0.1)
                    except psycopg2.Error as db_error:
                        # Database connection error - try to reconnect
                        self.log_store.log(
                            'ERROR',
                            'Database connection error in listen loop',
                            {'error': str(db_error)}
                        )
                        print(f"❌ Database error: {db_error}", flush=True)
                        
                        # Try to reconnect
                        try:
                            if cursor:
                                cursor.close()
                            if conn:
                                conn.close()
                            
                            time.sleep(1)  # Wait before reconnecting
                            conn = psycopg2.connect(self.db_url)
                            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                            cursor = conn.cursor()
                            cursor.execute("LISTEN transaction_created;")
                            cursor.execute("LISTEN price_update_trigger;")  # Re-establish manual trigger listener
                            
                            self.log_store.log('INFO', 'Database connection restored')
                            print("✅ Database connection restored", flush=True)
                        except Exception as reconnect_error:
                            self.log_store.log(
                                'ERROR',
                                'Failed to reconnect to database',
                                {'error': str(reconnect_error)}
                            )
                            print(f"❌ Reconnection failed: {reconnect_error}", flush=True)
                            time.sleep(5)  # Wait longer before next attempt
                    except Exception as e:
                        # Unexpected error - log and continue
                        self.log_store.log(
                            'ERROR',
                            'Unexpected error in listen loop',
                            {'error': str(e)}
                        )
                        print(f"❌ Unexpected error: {e}", flush=True)
                        time.sleep(1)  # Brief pause before continuing
                        
            except KeyboardInterrupt:
                print("\n👋 Shutting down...", flush=True)
                self.log_store.log('INFO', 'Daemon shutdown requested')
                self.running = False
                
        except Exception as e:
            # Critical startup error
            self.log_store.log(
                'CRITICAL',
                'Critical error during daemon startup',
                {'error': str(e)}
            )
            print(f"❌ Critical startup error: {e}", flush=True)
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            self.loader.close()
            self.log_store.close()
            self.stats_tracker.close()
            self.portfolio_calculator.close()
            self.log_store.log('INFO', 'Daemon stopped')
    
    def _price_update_loop(self):
        """Periodically update prices for tracked assets every 10 minutes."""
        while self.running:
            time.sleep(600)  # 10 minutes (changed from 900 seconds / 15 minutes)
            if not self.running:
                break
            
            # Record cycle start
            cycle_id = self.stats_tracker.record_cycle_start()
            cycle_start_time = datetime.now()
            
            # Execute price update
            try:
                self._update_tracked_prices()
                
                # Calculate cycle duration
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                
                # Record successful cycle completion
                self.stats_tracker.record_cycle_end(cycle_id, success=True, duration=cycle_duration)
                
                # Persist statistics to database after successful cycle
                try:
                    self.stats_tracker.persist_statistics()
                except Exception as persist_error:
                    # Log error but don't fail the cycle
                    self.log_store.log(
                        'WARNING',
                        'Failed to persist statistics',
                        {'error': str(persist_error)}
                    )
                
            except Exception as e:
                # Calculate cycle duration even on failure
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                
                # Record failed cycle completion
                self.stats_tracker.record_cycle_end(cycle_id, success=False, duration=cycle_duration)
                
                # Persist statistics even on failure
                try:
                    self.stats_tracker.persist_statistics()
                except Exception as persist_error:
                    self.log_store.log(
                        'WARNING',
                        'Failed to persist statistics after failed cycle',
                        {'error': str(persist_error)}
                    )
                
                # Log error but continue running
                self.log_store.log(
                    'ERROR',
                    'Price update cycle failed',
                    {'error': str(e), 'cycle_id': cycle_id, 'duration_seconds': cycle_duration}
                )
    
    def _statistics_persistence_loop(self):
        """Periodically persist statistics to database every 5 minutes."""
        while self.running:
            time.sleep(300)  # 5 minutes
            if not self.running:
                break
            
            try:
                self.stats_tracker.persist_statistics()
                print("📊 Statistics persisted to database", flush=True)
            except Exception as e:
                # Log error but continue running
                print(f"⚠️  Failed to persist statistics: {e}", flush=True)
                self.log_store.log(
                    'WARNING',
                    'Failed to persist statistics in periodic update',
                    {'error': str(e)}
                )
    
    def _update_tracked_prices(self):
        """Update current prices for all tracked assets with logging and statistics."""
        update_start_time = datetime.now()
        
        try:
            tracked = self.loader.get_tracked_assets()
            if not tracked:
                self.log_store.log('INFO', 'No tracked assets to update')
                return
            
            # Log cycle start
            self.log_store.log(
                'INFO',
                f'Starting price update cycle for {len(tracked)} tracked assets',
                {'asset_count': len(tracked)}
            )
            
            print(f"🔄 Updating prices for {len(tracked)} tracked assets...", flush=True)
            
            successful_updates = 0
            failed_updates = 0
            
            for symbol, asset_type, last_update in tracked:
                asset_update_start = datetime.now()
                
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
                        
                        # Record successful update to price_update_log
                        update_duration_ms = int((datetime.now() - asset_update_start).total_seconds() * 1000)
                        cursor.execute(
                            """
                            INSERT INTO price_update_log (asset_id, timestamp, price, success, error_message, duration_ms)
                            VALUES (%s, NOW(), %s, %s, %s, %s)
                            """,
                            (asset_id, price_data.close, True, None, update_duration_ms)
                        )
                        self.loader.conn.commit()
                        cursor.close()
                        
                        self.loader.update_tracked_asset_timestamp(symbol)
                        print(f"  ✓ {symbol}: ${price_data.close}", flush=True)
                        successful_updates += 1
                    else:
                        # No price data returned
                        cursor = self.loader.conn.cursor()
                        cursor.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                        result = cursor.fetchone()
                        if result:
                            asset_id = result[0]
                            update_duration_ms = int((datetime.now() - asset_update_start).total_seconds() * 1000)
                            cursor.execute(
                                """
                                INSERT INTO price_update_log (asset_id, timestamp, price, success, error_message, duration_ms)
                                VALUES (%s, NOW(), %s, %s, %s, %s)
                                """,
                                (asset_id, None, False, 'No price data returned', update_duration_ms)
                            )
                            self.loader.conn.commit()
                        cursor.close()
                        
                        print(f"  ✗ {symbol}: No price data", flush=True)
                        failed_updates += 1
                    
                except Exception as e:
                    # Log individual asset update failure
                    error_msg = str(e)
                    print(f"  ✗ {symbol}: {error_msg}", flush=True)
                    failed_updates += 1
                    
                    # Record failed update to price_update_log
                    try:
                        cursor = self.loader.conn.cursor()
                        cursor.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                        result = cursor.fetchone()
                        if result:
                            asset_id = result[0]
                            update_duration_ms = int((datetime.now() - asset_update_start).total_seconds() * 1000)
                            cursor.execute(
                                """
                                INSERT INTO price_update_log (asset_id, timestamp, price, success, error_message, duration_ms)
                                VALUES (%s, NOW(), %s, %s, %s, %s)
                                """,
                                (asset_id, None, False, error_msg[:500], update_duration_ms)  # Truncate error message
                            )
                            self.loader.conn.commit()
                        cursor.close()
                    except Exception as log_error:
                        # If logging fails, just continue
                        print(f"  ⚠ Failed to log error for {symbol}: {log_error}", flush=True)
            
            # Calculate total cycle duration
            cycle_duration = (datetime.now() - update_start_time).total_seconds()
            
            # Log cycle completion
            self.log_store.log(
                'INFO',
                'Price update cycle complete',
                {
                    'assets_updated': successful_updates,
                    'assets_failed': failed_updates,
                    'duration_seconds': cycle_duration
                }
            )
            
            print(f"✅ Price update complete: {successful_updates} successful, {failed_updates} failed", flush=True)
            
            # Trigger portfolio value update on successful completion
            if successful_updates > 0:
                self._trigger_portfolio_update()
            
        except Exception as e:
            # Log critical error
            error_msg = str(e)
            self.log_store.log(
                'ERROR',
                'Critical error during price update cycle',
                {'error': error_msg}
            )
            print(f"❌ Error updating prices: {error_msg}", flush=True)
            raise  # Re-raise to be caught by _price_update_loop
    
    def _trigger_portfolio_update(self):
        """Trigger portfolio value recalculation after successful price updates."""
        try:
            # Log portfolio update start
            self.log_store.log('INFO', 'Starting portfolio value recalculation')
            print("💼 Recalculating portfolio values...", flush=True)
            
            # Call portfolio calculator
            result = self.portfolio_calculator.recalculate_all_portfolios()
            
            # Log completion with results
            self.log_store.log(
                'INFO',
                'Portfolio value recalculation complete',
                {
                    'portfolios_processed': result['portfolios_processed'],
                    'portfolios_updated': result['portfolios_updated'],
                    'portfolios_failed': result['portfolios_failed']
                }
            )
            
            print(f"✅ Portfolio recalculation complete: {result['portfolios_updated']} updated, {result['portfolios_failed']} failed", flush=True)
            
            # Log any errors that occurred
            if result['errors']:
                for error in result['errors']:
                    self.log_store.log('WARNING', f'Portfolio calculation error: {error}')
            
        except Exception as e:
            # Log error but don't stop daemon
            error_msg = str(e)
            self.log_store.log(
                'ERROR',
                'Failed to trigger portfolio recalculation',
                {'error': error_msg}
            )
            print(f"❌ Portfolio recalculation failed: {error_msg}", flush=True)
            # Don't re-raise - daemon should continue running
    
    def _handle_notification(self, payload: str):
        """Handle transaction notification and backfill if needed."""
        try:
            data = json.loads(payload)
            asset_id = data['asset_id']
            
            # Check if asset needs backfill
            if self._needs_backfill(asset_id):
                self.log_store.log(
                    'INFO',
                    f'New asset detected, starting backfill',
                    {'asset_id': asset_id}
                )
                print(f"📥 New asset detected (ID: {asset_id}), starting backfill...", flush=True)
                self._backfill_asset(asset_id)
            
        except json.JSONDecodeError as e:
            # Log JSON parsing error
            self.log_store.log(
                'ERROR',
                'Failed to parse notification payload',
                {'error': str(e), 'payload': payload}
            )
            print(f"❌ Error parsing notification: {e}", flush=True)
        except Exception as e:
            # Log general error with context
            self.log_store.log(
                'ERROR',
                'Error handling notification',
                {'error': str(e), 'payload': payload}
            )
            print(f"❌ Error handling notification: {e}", flush=True)
    
    def _handle_manual_trigger(self, payload: str):
        """Handle manual price update trigger."""
        try:
            self.log_store.log('INFO', 'Manual price update triggered', {'payload': payload})
            print("🔄 Manual price update triggered...", flush=True)
            
            # Record cycle start
            cycle_id = self.stats_tracker.record_cycle_start()
            cycle_start_time = datetime.now()
            
            # Execute price update
            try:
                self._update_tracked_prices()
                
                # Calculate cycle duration
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                
                # Record successful cycle completion
                self.stats_tracker.record_cycle_end(cycle_id, success=True, duration=cycle_duration)
                
                # Persist statistics to database
                try:
                    self.stats_tracker.persist_statistics()
                except Exception as persist_error:
                    self.log_store.log(
                        'WARNING',
                        'Failed to persist statistics after manual trigger',
                        {'error': str(persist_error)}
                    )
                
                print("✅ Manual price update complete", flush=True)
                
            except Exception as e:
                # Calculate cycle duration even on failure
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                
                # Record failed cycle completion
                self.stats_tracker.record_cycle_end(cycle_id, success=False, duration=cycle_duration)
                
                # Persist statistics even on failure
                try:
                    self.stats_tracker.persist_statistics()
                except Exception as persist_error:
                    self.log_store.log(
                        'WARNING',
                        'Failed to persist statistics after failed manual trigger',
                        {'error': str(persist_error)}
                    )
                
                # Log error
                self.log_store.log(
                    'ERROR',
                    'Manual price update failed',
                    {'error': str(e), 'cycle_id': cycle_id, 'duration_seconds': cycle_duration}
                )
                print(f"❌ Manual price update failed: {e}", flush=True)
                
        except Exception as e:
            self.log_store.log(
                'ERROR',
                'Error handling manual trigger',
                {'error': str(e), 'payload': payload}
            )
            print(f"❌ Error handling manual trigger: {e}", flush=True)
    
    def _needs_backfill(self, asset_id: int) -> bool:
        """Check if asset has no price data."""
        try:
            cursor = self.loader.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM asset_prices WHERE asset_id = %s",
                (asset_id,)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            return count == 0
        except Exception as e:
            # Log database error
            self.log_store.log(
                'ERROR',
                'Error checking backfill status',
                {'asset_id': asset_id, 'error': str(e)}
            )
            # Return False to skip backfill on error
            return False
    
    def _backfill_asset(self, asset_id: int):
        """Fetch 1 year of historical data for asset."""
        try:
            cursor = self.loader.conn.cursor()
            cursor.execute(
                "SELECT symbol, asset_type FROM assets WHERE id = %s",
                (asset_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                self.log_store.log(
                    'WARNING',
                    'Asset not found for backfill',
                    {'asset_id': asset_id}
                )
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
                    
                    # Log successful backfill
                    self.log_store.log(
                        'INFO',
                        f'Backfill complete for {symbol}',
                        {'symbol': symbol, 'asset_id': asset_id, 'records_inserted': inserted}
                    )
                    print(f"✅ Backfilled {symbol}: {inserted} records", flush=True)
                    
                    # Add to tracked_assets with retry logic
                    retry_count = 0
                    max_retries = 1
                    
                    while retry_count <= max_retries:
                        try:
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
                            break  # Success, exit retry loop
                            
                        except psycopg2.Error as db_error:
                            cursor.close()
                            retry_count += 1
                            
                            if retry_count > max_retries:
                                # Log database error after retry
                                self.log_store.log(
                                    'ERROR',
                                    'Failed to add asset to tracked_assets after retry',
                                    {'symbol': symbol, 'asset_id': asset_id, 'error': str(db_error)}
                                )
                                print(f"❌ Failed to track {symbol}: {db_error}", flush=True)
                            else:
                                # Wait before retry
                                time.sleep(1)
                                self.log_store.log(
                                    'WARNING',
                                    'Retrying database operation',
                                    {'symbol': symbol, 'asset_id': asset_id, 'retry': retry_count}
                                )
                else:
                    # Log failed fetch
                    self.log_store.log(
                        'ERROR',
                        f'Failed to fetch historical data for {symbol}',
                        {'symbol': symbol, 'asset_id': asset_id}
                    )
                    print(f"❌ Failed to fetch data for {symbol}", flush=True)
                    
            except Exception as fetch_error:
                # Log fetcher error
                self.log_store.log(
                    'ERROR',
                    f'Error during backfill for {symbol}',
                    {'symbol': symbol, 'asset_id': asset_id, 'error': str(fetch_error)}
                )
                print(f"❌ Error backfilling {symbol}: {fetch_error}", flush=True)
                
        except Exception as e:
            # Log critical error
            self.log_store.log(
                'ERROR',
                'Critical error in backfill process',
                {'asset_id': asset_id, 'error': str(e)}
            )
            print(f"❌ Critical error in backfill: {e}", flush=True)


def main():
    import os
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    daemon = BackfillDaemon(db_url)
    daemon.listen()


if __name__ == "__main__":
    main()
