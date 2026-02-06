"""
Comprehensive integration tests for database logging.

These tests verify that logging works correctly with a real database connection
and that logs are properly written to both console and database.
"""

import pytest
import logging
import psycopg2
import os
from datetime import datetime
from log_store import DatabaseLogHandler, setup_logging, log_with_context


# Skip these tests if no database connection is available
DB_CONNECTION_STRING = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/portfolio_tracker'
)


def check_database_available():
    """Check if database is available for testing."""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.close()
        return True
    except psycopg2.Error:
        return False


@pytest.mark.skipif(
    not check_database_available(),
    reason="Database not available for integration testing"
)
class TestDatabaseLogHandlerIntegration:
    """Integration tests for DatabaseLogHandler with real database."""
    
    def test_emit_to_database(self):
        """Test that log records are written to the database."""
        # Create handler with real database connection
        handler = DatabaseLogHandler(DB_CONNECTION_STRING)
        
        # Verify connection was established
        assert handler.conn is not None
        
        # Create logger and add handler
        logger = logging.getLogger("test_emit")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Log a test message
        test_message = f"Test log message at {datetime.now().isoformat()}"
        logger.info(test_message)
        
        # Query database to verify log was written
        cursor = handler.conn.cursor()
        cursor.execute(
            """
            SELECT message, level FROM fetcher_logs
            WHERE message LIKE %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (f"%{test_message}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        
        # Verify log was written
        assert result is not None
        assert test_message in result[0]
        assert result[1] == "INFO"
        
        # Clean up
        logger.removeHandler(handler)
        handler.close()
    
    def test_emit_with_context(self):
        """Test that context is properly stored in database."""
        # Create handler with real database connection
        handler = DatabaseLogHandler(DB_CONNECTION_STRING)
        
        # Create logger and add handler
        logger = logging.getLogger("test_context")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Log with context
        test_message = f"Test context log at {datetime.now().isoformat()}"
        log_with_context(
            logger, logging.INFO,
            test_message,
            symbol="AAPL",
            task_id=12345,
            duration=1.5
        )
        
        # Query database to verify log and context were written
        cursor = handler.conn.cursor()
        cursor.execute(
            """
            SELECT message, level, context FROM fetcher_logs
            WHERE message LIKE %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (f"%{test_message}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        
        # Verify log was written
        assert result is not None
        assert test_message in result[0]
        assert result[1] == "INFO"
        
        # Verify context was stored
        context = result[2]
        assert context is not None
        assert context["symbol"] == "AAPL"
        assert context["task_id"] == 12345
        assert context["duration"] == 1.5
        
        # Clean up
        logger.removeHandler(handler)
        handler.close()
    
    def test_emit_different_log_levels(self):
        """Test that different log levels are properly recorded."""
        # Create handler with real database connection
        handler = DatabaseLogHandler(DB_CONNECTION_STRING)
        
        # Create logger and add handler
        logger = logging.getLogger("test_levels")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        # Log messages at different levels
        timestamp = datetime.now().isoformat()
        logger.debug(f"Debug message {timestamp}")
        logger.info(f"Info message {timestamp}")
        logger.warning(f"Warning message {timestamp}")
        logger.error(f"Error message {timestamp}")
        
        # Query database to verify all levels were written
        cursor = handler.conn.cursor()
        cursor.execute(
            """
            SELECT level, COUNT(*) FROM fetcher_logs
            WHERE message LIKE %s
            GROUP BY level
            ORDER BY level
            """,
            (f"%{timestamp}%",)
        )
        results = cursor.fetchall()
        cursor.close()
        
        # Verify all levels were recorded
        levels = {row[0]: row[1] for row in results}
        assert "DEBUG" in levels
        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels
        
        # Clean up
        logger.removeHandler(handler)
        handler.close()
    
    def test_dual_logging(self):
        """Test that logs appear in both console and database."""
        # Setup logging with both console and database handlers
        logger = setup_logging(
            db_connection_string=DB_CONNECTION_STRING,
            log_level=logging.INFO
        )
        
        # Verify both handlers are present
        assert len(logger.handlers) >= 2
        
        # Find the database handler
        db_handler = None
        for handler in logger.handlers:
            if isinstance(handler, DatabaseLogHandler):
                db_handler = handler
                break
        
        assert db_handler is not None
        assert db_handler.conn is not None
        
        # Log a test message
        test_message = f"Dual logging test at {datetime.now().isoformat()}"
        logger.info(test_message)
        
        # Query database to verify log was written
        cursor = db_handler.conn.cursor()
        cursor.execute(
            """
            SELECT message FROM fetcher_logs
            WHERE message LIKE %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (f"%{test_message}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        
        # Verify log was written to database
        assert result is not None
        assert test_message in result[0]
        
        # Clean up
        logger.handlers.clear()


@pytest.mark.skipif(
    not check_database_available(),
    reason="Database not available for integration testing"
)
class TestLoggingInfrastructure:
    """Integration tests for complete logging infrastructure."""
    
    def test_setup_logging_creates_table_entries(self):
        """Test that setup_logging properly initializes logging infrastructure."""
        # Setup logging
        logger = setup_logging(
            db_connection_string=DB_CONNECTION_STRING,
            log_level=logging.INFO
        )
        
        # Log some test messages
        timestamp = datetime.now().isoformat()
        logger.info(f"Infrastructure test 1 {timestamp}")
        logger.warning(f"Infrastructure test 2 {timestamp}")
        logger.error(f"Infrastructure test 3 {timestamp}")
        
        # Find database handler
        db_handler = None
        for handler in logger.handlers:
            if isinstance(handler, DatabaseLogHandler):
                db_handler = handler
                break
        
        assert db_handler is not None
        
        # Query database to verify logs were written
        cursor = db_handler.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM fetcher_logs
            WHERE message LIKE %s
            """,
            (f"%{timestamp}%",)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        # Should have at least 3 log entries
        assert count >= 3
        
        # Clean up
        logger.handlers.clear()
