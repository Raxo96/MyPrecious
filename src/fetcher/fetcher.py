from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests


class PriceData:
    """Represents a single price point."""
    def __init__(self, timestamp: str, open: float, high: float, low: float, close: float, volume: int):
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


class AssetData:
    """Represents asset metadata and price history."""
    def __init__(self, symbol: str, name: str, asset_type: str, exchange: str, currency: str, prices: List[PriceData]):
        self.symbol = symbol
        self.name = name
        self.asset_type = asset_type
        self.exchange = exchange
        self.currency = currency
        self.prices = prices
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "exchange": self.exchange,
            "currency": self.currency,
            "prices": [p.to_dict() for p in self.prices]
        }


class BaseFetcher(ABC):
    """Abstract base class for asset data fetchers."""
    
    @abstractmethod
    def fetch_historical(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[AssetData]:
        """Fetch historical OHLCV data for a symbol."""
        pass
    
    @abstractmethod
    def fetch_current(self, symbol: str) -> Optional[PriceData]:
        """Fetch current price for a symbol."""
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol format is correct for this asset type."""
        pass


class StockFetcher(BaseFetcher):
    """Fetcher for stock market data using Yahoo Finance."""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
    
    def fetch_historical(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[AssetData]:
        """Fetch historical stock data from Yahoo Finance."""
        url = f"{self.base_url}/{symbol}"
        params = {
            "period1": int(start_date.timestamp()),
            "period2": int(end_date.timestamp()),
            "interval": "1d"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"]:
                return None
            
            result = data["chart"]["result"][0]
            
            if "timestamp" not in result or "indicators" not in result:
                return None
            
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            meta = result.get("meta", {})
            
            # Convert to PriceData objects
            prices = []
            for i, ts in enumerate(timestamps):
                if quotes["close"][i] is None:
                    continue
                
                prices.append(PriceData(
                    timestamp=datetime.fromtimestamp(ts).isoformat(),
                    open=round(quotes["open"][i], 2) if quotes["open"][i] else 0,
                    high=round(quotes["high"][i], 2) if quotes["high"][i] else 0,
                    low=round(quotes["low"][i], 2) if quotes["low"][i] else 0,
                    close=round(quotes["close"][i], 2),
                    volume=int(quotes["volume"][i]) if quotes["volume"][i] else 0
                ))
            
            return AssetData(
                symbol=symbol,
                name=meta.get("longName", symbol),
                asset_type="stock",
                exchange=meta.get("exchangeName", "UNKNOWN"),
                currency=meta.get("currency", "USD"),
                prices=prices
            )
        
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def fetch_current(self, symbol: str) -> Optional[PriceData]:
        """Fetch current stock price."""
        # Fetch last 2 days to get most recent price
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        asset_data = self.fetch_historical(symbol, start_date, end_date)
        
        if asset_data and asset_data.prices:
            return asset_data.prices[-1]  # Return most recent price
        
        return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format."""
        # Basic validation: 1-5 uppercase letters, optionally with dash
        import re
        return bool(re.match(r'^[A-Z]{1,5}(-[A-Z])?$', symbol))


class CryptoFetcher(BaseFetcher):
    """Fetcher for cryptocurrency data (placeholder for future implementation)."""
    
    def fetch_historical(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[AssetData]:
        """Fetch historical crypto data."""
        # TODO: Implement using ccxt or CoinGecko API
        raise NotImplementedError("Crypto fetcher not yet implemented")
    
    def fetch_current(self, symbol: str) -> Optional[PriceData]:
        """Fetch current crypto price."""
        # TODO: Implement using ccxt or CoinGecko API
        raise NotImplementedError("Crypto fetcher not yet implemented")
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate crypto symbol format."""
        # TODO: Implement crypto symbol validation
        return True


class FetcherFactory:
    """Factory for creating appropriate fetchers based on asset type."""
    
    @staticmethod
    def create_fetcher(asset_type: str) -> BaseFetcher:
        """Create and return appropriate fetcher for asset type."""
        fetchers = {
            "stock": StockFetcher(),
            "crypto": CryptoFetcher(),
            # Add more as needed: commodity, bond, forex
        }
        
        fetcher = fetchers.get(asset_type.lower())
        if not fetcher:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        return fetcher
