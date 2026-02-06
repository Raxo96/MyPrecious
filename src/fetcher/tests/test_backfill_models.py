"""
Unit tests for backfill data models.

Tests the dataclass definitions to ensure they can be instantiated
correctly and hold the expected data.
"""

import pytest
from datetime import date, datetime
from backfill_models import BackfillTask, ProcessingResult, BackfillReport


class TestBackfillTask:
    """Tests for BackfillTask dataclass."""
    
    def test_backfill_task_creation(self):
        """Test creating a BackfillTask with all fields."""
        task = BackfillTask(
            id=1,
            asset_id=100,
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            status="pending",
            attempts=0,
            retry_after=None
        )
        
        assert task.id == 1
        assert task.asset_id == 100
        assert task.symbol == "AAPL"
        assert task.start_date == date(2024, 1, 1)
        assert task.end_date == date(2025, 1, 1)
        assert task.status == "pending"
        assert task.attempts == 0
        assert task.retry_after is None
    
    def test_backfill_task_with_retry_after(self):
        """Test creating a BackfillTask with retry_after timestamp."""
        retry_time = datetime(2025, 1, 15, 10, 30, 0)
        task = BackfillTask(
            id=2,
            asset_id=None,
            symbol="MSFT",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            status="rate_limited",
            attempts=2,
            retry_after=retry_time
        )
        
        assert task.id == 2
        assert task.asset_id is None
        assert task.symbol == "MSFT"
        assert task.status == "rate_limited"
        assert task.attempts == 2
        assert task.retry_after == retry_time


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""
    
    def test_processing_result_success(self):
        """Test creating a successful ProcessingResult."""
        result = ProcessingResult(
            symbol="GOOGL",
            success=True,
            records_inserted=365,
            records_skipped=5,
            completeness_pct=98.6,
            duration_seconds=2.5,
            error_message=None
        )
        
        assert result.symbol == "GOOGL"
        assert result.success is True
        assert result.records_inserted == 365
        assert result.records_skipped == 5
        assert result.completeness_pct == 98.6
        assert result.duration_seconds == 2.5
        assert result.error_message is None
    
    def test_processing_result_failure(self):
        """Test creating a failed ProcessingResult."""
        result = ProcessingResult(
            symbol="INVALID",
            success=False,
            records_inserted=0,
            records_skipped=0,
            completeness_pct=0.0,
            duration_seconds=0.5,
            error_message="Symbol not found"
        )
        
        assert result.symbol == "INVALID"
        assert result.success is False
        assert result.records_inserted == 0
        assert result.records_skipped == 0
        assert result.completeness_pct == 0.0
        assert result.duration_seconds == 0.5
        assert result.error_message == "Symbol not found"


class TestBackfillReport:
    """Tests for BackfillReport dataclass."""
    
    def test_backfill_report_creation(self):
        """Test creating a BackfillReport with all fields."""
        start = datetime(2025, 1, 15, 10, 0, 0)
        end = datetime(2025, 1, 15, 10, 30, 0)
        
        report = BackfillReport(
            total_symbols=500,
            successful=495,
            failed=5,
            total_records_inserted=180000,
            total_duration_seconds=1800.0,
            start_time=start,
            end_time=end,
            failed_symbols=["INVALID1", "INVALID2", "INVALID3", "INVALID4", "INVALID5"]
        )
        
        assert report.total_symbols == 500
        assert report.successful == 495
        assert report.failed == 5
        assert report.total_records_inserted == 180000
        assert report.total_duration_seconds == 1800.0
        assert report.start_time == start
        assert report.end_time == end
        assert len(report.failed_symbols) == 5
        assert "INVALID1" in report.failed_symbols
    
    def test_backfill_report_no_failures(self):
        """Test creating a BackfillReport with no failures."""
        start = datetime(2025, 1, 15, 10, 0, 0)
        end = datetime(2025, 1, 15, 10, 30, 0)
        
        report = BackfillReport(
            total_symbols=10,
            successful=10,
            failed=0,
            total_records_inserted=3650,
            total_duration_seconds=30.0,
            start_time=start,
            end_time=end,
            failed_symbols=[]
        )
        
        assert report.total_symbols == 10
        assert report.successful == 10
        assert report.failed == 0
        assert report.total_records_inserted == 3650
        assert len(report.failed_symbols) == 0
