from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

from database import get_db
from models import Asset, AssetPrice, Portfolio, PortfolioPosition, Transaction

app = FastAPI(title="Portfolio Tracker API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: str
    exchange: str
    current_price: float = 0.0

class PositionResponse(BaseModel):
    symbol: str
    name: str
    quantity: float
    current_price: float
    value: float
    change: float = 0.0

class PortfolioResponse(BaseModel):
    id: int
    name: str
    total_value: float
    day_change: float = 0.0

class TransactionCreate(BaseModel):
    asset_id: int
    quantity: float
    price: float
    timestamp: str

# Routes
@app.get("/")
def root():
    return {"message": "Portfolio Tracker API", "status": "running"}

@app.get("/api/assets/search")
def search_assets(q: str = "", db: Session = Depends(get_db)):
    """Search assets by symbol or name"""
    query = db.query(Asset).filter(Asset.is_active == True)
    
    if q:
        search = f"%{q}%"
        query = query.filter(
            (Asset.symbol.ilike(search)) | (Asset.name.ilike(search))
        )
    
    assets = query.limit(20).all()
    
    # Get latest prices
    result = []
    for asset in assets:
        latest_price = db.query(AssetPrice).filter(
            AssetPrice.asset_id == asset.id
        ).order_by(desc(AssetPrice.timestamp)).first()
        
        result.append({
            "id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "exchange": asset.exchange,
            "current_price": float(latest_price.close) if latest_price else 0.0
        })
    
    return {"assets": result}

@app.get("/api/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get portfolio summary with P&L"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Calculate total value and cost
    positions = db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == portfolio_id
    ).all()
    
    total_value = 0.0
    total_cost = 0.0
    
    for pos in positions:
        latest_price = db.query(AssetPrice).filter(
            AssetPrice.asset_id == pos.asset_id
        ).order_by(desc(AssetPrice.timestamp)).first()
        
        if latest_price:
            total_value += float(pos.quantity) * float(latest_price.close)
            total_cost += float(pos.quantity) * float(pos.average_buy_price)
    
    total_profit_loss = total_value - total_cost
    total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "total_profit_loss_pct": round(total_profit_loss_pct, 2),
        "day_change": 0.0  # TODO: Calculate from snapshots
    }

@app.get("/api/portfolios/{portfolio_id}/positions")
def get_positions(portfolio_id: int, db: Session = Depends(get_db)):
    """Get portfolio positions with P&L"""
    positions = db.query(PortfolioPosition, Asset).join(
        Asset, PortfolioPosition.asset_id == Asset.id
    ).filter(PortfolioPosition.portfolio_id == portfolio_id).all()
    
    result = []
    total_cost = 0.0
    total_value = 0.0
    
    for pos, asset in positions:
        latest_price = db.query(AssetPrice).filter(
            AssetPrice.asset_id == asset.id
        ).order_by(desc(AssetPrice.timestamp)).first()
        
        current_price = float(latest_price.close) if latest_price else 0.0
        quantity = float(pos.quantity)
        avg_buy_price = float(pos.average_buy_price)
        
        cost_basis = quantity * avg_buy_price
        current_value = quantity * current_price
        profit_loss = current_value - cost_basis
        profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0.0
        
        total_cost += cost_basis
        total_value += current_value
        
        result.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "quantity": quantity,
            "average_buy_price": avg_buy_price,
            "current_price": current_price,
            "cost_basis": round(cost_basis, 2),
            "value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2)
        })
    
    return {
        "positions": result,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_value": round(total_value, 2),
            "total_profit_loss": round(total_value - total_cost, 2),
            "total_profit_loss_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0
        }
    }

@app.post("/api/transactions")
def create_transaction(
    transaction: TransactionCreate,
    portfolio_id: int = 1,  # Default to first portfolio
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    # Create transaction
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=transaction.asset_id,
        transaction_type="buy",
        quantity=transaction.quantity,
        price=transaction.price,
        timestamp=datetime.fromisoformat(transaction.timestamp),
        fee=0.0
    )
    db.add(new_transaction)
    
    # Update or create position
    position = db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == portfolio_id,
        PortfolioPosition.asset_id == transaction.asset_id
    ).first()
    
    if position:
        # Update existing position
        total_cost = float(position.quantity) * float(position.average_buy_price)
        new_cost = transaction.quantity * transaction.price
        new_quantity = float(position.quantity) + transaction.quantity
        
        position.quantity = new_quantity
        position.average_buy_price = (total_cost + new_cost) / new_quantity
        position.last_updated = datetime.now()
    else:
        # Create new position
        position = PortfolioPosition(
            portfolio_id=portfolio_id,
            asset_id=transaction.asset_id,
            quantity=transaction.quantity,
            average_buy_price=transaction.price,
            first_purchase_date=datetime.fromisoformat(transaction.timestamp).date()
        )
        db.add(position)
    
    db.commit()
    
    return {"message": "Transaction created", "id": new_transaction.id}

@app.get("/api/assets/{asset_id}/prices")
def get_asset_prices(asset_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get historical prices for an asset"""
    cutoff = datetime.now() - timedelta(days=days)
    
    prices = db.query(AssetPrice).filter(
        AssetPrice.asset_id == asset_id,
        AssetPrice.timestamp >= cutoff
    ).order_by(AssetPrice.timestamp).all()
    
    return {
        "prices": [
            {
                "time": int(p.timestamp.timestamp()),
                "value": float(p.close)
            }
            for p in prices
        ]
    }

@app.get("/api/portfolios/{portfolio_id}/history")
def get_portfolio_history(portfolio_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get portfolio value history"""
    cutoff = datetime.now() - timedelta(days=days)
    
    # Get all positions
    positions = db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == portfolio_id
    ).all()
    
    if not positions:
        return {"history": []}
    
    # Get unique timestamps from all assets
    timestamps = db.query(AssetPrice.timestamp).filter(
        AssetPrice.asset_id.in_([p.asset_id for p in positions]),
        AssetPrice.timestamp >= cutoff
    ).distinct().order_by(AssetPrice.timestamp).all()
    
    history = []
    for (ts,) in timestamps:
        total_value = 0.0
        for pos in positions:
            price = db.query(AssetPrice).filter(
                AssetPrice.asset_id == pos.asset_id,
                AssetPrice.timestamp <= ts
            ).order_by(desc(AssetPrice.timestamp)).first()
            
            if price:
                total_value += float(pos.quantity) * float(price.close)
        
        if total_value > 0:
            history.append({
                "time": int(ts.timestamp()),
                "value": round(total_value, 2)
            })
    
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
