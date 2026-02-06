#!/usr/bin/env python3
"""
Validation script for S&P 500 configuration file.
Validates JSON format, symbol count, uniqueness, and format.
"""
import json
import re

def validate_sp500_config(config_path='sp500_symbols.json'):
    """Validate the S&P 500 configuration file."""
    
    # Load and validate JSON
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        print("✓ Valid JSON file")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ File not found: {config_path}")
        return False
    
    # Check required fields
    required_fields = ['name', 'last_updated', 'symbols']
    for field in required_fields:
        if field not in data:
            print(f"✗ Missing required field: {field}")
            return False
    
    print(f"✓ Name: {data['name']}")
    print(f"✓ Last updated: {data['last_updated']}")
    
    # Check symbols
    symbols = data['symbols']
    print(f"✓ Total symbols in list: {len(symbols)}")
    
    # Check for duplicates
    unique_symbols = set(symbols)
    print(f"✓ Unique symbols: {len(unique_symbols)}")
    
    if len(symbols) != len(unique_symbols):
        duplicates = [s for s in unique_symbols if symbols.count(s) > 1]
        print(f"⚠ Warning: Duplicate symbols found: {duplicates}")
    else:
        print(f"✓ No duplicate symbols")
    
    # Validate symbol format (1-5 uppercase letters, optionally with dash)
    symbol_pattern = re.compile(r'^[A-Z]{1,5}(-[A-Z])?$')
    invalid_symbols = [s for s in symbols if not symbol_pattern.match(s)]
    
    if invalid_symbols:
        print(f"⚠ Warning: Invalid symbol formats: {invalid_symbols}")
    else:
        print(f"✓ All symbols have valid ticker format")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Configuration file validation: {'PASSED' if not invalid_symbols else 'PASSED WITH WARNINGS'}")
    print(f"{'='*50}")
    
    return True

if __name__ == '__main__':
    validate_sp500_config()
