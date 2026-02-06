# Fetcher Module Tests

This directory contains all test files for the fetcher module components.

## Test Files

### Component Tests

- **test_log_store.py** - Basic functionality tests for LogStore component
- **test_log_store_comprehensive.py** - Comprehensive validation of LogStore requirements (4.1-4.5)
- **test_statistics_tracker.py** - Tests for StatisticsTracker component
- **test_portfolio_value_calculator.py** - Tests for PortfolioValueCalculator component

### Integration Tests

- **test_price_update.py** - Manual trigger for price update testing

## Running Tests

All tests can be run directly as Python scripts:

```bash
# Run individual test
python src/fetcher/tests/test_log_store.py

# Run from tests directory
cd src/fetcher/tests
python test_log_store.py

# Run comprehensive validation
python src/fetcher/tests/test_log_store_comprehensive.py
```

## Test Requirements

- PostgreSQL database running at `localhost:5432`
- Database name: `portfolio_tracker`
- Default credentials: `postgres:postgres`
- Can be overridden with `DATABASE_URL` environment variable

## Test Structure

Each test file follows this pattern:

1. Import required modules with proper path handling
2. Define test functions for each component method
3. Create test data and verify behavior
4. Clean up test data after each test
5. Print clear pass/fail indicators

## Adding New Tests

When creating new test files:

1. Place them in this `src/fetcher/tests/` directory
2. Use the naming convention `test_<component_name>.py`
3. Add proper path handling for imports:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
   ```
4. Follow the existing test structure and output format
5. Include cleanup code to remove test data
6. Update this README with the new test file description
