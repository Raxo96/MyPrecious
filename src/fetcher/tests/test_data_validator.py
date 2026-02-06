"""
Unit tests for DataValidator class.

Tests validation logic for price records including required fields,
value constraints, and OHLC consistency.
"""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fetcher import PriceData
from data_validator import DataValidator, ValidationResult


class TestDataValidator:
    """Test suite for DataValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_valid_price_record(self):
        """Test validation of a valid price record."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_missing_timestamp(self):
        """Test validation fails when timestamp is missing."""
        price = PriceData(
            timestamp=None,
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert "Missing timestamp" in result.errors
    
    def test_missing_close_price(self):
        """Test validation fails when close price is missing."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=None,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert "Missing close price" in result.errors
    
    def test_missing_volume(self):
        """Test validation fails when volume is missing."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=None
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert "Missing volume" in result.errors
    
    def test_negative_close_price(self):
        """Test validation fails when close price is negative."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=-10.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("positive" in error.lower() for error in result.errors)
    
    def test_zero_close_price(self):
        """Test validation fails when close price is zero."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=0.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("positive" in error.lower() for error in result.errors)
    
    def test_negative_volume(self):
        """Test validation fails when volume is negative."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=-1000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("non-negative" in error.lower() for error in result.errors)
    
    def test_invalid_timestamp_format(self):
        """Test validation fails when timestamp format is invalid."""
        price = PriceData(
            timestamp="not-a-valid-timestamp",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("timestamp" in error.lower() for error in result.errors)
    
    def test_ohlc_consistency_valid(self):
        """Test OHLC consistency validation with valid data."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        is_consistent = self.validator.validate_ohlc_consistency(price)
        
        assert is_consistent is True
    
    def test_ohlc_high_less_than_low(self):
        """Test OHLC validation fails when high < low."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=95.0,  # Invalid: high < low
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("high" in error.lower() and "low" in error.lower() for error in result.errors)
    
    def test_ohlc_high_less_than_open(self):
        """Test OHLC validation fails when high < open."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=110.0,
            high=105.0,  # Invalid: high < open
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("high" in error.lower() and "open" in error.lower() for error in result.errors)
    
    def test_ohlc_high_less_than_close(self):
        """Test OHLC validation fails when high < close."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=102.0,  # Invalid: high < close
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("high" in error.lower() and "close" in error.lower() for error in result.errors)
    
    def test_ohlc_low_greater_than_open(self):
        """Test OHLC validation fails when low > open."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=98.0,
            high=105.0,
            low=99.0,  # Invalid: low > open
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("low" in error.lower() and "open" in error.lower() for error in result.errors)
    
    def test_ohlc_low_greater_than_close(self):
        """Test OHLC validation fails when low > close."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=100.0,
            high=105.0,
            low=104.0,  # Invalid: low > close
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        assert any("low" in error.lower() and "close" in error.lower() for error in result.errors)
    
    def test_ohlc_with_none_values(self):
        """Test OHLC validation skips when values are None."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=None,
            high=None,
            low=None,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        # Should be valid since OHLC validation is skipped for None values
        assert result.valid is True
    
    def test_ohlc_with_zero_values(self):
        """Test OHLC validation skips when values are zero."""
        price = PriceData(
            timestamp="2024-01-15T10:00:00",
            open=0,
            high=0,
            low=0,
            close=103.0,
            volume=1000000
        )
        
        result = self.validator.validate_price_record(price)
        
        # Should be valid since OHLC validation is skipped for zero values
        assert result.valid is True
    
    def test_calculate_completeness_full(self):
        """Test completeness calculation with 100% data."""
        completeness = self.validator.calculate_completeness(
            expected_days=252,
            actual_records=252
        )
        
        assert completeness == 100.0
    
    def test_calculate_completeness_partial(self):
        """Test completeness calculation with partial data."""
        completeness = self.validator.calculate_completeness(
            expected_days=252,
            actual_records=200
        )
        
        expected = (200 / 252) * 100
        assert abs(completeness - expected) < 0.01
    
    def test_calculate_completeness_over_100(self):
        """Test completeness calculation caps at 100%."""
        completeness = self.validator.calculate_completeness(
            expected_days=252,
            actual_records=300
        )
        
        # Should cap at 100%
        assert completeness == 100.0
    
    def test_calculate_completeness_zero_expected(self):
        """Test completeness calculation with zero expected days."""
        completeness = self.validator.calculate_completeness(
            expected_days=0,
            actual_records=100
        )
        
        assert completeness == 0.0
    
    def test_calculate_completeness_negative_expected(self):
        """Test completeness calculation with negative expected days."""
        completeness = self.validator.calculate_completeness(
            expected_days=-10,
            actual_records=100
        )
        
        assert completeness == 0.0
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are captured."""
        price = PriceData(
            timestamp="invalid-timestamp",
            open=110.0,
            high=95.0,  # Invalid: high < low and high < open
            low=99.0,
            close=-10.0,  # Invalid: negative
            volume=-1000  # Invalid: negative
        )
        
        result = self.validator.validate_price_record(price)
        
        assert result.valid is False
        # Should have multiple errors
        assert len(result.errors) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
