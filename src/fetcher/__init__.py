"""
Fetcher Module - Market Data Collection

This module provides classes for fetching market data from various sources.

Classes:
    - BaseFetcher: Abstract base class for all fetchers
    - StockFetcher: Fetch stock data from Yahoo Finance
    - CryptoFetcher: Fetch crypto data (placeholder)
    - FetcherFactory: Create appropriate fetcher for asset type

Usage:
    from fetcher import FetcherFactory
    from datetime import datetime, timedelta
    
    # Create fetcher
    fetcher = FetcherFactory.create_fetcher("stock")
    
    # Fetch historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = fetcher.fetch_historical("AAPL", start_date, end_date)
    
    # Fetch current price
    current = fetcher.fetch_current("AAPL")
"""

from .fetcher import (
    BaseFetcher,
    StockFetcher,
    CryptoFetcher,
    FetcherFactory,
    PriceData,
    AssetData
)

__all__ = [
    "BaseFetcher",
    "StockFetcher", 
    "CryptoFetcher",
    "FetcherFactory",
    "PriceData",
    "AssetData"
]
