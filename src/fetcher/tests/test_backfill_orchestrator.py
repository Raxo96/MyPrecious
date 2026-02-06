"""
Tests for BackfillOrchestrator class.

These tests verify the core functionality of the backfill orchestrator
including symbol loading, queue initialization, and report generation.
"""

import json
import pytest
import signal
import tempfile
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from backfill_orchestrator import BackfillOrchestrator
from backfill_models import BackfillTask, ProcessingResult


class TestBackfillOrchestrator:
    """Test suite for BackfillOrchestrator class."""
    
    def test_load_symbols_valid_config(self):
        """Test loading symbols from a valid configuration file."""
        # Create temporary config file
        config_data = {
            "name": "Test Symbols",
            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path=config_path
            )
            
            symbols = orchestrator.load_symbols()
            
            assert len(symbols) == 4
            assert "AAPL" in symbols
            assert "MSFT" in symbols
            assert "GOOGL" in symbols
            assert "AMZN" in symbols
        finally:
            os.unlink(config_path)
    
    def test_load_symbols_filters_invalid_symbols(self):
        """Test that invalid symbol formats are filtered out."""
        config_data = {
            "name": "Test Symbols",
            "symbols": ["AAPL", "invalid123", "MSFT", "toolong", "BRK.B"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path=config_path
            )
            
            symbols = orchestrator.load_symbols()
            
            # Should only include valid symbols
            assert len(symbols) == 3
            assert "AAPL" in symbols
            assert "MSFT" in symbols
            assert "BRK.B" in symbols
            assert "invalid123" not in symbols
            assert "toolong" not in symbols
        finally:
            os.unlink(config_path)
    
    def test_load_symbols_missing_file(self):
        """Test that FileNotFoundError is raised for missing config file."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="/nonexistent/config.json"
        )
        
        with pytest.raises(FileNotFoundError):
            orchestrator.load_symbols()
    
    def test_load_symbols_invalid_json(self):
        """Test that ValueError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path=config_path
            )
            
            with pytest.raises(ValueError):
                orchestrator.load_symbols()
        finally:
            os.unlink(config_path)
    
    def test_load_symbols_missing_symbols_field(self):
        """Test that ValueError is raised when 'symbols' field is missing."""
        config_data = {
            "name": "Test Symbols"
            # Missing 'symbols' field
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path=config_path
            )
            
            with pytest.raises(ValueError, match="missing 'symbols' field"):
                orchestrator.load_symbols()
        finally:
            os.unlink(config_path)
    
    def test_validate_symbol_valid_formats(self):
        """Test symbol validation with various valid formats."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Valid formats
        assert orchestrator._validate_symbol("AAPL") is True
        assert orchestrator._validate_symbol("MSFT") is True
        assert orchestrator._validate_symbol("A") is True
        assert orchestrator._validate_symbol("GOOGL") is True
        assert orchestrator._validate_symbol("BRK.B") is True
        assert orchestrator._validate_symbol("BF.A") is True
    
    def test_validate_symbol_invalid_formats(self):
        """Test symbol validation rejects invalid formats."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Invalid formats
        assert orchestrator._validate_symbol("invalid123") is False
        assert orchestrator._validate_symbol("toolongname") is False
        assert orchestrator._validate_symbol("lower") is False
        assert orchestrator._validate_symbol("123") is False
        assert orchestrator._validate_symbol("") is False
        assert orchestrator._validate_symbol("AAPL.BBB") is False  # Too many letters after dot
    
    def test_generate_report_empty_results(self):
        """Test report generation with no processing results."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        orchestrator.start_time = datetime.now()
        orchestrator.end_time = datetime.now()
        
        report = orchestrator.generate_report()
        
        assert report.total_symbols == 0
        assert report.successful == 0
        assert report.failed == 0
        assert report.total_records_inserted == 0
        assert report.failed_symbols == []
    
    def test_generate_report_with_results(self):
        """Test report generation with processing results."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        orchestrator.start_time = datetime.now()
        orchestrator.end_time = datetime.now() + timedelta(seconds=100)
        
        # Add some processing results
        orchestrator.processing_results = [
            ProcessingResult(
                symbol="AAPL",
                success=True,
                records_inserted=250,
                records_skipped=5,
                completeness_pct=98.0,
                duration_seconds=2.5,
                error_message=None
            ),
            ProcessingResult(
                symbol="MSFT",
                success=True,
                records_inserted=248,
                records_skipped=3,
                completeness_pct=97.0,
                duration_seconds=2.3,
                error_message=None
            ),
            ProcessingResult(
                symbol="INVALID",
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=1.0,
                error_message="Symbol not found"
            )
        ]
        
        report = orchestrator.generate_report()
        
        assert report.total_symbols == 3
        assert report.successful == 2
        assert report.failed == 1
        assert report.total_records_inserted == 498
        assert report.failed_symbols == ["INVALID"]
        assert report.total_duration_seconds == 100.0
    
    def test_mark_permanently_failed(self):
        """Test marking a task as permanently failed after max retries."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mark task as permanently failed
        orchestrator._mark_permanently_failed(task_id=123, symbol="AAPL")
        
        # Verify UPDATE query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE backfill_queue" in query
        assert "status = %s" in query
        assert params[0] == 'failed'
        assert "exceeded maximum retry attempts" in params[1]
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_update_queue_status_completed(self):
        """Test updating queue status to completed."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Update status to completed
        orchestrator.update_queue_status(task_id=123, status='completed')
        
        # Verify UPDATE query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE backfill_queue" in query
        assert "status = %s" in query
        assert "completed_at = NOW()" in query
        assert params[0] == 'completed'
        assert params[-1] == 123
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_update_queue_status_failed_with_error(self):
        """Test updating queue status to failed with error message."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Update status to failed with error message
        orchestrator.update_queue_status(
            task_id=123,
            status='failed',
            error_message="Network timeout",
            increment_attempts=True
        )
        
        # Verify UPDATE query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE backfill_queue" in query
        assert "status = %s" in query
        assert "error_message = %s" in query
        assert "attempts = attempts + 1" in query
        assert params[0] == 'failed'
        assert params[1] == "Network timeout"
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_update_queue_status_rate_limited_with_retry_after(self):
        """Test updating queue status to rate_limited with retry_after timestamp."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Update status to rate_limited with retry_after
        retry_time = datetime.now() + timedelta(seconds=60)
        orchestrator.update_queue_status(
            task_id=123,
            status='rate_limited',
            retry_after=retry_time,
            increment_attempts=True
        )
        
        # Verify UPDATE query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE backfill_queue" in query
        assert "status = %s" in query
        assert "retry_after = %s" in query
        assert "attempts = attempts + 1" in query
        assert params[0] == 'rate_limited'
        assert params[1] == retry_time
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_update_tracked_asset(self):
        """Test updating tracked_assets table for an asset."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Update tracked asset
        orchestrator.update_tracked_asset(asset_id=456, symbol="AAPL")
        
        # Verify INSERT ... ON CONFLICT query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO tracked_assets" in query
        assert "ON CONFLICT" in query
        assert "DO UPDATE SET" in query
        assert "last_price_update = NOW()" in query
        assert params[0] == 456
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()


    def test_initialize_queue_creates_tasks(self):
        """Test that initialize_queue creates backfill tasks for symbols."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mock cursor.fetchone() to return asset_id for existing assets
        # and None for new assets (to trigger INSERT)
        mock_cursor.fetchone.side_effect = [
            (1,),  # AAPL exists with id=1
            None,  # No existing task for AAPL
            None,  # MSFT doesn't exist
            (2,),  # New MSFT asset created with id=2
            None,  # No existing task for MSFT
        ]
        
        # Initialize queue with test symbols
        symbols = ["AAPL", "MSFT"]
        orchestrator.initialize_queue(symbols, days=365)
        
        # Verify database operations were called
        assert mock_cursor.execute.call_count >= 4  # At least 2 asset checks + 2 task inserts
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_get_pending_backfills_returns_tasks(self):
        """Test that get_pending_backfills retrieves pending tasks from queue."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mock cursor.fetchall() to return sample tasks
        today = date.today()
        start_date = today - timedelta(days=365)
        mock_cursor.fetchall.return_value = [
            (1, 10, "AAPL", start_date, today, "pending", 0, None),
            (2, 11, "MSFT", start_date, today, "failed", 2, None),
        ]
        
        # Get pending backfills
        tasks = orchestrator.get_pending_backfills()
        
        # Verify query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        
        assert "SELECT" in query
        assert "FROM backfill_queue" in query
        assert "WHERE" in query
        
        # Verify tasks were returned
        assert len(tasks) == 2
        assert tasks[0].symbol == "AAPL"
        assert tasks[0].status == "pending"
        assert tasks[1].symbol == "MSFT"
        assert tasks[1].status == "failed"
        
        mock_cursor.close.assert_called_once()


    def test_signal_handler_registration(self):
        """Test that signal handlers are registered during initialization."""
        with patch('signal.signal') as mock_signal:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path="dummy.json"
            )
            
            # Verify SIGINT handler was registered
            calls = mock_signal.call_args_list
            sigint_registered = any(
                call[0][0] == signal.SIGINT for call in calls
            )
            assert sigint_registered, "SIGINT handler should be registered"
            
            # Verify SIGTERM handler was registered (if available)
            if hasattr(signal, 'SIGTERM'):
                sigterm_registered = any(
                    call[0][0] == signal.SIGTERM for call in calls
                )
                assert sigterm_registered, "SIGTERM handler should be registered"
    
    def test_handle_shutdown_signal_sets_flag(self):
        """Test that shutdown signal handler sets the shutdown_requested flag."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Initially shutdown should not be requested
        assert orchestrator.shutdown_requested is False
        
        # Simulate receiving SIGINT signal
        orchestrator._handle_shutdown_signal(signal.SIGINT, None)
        
        # Verify shutdown flag is set
        assert orchestrator.shutdown_requested is True
    
    def test_save_shutdown_progress_logs_partial_report(self):
        """Test that _save_shutdown_progress logs progress and generates report."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        orchestrator.start_time = datetime.now()
        
        # Add some processing results
        orchestrator.processing_results = [
            ProcessingResult(
                symbol="AAPL",
                success=True,
                records_inserted=250,
                records_skipped=5,
                completeness_pct=98.0,
                duration_seconds=2.5,
                error_message=None
            ),
            ProcessingResult(
                symbol="MSFT",
                success=True,
                records_inserted=248,
                records_skipped=3,
                completeness_pct=97.0,
                duration_seconds=2.3,
                error_message=None
            )
        ]
        
        # Call _save_shutdown_progress
        with patch('backfill_orchestrator.log_with_context') as mock_log:
            orchestrator._save_shutdown_progress(processed_count=2, total_tasks=10)
            
            # Verify end_time was set
            assert orchestrator.end_time is not None
            
            # Verify log_with_context was called with shutdown info
            mock_log.assert_called()
            call_args = mock_log.call_args_list[0]
            assert "graceful_shutdown" in str(call_args)
    
    def test_run_checks_shutdown_flag_during_processing(self):
        """Test that run() checks shutdown flag and exits gracefully."""
        # Create temporary config file
        config_data = {
            "name": "Test Symbols",
            "symbols": ["AAPL", "MSFT", "GOOGL"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string="postgresql://test",
                config_path=config_path
            )
            
            # Mock database connection and operations
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            orchestrator.db_loader.conn = mock_conn
            
            # Mock db_loader.connect to avoid actual database connection
            orchestrator.db_loader.connect = Mock()
            orchestrator.db_loader.close = Mock()
            
            # Mock initialize_queue to avoid database operations
            orchestrator.initialize_queue = Mock()
            
            # Mock get_pending_backfills to return 3 tasks
            today = date.today()
            start_date = today - timedelta(days=365)
            orchestrator.get_pending_backfills = Mock(return_value=[
                BackfillTask(1, 10, "AAPL", start_date, today, "pending", 0, None),
                BackfillTask(2, 11, "MSFT", start_date, today, "pending", 0, None),
                BackfillTask(3, 12, "GOOGL", start_date, today, "pending", 0, None),
            ])
            
            # Mock symbol_processor.process to set shutdown flag after first task
            processed_symbols = []
            def mock_process(task):
                processed_symbols.append(task.symbol)
                if task.symbol == "AAPL":
                    # Process first task successfully, then set shutdown flag
                    result = ProcessingResult(
                        symbol=task.symbol,
                        success=True,
                        records_inserted=250,
                        records_skipped=0,
                        completeness_pct=100.0,
                        duration_seconds=2.0,
                        error_message=None
                    )
                    # Set shutdown flag after processing first task
                    orchestrator.shutdown_requested = True
                    return result
                else:
                    # This should not be reached due to shutdown flag
                    return ProcessingResult(
                        symbol=task.symbol,
                        success=False,
                        records_inserted=0,
                        records_skipped=0,
                        completeness_pct=0.0,
                        duration_seconds=0.0,
                        error_message="Should not be processed"
                    )
            
            orchestrator.symbol_processor.process = Mock(side_effect=mock_process)
            
            # Mock _filter_tasks_with_existing_data to return all tasks
            orchestrator._filter_tasks_with_existing_data = Mock(side_effect=lambda tasks: tasks)
            
            # Mock _save_shutdown_progress
            orchestrator._save_shutdown_progress = Mock()
            
            # Run should exit with code 130 when shutdown is requested
            with pytest.raises(SystemExit) as exc_info:
                orchestrator.run(force=False, days=365)
            
            # Verify exit code is 130 (SIGINT)
            assert exc_info.value.code == 130
            
            # Verify only 1 task was processed (AAPL)
            assert len(orchestrator.processing_results) == 1
            assert orchestrator.processing_results[0].symbol == "AAPL"
            
            # Verify _save_shutdown_progress was called
            orchestrator._save_shutdown_progress.assert_called_once_with(1, 3)
            
        finally:
            os.unlink(config_path)
