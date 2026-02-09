# MyPrecious 💎

A modern, full-stack portfolio tracking application for monitoring stock investments with real-time price updates, performance analytics, and comprehensive monitoring capabilities.

![Portfolio Overview](screenshots/PortfolioOverview.png)

## 📋 Overview

MyPrecious is a web-based portfolio tracker that helps investors monitor their stock holdings, track performance, and analyze investment returns. The application features a clean, responsive interface with real-time price updates, interactive charts, and detailed asset information.

### Key Features

- **📊 Portfolio Management**: Track multiple positions with real-time valuations and P&L calculations
- **💹 Real-Time Price Updates**: Automated background daemon fetches stock prices every 10 minutes from Yahoo Finance
- **📈 Interactive Charts**: Visualize portfolio performance and individual asset price history using Lightweight Charts
- **🔍 Asset Search**: Search and explore thousands of stocks with detailed information
- **📝 Transaction Tracking**: Record buy/sell transactions with automatic position calculations
- **📡 Monitoring Dashboard**: Real-time monitoring of the data fetcher daemon with logs, statistics, and health status
- **🎯 Performance Analytics**: Calculate returns, P&L, and percentage changes across multiple time periods (1D, 1M, 3M, 6M, 1Y)

## 🖼️ Screenshots

### Portfolio Overview
![Portfolio Overview](screenshots/PortfolioOverview.png)
*Track your total portfolio value, returns, and individual positions at a glance*

### Asset Details
![Asset Details](screenshots/AssetDetails.png)
*View detailed price charts and performance metrics for any stock*

### Assets Overview
![Assets Overview](screenshots/AssetsOverview.png)
*Browse and search through available stocks with real-time prices*

### Fetcher Monitoring
![Fetcher Monitor](screenshots/FetcherMonitor.png)
*Monitor the background price fetcher daemon with real-time logs and statistics*

## 🏗️ Architecture

MyPrecious follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│                    http://localhost:5173                    │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                    API Service (FastAPI)                    │
│                    http://localhost:8000                    │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL Queries
┌────────────────────────▼────────────────────────────────────┐
│              PostgreSQL Database (Port 5432)                │
│  • Assets & Prices (Partitioned by Year)                   │
│  • Portfolios & Positions                                   │
│  • Transactions & Performance Cache                         │
│  • Fetcher Logs & Statistics                                │
└────────────────────────┬────────────────────────────────────┘
                         │ Price Updates
┌────────────────────────▼────────────────────────────────────┐
│           Fetcher Daemon (Python Background Service)        │
│  • Fetches prices every 10 minutes                          │
│  • Yahoo Finance API integration                            │
│  • Automatic retry & error handling                         │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Frontend
- **React 18** - Modern UI library with hooks
- **Vite** - Fast build tool and dev server
- **React Router 6** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Lightweight Charts** - High-performance financial charts
- **Axios** - HTTP client for API requests

### Backend
- **FastAPI** - Modern Python web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type hints
- **Uvicorn** - ASGI server for production
- **psycopg2** - PostgreSQL adapter

### Database
- **PostgreSQL 14** - Robust relational database
- **Partitioned Tables** - Efficient price data storage by year (2016-2027)
- **Full-Text Search** - Fast asset search capabilities
- **JSONB Support** - Flexible metadata storage

### Data Fetcher
- **Python 3.11** - Core language
- **Requests** - HTTP library for Yahoo Finance API
- **Object-Oriented Design** - Extensible fetcher architecture (BaseFetcher, StockFetcher)

### DevOps
- **Docker & Docker Compose** - Containerization and orchestration
- **PostgreSQL Alpine** - Lightweight database image
- **Node 18 Alpine** - Lightweight Node.js runtime
- **Python 3.11 Slim** - Optimized Python runtime

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd MyPrecious
```

2. **Start all services**:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- FastAPI backend (port 8000)
- React frontend (port 5173)
- Fetcher daemon (background service)

3. **Access the application**:
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)

4. **Initialize with sample data** (optional):
```bash
# The database is automatically seeded with sample assets on first run
# Check the seed.sql file for initial data
```

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove all data (including database)
docker-compose down -v
```

## 📖 Usage

### Adding Your First Transaction

1. Navigate to the Portfolio Overview page
2. Click "Add Transaction"
3. Search for a stock symbol (e.g., AAPL, MSFT, GOOGL)
4. Enter transaction details:
   - Type: Buy or Sell
   - Quantity: Number of shares
   - Price: Purchase price per share
   - Date: Transaction date
   - Fee: Optional transaction fee
5. Submit the transaction

The system will automatically:
- Update your portfolio positions
- Calculate average buy price
- Fetch historical price data
- Update P&L calculations

### Viewing Asset Details

1. Click on any asset symbol in your portfolio or search results
2. View detailed information:
   - Current price and day change
   - Price performance across multiple periods (1D, 1M, 3M, 6M, 1Y)
   - Interactive price chart with 1 year of historical data
   - OHLC (Open, High, Low, Close) data

### Monitoring the Fetcher

1. Navigate to the Fetcher Monitoring page
2. View real-time information:
   - Daemon status (running/stopped)
   - Uptime and cycle statistics
   - Recent price updates with success/failure status
   - Operational logs with filtering by level
   - Performance metrics

## ⚙️ Configuration

### Fetcher Daemon Settings

Configure the fetcher daemon by modifying environment variables in `docker-compose.yml`:

```yaml
environment:
  - UPDATE_INTERVAL_MINUTES=10    # Price update frequency
  - LOG_RETENTION_DAYS=30         # Log retention period
  - STATS_PERSIST_INTERVAL=300    # Statistics save interval (seconds)
```

### Database Connection

The default database connection string is:
```
postgresql://postgres:postgres@localhost:5432/portfolio_tracker
```

Modify in `docker-compose.yml` if needed.

## 📁 Project Structure

```
MyPrecious/
├── src/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py            # API routes and endpoints
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── database.py        # Database connection
│   │   └── tests/             # API tests
│   ├── frontend/              # React frontend
│   │   ├── src/
│   │   │   ├── components/    # Reusable UI components
│   │   │   ├── pages/         # Page components
│   │   │   ├── services/      # API client
│   │   │   └── utils/         # Helper functions
│   │   └── package.json
│   ├── fetcher/               # Price fetcher daemon
│   │   ├── fetcher.py         # Core fetcher classes
│   │   ├── backfill_daemon.py # Background daemon
│   │   ├── log_store.py       # Logging system
│   │   └── tests/             # Fetcher tests
│   └── database/              # Database schema
│       ├── schema.sql         # Table definitions
│       └── seed.sql           # Initial data
├── design/                    # Design documents
├── screenshots/               # Application screenshots
├── docker-compose.yml         # Docker orchestration
└── README.md
```

## 🔌 API Endpoints

### Portfolio Endpoints
- `GET /api/portfolios/{id}` - Get portfolio summary with P&L
- `GET /api/portfolios/{id}/positions` - Get all positions
- `GET /api/portfolios/{id}/history` - Get portfolio value history

### Asset Endpoints
- `GET /api/assets` - List all assets with current prices
- `GET /api/assets/search?q={query}` - Search assets
- `GET /api/assets/{symbol}` - Get asset details
- `GET /api/assets/{symbol}/chart` - Get price chart data

### Transaction Endpoints
- `POST /api/transactions` - Create new transaction

### Fetcher Endpoints
- `GET /api/fetcher/status` - Get daemon status
- `GET /api/fetcher/logs` - Get operational logs
- `GET /api/fetcher/statistics` - Get performance statistics
- `GET /api/fetcher/recent-updates` - Get recent price updates

Full API documentation available at: http://localhost:8000/docs

## 🧪 Testing

### Run API Tests
```bash
cd src/api
pytest
```

### Run Fetcher Tests
```bash
cd src/fetcher
pytest
```

## 📊 Database Schema

The application uses PostgreSQL with the following key tables:

- **assets** - Stock metadata (symbol, name, type, exchange)
- **asset_prices** - Historical OHLC price data (partitioned by year)
- **portfolios** - User portfolios
- **portfolio_positions** - Current holdings
- **transactions** - Buy/sell transaction history
- **fetcher_logs** - Daemon operational logs
- **fetcher_statistics** - Performance metrics
- **price_update_log** - Individual price update tracking

## 🔄 Data Flow

1. **User adds transaction** → API validates and stores in database
2. **Position updated** → Automatic calculation of average buy price and quantity
3. **Fetcher daemon** → Runs every 10 minutes, fetches latest prices from Yahoo Finance
4. **Prices stored** → Inserted into partitioned asset_prices table
5. **Frontend updates** → Real-time display of current values and P&L

## 🚧 Future Enhancements

- [ ] User authentication and multi-user support
- [ ] Multiple portfolios per user
- [ ] Cryptocurrency support
- [ ] Real-time WebSocket price updates
- [ ] Price alerts and notifications
- [ ] Tax reporting and export
- [ ] Mobile responsive design improvements
- [ ] Advanced analytics and insights

## 📝 License

This project is for educational and personal use.

## 🤝 Contributing

This project has been created by single developer, using Kiro AI agent, within 2 days, consuming 225 credits. 
