"""
Data validation module for historical price data.

This module provides validation functionality for price records to ensure
data quality before storage in the database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from fetcher import PriceData


@dataclass
class ValidationResult:
    """Result of data validation."""
    valid: bool
    errors: List[str]


class DataValidator:
    """
    Validates quality of fetched price data.
    
    Ensures that price records meet all quality requirements including:
    - Required fields are present
    - Values are within valid ranges
    - OHLC relationships are consistent
    """
    
    def validate_price_record(self, price: PriceData) -> ValidationResult:
        """
        Validate a single price record.
        
        Checks:
        - Required fields (timestamp, close, volume) are present
        - Close price is positive
        - Volume is non-negative
        - Timestamp is valid
        
        Args:
            price: PriceData object to validate
            
        Returns:
            ValidationResult indicating pass/fail and any errors
        """
        errors = []
        
        # Check required fields are present
        if not price.timestamp:
            errors.append("Missing timestamp")
        
        if price.close is None:
            errors.append("Missing close price")
        
        if price.volume is None:
            errors.append("Missing volume")
        
        # If required fields are missing, return early
        if errors:
            return ValidationResult(valid=False, errors=errors)
        
        # Validate close price is positive (Requirement 8.1)
        if price.close <= 0:
            errors.append(f"Close price must be positive, got {price.close}")
        
        # Validate volume is non-negative (Requirement 8.3)
        if price.volume < 0:
            errors.append(f"Volume must be non-negative, got {price.volume}")
        
        # Validate timestamp format and parsability (Requirement 8.2)
        try:
            datetime.fromisoformat(price.timestamp)
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid timestamp format: {price.timestamp} - {str(e)}")
        
        # Validate OHLC consistency if OHLC values are present (Requirement 8.4)
        if price.open is not None and price.high is not None and price.low is not None:
            ohlc_errors = self._validate_ohlc_consistency(price)
            errors.extend(ohlc_errors)
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    
    def validate_ohlc_consistency(self, price: PriceData) -> bool:
        """
        Validate OHLC price consistency.
        
        Verifies that:
        - high >= low
        - high >= open
        - high >= close
        - low <= open
        - low <= close
        
        Args:
            price: PriceData object to validate
            
        Returns:
            True if consistent, False otherwise
        """
        errors = self._validate_ohlc_consistency(price)
        return len(errors) == 0
    
    def _validate_ohlc_consistency(self, price: PriceData) -> List[str]:
        """
        Internal method to validate OHLC consistency and return error messages.
        
        Args:
            price: PriceData object to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Skip validation if any OHLC value is None or 0
        if price.open is None or price.high is None or price.low is None:
            return errors
        
        if price.open == 0 or price.high == 0 or price.low == 0:
            return errors
        
        # Requirement 8.4: Validate OHLC relationships
        if price.high < price.low:
            errors.append(f"High ({price.high}) must be >= low ({price.low})")
        
        if price.high < price.open:
            errors.append(f"High ({price.high}) must be >= open ({price.open})")
        
        if price.high < price.close:
            errors.append(f"High ({price.high}) must be >= close ({price.close})")
        
        if price.low > price.open:
            errors.append(f"Low ({price.low}) must be <= open ({price.open})")
        
        if price.low > price.close:
            errors.append(f"Low ({price.low}) must be <= close ({price.close})")
        
        return errors
    
    def calculate_completeness(self, expected_days: int, actual_records: int) -> float:
        """
        Calculate data completeness percentage.
        
        Args:
            expected_days: Expected number of trading days
            actual_records: Actual number of records received
            
        Returns:
            Completeness percentage (0-100)
        """
        if expected_days <= 0:
            return 0.0
        
        # Calculate percentage and cap at 100%
        completeness = (actual_records / expected_days) * 100.0
        return min(completeness, 100.0)
