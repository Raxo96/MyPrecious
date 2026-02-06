"""
Unit tests for SymbolProcessor class.

Tests the orchestration of fetching, validation, and storage for a single symbol.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fetcher import PriceData, AssetData, StockFetcher
from db_loader import DatabaseLoader
from rate_limiter import RateLimiter
from data_validator import DataValidator, ValidationResult
from backfill_models import BackfillTask, ProcessingResult
from symbol_processor import SymbolProcessor


class TestSymbolProcessor:
    """Test suite for SymbolProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.fetcher = Mock(spec=StockFetcher)
        self.db_loader = Mock(spec=DatabaseLoader)
        self.rate_limiter = Mock(spec=RateLimiter)
        self.validator = Mock(spec=DataValidator)
        
        # Create processor with mocks
        self.processor = SymbolProcessor(
            self.fetcher,
            self.db_loader,
            self.rate_limiter,
            self.validator
        )
    
    def test_process_successful(self):
        """Test successful processing of a symbol."""
        # Create test task
        task = BackfillTask(
            id=1,
            asset_id=None,
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        # Create mock price data
        prices = [
            PriceData(
                timestamp="2024-01-15T10:00:00",
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=1000000
            )
        ]
        
        # Create mock asset data
        asset_data = AssetData(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD",
            prices=prices
        )
        
        # Configure mocks
        self.fetcher.fetch_historical.return_value = asset_data
        self.validator.validate_price_record.return_value = ValidationResult(
            valid=True,
            errors=[]
        )
        self.validator.calculate_completeness.return_value = 100.0
        self.db_loader.load_asset_prices.return_value = 1
        self.db_loader.conn = MagicMock()  # Mock database connection
        
        # Process the task
        result = self.processor.process(task)
        
        # Verify result
        assert result.success is True
        assert result.symbol == "AAPL"
        assert result.records_inserted == 1
        assert result.error_message is None
        
        # Verify rate limiter was called
        self.rate_limiter.wait_if_needed.assert_called_once()
        self.rate_limiter.record_request.assert_called_once()
        
        # Verify fetcher was called with correct parameters
        self.fetcher.fetch_historical.assert_called_once()
        
        # Verify validator was called
        self.validator.validate_price_record.assert_called_once()
        
        # Verify data was stored
        self.db_loader.load_asset_prices.assert_called_once()
        self.db_loader.update_tracked_asset_timestamp.assert_called_once_with("AAPL")
    
    def test_process_fetch_returns_none(self):
        """Test processing when fetcher returns None (invalid symbol or network error)."""
        task = BackfillTask(
            id=1,
            asset_id=None,
            symbol="INVALID",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        # Configure fetcher to return None
        self.fetcher.fetch_historical.return_value = None
        self.db_loader.conn = MagicMock()
        
        # Process the task
        result = self.processor.process(task)
        
        # Verify result indicates failure
        assert result.success is False
        assert result.symbol == "INVALID"
        assert result.records_inserted == 0
        assert result.error_message is not None
        assert "no data" in result.error_message.lower()
    
    def test_process_validation_filters_invalid_records(self):
        """Test that invalid records are filtered out during validation."""
        task = BackfillTask(
            id=1,
            asset_id=None,
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        # Create mix of valid and invalid price data
        prices = [
            PriceData(
                timestamp="2024-01-15T10:00:00",
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=1000000
            ),
            PriceData(
                timestamp="2024-01-16T10:00:00",
                open=100.0,
                high=105.0,
                low=99.0,
                close=-10.0,  # Invalid: negative price
                volume=1000000
            )
        ]
        
        asset_data = AssetData(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD",
            prices=prices
        )
        
        # Configure mocks
        self.fetcher.fetch_historical.return_value = asset_data
        
        # First price is valid, second is invalid
        self.validator.validate_price_record.side_effect = [
            ValidationResult(valid=True, errors=[]),
            ValidationResult(valid=False, errors=["Close price must be positive"])
        ]
        self.validator.calculate_completeness.return_value = 50.0
        self.db_loader.load_asset_prices.return_value = 1
        self.db_loader.conn = MagicMock()
        
        # Process the task
        result = self.processor.process(task)
        
        # Verify result
        assert result.success is True
        assert result.records_inserted == 1
        assert result.records_skipped == 1  # One invalid record skipped
        
        # Verify validator was called twice
        assert self.validator.validate_price_record.call_count == 2
    
    def test_process_database_error(self):
        """Test handling of database errors during storage."""
        task = BackfillTask(
            id=1,
            asset_id=None,
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        prices = [
            PriceData(
                timestamp="2024-01-15T10:00:00",
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=1000000
            )
        ]
        
        asset_data = AssetData(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD",
            prices=prices
        )
        
        # Configure mocks
        self.fetcher.fetch_historical.return_value = asset_data
        self.validator.validate_price_record.return_value = ValidationResult(
            valid=True,
            errors=[]
        )
        
        # Simulate database error
        import psycopg2
        self.db_loader.load_asset_prices.side_effect = psycopg2.Error("Connection failed")
        self.db_loader.conn = MagicMock()
        
        # Process the task
        result = self.processor.process(task)
        
        # Verify result indicates failure
        assert result.success is False
        assert result.records_inserted == 0
        assert "database error" in result.error_message.lower()
    
    def test_update_queue_status_completed(self):
        """Test updating queue status to completed."""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        self.db_loader.conn = MagicMock()
        self.db_loader.conn.cursor.return_value = mock_cursor
        
        # Update status
        self.processor.update_queue_status(1, 'completed')
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        
        # Verify completed_at is set
        assert 'completed_at' in sql.lower()
        assert 'NOW()' in sql
        
        # Verify commit was called
        self.db_loader.conn.commit.assert_called_once()
    
    def test_update_queue_status_failed(self):
        """Test updating queue status to failed with error message."""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        self.db_loader.conn = MagicMock()
        self.db_loader.conn.cursor.return_value = mock_cursor
        
        # Update status
        error_msg = "Network timeout"
        self.processor.update_queue_status(1, 'failed', error_msg)
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        # Verify attempts is incremented and error_message is set
        assert 'attempts' in sql.lower()
        assert 'error_message' in sql.lower()
        assert error_msg in params
        
        # Verify commit was called
        self.db_loader.conn.commit.assert_called_once()
    
    def test_update_queue_status_in_progress(self):
        """Test updating queue status to in_progress."""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        self.db_loader.conn = MagicMock()
        self.db_loader.conn.cursor.return_value = mock_cursor
        
        # Update status
        self.processor.update_queue_status(1, 'in_progress')
        
        # Verify SQL was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        # Verify status is set to in_progress
        assert 'in_progress' in params
        
        # Verify commit was called
        self.db_loader.conn.commit.assert_called_once()
    
    def test_process_no_valid_records(self):
        """Test processing when all records fail validation."""
        task = BackfillTask(
            id=1,
            asset_id=None,
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        # Create price data that will fail validation
        prices = [
            PriceData(
                timestamp="2024-01-15T10:00:00",
                open=100.0,
                high=105.0,
                low=99.0,
                close=-10.0,  # Invalid
                volume=1000000
            )
        ]
        
        asset_data = AssetData(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD",
            prices=prices
        )
        
        # Configure mocks
        self.fetcher.fetch_historical.return_value = asset_data
        self.validator.validate_price_record.return_value = ValidationResult(
            valid=False,
            errors=["Close price must be positive"]
        )
        self.validator.calculate_completeness.return_value = 0.0
        self.db_loader.conn = MagicMock()
        
        # Process the task
        result = self.processor.process(task)
        
        # Verify result - should still be successful but with no records inserted
        assert result.success is True
        assert result.records_inserted == 0
        assert result.records_skipped == 1
        
        # Verify load_asset_prices was not called (no valid records)
        self.db_loader.load_asset_prices.assert_not_called()
    
    def test_calculate_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        # Test backoff delays for attempts 1-5
        assert self.processor._calculate_backoff_delay(1) == 5
        assert self.processor._calculate_backoff_delay(2) == 10
        assert self.processor._calculate_backoff_delay(3) == 20
        assert self.processor._calculate_backoff_delay(4) == 40
        assert self.processor._calculate_backoff_delay(5) == 80


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
