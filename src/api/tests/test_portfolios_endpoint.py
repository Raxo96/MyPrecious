"""Tests for portfolio endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
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


def test_get_all_portfolios_empty(client, test_db):
    """Test GET /api/portfolios returns empty list when no portfolios exist"""
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    assert "portfolios" in data
    assert data["portfolios"] == []


def test_get_all_portfolios_single(client, test_db):
    """Test GET /api/portfolios returns single portfolio with correct fields"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    
    assert "portfolios" in data
    assert len(data["portfolios"]) == 1
    
    portfolio_data = data["portfolios"][0]
    assert portfolio_data["id"] == 1
    assert portfolio_data["name"] == "Test Portfolio"
    assert portfolio_data["total_value_usd"] == 0.0
    assert portfolio_data["total_return_pct"] == 0.0
    assert portfolio_data["position_count"] == 0
    assert "created_at" in portfolio_data


def test_get_all_portfolios_with_positions(client, test_db):
    """Test GET /api/portfolios calculates values correctly with positions"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create asset
    asset = Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset)
    
    # Create position
    position = PortfolioPosition(
        id=1,
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position)
    
    # Create price
    price = AssetPrice(
        id=1,
        asset_id=1,
        timestamp=datetime.now(),
        open=150.0,
        high=155.0,
        low=149.0,
        close=150.0,
        volume=1000000,
        source="test"
    )
    test_db.add(price)
    test_db.commit()
    
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["portfolios"]) == 1
    portfolio_data = data["portfolios"][0]
    
    # 10 shares * $150 = $1500 total value
    assert portfolio_data["total_value_usd"] == 1500.0
    
    # Cost: 10 * $100 = $1000
    # Value: 10 * $150 = $1500
    # Return: ($1500 - $1000) / $1000 * 100 = 50%
    assert portfolio_data["total_return_pct"] == 50.0
    
    assert portfolio_data["position_count"] == 1


def test_get_all_portfolios_multiple(client, test_db):
    """Test GET /api/portfolios returns multiple portfolios ordered by created_at DESC"""
    # Create portfolios with different timestamps
    now = datetime.now()
    
    portfolio1 = Portfolio(
        id=1,
        user_id=1,
        name="Old Portfolio",
        currency="USD",
        created_at=now - timedelta(days=10)
    )
    test_db.add(portfolio1)
    
    portfolio2 = Portfolio(
        id=2,
        user_id=1,
        name="New Portfolio",
        currency="USD",
        created_at=now
    )
    test_db.add(portfolio2)
    
    portfolio3 = Portfolio(
        id=3,
        user_id=1,
        name="Middle Portfolio",
        currency="USD",
        created_at=now - timedelta(days=5)
    )
    test_db.add(portfolio3)
    test_db.commit()
    
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["portfolios"]) == 3
    
    # Should be ordered by created_at DESC (newest first)
    assert data["portfolios"][0]["name"] == "New Portfolio"
    assert data["portfolios"][1]["name"] == "Middle Portfolio"
    assert data["portfolios"][2]["name"] == "Old Portfolio"


def test_get_all_portfolios_filters_by_user(client, test_db):
    """Test GET /api/portfolios only returns portfolios for user_id=1"""
    # Create portfolios for different users
    portfolio1 = Portfolio(
        id=1,
        user_id=1,
        name="User 1 Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio1)
    
    portfolio2 = Portfolio(
        id=2,
        user_id=2,
        name="User 2 Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio2)
    test_db.commit()
    
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    
    # Should only return user_id=1 portfolio
    assert len(data["portfolios"]) == 1
    assert data["portfolios"][0]["name"] == "User 1 Portfolio"


def test_get_all_portfolios_multiple_positions(client, test_db):
    """Test GET /api/portfolios correctly counts multiple positions"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create multiple assets and positions
    for i in range(3):
        asset = Asset(
            id=i+1,
            symbol=f"TEST{i}",
            name=f"Test Asset {i}",
            asset_type="stock",
            exchange="NASDAQ",
            native_currency="USD",
            is_active=True
        )
        test_db.add(asset)
        
        position = PortfolioPosition(
            id=i+1,
            portfolio_id=1,
            asset_id=i+1,
            quantity=10.0,
            average_buy_price=100.0,
            first_purchase_date=datetime.now().date()
        )
        test_db.add(position)
        
        price = AssetPrice(
            id=i+1,
            asset_id=i+1,
            timestamp=datetime.now(),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000,
            source="test"
        )
        test_db.add(price)
    
    test_db.commit()
    
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["portfolios"]) == 1
    assert data["portfolios"][0]["position_count"] == 3


def test_create_portfolio_success(client, test_db):
    """Test POST /api/portfolios creates a portfolio successfully"""
    response = client.post(
        "/api/portfolios",
        json={"name": "My New Portfolio", "currency": "USD"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["name"] == "My New Portfolio"
    assert data["currency"] == "USD"
    assert "created_at" in data
    
    # Verify portfolio was created in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == data["id"]).first()
    assert portfolio is not None
    assert portfolio.name == "My New Portfolio"
    assert portfolio.currency == "USD"
    assert portfolio.user_id == 1


def test_create_portfolio_default_currency(client, test_db):
    """Test POST /api/portfolios uses default currency when not provided"""
    response = client.post(
        "/api/portfolios",
        json={"name": "Test Portfolio"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["currency"] == "USD"


def test_create_portfolio_empty_name(client, test_db):
    """Test POST /api/portfolios rejects empty name"""
    response = client.post(
        "/api/portfolios",
        json={"name": "", "currency": "USD"}
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_create_portfolio_whitespace_name(client, test_db):
    """Test POST /api/portfolios rejects whitespace-only name"""
    response = client.post(
        "/api/portfolios",
        json={"name": "   ", "currency": "USD"}
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower() or "whitespace" in response.json()["detail"].lower()


def test_create_portfolio_trims_whitespace(client, test_db):
    """Test POST /api/portfolios trims leading/trailing whitespace from name"""
    response = client.post(
        "/api/portfolios",
        json={"name": "  Test Portfolio  ", "currency": "USD"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Test Portfolio"
    
    # Verify in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == data["id"]).first()
    assert portfolio.name == "Test Portfolio"


def test_create_portfolio_unique_id(client, test_db):
    """Test POST /api/portfolios assigns unique IDs to multiple portfolios"""
    # Create first portfolio
    response1 = client.post(
        "/api/portfolios",
        json={"name": "Portfolio 1"}
    )
    assert response1.status_code == 200
    id1 = response1.json()["id"]
    
    # Create second portfolio
    response2 = client.post(
        "/api/portfolios",
        json={"name": "Portfolio 2"}
    )
    assert response2.status_code == 200
    id2 = response2.json()["id"]
    
    # IDs should be different
    assert id1 != id2


def test_create_portfolio_has_timestamp(client, test_db):
    """Test POST /api/portfolios assigns creation timestamp"""
    before = datetime.now()
    
    response = client.post(
        "/api/portfolios",
        json={"name": "Test Portfolio"}
    )
    
    after = datetime.now()
    
    assert response.status_code == 200
    data = response.json()
    
    created_at = datetime.fromisoformat(data["created_at"])
    
    # Timestamp should be between before and after
    assert before <= created_at <= after


def test_create_portfolio_starts_empty(client, test_db):
    """Test newly created portfolio has no positions"""
    # Create portfolio
    response = client.post(
        "/api/portfolios",
        json={"name": "Test Portfolio"}
    )
    
    assert response.status_code == 200
    portfolio_id = response.json()["id"]
    
    # Query positions for this portfolio
    positions = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == portfolio_id
    ).all()
    
    assert len(positions) == 0


def test_create_portfolio_appears_in_list(client, test_db):
    """Test created portfolio appears in GET /api/portfolios"""
    # Create portfolio
    response = client.post(
        "/api/portfolios",
        json={"name": "New Portfolio"}
    )
    
    assert response.status_code == 200
    portfolio_id = response.json()["id"]
    
    # Get all portfolios
    list_response = client.get("/api/portfolios")
    assert list_response.status_code == 200
    
    portfolios = list_response.json()["portfolios"]
    
    # Find the created portfolio
    created_portfolio = next((p for p in portfolios if p["id"] == portfolio_id), None)
    assert created_portfolio is not None
    assert created_portfolio["name"] == "New Portfolio"
    assert created_portfolio["position_count"] == 0
    assert created_portfolio["total_value_usd"] == 0.0


def test_update_portfolio_success(client, test_db):
    """Test PUT /api/portfolios/:id updates portfolio name successfully"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Update the portfolio
    response = client.put(
        "/api/portfolios/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == 1
    assert data["name"] == "Updated Name"
    assert data["currency"] == "USD"
    assert "created_at" in data
    
    # Verify portfolio was updated in database
    updated_portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert updated_portfolio.name == "Updated Name"


def test_update_portfolio_not_found(client, test_db):
    """Test PUT /api/portfolios/:id returns 404 for non-existent portfolio"""
    response = client.put(
        "/api/portfolios/999",
        json={"name": "New Name"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_portfolio_empty_name(client, test_db):
    """Test PUT /api/portfolios/:id rejects empty name"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Try to update with empty name
    response = client.put(
        "/api/portfolios/1",
        json={"name": ""}
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
    
    # Verify portfolio name was not changed
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio.name == "Original Name"


def test_update_portfolio_whitespace_name(client, test_db):
    """Test PUT /api/portfolios/:id rejects whitespace-only name"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Try to update with whitespace-only name
    response = client.put(
        "/api/portfolios/1",
        json={"name": "   "}
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower() or "whitespace" in response.json()["detail"].lower()
    
    # Verify portfolio name was not changed
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio.name == "Original Name"


def test_update_portfolio_trims_whitespace(client, test_db):
    """Test PUT /api/portfolios/:id trims leading/trailing whitespace from name"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Update with whitespace around name
    response = client.put(
        "/api/portfolios/1",
        json={"name": "  Updated Name  "}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Updated Name"
    
    # Verify in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio.name == "Updated Name"


def test_update_portfolio_preserves_currency(client, test_db):
    """Test PUT /api/portfolios/:id preserves currency when updating name"""
    # Create a portfolio with EUR currency
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="EUR",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Update the name
    response = client.put(
        "/api/portfolios/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Currency should remain EUR
    assert data["currency"] == "EUR"
    
    # Verify in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio.currency == "EUR"


def test_update_portfolio_preserves_created_at(client, test_db):
    """Test PUT /api/portfolios/:id preserves creation timestamp"""
    # Create a portfolio with specific timestamp
    original_timestamp = datetime.now() - timedelta(days=10)
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=original_timestamp
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Update the name
    response = client.put(
        "/api/portfolios/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify created_at is preserved
    returned_timestamp = datetime.fromisoformat(data["created_at"])
    assert abs((returned_timestamp - original_timestamp).total_seconds()) < 1
    
    # Verify in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert abs((portfolio.created_at - original_timestamp).total_seconds()) < 1


def test_update_portfolio_appears_in_list(client, test_db):
    """Test updated portfolio name appears in GET /api/portfolios"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Update the portfolio
    response = client.put(
        "/api/portfolios/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    
    # Get all portfolios
    list_response = client.get("/api/portfolios")
    assert list_response.status_code == 200
    
    portfolios = list_response.json()["portfolios"]
    
    # Find the updated portfolio
    updated_portfolio = next((p for p in portfolios if p["id"] == 1), None)
    assert updated_portfolio is not None
    assert updated_portfolio["name"] == "Updated Name"


def test_update_portfolio_with_positions(client, test_db):
    """Test PUT /api/portfolios/:id works correctly when portfolio has positions"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Original Name",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create asset and position
    asset = Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset)
    
    position = PortfolioPosition(
        id=1,
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position)
    test_db.commit()
    
    # Update the portfolio name
    response = client.put(
        "/api/portfolios/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    
    # Verify positions are still intact
    positions = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions) == 1
    assert positions[0].quantity == 10.0


def test_update_portfolio_multiple_times(client, test_db):
    """Test PUT /api/portfolios/:id can be called multiple times"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Name 1",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # First update
    response1 = client.put(
        "/api/portfolios/1",
        json={"name": "Name 2"}
    )
    assert response1.status_code == 200
    assert response1.json()["name"] == "Name 2"
    
    # Second update
    response2 = client.put(
        "/api/portfolios/1",
        json={"name": "Name 3"}
    )
    assert response2.status_code == 200
    assert response2.json()["name"] == "Name 3"
    
    # Verify final state in database
    portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio.name == "Name 3"


def test_delete_portfolio_success(client, test_db):
    """Test DELETE /api/portfolios/:id deletes portfolio successfully"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Delete the portfolio
    response = client.delete("/api/portfolios/1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "deleted" in data["message"].lower()
    
    # Verify portfolio was deleted from database
    deleted_portfolio = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert deleted_portfolio is None


def test_delete_portfolio_not_found(client, test_db):
    """Test DELETE /api/portfolios/:id returns 404 for non-existent portfolio"""
    response = client.delete("/api/portfolios/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_portfolio_removes_from_list(client, test_db):
    """Test deleted portfolio no longer appears in GET /api/portfolios"""
    # Create two portfolios
    portfolio1 = Portfolio(
        id=1,
        user_id=1,
        name="Portfolio 1",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio1)
    
    portfolio2 = Portfolio(
        id=2,
        user_id=1,
        name="Portfolio 2",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio2)
    test_db.commit()
    
    # Delete first portfolio
    response = client.delete("/api/portfolios/1")
    assert response.status_code == 200
    
    # Get all portfolios
    list_response = client.get("/api/portfolios")
    assert list_response.status_code == 200
    
    portfolios = list_response.json()["portfolios"]
    
    # Should only have portfolio 2
    assert len(portfolios) == 1
    assert portfolios[0]["id"] == 2
    assert portfolios[0]["name"] == "Portfolio 2"


def test_delete_portfolio_with_positions_cascade(client, test_db):
    """Test DELETE /api/portfolios/:id removes associated positions (CASCADE)"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create asset
    asset = Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset)
    
    # Create position
    position = PortfolioPosition(
        id=1,
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position)
    test_db.commit()
    
    # Verify position exists
    positions_before = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions_before) == 1
    
    # Delete the portfolio
    response = client.delete("/api/portfolios/1")
    assert response.status_code == 200
    
    # Verify positions were deleted (CASCADE)
    positions_after = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions_after) == 0


def test_delete_portfolio_with_transactions_cascade(client, test_db):
    """Test DELETE /api/portfolios/:id removes associated transactions (CASCADE)"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create asset
    asset = Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset)
    
    # Create transaction
    transaction = Transaction(
        id=1,
        portfolio_id=1,
        asset_id=1,
        transaction_type="buy",
        quantity=10.0,
        price=100.0,
        transaction_date=datetime.now().date(),
        notes="Test transaction"
    )
    test_db.add(transaction)
    test_db.commit()
    
    # Verify transaction exists
    transactions_before = test_db.query(Transaction).filter(
        Transaction.portfolio_id == 1
    ).all()
    assert len(transactions_before) == 1
    
    # Delete the portfolio
    response = client.delete("/api/portfolios/1")
    assert response.status_code == 200
    
    # Verify transactions were deleted (CASCADE)
    transactions_after = test_db.query(Transaction).filter(
        Transaction.portfolio_id == 1
    ).all()
    assert len(transactions_after) == 0


def test_delete_portfolio_with_multiple_positions_and_transactions(client, test_db):
    """Test DELETE /api/portfolios/:id removes all associated data (CASCADE)"""
    # Create portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    
    # Create multiple assets, positions, and transactions
    for i in range(3):
        asset = Asset(
            id=i+1,
            symbol=f"TEST{i}",
            name=f"Test Asset {i}",
            asset_type="stock",
            exchange="NASDAQ",
            native_currency="USD",
            is_active=True
        )
        test_db.add(asset)
        
        position = PortfolioPosition(
            id=i+1,
            portfolio_id=1,
            asset_id=i+1,
            quantity=10.0,
            average_buy_price=100.0,
            first_purchase_date=datetime.now().date()
        )
        test_db.add(position)
        
        transaction = Transaction(
            id=i+1,
            portfolio_id=1,
            asset_id=i+1,
            transaction_type="buy",
            quantity=10.0,
            price=100.0,
            transaction_date=datetime.now().date(),
            notes=f"Test transaction {i}"
        )
        test_db.add(transaction)
    
    test_db.commit()
    
    # Verify data exists
    positions_before = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions_before) == 3
    
    transactions_before = test_db.query(Transaction).filter(
        Transaction.portfolio_id == 1
    ).all()
    assert len(transactions_before) == 3
    
    # Delete the portfolio
    response = client.delete("/api/portfolios/1")
    assert response.status_code == 200
    
    # Verify all data was deleted (CASCADE)
    positions_after = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions_after) == 0
    
    transactions_after = test_db.query(Transaction).filter(
        Transaction.portfolio_id == 1
    ).all()
    assert len(transactions_after) == 0


def test_delete_portfolio_does_not_affect_other_portfolios(client, test_db):
    """Test DELETE /api/portfolios/:id only deletes the specified portfolio"""
    # Create two portfolios
    portfolio1 = Portfolio(
        id=1,
        user_id=1,
        name="Portfolio 1",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio1)
    
    portfolio2 = Portfolio(
        id=2,
        user_id=1,
        name="Portfolio 2",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio2)
    
    # Create assets
    asset1 = Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset1)
    
    asset2 = Asset(
        id=2,
        symbol="GOOGL",
        name="Alphabet Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        native_currency="USD",
        is_active=True
    )
    test_db.add(asset2)
    
    # Create positions for both portfolios
    position1 = PortfolioPosition(
        id=1,
        portfolio_id=1,
        asset_id=1,
        quantity=10.0,
        average_buy_price=100.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position1)
    
    position2 = PortfolioPosition(
        id=2,
        portfolio_id=2,
        asset_id=2,
        quantity=20.0,
        average_buy_price=200.0,
        first_purchase_date=datetime.now().date()
    )
    test_db.add(position2)
    test_db.commit()
    
    # Delete first portfolio
    response = client.delete("/api/portfolios/1")
    assert response.status_code == 200
    
    # Verify portfolio 1 is deleted
    portfolio1_after = test_db.query(Portfolio).filter(Portfolio.id == 1).first()
    assert portfolio1_after is None
    
    # Verify portfolio 2 still exists
    portfolio2_after = test_db.query(Portfolio).filter(Portfolio.id == 2).first()
    assert portfolio2_after is not None
    assert portfolio2_after.name == "Portfolio 2"
    
    # Verify portfolio 1 positions are deleted
    positions1_after = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 1
    ).all()
    assert len(positions1_after) == 0
    
    # Verify portfolio 2 positions still exist
    positions2_after = test_db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == 2
    ).all()
    assert len(positions2_after) == 1
    assert positions2_after[0].quantity == 20.0


def test_delete_portfolio_get_returns_404(client, test_db):
    """Test GET /api/portfolios/:id returns 404 after deletion"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # Verify portfolio exists
    get_response = client.get("/api/portfolios/1")
    assert get_response.status_code == 200
    
    # Delete the portfolio
    delete_response = client.delete("/api/portfolios/1")
    assert delete_response.status_code == 200
    
    # Try to get the deleted portfolio
    get_after_delete = client.get("/api/portfolios/1")
    assert get_after_delete.status_code == 404


def test_delete_portfolio_idempotent_404(client, test_db):
    """Test DELETE /api/portfolios/:id returns 404 when called twice"""
    # Create a portfolio
    portfolio = Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        currency="USD",
        created_at=datetime.now()
    )
    test_db.add(portfolio)
    test_db.commit()
    
    # First delete succeeds
    response1 = client.delete("/api/portfolios/1")
    assert response1.status_code == 200
    
    # Second delete returns 404
    response2 = client.delete("/api/portfolios/1")
    assert response2.status_code == 404
