import json
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path


def plot_stocks():
    """Plot all stocks on a single chart."""
    # Load data
    data_file = Path(__file__).parent / "stock_data.json"
    with open(data_file, "r") as f:
        stocks = json.load(f)
    
    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Plot each stock
    for stock in stocks:
        symbol = stock["symbol"]
        prices = stock["prices"]
        
        # Extract dates and closing prices
        dates = [datetime.fromisoformat(p["timestamp"]) for p in prices]
        closes = [p["close"] for p in prices]
        
        # Normalize to percentage change from first price
        first_price = closes[0]
        normalized = [(c / first_price - 1) * 100 for c in closes]
        
        plt.plot(dates, normalized, label=symbol, linewidth=2)
    
    plt.title("10 Popular Stocks - 1 Year Performance (Normalized)", fontsize=16, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Return (%)", fontsize=12)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save
    output_file = Path(__file__).parent / "stocks_chart.png"
    plt.savefig(output_file, dpi=150)
    print(f"✓ Chart saved to {output_file}")
    
    # Show
    plt.show()


if __name__ == "__main__":
    plot_stocks()
