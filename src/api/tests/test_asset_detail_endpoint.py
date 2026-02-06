"""Unit tests for GET /api/assets/{asset_symbol} endpoint"""
import pytest
from fastapi.testclient import TestClient


class TestGetAssetBySymbol:
    """Test suite for the asset detail endpoint"""
    
    def test_get_existing_asset(self, client):
        """Test retrieving an existing asset (AAPL should exist in seed data)"""
        response = client.get("/api/assets/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "id" in data
        assert "symbol" in data
        assert "name" in data
        assert "asset_type" in data
        assert "exchange" in data
        assert "current_price" in data
        
        # Verify correct values
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["asset_type"] == "stock"
        assert data["exchange"] == "NASDAQ"
        assert isinstance(data["current_price"], (int, float))
    
    def test_get_asset_case_insensitive(self, client):
        """Test that symbol lookup is case-insensitive"""
        # Test with lowercase
        response_lower = client.get("/api/assets/aapl")
        assert response_lower.status_code == 200
        
        # Test with uppercase
        response_upper = client.get("/api/assets/AAPL")
        assert response_upper.status_code == 200
        
        # Test with mixed case
        response_mixed = client.get("/api/assets/AaPl")
        assert response_mixed.status_code == 200
        
        # All should return the same asset
        assert response_lower.json()["id"] == response_upper.json()["id"]
        assert response_lower.json()["id"] == response_mixed.json()["id"]
        assert response_lower.json()["symbol"] == "AAPL"
    
    def test_get_nonexistent_asset(self, client):
        """Test retrieving an asset that doesn't exist - should return 404"""
        response = client.get("/api/assets/NONEXISTENT123")
        
        assert response.status_code == 404
        assert "detail" in response.json()
        assert response.json()["detail"] == "Asset not found"
    
    def test_response_schema(self, client):
        """Test that the response matches the expected schema"""
        response = client.get("/api/assets/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify data types
        assert isinstance(data["id"], int)
        assert isinstance(data["symbol"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["asset_type"], str)
        assert isinstance(data["exchange"], str)
        assert isinstance(data["current_price"], (int, float))
        
        # Verify no extra fields
        expected_fields = {"id", "symbol", "name", "asset_type", "exchange", "current_price"}
        assert set(data.keys()) == expected_fields
    
    def test_multiple_different_assets(self, client):
        """Test retrieving multiple different assets"""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for symbol in symbols:
            response = client.get(f"/api/assets/{symbol}")
            if response.status_code == 200:
                data = response.json()
                assert data["symbol"] == symbol
                assert "current_price" in data
