from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Date, Text, Boolean, BigInteger
from sqlalchemy.sql import func
from database import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50))
    name = Column(String(255))
    asset_type = Column(String(20))
    exchange = Column(String(50))
    native_currency = Column(String(3))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class AssetPrice(Base):
    __tablename__ = "asset_prices"
    
    id = Column(BigInteger, primary_key=True)
    asset_id = Column(Integer)
    timestamp = Column(TIMESTAMP)
    open = Column(DECIMAL(18, 8))
    high = Column(DECIMAL(18, 8))
    low = Column(DECIMAL(18, 8))
    close = Column(DECIMAL(18, 8))
    volume = Column(BigInteger)
    source = Column(String(50))

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(255))
    currency = Column(String(3))
    created_at = Column(TIMESTAMP, server_default=func.now())

class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer)
    asset_id = Column(Integer)
    quantity = Column(DECIMAL(18, 8))
    average_buy_price = Column(DECIMAL(18, 8))
    first_purchase_date = Column(Date)
    last_updated = Column(TIMESTAMP, server_default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(BigInteger, primary_key=True)
    portfolio_id = Column(Integer)
    asset_id = Column(Integer)
    transaction_type = Column(String(10))
    quantity = Column(DECIMAL(18, 8))
    price = Column(DECIMAL(18, 8))
    fee = Column(DECIMAL(18, 8), default=0)
    timestamp = Column(TIMESTAMP)
    notes = Column(Text)
