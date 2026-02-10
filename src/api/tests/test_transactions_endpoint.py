"""Tests for transaction endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base, get_db
# Import ALL models to ensure they're registered with Base before creating tables
from models import (
    Portfolio, PortfolioPosition, Asset, AssetPrice,
    Transaction, FetcherLog, FetcherStatistics, PriceUpdateLog
)
from main import app


@pytest.fixture(scope="function")
def test_db():
    """Create a test database"""
    # Use in-memory SQLite for testing with check_same_thread=False
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=None  # Disable pooling for in-memory database
    )
    
    # Create all tables (models are already imported at module level)
    Base.metadata.create_all(bind=engine)
    
    # Create a session bound to this engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_transaction_requires_portfolio_id(client, test_db):
    """Test POST /api/transactions requires portfolio_id in request body"""
    # Create portfolio and asset
    portfolio = Portfolio(id=1, user_id=1, name="Test Portfolio", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio)
    test_db.add(asset)
    test_db.commit()
    
    # Try to create transaction without portfolio_id
    response = client.post("/api/transactions", json={
        "asset_id": 1,
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Should fail with 422 (validation error) because portfolio_id is required
    assert response.status_code == 422


def test_create_transaction_validates_portfolio_exists(client, test_db):
    """Test POST /api/transactions validates that portfolio_id exists"""
    # Create asset but no portfolio
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(asset)
    test_db.commit()
    
    # Try to create transaction with non-existent portfolio_id
    response = client.post("/api/transactions", json={
        "portfolio_id": 999,
        "asset_id": 1,
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Should fail with 404 (portfolio not found)
    assert response.status_code == 404
    assert "Portfolio with id 999 not found" in response.json()["detail"]


def test_create_transaction_with_valid_portfolio_id(client, test_db):
    """Test POST /api/transactions creates transaction with valid portfolio_id"""
    # Create portfolio and asset
    portfolio = Portfolio(id=1, user_id=1, name="Test Portfolio", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio)
    test_db.add(asset)
    test_db.commit()
    
    # Create transaction with valid portfolio_id
    response = client.post("/api/transactions", json={
        "portfolio_id": 1,
        "asset_id": 1,
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Should succeed
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Transaction created"
    assert "id" in data
    
    # Verify transaction was created in database
    transaction = test_db.query(Transaction).filter(Transaction.portfolio_id == 1).first()
    assert transaction is not None
    assert transaction.portfolio_id == 1
    assert transaction.asset_id == 1
    assert float(transaction.quantity) == 10.0


def test_create_transaction_creates_position_in_correct_portfolio(client, test_db):
    """Test POST /api/transactions creates position in the specified portfolio"""
    # Create two portfolios and one asset
    portfolio1 = Portfolio(id=1, user_id=1, name="Portfolio 1", currency="USD")
    portfolio2 = Portfolio(id=2, user_id=1, name="Portfolio 2", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio1)
    test_db.add(portfolio2)
    test_db.add(asset)
    test_db.commit()
    
    # Create transaction in portfolio 1
    response = client.post("/api/transactions", json={
        "portfolio_id": 1,
        "asset_id": 1,
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    
    # Verify position was created in portfolio 1
    position1 = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1,
        PortfolioPosition.asset_id == 1
    ).first()
    assert position1 is not None
    assert float(position1.quantity) == 10.0
    
    # Verify no position was created in portfolio 2
    position2 = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 2,
        PortfolioPosition.asset_id == 1
    ).first()
    assert position2 is None


def test_create_transaction_updates_position_in_correct_portfolio(client, test_db):
    """Test POST /api/transactions updates position in the specified portfolio only"""
    # Create two portfolios and one asset
    portfolio1 = Portfolio(id=1, user_id=1, name="Portfolio 1", currency="USD")
    portfolio2 = Portfolio(id=2, user_id=1, name="Portfolio 2", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio1)
    test_db.add(portfolio2)
    test_db.add(asset)
    test_db.commit()
    
    # Create initial positions in both portfolios
    position1 = PortfolioPosition(
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    position2 = PortfolioPosition(
        portfolio_id=2,
        asset_id=1,
        quantity=20.0,
        average_buy_price=110.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position1)
    test_db.add(position2)
    test_db.commit()
    
    # Add more to portfolio 1
    response = client.post("/api/transactions", json={
        "portfolio_id": 1,
        "asset_id": 1,
        "transaction_type": "buy",
        "quantity": 5.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    
    # Verify position 1 was updated
    test_db.refresh(position1)
    assert float(position1.quantity) == 15.0  # 10 + 5
    
    # Verify position 2 was NOT updated
    test_db.refresh(position2)
    assert float(position2.quantity) == 20.0  # unchanged


def test_create_transaction_sell_from_correct_portfolio(client, test_db):
    """Test POST /api/transactions sells from the specified portfolio only"""
    # Create two portfolios and one asset
    portfolio1 = Portfolio(id=1, user_id=1, name="Portfolio 1", currency="USD")
    portfolio2 = Portfolio(id=2, user_id=1, name="Portfolio 2", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio1)
    test_db.add(portfolio2)
    test_db.add(asset)
    test_db.commit()
    
    # Create positions in both portfolios
    position1 = PortfolioPosition(
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    position2 = PortfolioPosition(
        portfolio_id=2,
        asset_id=1,
        quantity=20.0,
        average_buy_price=110.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position1)
    test_db.add(position2)
    test_db.commit()
    
    # Sell from portfolio 1
    response = client.post("/api/transactions", json={
        "portfolio_id": 1,
        "asset_id": 1,
        "transaction_type": "sell",
        "quantity": 5.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    
    # Verify position 1 was reduced
    test_db.refresh(position1)
    assert float(position1.quantity) == 5.0  # 10 - 5
    
    # Verify position 2 was NOT changed
    test_db.refresh(position2)
    assert float(position2.quantity) == 20.0  # unchanged


def test_create_transaction_cannot_sell_from_wrong_portfolio(client, test_db):
    """Test POST /api/transactions cannot sell asset not in specified portfolio"""
    # Create two portfolios and one asset
    portfolio1 = Portfolio(id=1, user_id=1, name="Portfolio 1", currency="USD")
    portfolio2 = Portfolio(id=2, user_id=1, name="Portfolio 2", currency="USD")
    asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add(portfolio1)
    test_db.add(portfolio2)
    test_db.add(asset)
    test_db.commit()
    
    # Create position only in portfolio 2
    position2 = PortfolioPosition(
        portfolio_id=2,
        asset_id=1,
        quantity=20.0,
        average_buy_price=110.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position2)
    test_db.commit()
    
    # Try to sell from portfolio 1 (which doesn't have this asset)
    response = client.post("/api/transactions", json={
        "portfolio_id": 1,
        "asset_id": 1,
        "transaction_type": "sell",
        "quantity": 5.0,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Should fail because portfolio 1 doesn't have this asset
    assert response.status_code == 400
    assert "Cannot sell asset that is not in portfolio" in response.json()["detail"]


def test_create_transaction_multiple_portfolios_isolation(client, test_db):
    """Test that transactions in different portfolios are completely isolated"""
    # Create three portfolios and two assets
    portfolio1 = Portfolio(id=1, user_id=1, name="Portfolio 1", currency="USD")
    portfolio2 = Portfolio(id=2, user_id=1, name="Portfolio 2", currency="USD")
    portfolio3 = Portfolio(id=3, user_id=1, name="Portfolio 3", currency="USD")
    asset1 = Asset(id=1, symbol="AAPL", name="Apple Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    asset2 = Asset(id=2, symbol="GOOGL", name="Alphabet Inc.", asset_type="stock", exchange="NASDAQ", native_currency="USD")
    test_db.add_all([portfolio1, portfolio2, portfolio3, asset1, asset2])
    test_db.commit()
    
    # Create transactions in different portfolios
    transactions = [
        {"portfolio_id": 1, "asset_id": 1, "quantity": 10.0, "price": 150.0},
        {"portfolio_id": 1, "asset_id": 2, "quantity": 5.0, "price": 2800.0},
        {"portfolio_id": 2, "asset_id": 1, "quantity": 20.0, "price": 155.0},
        {"portfolio_id": 3, "asset_id": 2, "quantity": 15.0, "price": 2850.0},
    ]
    
    for txn in transactions:
        response = client.post("/api/transactions", json={
            **txn,
            "transaction_type": "buy",
            "timestamp": datetime.now().isoformat()
        })
        assert response.status_code == 200
    
    # Verify positions are correctly isolated
    # Portfolio 1 should have 2 positions
    p1_positions = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(p1_positions) == 2
    
    # Portfolio 2 should have 1 position
    p2_positions = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 2
    ).all()
    assert len(p2_positions) == 1
    assert float(p2_positions[0].quantity) == 20.0
    
    # Portfolio 3 should have 1 position
    p3_positions = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 3
    ).all()
    assert len(p3_positions) == 1
    assert float(p3_positions[0].quantity) == 15.0
