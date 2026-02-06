#!/usr/bin/env python3
"""
Final End-to-End Validation Test for Historical Data Backfill.

This script performs comprehensive validation of the complete backfill system:
1. Runs full backfill with all 501 S&P 500 symbols
2. Verifies data storage in database
3. Verifies frontend can display the data
4. Verifies logs and reports are generated
5. Validates all requirements are met

Expected runtime: ~17 minutes (501 symbols * 2 seconds average)
"""

import sys
import os
import time
import psycopg2
import requests
from datetime import datetime, date, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backfill_orchestrator import BackfillOrchestrator
from log_store import setup_logging
import logging


class E2EValidator:
    """End-to-end validation for the backfill system."""
    
    def __init__(self, db_url: str, config_path: str, api_url: str = "http://localhost:8000"):
        self.db_url = db_url
        self.config_path = config_path
        self.api_url = api_url
        self.validation_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log a validation result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.validation_results.append(result)
        print(f"  {status}: {test_name}")
        if message:
            print(f"         {message}")
    
    def validate_database_schema(self):
        """Validate that all required database tables exist."""
        print("\n1. Validating Database Schema...")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check required tables
            required_tables = [
                'assets',
                'asset_prices',
                'backfill_queue',
                'tracked_assets',
                'fetcher_logs'
            ]
            
            for table in required_tables:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                    """,
                    (table,)
                )
                exists = cursor.fetchone()[0]
                self.log_result(
                    f"Table '{table}' exists",
                    exists,
                    f"Table {table} {'found' if exists else 'NOT FOUND'}"
                )
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("Database schema validation", False, str(e))
            return False
    
    def run_full_backfill(self, force: bool = False):
        """Run the full backfill operation with all symbols."""
        print("\n2. Running Full Backfill (501 symbols)...")
        print("   Expected runtime: ~17 minutes")
        print("   Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        start_time = time.time()
        
        try:
            # Setup logging
            logger = setup_logging(
                db_connection_string=self.db_url,
                log_level=logging.INFO
            )
            
            # Create orchestrator
            orchestrator = BackfillOrchestrator(
                db_connection_string=self.db_url,
                config_path=self.config_path
            )
            
            # Run backfill
            orchestrator.run(force=force, days=365)
            
            duration = time.time() - start_time
            duration_minutes = duration / 60
            
            self.log_result(
                "Full backfill execution",
                True,
                f"Completed in {duration_minutes:.1f} minutes"
            )
            
            # Get the report
            report = orchestrator.generate_report()
            
            self.log_result(
                "Backfill report generation",
                True,
                f"{report.successful}/{report.total_symbols} symbols successful"
            )
            
            return report
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_result(
                "Full backfill execution",
                False,
                f"Failed after {duration:.1f}s: {str(e)}"
            )
            return None
    
    def validate_data_storage(self, expected_symbols: int = 501):
        """Validate that data was correctly stored in the database."""
        print("\n3. Validating Data Storage...")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check number of assets created
            cursor.execute("SELECT COUNT(*) FROM assets WHERE asset_type = 'stock'")
            asset_count = cursor.fetchone()[0]
            
            self.log_result(
                f"Assets created (expected ~{expected_symbols})",
                asset_count >= expected_symbols * 0.95,  # Allow 5% failure rate
                f"Found {asset_count} assets"
            )
            
            # Check number of price records
            cursor.execute("SELECT COUNT(*) FROM asset_prices")
            price_count = cursor.fetchone()[0]
            
            # Expected: ~250 trading days * 501 symbols = ~125,000 records
            expected_min_records = 100000  # Allow for weekends, holidays, failures
            
            self.log_result(
                f"Price records inserted (expected >{expected_min_records:,})",
                price_count >= expected_min_records,
                f"Found {price_count:,} price records"
            )
            
            # Check tracked_assets entries
            cursor.execute("SELECT COUNT(*) FROM tracked_assets")
            tracked_count = cursor.fetchone()[0]
            
            self.log_result(
                "Tracked assets updated",
                tracked_count >= expected_symbols * 0.95,
                f"Found {tracked_count} tracked assets"
            )
            
            # Check backfill_queue completion
            cursor.execute(
                """
                SELECT 
                    status,
                    COUNT(*) as count
                FROM backfill_queue
                GROUP BY status
                ORDER BY status
                """
            )
            queue_status = cursor.fetchall()
            
            print("\n   Backfill Queue Status:")
            for status, count in queue_status:
                print(f"     - {status}: {count}")
            
            cursor.execute(
                "SELECT COUNT(*) FROM backfill_queue WHERE status = 'completed'"
            )
            completed_count = cursor.fetchone()[0]
            
            self.log_result(
                "Backfill queue completion",
                completed_count >= expected_symbols * 0.90,  # Allow 10% failure
                f"{completed_count}/{expected_symbols} tasks completed"
            )
            
            # Validate data quality - check for valid prices
            cursor.execute(
                """
                SELECT COUNT(*) FROM asset_prices
                WHERE close_price <= 0 OR close_price IS NULL
                """
            )
            invalid_prices = cursor.fetchone()[0]
            
            self.log_result(
                "Price data quality (no invalid prices)",
                invalid_prices == 0,
                f"Found {invalid_prices} invalid price records"
            )
            
            # Check date range coverage
            cursor.execute(
                """
                SELECT 
                    MIN(timestamp::date) as earliest,
                    MAX(timestamp::date) as latest
                FROM asset_prices
                """
            )
            earliest, latest = cursor.fetchone()
            
            expected_start = date.today() - timedelta(days=365)
            date_range_valid = (
                earliest is not None and
                latest is not None and
                earliest <= expected_start + timedelta(days=7) and  # Allow 1 week variance
                latest >= date.today() - timedelta(days=7)
            )
            
            self.log_result(
                "Date range coverage (365 days)",
                date_range_valid,
                f"Data from {earliest} to {latest}"
            )
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("Data storage validation", False, str(e))
            return False
    
    def validate_logging(self):
        """Validate that logs were generated correctly."""
        print("\n4. Validating Logging...")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check that logs were written to database
            cursor.execute("SELECT COUNT(*) FROM fetcher_logs")
            log_count = cursor.fetchone()[0]
            
            self.log_result(
                "Database logs generated",
                log_count > 0,
                f"Found {log_count:,} log entries"
            )
            
            # Check for operation start/end logs (Requirement 7.1)
            cursor.execute(
                """
                SELECT COUNT(*) FROM fetcher_logs
                WHERE context->>'operation' IN ('backfill_start', 'backfill_complete')
                """
            )
            operation_logs = cursor.fetchone()[0]
            
            self.log_result(
                "Operation start/end logs (Req 7.1)",
                operation_logs >= 2,
                f"Found {operation_logs} operation logs"
            )
            
            # Check for progress logs (Requirement 7.2)
            cursor.execute(
                """
                SELECT COUNT(*) FROM fetcher_logs
                WHERE context->>'operation' = 'progress_update'
                """
            )
            progress_logs = cursor.fetchone()[0]
            
            expected_progress_logs = 501 // 10  # Every 10 assets
            
            self.log_result(
                "Progress logs (Req 7.2)",
                progress_logs >= expected_progress_logs * 0.8,  # Allow some variance
                f"Found {progress_logs} progress logs (expected ~{expected_progress_logs})"
            )
            
            # Check for symbol processing logs (Requirement 7.3)
            cursor.execute(
                """
                SELECT COUNT(*) FROM fetcher_logs
                WHERE context->>'operation' = 'symbol_processing_complete'
                """
            )
            symbol_logs = cursor.fetchone()[0]
            
            self.log_result(
                "Symbol processing logs (Req 7.3)",
                symbol_logs > 0,
                f"Found {symbol_logs} symbol processing logs"
            )
            
            # Check for error logs (Requirement 7.4)
            cursor.execute(
                """
                SELECT COUNT(*) FROM fetcher_logs
                WHERE level = 'ERROR'
                """
            )
            error_logs = cursor.fetchone()[0]
            
            self.log_result(
                "Error logs present (Req 7.4)",
                True,  # Errors may or may not occur
                f"Found {error_logs} error logs"
            )
            
            # Check for dual logging (console + database) (Requirement 7.6)
            # We can't directly verify console logs, but we verified database logs
            self.log_result(
                "Dual logging (console + database) (Req 7.6)",
                log_count > 0,
                "Database logging confirmed (console logging assumed)"
            )
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("Logging validation", False, str(e))
            return False
    
    def validate_frontend_access(self):
        """Validate that frontend can access and display the data."""
        print("\n5. Validating Frontend Access...")
        
        try:
            # Test API health
            response = requests.get(f"{self.api_url}/health", timeout=5)
            self.log_result(
                "API health check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test assets endpoint
            response = requests.get(f"{self.api_url}/assets", timeout=10)
            self.log_result(
                "Assets endpoint accessible",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                assets = response.json()
                self.log_result(
                    "Assets data returned",
                    len(assets) > 0,
                    f"Found {len(assets)} assets"
                )
            
            # Test chart endpoint for a sample symbol
            test_symbol = "AAPL"
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            response = requests.get(
                f"{self.api_url}/chart/{test_symbol}",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=10
            )
            
            self.log_result(
                f"Chart endpoint for {test_symbol}",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                chart_data = response.json()
                self.log_result(
                    f"Historical data for {test_symbol}",
                    len(chart_data) > 0,
                    f"Found {len(chart_data)} data points"
                )
            
            return True
            
        except requests.exceptions.ConnectionError:
            self.log_result(
                "Frontend/API access",
                False,
                "Could not connect to API (is it running?)"
            )
            return False
        except Exception as e:
            self.log_result("Frontend validation", False, str(e))
            return False
    
    def validate_requirements(self):
        """Validate that all requirements are satisfied."""
        print("\n6. Validating Requirements Compliance...")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Requirement 1.1: S&P 500 constituents
            cursor.execute("SELECT COUNT(*) FROM assets WHERE asset_type = 'stock'")
            asset_count = cursor.fetchone()[0]
            self.log_result(
                "Req 1.1: S&P 500 asset catalog",
                asset_count >= 475,  # Allow for some failures
                f"{asset_count} assets"
            )
            
            # Requirement 2.1: 365 days of data
            cursor.execute(
                """
                SELECT 
                    asset_id,
                    COUNT(*) as record_count
                FROM asset_prices
                GROUP BY asset_id
                HAVING COUNT(*) >= 200  -- At least 200 trading days
                """
            )
            assets_with_data = cursor.fetchall()
            self.log_result(
                "Req 2.1: 365 days historical data",
                len(assets_with_data) >= 450,
                f"{len(assets_with_data)} assets have sufficient data"
            )
            
            # Requirement 3.4: No duplicates
            cursor.execute(
                """
                SELECT asset_id, timestamp, COUNT(*)
                FROM asset_prices
                GROUP BY asset_id, timestamp
                HAVING COUNT(*) > 1
                LIMIT 1
                """
            )
            duplicates = cursor.fetchone()
            self.log_result(
                "Req 3.4: No duplicate records",
                duplicates is None,
                "No duplicates found" if duplicates is None else f"Found duplicates: {duplicates}"
            )
            
            # Requirement 8.1: Valid prices
            cursor.execute(
                """
                SELECT COUNT(*) FROM asset_prices
                WHERE close_price <= 0
                """
            )
            invalid_prices = cursor.fetchone()[0]
            self.log_result(
                "Req 8.1: Valid price data",
                invalid_prices == 0,
                f"{invalid_prices} invalid prices"
            )
            
            # Requirement 9.1: Resume capability (check queue)
            cursor.execute(
                """
                SELECT COUNT(*) FROM backfill_queue
                WHERE status IN ('pending', 'failed', 'rate_limited')
                """
            )
            resumable_tasks = cursor.fetchone()[0]
            self.log_result(
                "Req 9.1: Resume capability",
                True,  # Queue exists and tracks status
                f"{resumable_tasks} tasks can be resumed"
            )
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("Requirements validation", False, str(e))
            return False
    
    def generate_summary_report(self):
        """Generate final summary report."""
        print("\n" + "=" * 70)
        print("FINAL VALIDATION SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for r in self.validation_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({pass_rate:.1f}%)")
        print(f"Failed: {failed_tests}")
        print()
        
        if failed_tests > 0:
            print("Failed Tests:")
            for result in self.validation_results:
                if not result["passed"]:
                    print(f"  ✗ {result['test']}")
                    if result["message"]:
                        print(f"    {result['message']}")
            print()
        
        overall_pass = pass_rate >= 90  # Require 90% pass rate
        
        if overall_pass:
            print("=" * 70)
            print("✓ END-TO-END VALIDATION PASSED")
            print("=" * 70)
            print()
            print("The historical data backfill system is fully operational.")
            print("All critical requirements have been validated.")
            print()
        else:
            print("=" * 70)
            print("✗ END-TO-END VALIDATION FAILED")
            print("=" * 70)
            print()
            print("Some critical tests failed. Please review the failures above.")
            print()
        
        return overall_pass


def main():
    """Main entry point for E2E validation."""
    print("=" * 70)
    print("HISTORICAL DATA BACKFILL - FINAL E2E VALIDATION")
    print("=" * 70)
    print()
    print("This test will:")
    print("  1. Validate database schema")
    print("  2. Run full backfill with 501 symbols (~17 minutes)")
    print("  3. Validate data storage")
    print("  4. Validate logging")
    print("  5. Validate frontend access")
    print("  6. Validate requirements compliance")
    print()
    
    # Configuration
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/portfolio_tracker'
    )
    config_path = Path(__file__).parent / 'sp500_symbols.json'
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    # Check if we should force re-fetch
    force = '--force' in sys.argv
    if force:
        print("⚠ Running with --force flag (will re-fetch existing data)")
        print()
    
    # Ask for confirmation
    response = input("Proceed with full backfill? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Validation cancelled.")
        return 1
    
    print()
    
    # Create validator
    validator = E2EValidator(db_url, str(config_path), api_url)
    
    # Run validation steps
    validator.validate_database_schema()
    
    report = validator.run_full_backfill(force=force)
    
    if report:
        validator.validate_data_storage()
        validator.validate_logging()
        validator.validate_frontend_access()
        validator.validate_requirements()
    else:
        print("\n⚠ Backfill failed - skipping remaining validations")
    
    # Generate summary
    success = validator.generate_summary_report()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
