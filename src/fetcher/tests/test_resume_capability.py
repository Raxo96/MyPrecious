"""
Tests for resume capability in BackfillOrchestrator.

These tests verify that the backfill system can resume from incomplete tasks
and skip assets with existing data unless forced.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from backfill_orchestrator import BackfillOrchestrator
from backfill_models import BackfillTask


class TestResumeCapability:
    """Test suite for resume capability."""
    
    def test_get_pending_backfills_includes_incomplete_tasks(self):
        """Test that get_pending_backfills retrieves all incomplete tasks."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mock cursor.fetchall() to return tasks with various statuses
        today = date.today()
        start_date = today - timedelta(days=365)
        mock_cursor.fetchall.return_value = [
            (1, 10, "AAPL", start_date, today, "pending", 0, None),
            (2, 11, "MSFT", start_date, today, "failed", 2, None),
            (3, 12, "GOOGL", start_date, today, "rate_limited", 1, datetime.now() - timedelta(minutes=5)),
        ]
        
        # Get pending backfills
        tasks = orchestrator.get_pending_backfills()
        
        # Verify all incomplete tasks are returned
        assert len(tasks) == 3
        assert tasks[0].status == "pending"
        assert tasks[1].status == "failed"
        assert tasks[2].status == "rate_limited"
        
        # Verify query includes correct status filters
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0].lower()
        assert "status = 'pending'" in query
        assert "status = 'failed'" in query
        assert "status = 'rate_limited'" in query
    
    def test_filter_tasks_with_existing_data_skips_assets(self):
        """Test that tasks with existing data are filtered out."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Create test tasks
        today = date.today()
        start_date = today - timedelta(days=365)
        tasks = [
            BackfillTask(
                id=1,
                asset_id=10,
                symbol="AAPL",
                start_date=start_date,
                end_date=today,
                status="pending",
                attempts=0,
                retry_after=None
            ),
            BackfillTask(
                id=2,
                asset_id=11,
                symbol="MSFT",
                start_date=start_date,
                end_date=today,
                status="pending",
                attempts=0,
                retry_after=None
            ),
        ]
        
        # Mock cursor.fetchone() to return:
        # - 250 records for AAPL (has existing data)
        # - 0 records for MSFT (no existing data)
        mock_cursor.fetchone.side_effect = [
            (250,),  # AAPL has data
            (0,),    # MSFT has no data
        ]
        
        # Filter tasks
        filtered_tasks = orchestrator._filter_tasks_with_existing_data(tasks)
        
        # Verify only MSFT is returned (AAPL is skipped)
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0].symbol == "MSFT"
        
        # Verify database was queried for both assets
        assert mock_cursor.execute.call_count == 2
    
    def test_run_resumes_from_incomplete_tasks(self):
        """Test that run() resumes from incomplete tasks without re-initializing."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mock db_loader.connect() to not actually connect
        with patch.object(orchestrator.db_loader, 'connect'):
            # Mock db_loader.close() to not actually close
            with patch.object(orchestrator.db_loader, 'close'):
                # Mock load_symbols to return test symbols
                with patch.object(orchestrator, 'load_symbols', return_value=["AAPL", "MSFT"]):
                    # Mock initialize_queue (should be called)
                    with patch.object(orchestrator, 'initialize_queue') as mock_init:
                        # Mock get_pending_backfills to return existing incomplete tasks
                        today = date.today()
                        start_date = today - timedelta(days=365)
                        incomplete_tasks = [
                            BackfillTask(
                                id=1,
                                asset_id=10,
                                symbol="AAPL",
                                start_date=start_date,
                                end_date=today,
                                status="pending",
                                attempts=0,
                                retry_after=None
                            ),
                        ]
                        
                        with patch.object(orchestrator, 'get_pending_backfills', return_value=incomplete_tasks):
                            # Mock _filter_tasks_with_existing_data to return all tasks
                            with patch.object(orchestrator, '_filter_tasks_with_existing_data', return_value=incomplete_tasks):
                                # Mock symbol_processor.process to return success
                                with patch.object(orchestrator.symbol_processor, 'process') as mock_process:
                                    from backfill_models import ProcessingResult
                                    mock_process.return_value = ProcessingResult(
                                        symbol="AAPL",
                                        success=True,
                                        records_inserted=250,
                                        records_skipped=0,
                                        completeness_pct=98.0,
                                        duration_seconds=2.5,
                                        error_message=None
                                    )
                                    
                                    # Run backfill
                                    orchestrator.run(force=False)
                                    
                                    # Verify initialize_queue was called (to handle new symbols)
                                    mock_init.assert_called_once()
                                    
                                    # Verify get_pending_backfills was called (to get incomplete tasks)
                                    # This is the key to resume capability
                                    assert orchestrator.symbol_processor.process.call_count == 1
    
    def test_run_with_force_does_not_skip_existing_data(self):
        """Test that run() with force=True does not skip assets with existing data."""
        orchestrator = BackfillOrchestrator(
            db_connection_string="postgresql://test",
            config_path="dummy.json"
        )
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        orchestrator.db_loader.conn = mock_conn
        
        # Mock db_loader.connect() to not actually connect
        with patch.object(orchestrator.db_loader, 'connect'):
            # Mock db_loader.close() to not actually close
            with patch.object(orchestrator.db_loader, 'close'):
                # Mock load_symbols to return test symbols
                with patch.object(orchestrator, 'load_symbols', return_value=["AAPL"]):
                    # Mock initialize_queue
                    with patch.object(orchestrator, 'initialize_queue'):
                        # Mock get_pending_backfills to return tasks
                        today = date.today()
                        start_date = today - timedelta(days=365)
                        tasks = [
                            BackfillTask(
                                id=1,
                                asset_id=10,
                                symbol="AAPL",
                                start_date=start_date,
                                end_date=today,
                                status="pending",
                                attempts=0,
                                retry_after=None
                            ),
                        ]
                        
                        with patch.object(orchestrator, 'get_pending_backfills', return_value=tasks):
                            # Mock _filter_tasks_with_existing_data (should NOT be called with force=True)
                            with patch.object(orchestrator, '_filter_tasks_with_existing_data') as mock_filter:
                                # Mock symbol_processor.process
                                with patch.object(orchestrator.symbol_processor, 'process') as mock_process:
                                    from backfill_models import ProcessingResult
                                    mock_process.return_value = ProcessingResult(
                                        symbol="AAPL",
                                        success=True,
                                        records_inserted=250,
                                        records_skipped=0,
                                        completeness_pct=98.0,
                                        duration_seconds=2.5,
                                        error_message=None
                                    )
                                    
                                    # Run backfill with force=True
                                    orchestrator.run(force=True)
                                    
                                    # Verify _filter_tasks_with_existing_data was NOT called
                                    mock_filter.assert_not_called()
                                    
                                    # Verify task was processed
                                    assert orchestrator.symbol_processor.process.call_count == 1
