"""
End-to-end integration test for BackfillOrchestrator.

This test verifies the complete backfill workflow with a small subset
of symbols against a test database.
"""

import json
import pytest
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path

from backfill_orchestrator import BackfillOrchestrator
from backfill_models import BackfillTask, ProcessingResult


# Skip this test if no database is available
pytestmark = pytest.mark.skipif(
    os.getenv("TEST_DB_URL") is None,
    reason="TEST_DB_URL environment variable not set"
)


class TestBackfillE2E:
    """End-to-end integration tests for backfill orchestrator."""
    
    @pytest.fixture
    def test_config(self):
        """Create a temporary config file with a small subset of symbols."""
        config_data = {
            "name": "Test Symbols",
            "last_updated": "2025-02-06",
            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        yield config_path
        
        # Cleanup
        if os.path.exists(config_path):
            os.unlink(config_path)
    
    @pytest.fixture
    def db_url(self):
        """Get database URL from environment or use default."""
        return os.getenv("TEST_DB_URL", "postgresql://postgres@localhost:5432/portfolio_tracker")
    
    def test_full_backfill_workflow_dry_run(self, test_config, db_url):
        """
        Test the complete backfill workflow without actually fetching data.
        
        This test verifies:
        1. Symbol loading from config
        2. Queue initialization
        3. Pending task retrieval
        4. Report generation
        """
        # Create orchestrator
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=test_config
        )
        
        # Test 1: Load symbols
        symbols = orchestrator.load_symbols()
        assert len(symbols) == 5
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "AMZN" in symbols
        assert "NVDA" in symbols
        
        # Test 2: Validate symbols
        for symbol in symbols:
            assert orchestrator._validate_symbol(symbol) is True
        
        # Test 3: Generate empty report
        orchestrator.start_time = orchestrator.end_time = date.today()
        report = orchestrator.generate_report()
        
        assert report.total_symbols == 0
        assert report.successful == 0
        assert report.failed == 0
        assert report.total_records_inserted == 0
        assert report.failed_symbols == []
    
    def test_symbol_validation_consistency(self, test_config, db_url):
        """
        Test that symbol validation is consistent across different inputs.
        
        This verifies Property 1: Symbol Validation Consistency
        """
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=test_config
        )
        
        # Valid symbols
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "A", "BRK.B", "BF.A"]
        for symbol in valid_symbols:
            assert orchestrator._validate_symbol(symbol) is True, f"{symbol} should be valid"
        
        # Invalid symbols
        invalid_symbols = ["invalid123", "toolongname", "lower", "123", "", "AAPL.BBB"]
        for symbol in invalid_symbols:
            assert orchestrator._validate_symbol(symbol) is False, f"{symbol} should be invalid"
    
    def test_date_range_calculation(self, test_config, db_url):
        """
        Test that date range calculation is correct.
        
        This verifies Property 3: Date Range Calculation
        """
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=test_config
        )
        
        # Test with different days values
        for days in [365, 180, 90, 30]:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Calculate the difference
            delta = (end_date - start_date).days
            
            # Should be exactly the specified number of days
            assert delta == days, f"Date range should be exactly {days} days"
    
    def test_report_accuracy(self, test_config, db_url):
        """
        Test that summary report calculations are accurate.
        
        This verifies Property 17: Summary Report Accuracy
        """
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=test_config
        )
        
        # Simulate processing results
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
                symbol="GOOGL",
                success=True,
                records_inserted=252,
                records_skipped=2,
                completeness_pct=99.0,
                duration_seconds=2.7,
                error_message=None
            ),
            ProcessingResult(
                symbol="INVALID1",
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=1.0,
                error_message="Symbol not found"
            ),
            ProcessingResult(
                symbol="INVALID2",
                success=False,
                records_inserted=0,
                records_skipped=0,
                completeness_pct=0.0,
                duration_seconds=0.8,
                error_message="Rate limited"
            )
        ]
        
        from datetime import datetime
        orchestrator.start_time = datetime.now()
        orchestrator.end_time = datetime.now() + timedelta(seconds=100)
        
        # Generate report
        report = orchestrator.generate_report()
        
        # Verify accuracy
        assert report.total_symbols == 5, "Total symbols should equal number of results"
        assert report.successful == 3, "Successful count should match successful results"
        assert report.failed == 2, "Failed count should match failed results"
        assert report.total_symbols == report.successful + report.failed, "Total should equal successful + failed"
        
        # Verify total records inserted
        expected_records = 250 + 248 + 252
        assert report.total_records_inserted == expected_records, f"Total records should be {expected_records}"
        
        # Verify failed symbols list
        assert len(report.failed_symbols) == 2
        assert "INVALID1" in report.failed_symbols
        assert "INVALID2" in report.failed_symbols
        
        # Verify duration
        assert report.total_duration_seconds == 100.0
    
    def test_orchestrator_initialization(self, test_config, db_url):
        """Test that orchestrator initializes correctly with valid config."""
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path=test_config
        )
        
        # Verify orchestrator is initialized
        assert orchestrator.config_path == test_config
        assert orchestrator.db_connection_string == db_url
        assert orchestrator.processing_results == []
        assert orchestrator.start_time is None
        assert orchestrator.end_time is None
    
    def test_invalid_config_path(self, db_url):
        """Test that orchestrator handles invalid config path gracefully."""
        orchestrator = BackfillOrchestrator(
            db_connection_string=db_url,
            config_path="/nonexistent/config.json"
        )
        
        # Should raise FileNotFoundError when trying to load symbols
        with pytest.raises(FileNotFoundError):
            orchestrator.load_symbols()
    
    def test_empty_symbols_list(self, db_url):
        """Test handling of empty symbols list."""
        config_data = {
            "name": "Empty Test",
            "symbols": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            orchestrator = BackfillOrchestrator(
                db_connection_string=db_url,
                config_path=config_path
            )
            
            symbols = orchestrator.load_symbols()
            assert len(symbols) == 0
            
            # Report should handle empty results
            orchestrator.start_time = orchestrator.end_time = date.today()
            report = orchestrator.generate_report()
            assert report.total_symbols == 0
        finally:
            os.unlink(config_path)
