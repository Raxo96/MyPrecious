"""
Example script demonstrating the logging infrastructure.

This script shows how to set up and use the dual logging system
(console + database) for the backfill operations.
"""

import logging
import os
from log_store import setup_logging, log_with_context


def main():
    """Demonstrate logging infrastructure usage."""
    
    # Get database connection string from environment or use default
    db_connection_string = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/portfolio_tracker'
    )
    
    # Setup logging with both console and database handlers
    print("Setting up logging infrastructure...")
    logger = setup_logging(
        db_connection_string=db_connection_string,
        log_level=logging.INFO
    )
    
    print("Logging infrastructure initialized.")
    print("Logs will be written to both console and database (fetcher_logs table).")
    print("-" * 60)
    
    # Example 1: Simple logging
    logger.info("This is a simple info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("-" * 60)
    
    # Example 2: Logging with structured context
    print("\nLogging with structured context:")
    log_with_context(
        logger, logging.INFO,
        "Processing symbol AAPL",
        symbol="AAPL",
        task_id=123,
        operation="fetch_data"
    )
    
    log_with_context(
        logger, logging.INFO,
        "Completed processing for AAPL",
        symbol="AAPL",
        task_id=123,
        operation="processing_complete",
        records_inserted=252,
        duration_seconds=1.5,
        completeness_pct=98.5
    )
    
    print("-" * 60)
    
    # Example 3: Error logging with context
    print("\nLogging errors with context:")
    try:
        # Simulate an error
        raise ValueError("Example error for demonstration")
    except Exception as e:
        log_with_context(
            logger, logging.ERROR,
            f"Error occurred: {str(e)}",
            operation="error_example",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
    
    print("-" * 60)
    print("\nLogging examples complete!")
    print("Check the console output above and the fetcher_logs table in the database.")
    print("\nTo query logs from database:")
    print("  SELECT * FROM fetcher_logs ORDER BY timestamp DESC LIMIT 10;")
    print("\nTo query logs with context:")
    print("  SELECT timestamp, level, message, context FROM fetcher_logs")
    print("  WHERE context->>'symbol' = 'AAPL' ORDER BY timestamp DESC;")


if __name__ == "__main__":
    main()
