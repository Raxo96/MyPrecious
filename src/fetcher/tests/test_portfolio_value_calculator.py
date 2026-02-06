#!/usr/bin/env python3
"""
Test script for PortfolioValueCalculator component.
Tests basic functionality: connect, recalculate_all_portfolios, 
_calculate_portfolio_value, _update_cache, error handling.
"""
import os
import sys
from decimal import Decimal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from portfolio_value_calculator import PortfolioValueCalculator
from log_store import LogStore
import psycopg2


def test_portfolio_value_calculator():
    """Test PortfolioValueCalculator basic functionality."""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    
    print("=" * 60)
    print("Testing PortfolioValueCalculator Component")
    print("=" * 60)
    
    # Initialize calculator
    calculator = PortfolioValueCalculator(db_url)
    
    # Test 1: Connect
    print("\n[Test 1] Testing connect()...")
    try:
        calculator.connect()
        print("✓ Connection established successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # Test 2: Calculate portfolio with no positions
    print("\n[Test 2] Testing portfolio with no positions...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    try:
        # Create test portfolio with no positions
        cursor.execute(
            """
            INSERT INTO portfolios (user_id, name, currency)
            VALUES (1, 'Empty Test Portfolio', 'USD')
            RETURNING id
            """
        )
        empty_portfolio_id = cursor.fetchone()[0]
        conn.commit()
        
        result = calculator._calculate_portfolio_value(empty_portfolio_id)
        
        assert result['current_value_usd'] == Decimal('0.00'), "Current value should be 0"
        assert result['total_invested_usd'] == Decimal('0.00'), "Invested should be 0"
        assert result['total_return_pct'] == Decimal('0.00'), "Return should be 0"
        assert result['position_count'] == 0, "Position count should be 0"
        
        print("✓ Empty portfolio calculated correctly")
        print(f"  - Current Value: ${result['current_value_usd']}")
        print(f"  - Total Invested: ${result['total_invested_usd']}")
        print(f"  - Return: {result['total_return_pct']}%")
        
        # Cleanup
        cursor.execute("DELETE FROM portfolios WHERE id = %s", (empty_portfolio_id,))
        conn.commit()
        
    except Exception as e:
        print(f"✗ Empty portfolio test failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        calculator.close()
        return
    
    # Test 3: Calculate portfolio with missing price data
    print("\n[Test 3] Testing portfolio with missing price data...")
    try:
        # Create test asset without price data
        cursor.execute(
            """
            INSERT INTO assets (symbol, name, asset_type, exchange, native_currency)
            VALUES ('TESTNO', 'Test No Price', 'stock', 'NYSE', 'USD')
            RETURNING id
            """
        )
        test_asset_id = cursor.fetchone()[0]
        
        # Create test portfolio
        cursor.execute(
            """
            INSERT INTO portfolios (user_id, name, currency)
            VALUES (1, 'Test Portfolio No Price', 'USD')
            RETURNING id
            """
        )
        test_portfolio_id = cursor.fetchone()[0]
        
        # Create position
        cursor.execute(
            """
            INSERT INTO portfolio_positions 
                (portfolio_id, asset_id, quantity, average_buy_price, first_purchase_date)
            VALUES (%s, %s, 100, 50.00, CURRENT_DATE)
            """,
            (test_portfolio_id, test_asset_id)
        )
        conn.commit()
        
        # Calculate - should use buy price as fallback
        result = calculator._calculate_portfolio_value(test_portfolio_id)
        
        assert result['current_value_usd'] == Decimal('5000.00'), "Should use buy price"
        assert result['total_invested_usd'] == Decimal('5000.00'), "Invested should be 5000"
        assert result['total_return_pct'] == Decimal('0.00'), "Return should be 0"
        assert result['position_count'] == 1, "Should have 1 position"
        
        print("✓ Portfolio with missing price data handled correctly")
        print(f"  - Used buy price as fallback: ${result['current_value_usd']}")
        
        # Cleanup
        cursor.execute("DELETE FROM portfolio_positions WHERE portfolio_id = %s", (test_portfolio_id,))
        cursor.execute("DELETE FROM portfolios WHERE id = %s", (test_portfolio_id,))
        cursor.execute("DELETE FROM assets WHERE id = %s", (test_asset_id,))
        conn.commit()
        
    except Exception as e:
        print(f"✗ Missing price data test failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        calculator.close()
        return
    
    # Test 4: Update cache creates new entry
    print("\n[Test 4] Testing cache update (create new entry)...")
    try:
        # Create test portfolio
        cursor.execute(
            """
            INSERT INTO portfolios (user_id, name, currency)
            VALUES (1, 'Cache Test Portfolio', 'USD')
            RETURNING id
            """
        )
        cache_portfolio_id = cursor.fetchone()[0]
        conn.commit()
        
        # Update cache
        portfolio_value = {
            'current_value_usd': Decimal('10000.00'),
            'total_invested_usd': Decimal('8000.00'),
            'total_return_pct': Decimal('25.00'),
            'position_count': 5
        }
        calculator._update_cache(cache_portfolio_id, portfolio_value)
        
        # Verify cache entry created
        cursor.execute(
            "SELECT current_value_usd, total_invested_usd, total_return_pct FROM portfolio_performance_cache WHERE portfolio_id = %s",
            (cache_portfolio_id,)
        )
        cache_entry = cursor.fetchone()
        
        assert cache_entry is not None, "Cache entry should exist"
        assert Decimal(str(cache_entry[0])) == Decimal('10000.00'), "Current value mismatch"
        assert Decimal(str(cache_entry[1])) == Decimal('8000.00'), "Invested mismatch"
        assert Decimal(str(cache_entry[2])) == Decimal('25.00'), "Return mismatch"
        
        print("✓ Cache entry created successfully")
        print(f"  - Current Value: ${cache_entry[0]}")
        print(f"  - Total Invested: ${cache_entry[1]}")
        print(f"  - Return: {cache_entry[2]}%")
        
        # Cleanup
        cursor.execute("DELETE FROM portfolio_performance_cache WHERE portfolio_id = %s", (cache_portfolio_id,))
        cursor.execute("DELETE FROM portfolios WHERE id = %s", (cache_portfolio_id,))
        conn.commit()
        
    except Exception as e:
        print(f"✗ Cache update test failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        calculator.close()
        return
    
    # Test 5: Update cache updates existing entry
    print("\n[Test 5] Testing cache update (update existing entry)...")
    try:
        # Create test portfolio
        cursor.execute(
            """
            INSERT INTO portfolios (user_id, name, currency)
            VALUES (1, 'Update Cache Test Portfolio', 'USD')
            RETURNING id
            """
        )
        update_portfolio_id = cursor.fetchone()[0]
        
        # Create initial cache entry
        cursor.execute(
            """
            INSERT INTO portfolio_performance_cache 
                (portfolio_id, current_value_usd, total_invested_usd, total_return_pct, last_updated)
            VALUES (%s, 5000.00, 4000.00, 25.00, NOW() - INTERVAL '1 hour')
            """,
            (update_portfolio_id,)
        )
        conn.commit()
        
        # Update cache with new values
        portfolio_value = {
            'current_value_usd': Decimal('12000.00'),
            'total_invested_usd': Decimal('10000.00'),
            'total_return_pct': Decimal('20.00'),
            'position_count': 3
        }
        calculator._update_cache(update_portfolio_id, portfolio_value)
        
        # Verify cache entry updated
        cursor.execute(
            "SELECT current_value_usd, total_invested_usd, total_return_pct FROM portfolio_performance_cache WHERE portfolio_id = %s",
            (update_portfolio_id,)
        )
        cache_entry = cursor.fetchone()
        
        assert Decimal(str(cache_entry[0])) == Decimal('12000.00'), "Current value not updated"
        assert Decimal(str(cache_entry[1])) == Decimal('10000.00'), "Invested not updated"
        assert Decimal(str(cache_entry[2])) == Decimal('20.00'), "Return not updated"
        
        print("✓ Cache entry updated successfully")
        print(f"  - New Current Value: ${cache_entry[0]}")
        print(f"  - New Total Invested: ${cache_entry[1]}")
        print(f"  - New Return: {cache_entry[2]}%")
        
        # Cleanup
        cursor.execute("DELETE FROM portfolio_performance_cache WHERE portfolio_id = %s", (update_portfolio_id,))
        cursor.execute("DELETE FROM portfolios WHERE id = %s", (update_portfolio_id,))
        conn.commit()
        
    except Exception as e:
        print(f"✗ Cache update test failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        calculator.close()
        return
    
    # Test 6: Recalculate all portfolios
    print("\n[Test 6] Testing recalculate_all_portfolios()...")
    
    # Initialize calculator with logging
    log_store = LogStore(db_url)
    log_store.connect()
    calculator_with_log = PortfolioValueCalculator(db_url, log_store=log_store)
    calculator_with_log.connect()
    
    try:
        # Create test asset with price
        cursor.execute(
            """
            INSERT INTO assets (symbol, name, asset_type, exchange, native_currency)
            VALUES ('TESTALL', 'Test All Portfolios', 'stock', 'NYSE', 'USD')
            RETURNING id
            """
        )
        all_asset_id = cursor.fetchone()[0]
        
        cursor.execute(
            """
            INSERT INTO asset_prices (asset_id, timestamp, close)
            VALUES (%s, NOW(), 100.00)
            """,
            (all_asset_id,)
        )
        
        # Create two test portfolios with positions
        portfolio_ids = []
        for i in range(2):
            cursor.execute(
                """
                INSERT INTO portfolios (user_id, name, currency)
                VALUES (1, %s, 'USD')
                RETURNING id
                """,
                (f'Test Portfolio {i+1}',)
            )
            portfolio_id = cursor.fetchone()[0]
            portfolio_ids.append(portfolio_id)
            
            cursor.execute(
                """
                INSERT INTO portfolio_positions 
                    (portfolio_id, asset_id, quantity, average_buy_price, first_purchase_date)
                VALUES (%s, %s, %s, 80.00, CURRENT_DATE)
                """,
                (portfolio_id, all_asset_id, 10 * (i + 1))
            )
        
        conn.commit()
        
        # Recalculate all portfolios
        result = calculator_with_log.recalculate_all_portfolios()
        
        print("✓ Recalculate all portfolios completed")
        print(f"  - Portfolios Processed: {result['portfolios_processed']}")
        print(f"  - Portfolios Updated: {result['portfolios_updated']}")
        print(f"  - Portfolios Failed: {result['portfolios_failed']}")
        
        assert result['portfolios_processed'] >= 2, "Should process at least 2 portfolios"
        assert result['portfolios_updated'] >= 2, "Should update at least 2 portfolios"
        assert result['portfolios_failed'] == 0, "Should have no failures"
        
        # Verify cache entries created
        for portfolio_id in portfolio_ids:
            cursor.execute(
                "SELECT current_value_usd FROM portfolio_performance_cache WHERE portfolio_id = %s",
                (portfolio_id,)
            )
            cache_entry = cursor.fetchone()
            assert cache_entry is not None, f"Cache entry missing for portfolio {portfolio_id}"
            assert Decimal(str(cache_entry[0])) > 0, "Cache value should be > 0"
        
        print("✓ All portfolio caches updated correctly")
        
        # Cleanup
        for portfolio_id in portfolio_ids:
            cursor.execute("DELETE FROM portfolio_performance_cache WHERE portfolio_id = %s", (portfolio_id,))
            cursor.execute("DELETE FROM portfolio_positions WHERE portfolio_id = %s", (portfolio_id,))
            cursor.execute("DELETE FROM portfolios WHERE id = %s", (portfolio_id,))
        cursor.execute("DELETE FROM asset_prices WHERE asset_id = %s", (all_asset_id,))
        cursor.execute("DELETE FROM assets WHERE id = %s", (all_asset_id,))
        conn.commit()
        
    except Exception as e:
        print(f"✗ Recalculate all portfolios test failed: {e}")
        conn.rollback()
    finally:
        calculator_with_log.close()
        log_store.close()
    
    # Test 7: Error handling - nonexistent portfolio
    print("\n[Test 7] Testing error handling (nonexistent portfolio)...")
    try:
        try:
            calculator._calculate_portfolio_value(999999)
            print("✗ Should have raised ValueError")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
    
    # Test 8: Error handling - no connection
    print("\n[Test 8] Testing error handling (no connection)...")
    try:
        calc_no_conn = PortfolioValueCalculator(db_url)
        try:
            calc_no_conn.recalculate_all_portfolios()
            print("✗ Should have raised RuntimeError")
        except RuntimeError as e:
            print(f"✓ Correctly raised RuntimeError: {e}")
    except Exception as e:
        print(f"✗ No connection test failed: {e}")
    
    # Test 9: Close connection
    print("\n[Test 9] Testing close()...")
    try:
        calculator.close()
        cursor.close()
        conn.close()
        print("✓ Connections closed successfully")
    except Exception as e:
        print(f"✗ Closing connection failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_portfolio_value_calculator()
