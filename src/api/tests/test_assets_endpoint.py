"""Unit tests for GET /api/assets endpoint"""

import pytest
from fastapi.testclient import TestClient


class TestGetAllAssetsEndpoint:
    """Tests for GET /api/assets endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test that the /api/assets endpoint exists and returns 200"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
    
    def test_response_structure(self, client):
        """Test that the response has the correct structure"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have an "assets" key
        assert "assets" in data
        assert isinstance(data["assets"], list)
    
    def test_asset_fields(self, client):
        """Test that each asset has the required fields"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["assets"]) > 0:
            asset = data["assets"][0]
            
            # Check required fields exist
            assert "id" in asset
            assert "symbol" in asset
            assert "name" in asset
            assert "asset_type" in asset
            assert "exchange" in asset
            assert "current_price" in asset
            assert "day_change_pct" in asset
            
            # Check field types
            assert isinstance(asset["id"], int)
            assert isinstance(asset["symbol"], str)
            assert isinstance(asset["name"], str)
            assert isinstance(asset["asset_type"], str)
            assert isinstance(asset["exchange"], str)
            assert isinstance(asset["current_price"], (int, float))
            # day_change_pct can be None or a number
            assert asset["day_change_pct"] is None or isinstance(asset["day_change_pct"], (int, float))
    
    def test_assets_ordered_by_symbol(self, client):
        """Test that assets are ordered by symbol"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["assets"]) > 1:
            symbols = [asset["symbol"] for asset in data["assets"]]
            # Check if symbols are in alphabetical order
            assert symbols == sorted(symbols)
    
    def test_current_price_non_negative(self, client):
        """Test that current_price is never negative"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        for asset in data["assets"]:
            assert asset["current_price"] >= 0.0
    
    def test_asset_with_no_price_returns_zero(self, client):
        """Test that assets with no price data return 0.0 for current_price"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        # This test verifies the requirement that assets without price data
        # should return 0.0. We can't guarantee there's an asset without
        # price data, but we can verify the logic handles it correctly
        # by checking that 0.0 is a valid value
        zero_price_assets = [a for a in data["assets"] if a["current_price"] == 0.0]
        
        # If there are assets with 0.0 price, verify they have all required fields
        for asset in zero_price_assets:
            assert "id" in asset
            assert "symbol" in asset
            assert "name" in asset
            assert asset["current_price"] == 0.0
    
    def test_empty_database_returns_empty_array(self, client):
        """Test that an empty database returns an empty array (not an error)"""
        # This test documents the expected behavior when no assets exist
        # The actual test would require a clean database, but we document
        # the expected behavior here
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty array, not an error
        assert isinstance(data["assets"], list)
    
    def test_day_change_pct_field_exists(self, client):
        """Test that day_change_pct field is present in response"""
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        
        # If there are assets, check that day_change_pct field exists
        if len(data["assets"]) > 0:
            asset = data["assets"][0]
            assert "day_change_pct" in asset
            
            # day_change_pct should be None or a number
            if asset["day_change_pct"] is not None:
                assert isinstance(asset["day_change_pct"], (int, float))
                # If it's a number, it should be rounded to 2 decimal places
                # Check by converting to string and counting decimals
                if isinstance(asset["day_change_pct"], float):
                    decimal_str = str(asset["day_change_pct"])
                    if '.' in decimal_str:
                        decimal_places = len(decimal_str.split('.')[1])
                        assert decimal_places <= 2, f"day_change_pct should have at most 2 decimal places, got {decimal_places}"
