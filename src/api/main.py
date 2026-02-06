from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

from database import get_db
from models import Asset, AssetPrice, Portfolio, PortfolioPosition, Transaction, FetcherLog, FetcherStatistics, PriceUpdateLog

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
    transaction_type: str
    quantity: float
    price: float
    fee: float = 0.0
    timestamp: str
    notes: str = None

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

@app.get("/api/assets/{asset_symbol}")
def get_asset_by_symbol(asset_symbol: str, db: Session = Depends(get_db)):
    """Get asset details by symbol (case-insensitive)"""
    # Look up asset by symbol (case-insensitive)
    asset = db.query(Asset).filter(
        func.lower(Asset.symbol) == asset_symbol.lower(),
        Asset.is_active == True
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Query latest price from AssetPrice table
    latest_price = db.query(AssetPrice).filter(
        AssetPrice.asset_id == asset.id
    ).order_by(desc(AssetPrice.timestamp)).first()
    
    # Return asset details with current_price
    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "exchange": asset.exchange,
        "current_price": float(latest_price.close) if latest_price else 0.0
    }

@app.get("/api/assets/{asset_symbol}/chart")
def get_asset_chart(asset_symbol: str, db: Session = Depends(get_db)):
    """Get asset price changes for multiple time periods"""
    # Look up asset by symbol (case-insensitive)
    asset = db.query(Asset).filter(
        func.lower(Asset.symbol) == asset_symbol.lower(),
        Asset.is_active == True
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get current price (most recent AssetPrice record)
    latest_price_record = db.query(AssetPrice).filter(
        AssetPrice.asset_id == asset.id
    ).order_by(desc(AssetPrice.timestamp)).first()
    
    current_price = float(latest_price_record.close) if latest_price_record else 0.0
    
    # Helper function to get market close price for a given date
    def get_market_close_price(target_date):
        """
        Get the price closest to market close (4:00 PM ET / 9:00 PM UTC) for a given date.
        Falls back to the most recent price before the target date if no price exists on that exact date.
        """
        # Market close is around 21:00 UTC (4:00 PM ET)
        market_close_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
        
        # Try to find price within 2 hours of market close on the target date
        price_near_close = db.query(AssetPrice).filter(
            AssetPrice.asset_id == asset.id,
            AssetPrice.timestamp >= market_close_time - timedelta(hours=2),
            AssetPrice.timestamp <= market_close_time + timedelta(hours=2)
        ).order_by(
            func.abs(func.extract('epoch', AssetPrice.timestamp - market_close_time))
        ).first()
        
        if price_near_close:
            return price_near_close
        
        # Fallback: get the most recent price at or before the target date
        return db.query(AssetPrice).filter(
            AssetPrice.asset_id == asset.id,
            AssetPrice.timestamp <= target_date
        ).order_by(desc(AssetPrice.timestamp)).first()
    
    # Time period mappings (in days)
    time_periods = {
        "1D": 1,
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365
    }
    
    # Calculate price changes for each period
    price_changes = {}
    now = datetime.now()
    
    for period_name, days in time_periods.items():
        # Calculate target date (N days ago)
        target_date = now - timedelta(days=days)
        
        # Get market close price for that date
        historical_price_record = get_market_close_price(target_date)
        
        # Calculate percentage change if historical price exists
        if historical_price_record and current_price > 0:
            historical_price = float(historical_price_record.close)
            if historical_price > 0:
                # Formula: ((current - historical) / historical) * 100
                price_change = ((current_price - historical_price) / historical_price) * 100
                price_changes[period_name] = price_change
            else:
                price_changes[period_name] = None
        else:
            price_changes[period_name] = None
    
    return {
        "symbol": asset.symbol,
        "current_price": current_price,
        "price_changes": price_changes
    }

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
    
    total_return = total_value - total_cost
    total_return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "total_value_usd": round(total_value, 2),
        "total_invested_usd": round(total_cost, 2),
        "total_return_usd": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "day_change_pct": 0.0  # TODO: Calculate from snapshots
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
        unrealized_gain = current_value - cost_basis
        unrealized_gain_pct = (unrealized_gain / cost_basis * 100) if cost_basis > 0 else 0.0
        
        total_cost += cost_basis
        total_value += current_value
        
        result.append({
            "asset_id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "quantity": quantity,
            "average_buy_price": avg_buy_price,
            "current_price": current_price,
            "cost_basis": round(cost_basis, 2),
            "current_value": round(current_value, 2),
            "unrealized_gain": round(unrealized_gain, 2),
            "unrealized_gain_pct": round(unrealized_gain_pct, 2)
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
    # Validate transaction type
    if transaction.transaction_type not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Transaction type must be 'buy' or 'sell'")
    
    # Create transaction
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=transaction.asset_id,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=transaction.price,
        timestamp=datetime.fromisoformat(transaction.timestamp),
        fee=transaction.fee,
        notes=transaction.notes
    )
    db.add(new_transaction)
    
    # Update or create position
    position = db.query(PortfolioPosition).filter(
        PortfolioPosition.portfolio_id == portfolio_id,
        PortfolioPosition.asset_id == transaction.asset_id
    ).first()
    
    if transaction.transaction_type == "buy":
        if position:
            # Update existing position - add to quantity
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
    
    elif transaction.transaction_type == "sell":
        if not position:
            raise HTTPException(status_code=400, detail="Cannot sell asset that is not in portfolio")
        
        if float(position.quantity) < transaction.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity. Available: {position.quantity}, Requested: {transaction.quantity}")
        
        # Reduce position quantity
        new_quantity = float(position.quantity) - transaction.quantity
        
        if new_quantity == 0:
            # Remove position if fully sold
            db.delete(position)
        else:
            # Update position with reduced quantity (keep same average buy price)
            position.quantity = new_quantity
            position.last_updated = datetime.now()
    
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

# Fetcher API endpoints
@app.get("/api/fetcher/status")
def get_fetcher_status(db: Session = Depends(get_db)):
    """Get current fetcher daemon status"""
    # Get latest statistics entry for uptime and cycle info
    latest_stats = db.query(FetcherStatistics).order_by(
        desc(FetcherStatistics.timestamp)
    ).first()
    
    # Get latest price update to determine if daemon is running
    latest_price_update = db.query(PriceUpdateLog).order_by(
        desc(PriceUpdateLog.timestamp)
    ).first()
    
    if not latest_price_update:
        return {
            "status": "stopped",
            "uptime_seconds": 0,
            "last_update": None,
            "next_update_in_seconds": None,
            "tracked_assets_count": 0,
            "update_interval_minutes": 10
        }
    
    # Check if daemon is running (last update within 15 minutes)
    now = datetime.now()
    time_since_update = (now - latest_price_update.timestamp).total_seconds()
    is_running = time_since_update < 900  # 15 minutes
    
    # Calculate next update time (10-minute intervals)
    update_interval_seconds = 600  # 10 minutes
    next_update_in_seconds = update_interval_seconds - (time_since_update % update_interval_seconds)
    
    # Get tracked assets count
    tracked_assets_count = db.query(func.count(Asset.id)).filter(
        Asset.is_active == True
    ).scalar()
    
    # Get uptime from statistics if available
    uptime_seconds = latest_stats.uptime_seconds if latest_stats else 0
    
    return {
        "status": "running" if is_running else "stopped",
        "uptime_seconds": int(uptime_seconds),
        "last_update": latest_price_update.timestamp.isoformat(),
        "next_update_in_seconds": int(next_update_in_seconds) if is_running else None,
        "tracked_assets_count": tracked_assets_count or 0,
        "update_interval_minutes": 10
    }

@app.get("/api/fetcher/logs")
def get_fetcher_logs(
    limit: int = 100,
    offset: int = 0,
    level: str = None,
    db: Session = Depends(get_db)
):
    """Get fetcher logs with pagination and filtering"""
    # Build query
    query = db.query(FetcherLog)
    
    # Filter by level if provided
    if level:
        query = query.filter(FetcherLog.level == level.upper())
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    logs = query.order_by(desc(FetcherLog.timestamp)).offset(offset).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "context": log.context
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/fetcher/statistics")
def get_fetcher_statistics(db: Session = Depends(get_db)):
    """Get fetcher performance statistics"""
    # Get latest statistics entry
    latest_stats = db.query(FetcherStatistics).order_by(
        desc(FetcherStatistics.timestamp)
    ).first()
    
    if not latest_stats:
        return {
            "uptime_seconds": 0,
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "success_rate": 0.0,
            "average_cycle_duration_seconds": 0.0,
            "last_cycle_duration_seconds": 0.0,
            "assets_tracked": 0
        }
    
    # Get last cycle duration from logs
    last_cycle_log = db.query(FetcherLog).filter(
        FetcherLog.message.like('%cycle complete%')
    ).order_by(desc(FetcherLog.timestamp)).first()
    
    last_cycle_duration = 0.0
    if last_cycle_log and last_cycle_log.context:
        last_cycle_duration = last_cycle_log.context.get('duration_seconds', 0.0)
    
    return {
        "uptime_seconds": int(latest_stats.uptime_seconds),
        "total_cycles": int(latest_stats.total_cycles),
        "successful_cycles": int(latest_stats.successful_cycles),
        "failed_cycles": int(latest_stats.failed_cycles),
        "success_rate": float(latest_stats.success_rate),
        "average_cycle_duration_seconds": float(latest_stats.average_cycle_duration),
        "last_cycle_duration_seconds": last_cycle_duration,
        "assets_tracked": int(latest_stats.assets_tracked)
    }

@app.get("/api/fetcher/recent-updates")
def get_recent_updates(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent price updates with asset information"""
    # Query price_update_log with asset join
    updates = db.query(PriceUpdateLog, Asset).join(
        Asset, PriceUpdateLog.asset_id == Asset.id
    ).order_by(desc(PriceUpdateLog.timestamp)).limit(limit).all()
    
    return {
        "updates": [
            {
                "symbol": asset.symbol,
                "name": asset.name,
                "timestamp": update.timestamp.isoformat(),
                "price": float(update.price) if update.price else 0.0,
                "success": update.success,
                "error": update.error_message
            }
            for update, asset in updates
        ]
    }

@app.post("/api/fetcher/trigger-update")
def trigger_price_update(db: Session = Depends(get_db)):
    """Manually trigger a price update cycle"""
    # Send a notification to trigger the daemon
    # We'll use a special notification that the daemon can listen for
    try:
        # Execute a NOTIFY command to trigger the update
        from sqlalchemy import text
        db.execute(text("NOTIFY price_update_trigger, 'manual_trigger'"))
        db.commit()
        
        return {
            "success": True,
            "message": "Price update triggered successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to trigger update: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
