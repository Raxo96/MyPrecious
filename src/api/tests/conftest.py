"""Test configuration and fixtures for API tests"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import os

from database import Base, get_db, DATABASE_URL
from models import Asset, AssetPrice
from main import app

@pytest.fixture(scope="function")
def client():
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client
