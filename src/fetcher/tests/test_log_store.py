"""
Tests for the database logging infrastructure.

This module tests the DatabaseLogHandler and logging setup functionality.
"""

import pytest
import logging
import psycopg2
from datetime import datetime
from log_store import DatabaseLogHandler, setup_logging, log_with_context


class TestDatabaseLogHandler:
    """Tests for DatabaseLogHandler class."""
    
    def test_handler_initialization_with_invalid_connection(self):
        """Test that handler gracefully handles invalid database connection."""
        # Use invalid connection string
        handler = DatabaseLogHandler("postgresql://invalid:invalid@localhost:5432/invalid")
        
        # Handler should be created but connection should be None
        assert handler.conn is None
    
    def test_emit_without_connection(self):
        """Test that emit() doesn't crash when database is unavailable."""
        handler = DatabaseLogHandler("postgresql://invalid:invalid@localhost:5432/invalid")
        
        # Create a log record
        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # This should not raise an exception
        logger.info("Test message")
        
        # Clean up
        logger.removeHandler(handler)
        handler.close()
    
    def test_extract_context(self):
        """Test that context extraction works correctly."""
        handler = DatabaseLogHandler("postgresql://invalid:invalid@localhost:5432/invalid")
        
        # Create a log record with custom attributes
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add custom attributes
        record.symbol = "AAPL"
        record.task_id = 123
        record.duration = 1.5
        
        # Extract context
        context = handler._extract_context(record)
        
        # Verify context contains custom attributes
        assert context is not None
        assert context["symbol"] == "AAPL"
        assert context["task_id"] == 123
        assert context["duration"] == 1.5
        
        # Verify standard attributes are excluded
        assert "name" not in context
        assert "msg" not in context
        assert "pathname" not in context
        
        handler.close()
    
    def test_extract_context_empty(self):
        """Test that extract_context returns None when no custom attributes."""
        handler = DatabaseLogHandler("postgresql://invalid:invalid@localhost:5432/invalid")
        
        # Create a log record without custom attributes
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Extract context
        context = handler._extract_context(record)
        
        # Should return None or empty dict
        assert context is None or len(context) == 0
        
        handler.close()


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_console_only(self):
        """Test that setup_logging creates console handler."""
        logger = setup_logging(db_connection_string=None, log_level=logging.INFO)
        
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1
        
        # First handler should be StreamHandler
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        
        # Clean up
        logger.handlers.clear()
    
    def test_setup_logging_with_database(self):
        """Test that setup_logging creates both console and database handlers."""
        # Use invalid connection to test handler creation without actual database
        logger = setup_logging(
            db_connection_string="postgresql://invalid:invalid@localhost:5432/invalid",
            log_level=logging.INFO
        )
        
        # Should have at least one handler (console, database may fail gracefully)
        assert len(logger.handlers) >= 1
        
        # Clean up
        logger.handlers.clear()
    
    def test_setup_logging_custom_format(self):
        """Test that setup_logging accepts custom log format."""
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logging(
            db_connection_string=None,
            log_level=logging.DEBUG,
            log_format=custom_format
        )
        
        # Verify handler has custom format
        assert len(logger.handlers) >= 1
        handler = logger.handlers[0]
        assert handler.formatter is not None
        
        # Clean up
        logger.handlers.clear()


class TestLogWithContext:
    """Tests for log_with_context function."""
    
    def test_log_with_context_adds_attributes(self):
        """Test that log_with_context adds context as attributes."""
        # Create a test logger with a custom handler that captures records
        logger = logging.getLogger("test_context")
        logger.setLevel(logging.INFO)
        
        # Create a handler that captures log records
        captured_records = []
        
        class CaptureHandler(logging.Handler):
            def emit(self, record):
                captured_records.append(record)
        
        handler = CaptureHandler()
        logger.addHandler(handler)
        
        # Log with context
        log_with_context(
            logger, logging.INFO,
            "Test message",
            symbol="AAPL",
            task_id=123,
            duration=1.5
        )
        
        # Verify record was captured
        assert len(captured_records) == 1
        record = captured_records[0]
        
        # Verify context attributes are present
        assert hasattr(record, 'symbol')
        assert record.symbol == "AAPL"
        assert hasattr(record, 'task_id')
        assert record.task_id == 123
        assert hasattr(record, 'duration')
        assert record.duration == 1.5
        
        # Clean up
        logger.removeHandler(handler)
