#!/usr/bin/env python3
"""
Command-line interface for the historical data backfill system.

This module provides a CLI for running the backfill operation with various
configuration options. It supports one-time execution, custom symbol lists,
date ranges, and force re-fetching of existing data.

Usage:
    python backfill_cli.py --once
    python backfill_cli.py --once --symbols AAPL MSFT GOOGL
    python backfill_cli.py --once --days 180 --force
    python backfill_cli.py --once --config custom_symbols.json --db postgresql://...
"""

import argparse
import sys
import os
import logging
from pathlib import Path

from backfill_orchestrator import BackfillOrchestrator
from log_store import setup_logging


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Historical data backfill system for stock price data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run one-time backfill with default settings (365 days, S&P 500)
  python backfill_cli.py --once
  
  # Backfill specific symbols only
  python backfill_cli.py --once --symbols AAPL MSFT GOOGL
  
  # Backfill 180 days of data instead of 365
  python backfill_cli.py --once --days 180
  
  # Force re-fetch existing data
  python backfill_cli.py --once --force
  
  # Use custom config file and database
  python backfill_cli.py --once --config /path/to/symbols.json --db postgresql://user:pass@host/db
        """
    )
    
    # Execution mode (Requirement 6.1, 6.2)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Run backfill once and exit'
    )
    mode_group.add_argument(
        '--scheduled',
        action='store_true',
        help='Run as daemon with scheduled backfills (not yet implemented)'
    )
    
    # Symbol selection (Requirement 6.4)
    parser.add_argument(
        '--symbols',
        nargs='+',
        metavar='SYMBOL',
        help='Specific symbols to backfill (e.g., AAPL MSFT GOOGL). If not specified, uses all symbols from config file.'
    )
    
    # Date range (Requirement 6.5)
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        metavar='N',
        help='Number of historical days to fetch (default: 365)'
    )
    
    # Force re-fetch (Requirement 9.4)
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch and overwrite existing data'
    )
    
    # Configuration file path
    parser.add_argument(
        '--config',
        type=str,
        default='sp500_symbols.json',
        metavar='PATH',
        help='Path to symbols configuration file (default: sp500_symbols.json)'
    )
    
    # Database connection string
    parser.add_argument(
        '--db',
        type=str,
        default=None,
        metavar='CONNECTION_STRING',
        help='PostgreSQL connection string (default: from DATABASE_URL env var or postgresql://postgres:postgres@localhost:5432/portfolio_tracker)'
    )
    
    # Logging level
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def get_database_url(args):
    """
    Get database connection string from arguments or environment.
    
    Priority:
    1. --db command-line argument
    2. DATABASE_URL environment variable
    3. Default connection string
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Database connection string
    """
    if args.db:
        return args.db
    
    return os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/portfolio_tracker'
    )


def get_config_path(args):
    """
    Get configuration file path, resolving relative paths.
    
    If the path is relative, it's resolved relative to the fetcher directory.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        str: Absolute path to configuration file
    """
    config_path = Path(args.config)
    
    # If path is relative, resolve it relative to the fetcher directory
    if not config_path.is_absolute():
        fetcher_dir = Path(__file__).parent
        config_path = fetcher_dir / config_path
    
    return str(config_path)


def create_custom_config(symbols, output_path):
    """
    Create a temporary configuration file for custom symbol list.
    
    When --symbols is specified, creates a temporary JSON config file
    with just those symbols.
    
    Args:
        symbols: List of stock symbols
        output_path: Path to write the config file
        
    Returns:
        str: Path to created config file
    """
    import json
    from datetime import date
    
    config = {
        "name": "Custom Symbol List",
        "last_updated": date.today().isoformat(),
        "symbols": symbols
    }
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return output_path


def run_once(args, db_url, config_path, logger):
    """
    Run backfill once and exit.
    
    Args:
        args: Parsed command-line arguments
        db_url: Database connection string
        config_path: Path to configuration file
        logger: Logger instance
    """
    logger.info("Starting one-time backfill operation")
    logger.info(f"Database: {db_url}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Days: {args.days}")
    logger.info(f"Force: {args.force}")
    
    try:
        # Create orchestrator
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=config_path
        )
        
        # If custom days specified, we need to modify the orchestrator's behavior
        # For now, we'll pass it through the run method
        # Note: The orchestrator's initialize_queue method accepts days parameter
        
        # Run the backfill
        orchestrator.run(force=args.force, days=args.days)
        
        logger.info("Backfill operation completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 1
    
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Backfill operation failed: {e}", exc_info=True)
        return 1


def run_scheduled(args, db_url, config_path, logger):
    """
    Run backfill as a scheduled daemon.
    
    This feature is not yet implemented and will be added in a future version.
    
    Args:
        args: Parsed command-line arguments
        db_url: Database connection string
        config_path: Path to configuration file
        logger: Logger instance
    """
    logger.error("Scheduled mode (--scheduled) is not yet implemented")
    logger.info("Please use --once for one-time execution")
    return 1


def main():
    """
    Main entry point for the CLI.
    
    Parses arguments, sets up logging, and executes the backfill operation.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    args = parse_arguments()
    
    # Get database URL
    db_url = get_database_url(args)
    
    # Setup logging (Requirement 7.6)
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(
        db_connection_string=db_url,
        log_level=log_level
    )
    
    logger.info("=" * 60)
    logger.info("Historical Data Backfill CLI")
    logger.info("=" * 60)
    
    # Handle custom symbol list (Requirement 6.4)
    if args.symbols:
        logger.info(f"Using custom symbol list: {', '.join(args.symbols)}")
        
        # Create temporary config file
        import tempfile
        temp_config = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        temp_config.close()
        
        config_path = create_custom_config(args.symbols, temp_config.name)
        cleanup_config = True
    else:
        config_path = get_config_path(args)
        cleanup_config = False
    
    try:
        # Execute based on mode
        if args.once:
            exit_code = run_once(args, db_url, config_path, logger)
        elif args.scheduled:
            exit_code = run_scheduled(args, db_url, config_path, logger)
        else:
            logger.error("No execution mode specified (use --once or --scheduled)")
            exit_code = 1
        
        return exit_code
        
    finally:
        # Cleanup temporary config file if created
        if cleanup_config:
            try:
                os.unlink(config_path)
                logger.debug(f"Cleaned up temporary config file: {config_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary config: {e}")


if __name__ == '__main__':
    sys.exit(main())
