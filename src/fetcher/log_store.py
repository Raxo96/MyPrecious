"""
Database logging handler for backfill operations.

This module provides a custom logging handler that writes log records
to the fetcher_logs database table, enabling dual logging to both
console and database as required by the specifications.
"""

import logging
import json
import psycopg2
from typing import Optional, Dict, Any
from datetime import datetime


class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes log records to the database.
    
    Writes to the fetcher_logs table with structured context information.
    Supports all standard Python logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    
    def __init__(self, db_connection_string: str):
        """
        Initialize the database log handler.
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        super().__init__()
        self.db_connection_string = db_connection_string
        self.conn: Optional[psycopg2.extensions.connection] = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.db_connection_string)
            self.conn.autocommit = True  # Auto-commit for logging
        except psycopg2.Error as e:
            # If we can't connect to the database, log to stderr but don't fail
            print(f"WARNING: Failed to connect to database for logging: {e}", flush=True)
            self.conn = None
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the database.
        
        Writes the log record to the fetcher_logs table with:
        - timestamp: When the log was created
        - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - message: Formatted log message
        - context: Additional structured data (symbol, task_id, etc.)
        
        Args:
            record: LogRecord to emit
        """
        if not self.conn:
            # Try to reconnect if connection was lost
            self._connect()
            if not self.conn:
                return  # Still can't connect, skip database logging
        
        try:
            # Extract context from the log record
            context = self._extract_context(record)
            
            # Format the message
            message = self.format(record)
            
            # Get the log level name
            level = record.levelname
            
            # Get timestamp from the record
            timestamp = datetime.fromtimestamp(record.created)
            
            # Insert into database
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO fetcher_logs (timestamp, level, message, context)
                VALUES (%s, %s, %s, %s)
                """,
                (timestamp, level, message, json.dumps(context) if context else None)
            )
            cursor.close()
            
        except psycopg2.Error as e:
            # If database write fails, don't crash - just print to stderr
            print(f"WARNING: Failed to write log to database: {e}", flush=True)
            # Try to reconnect for next time
            try:
                if self.conn:
                    self.conn.close()
            except:
                pass
            self.conn = None
        
        except Exception as e:
            # Catch any other errors to prevent logging from crashing the application
            print(f"WARNING: Unexpected error in database log handler: {e}", flush=True)
    
    def _extract_context(self, record: logging.LogRecord) -> Optional[Dict[str, Any]]:
        """
        Extract structured context from log record.
        
        Looks for custom attributes added to the log record:
        - symbol: Stock symbol being processed
        - task_id: Backfill task ID
        - asset_id: Asset database ID
        - duration: Operation duration
        - records_inserted: Number of records inserted
        - error_type: Type of error that occurred
        - Any other custom attributes
        
        Args:
            record: LogRecord to extract context from
            
        Returns:
            Dictionary of context data, or None if no context
        """
        context = {}
        
        # List of standard LogRecord attributes to exclude
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'getMessage', 'taskName'
        }
        
        # Extract custom attributes
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                # Convert non-serializable types to strings
                try:
                    json.dumps(value)
                    context[key] = value
                except (TypeError, ValueError):
                    context[key] = str(value)
        
        return context if context else None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
        super().close()


def setup_logging(
    db_connection_string: Optional[str] = None,
    log_level: int = logging.INFO,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the backfill system.
    
    Sets up dual logging to both console and database:
    - Console handler: Formatted output for human readability
    - Database handler: Structured logs in fetcher_logs table
    
    Args:
        db_connection_string: PostgreSQL connection string for database logging
        log_level: Minimum log level to capture (default: INFO)
        log_format: Custom log format string (optional)
        
    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Default log format with timestamp, level, module, and message
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create database handler if connection string provided
    if db_connection_string:
        try:
            db_handler = DatabaseLogHandler(db_connection_string)
            db_handler.setLevel(log_level)
            # Use same formatter for database logs
            db_formatter = logging.Formatter(log_format)
            db_handler.setFormatter(db_formatter)
            root_logger.addHandler(db_handler)
        except Exception as e:
            # If database handler fails to initialize, log warning but continue
            root_logger.warning(f"Failed to initialize database logging: {e}")
    
    return root_logger


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """
    Log a message with structured context.
    
    Convenience function for adding context to log messages.
    Context will be stored in the database for structured querying.
    
    Args:
        logger: Logger instance to use
        level: Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **context: Additional context as keyword arguments
        
    Example:
        log_with_context(
            logger, logging.INFO,
            "Processing complete",
            symbol="AAPL",
            records_inserted=252,
            duration=1.5
        )
    """
    # Extract exc_info if present (it's a special parameter for logger.log)
    exc_info = context.pop('exc_info', False)
    
    # Create a LogRecord with extra context
    extra = context
    logger.log(level, message, extra=extra, exc_info=exc_info)
