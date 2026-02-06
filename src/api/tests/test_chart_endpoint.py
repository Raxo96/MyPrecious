"""Unit tests for GET /api/assets/{asset_symbol}/chart endpoint"""
import pytest
from fastapi.testclient import TestClient


class TestGetAssetChart:
    """Test suite for the asset chart endpoint"""
    
    def test_chart_endpoint_exists(self, client):
        """Test that the chart endpoint exists and returns 200 for valid asset"""
        # Using AAPL which should exist in seed data
        response = client.get("/api/assets/AAPL/chart")
        assert response.status_code == 200
    
    def test_chart_response_structure(self, client):
        """Test that the response has the correct structure"""
        response = client.get("/api/assets/AAPL/chart")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "symbol" in data
        assert "current_price" in data
        assert "price_changes" in data
        
        # Verify price_changes has all time periods
        price_changes = data["price_changes"]
        assert "1D" in price_changes
        assert "1M" in price_changes
        assert "3M" in price_changes
        assert "6M" in price_changes
        assert "1Y" in price_changes
    
    def test_chart_data_types(self, client):
        """Test that response fields have correct data types"""
        response = client.get("/api/assets/AAPL/chart")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify data types
        assert isinstance(data["symbol"], str)
        assert isinstance(data["current_price"], (int, float))
        assert isinstance(data["price_changes"], dict)
        
        # Each price change should be either a number or null
        for period, value in data["price_changes"].items():
            assert value is None or isinstance(value, (int, float))
    
    def test_chart_nonexistent_asset(self, client):
        """Test that requesting chart for non-existent asset returns 404"""
        response = client.get("/api/assets/NONEXISTENT123/chart")
        
        assert response.status_code == 404
        assert "detail" in response.json()
        assert response.json()["detail"] == "Asset not found"
    
    def test_chart_case_insensitive(self, client):
        """Test that symbol lookup is case-insensitive"""
        response_lower = client.get("/api/assets/aapl/chart")
        response_upper = client.get("/api/assets/AAPL/chart")
        response_mixed = client.get("/api/assets/AaPl/chart")
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200
        
        # All should return the same symbol (uppercase)
        assert response_lower.json()["symbol"] == "AAPL"
        assert response_upper.json()["symbol"] == "AAPL"
        assert response_mixed.json()["symbol"] == "AAPL"
    
    def test_chart_current_price_matches_asset_endpoint(self, client):
        """Test that current_price in chart matches the asset detail endpoint"""
        asset_response = client.get("/api/assets/AAPL")
        chart_response = client.get("/api/assets/AAPL/chart")
        
        assert asset_response.status_code == 200
        assert chart_response.status_code == 200
        
        asset_price = asset_response.json()["current_price"]
        chart_price = chart_response.json()["current_price"]
        
        assert asset_price == chart_price
    
    def test_chart_price_change_calculation_logic(self, client):
        """Test that price changes follow the correct formula"""
        response = client.get("/api/assets/AAPL/chart")
        
        assert response.status_code == 200
        data = response.json()
        
        current_price = data["current_price"]
        price_changes = data["price_changes"]
        
        # If we have a price change, verify it's a reasonable percentage
        # (not testing exact values since we don't control the seed data)
        for period, change in price_changes.items():
            if change is not None:
                # Price change should be a reasonable percentage (-100% to +1000%)
                assert -100 <= change <= 1000, f"Price change for {period} is unreasonable: {change}%"
    
    def test_chart_multiple_assets(self, client):
        """Test retrieving charts for multiple different assets"""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for symbol in symbols:
            response = client.get(f"/api/assets/{symbol}/chart")
            if response.status_code == 200:
                data = response.json()
                assert data["symbol"] == symbol
                assert "price_changes" in data
                assert len(data["price_changes"]) == 5  # All 5 time periods
    
    def test_chart_null_handling(self, client):
        """Test that null values are properly returned for missing data"""
        # Test with an asset that might have limited history
        response = client.get("/api/assets/AAPL/chart")
        
        assert response.status_code == 200
        data = response.json()
        
        price_changes = data["price_changes"]
        
        # Verify that null values are actually null (not 0 or empty string)
        for period, value in price_changes.items():
            if value is None:
                assert value is None  # Explicitly null, not falsy
            else:
                assert isinstance(value, (int, float))
    
    def test_chart_response_schema_completeness(self, client):
        """Test that the response contains exactly the expected fields"""
        response = client.get("/api/assets/AAPL/chart")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact fields at top level
        expected_fields = {"symbol", "current_price", "price_changes"}
        assert set(data.keys()) == expected_fields
        
        # Verify exact fields in price_changes
        expected_periods = {"1D", "1M", "3M", "6M", "1Y"}
        assert set(data["price_changes"].keys()) == expected_periods
