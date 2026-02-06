"""
PortfolioValueCalculator component for recalculating portfolio values.

This module provides the PortfolioValueCalculator class which handles:
- Recalculating portfolio values based on latest asset prices
- Updating the portfolio_performance_cache table
- Error handling and logging for portfolio calculations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal


class PortfolioValueCalculator:
    """
    Manages portfolio value recalculation and cache updates.
    
    The PortfolioValueCalculator queries portfolio positions, fetches latest
    prices, calculates current values, and updates the performance cache.
    """
    
    def __init__(self, db_url: str, log_store=None):
        """
        Initialize PortfolioValueCalculator with database connection string.
        
        Args:
            db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
            log_store: Optional LogStore instance for logging operations
        """
        self.db_url = db_url
        self.conn = None
        self.log_store = log_store
    
    def connect(self) -> None:
        """
        Establish database connection.
        
        Creates a new connection to PostgreSQL using the provided connection string.
        Should be called before any other operations.
        
        Raises:
            psycopg2.Error: If connection fails
        """
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.db_url)
    
    def close(self) -> None:
        """
        Close database connection.
        
        Safely closes the database connection if it exists and is open.
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def recalculate_all_portfolios(self) -> Dict:
        """
        Recalculate values for all portfolios and update cache.
        
        Iterates through all portfolios, calculates their current values based
        on latest asset prices, and updates the portfolio_performance_cache table.
        
        Returns:
            Dictionary with summary statistics:
            - portfolios_processed: Number of portfolios processed
            - portfolios_updated: Number of portfolios successfully updated
            - portfolios_failed: Number of portfolios that failed
            - errors: List of error messages for failed portfolios
        
        Raises:
            RuntimeError: If database is not connected
        """
        if not self.conn or self.conn.closed:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        start_time = datetime.now()
        result = {
            'portfolios_processed': 0,
            'portfolios_updated': 0,
            'portfolios_failed': 0,
            'errors': []
        }
        
        try:
            # Log start of recalculation
            if self.log_store:
                self.log_store.log('INFO', 'Starting portfolio value recalculation')
            
            # Get all portfolio IDs
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM portfolios ORDER BY id")
            portfolio_ids = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            # Process each portfolio
            for portfolio_id in portfolio_ids:
                result['portfolios_processed'] += 1
                
                try:
                    # Calculate portfolio value
                    portfolio_value = self._calculate_portfolio_value(portfolio_id)
                    
                    # Update cache
                    self._update_cache(portfolio_id, portfolio_value)
                    
                    result['portfolios_updated'] += 1
                    
                except Exception as e:
                    result['portfolios_failed'] += 1
                    error_msg = f"Portfolio {portfolio_id}: {str(e)}"
                    result['errors'].append(error_msg)
                    
                    # Log error but continue processing
                    if self.log_store:
                        self.log_store.log(
                            'ERROR',
                            f'Failed to recalculate portfolio {portfolio_id}',
                            {'portfolio_id': portfolio_id, 'error': str(e)}
                        )
            
            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            if self.log_store:
                self.log_store.log(
                    'INFO',
                    'Portfolio value recalculation complete',
                    {
                        'duration_seconds': duration,
                        'portfolios_processed': result['portfolios_processed'],
                        'portfolios_updated': result['portfolios_updated'],
                        'portfolios_failed': result['portfolios_failed']
                    }
                )
            
            return result
            
        except Exception as e:
            # Log critical error
            if self.log_store:
                self.log_store.log(
                    'ERROR',
                    'Critical error during portfolio recalculation',
                    {'error': str(e)}
                )
            raise
    
    def _calculate_portfolio_value(self, portfolio_id: int) -> Dict:
        """
        Calculate current value for a single portfolio.
        
        Queries portfolio positions, fetches latest prices for each asset,
        and calculates total portfolio value and performance metrics.
        
        Args:
            portfolio_id: ID of the portfolio to calculate
        
        Returns:
            Dictionary containing:
            - current_value_usd: Total current value in USD
            - total_invested_usd: Total amount invested (cost basis)
            - total_return_pct: Total return percentage
            - position_count: Number of positions in portfolio
        
        Raises:
            ValueError: If portfolio not found or has invalid data
            psycopg2.Error: If database operation fails
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get portfolio currency
            cursor.execute(
                "SELECT currency FROM portfolios WHERE id = %s",
                (portfolio_id,)
            )
            portfolio_row = cursor.fetchone()
            
            if not portfolio_row:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            portfolio_currency = portfolio_row['currency']
            
            # Get all positions for this portfolio
            cursor.execute(
                """
                SELECT 
                    pp.asset_id,
                    pp.quantity,
                    pp.average_buy_price,
                    a.symbol,
                    a.native_currency
                FROM portfolio_positions pp
                JOIN assets a ON pp.asset_id = a.id
                WHERE pp.portfolio_id = %s
                """,
                (portfolio_id,)
            )
            positions = cursor.fetchall()
            
            # If no positions, return zero values
            if not positions:
                return {
                    'current_value_usd': Decimal('0.00'),
                    'total_invested_usd': Decimal('0.00'),
                    'total_return_pct': Decimal('0.00'),
                    'position_count': 0
                }
            
            total_current_value = Decimal('0.00')
            total_invested = Decimal('0.00')
            
            # Calculate value for each position
            for position in positions:
                asset_id = position['asset_id']
                quantity = Decimal(str(position['quantity']))
                avg_buy_price = Decimal(str(position['average_buy_price']))
                
                # Get latest price for this asset
                cursor.execute(
                    """
                    SELECT close
                    FROM asset_prices
                    WHERE asset_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (asset_id,)
                )
                price_row = cursor.fetchone()
                
                if not price_row or price_row['close'] is None:
                    # No price data available - use average buy price as fallback
                    current_price = avg_buy_price
                else:
                    current_price = Decimal(str(price_row['close']))
                
                # Calculate position values (assuming USD for now)
                position_current_value = quantity * current_price
                position_invested = quantity * avg_buy_price
                
                total_current_value += position_current_value
                total_invested += position_invested
            
            # Calculate return percentage
            if total_invested > 0:
                total_return_pct = ((total_current_value - total_invested) / total_invested) * 100
            else:
                total_return_pct = Decimal('0.00')
            
            return {
                'current_value_usd': total_current_value,
                'total_invested_usd': total_invested,
                'total_return_pct': total_return_pct,
                'position_count': len(positions)
            }
            
        finally:
            cursor.close()
    
    def _update_cache(self, portfolio_id: int, portfolio_value: Dict) -> None:
        """
        Update portfolio_performance_cache table with calculated values.
        
        Inserts or updates the cache entry for the specified portfolio with
        the calculated performance metrics. The transaction is committed
        immediately to ensure atomicity.
        
        Args:
            portfolio_id: ID of the portfolio to update
            portfolio_value: Dictionary with calculated values from _calculate_portfolio_value
        
        Raises:
            psycopg2.Error: If database operation fails
        """
        cursor = self.conn.cursor()
        
        try:
            # Use INSERT ... ON CONFLICT to upsert the cache entry
            cursor.execute(
                """
                INSERT INTO portfolio_performance_cache 
                    (portfolio_id, current_value_usd, total_invested_usd, total_return_pct, last_updated)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (portfolio_id) 
                DO UPDATE SET
                    current_value_usd = EXCLUDED.current_value_usd,
                    total_invested_usd = EXCLUDED.total_invested_usd,
                    total_return_pct = EXCLUDED.total_return_pct,
                    last_updated = EXCLUDED.last_updated
                """,
                (
                    portfolio_id,
                    portfolio_value['current_value_usd'],
                    portfolio_value['total_invested_usd'],
                    portfolio_value['total_return_pct']
                )
            )
            
            # Commit immediately for atomicity
            self.conn.commit()
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise
        finally:
            cursor.close()
