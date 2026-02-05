# API Layer - Design Document

## Overview

RESTful API service providing backend functionality for portfolio tracking application. Handles authentication, portfolio management, asset data, and transaction processing.

## Technology Stack

### Framework
- **FastAPI**: High-performance async Python framework
- **Alternative**: Flask + Flask-RESTX (if team prefers traditional approach)

### Core Libraries
- **SQLAlchemy 2.0**: ORM (shared with Fetcher service)
- **Pydantic**: Request/response validation and serialization
- **Alembic**: Database migrations
- **python-jose**: JWT token handling
- **passlib**: Password hashing (bcrypt)
- **uvicorn**: ASGI server
- **python-multipart**: File upload support

### Optional
- **Redis**: Caching and rate limiting
- **Celery**: Background task processing (future)

## Architecture

### Layered Architecture

```
Frontend (SvelteKit)
        ↓ HTTP/WebSocket
API Gateway (Auth, Rate Limiting)
        ↓
API Layer (FastAPI)
  ├── Routes (Controllers)
  ├── Services (Business Logic)
  └── Repositories (Data Access)
        ↓
PostgreSQL Database
        ↓
Fetcher Service (Event-driven)
```

### Module Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration
│   ├── dependencies.py            # Dependency injection
│   ├── database.py                # DB session management
│   ├── models/                    # SQLAlchemy models (shared with Fetcher)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── asset.py
│   │   ├── transaction.py
│   │   └── price.py
│   ├── schemas/                   # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── asset.py
│   │   └── transaction.py
│   ├── routes/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── portfolios.py
│   │   ├── assets.py
│   │   ├── transactions.py
│   │   └── websocket.py
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── portfolio_service.py
│   │   ├── asset_service.py
│   │   ├── transaction_service.py
│   │   └── analytics_service.py
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── portfolio_repository.py
│   │   ├── asset_repository.py
│   │   └── transaction_repository.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── rate_limit.py
│   └── utils/
│       ├── __init__.py
│       ├── security.py            # JWT, password hashing
│       ├── calculations.py        # P&L, returns
│       └── validators.py
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── requirements.txt
├── alembic.ini
└── .env.example
```

## API Endpoints

### Authentication

```
POST   /api/auth/register          # Create new user
POST   /api/auth/login             # Login (returns JWT)
POST   /api/auth/refresh           # Refresh JWT token
POST   /api/auth/logout            # Logout (invalidate token)
GET    /api/auth/me                # Get current user info
```

### Portfolios

```
GET    /api/portfolios             # List user's portfolios
POST   /api/portfolios             # Create portfolio
GET    /api/portfolios/:id         # Get portfolio summary
PUT    /api/portfolios/:id         # Update portfolio
DELETE /api/portfolios/:id         # Delete portfolio
GET    /api/portfolios/:id/positions        # List positions
GET    /api/portfolios/:id/performance      # Performance metrics
GET    /api/portfolios/:id/chart            # Chart data
  ?range=1D|1W|1M|3M|6M|1Y|3Y|5Y|ALL
```

### Assets

```
GET    /api/assets/search          # Search assets
  ?q=apple&type=stock&limit=20
GET    /api/assets/:id             # Get asset detail
GET    /api/assets/:id/chart       # Asset price chart
  ?range=1D|1W|1M|3M|6M|1Y|3Y|5Y|ALL
GET    /api/assets/types           # List asset types
GET    /api/assets/exchanges       # List exchanges
```

### Transactions

```
GET    /api/transactions           # List transactions
  ?portfolio_id=1&asset_id=2&type=buy
POST   /api/transactions           # Create transaction
GET    /api/transactions/:id       # Get transaction detail
PUT    /api/transactions/:id       # Update transaction
DELETE /api/transactions/:id       # Delete transaction
POST   /api/transactions/import    # Bulk import (CSV)
```

### Analytics (Future)

```
GET    /api/analytics/allocation   # Asset allocation
GET    /api/analytics/performance  # Performance attribution
GET    /api/analytics/risk         # Risk metrics
```

### WebSocket

```
WS     /api/ws/prices              # Real-time price updates
WS     /api/ws/portfolio/:id       # Real-time portfolio updates
```

### Health & Monitoring

```
GET    /health                     # Health check
GET    /metrics                    # Prometheus metrics (optional)
```

## Request/Response Schemas

### Authentication

**POST /api/auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response: 201
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**POST /api/auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response: 200
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Portfolios

**GET /api/portfolios/:id**
```json
Response: 200
{
  "id": 1,
  "name": "My Portfolio",
  "currency": "USD",
  "total_value_usd": 12450.00,
  "total_invested_usd": 10000.00,
  "total_return_usd": 2450.00,
  "total_return_pct": 24.50,
  "day_change_pct": 2.3,
  "week_change_pct": 5.1,
  "month_change_pct": 8.7,
  "year_change_pct": 18.2,
  "all_time_return_pct": 24.50,
  "created_at": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**GET /api/portfolios/:id/positions**
```json
Response: 200
{
  "positions": [
    {
      "asset_id": 123,
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "asset_type": "stock",
      "quantity": 10.0,
      "average_buy_price": 145.00,
      "current_price": 150.00,
      "cost_basis": 1450.00,
      "current_value": 1500.00,
      "unrealized_gain": 50.00,
      "unrealized_gain_pct": 3.45,
      "day_change_pct": 1.2,
      "first_purchase_date": "2024-01-01"
    }
  ]
}
```

**GET /api/portfolios/:id/chart?range=1M**
```json
Response: 200
{
  "range": "1M",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 10000.00
    },
    {
      "timestamp": "2024-01-02T00:00:00Z",
      "value": 10050.00
    }
  ]
}
```

### Assets

**GET /api/assets/search?q=apple&limit=10**
```json
Response: 200
{
  "total": 2,
  "assets": [
    {
      "id": 123,
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "asset_type": "stock",
      "exchange": "NASDAQ",
      "current_price": 150.00,
      "currency": "USD",
      "day_change_pct": 1.2,
      "is_tracked": true
    }
  ]
}
```

**GET /api/assets/:id/chart?range=1M**
```json
Response: 200
{
  "asset_id": 123,
  "symbol": "AAPL",
  "range": "1M",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 148.00,
      "high": 151.00,
      "low": 147.50,
      "close": 150.00,
      "volume": 50000000
    }
  ]
}
```

### Transactions

**POST /api/transactions**
```json
Request:
{
  "portfolio_id": 1,
  "asset_id": 123,
  "transaction_type": "buy",
  "quantity": 10.0,
  "price": 150.00,
  "fee": 5.00,
  "timestamp": "2024-01-15T10:30:00Z",
  "notes": "Initial purchase"
}

Response: 201
{
  "id": 456,
  "portfolio_id": 1,
  "asset_id": 123,
  "symbol": "AAPL",
  "transaction_type": "buy",
  "quantity": 10.0,
  "price": 150.00,
  "fee": 5.00,
  "timestamp": "2024-01-15T10:30:00Z",
  "notes": "Initial purchase",
  "backfill_status": "pending",
  "backfill_job_id": 789
}
```

## Business Logic

### Portfolio Service

**Responsibilities**:
- Calculate portfolio total value
- Calculate performance metrics (returns, P&L)
- Aggregate position data
- Generate chart data for time ranges
- Handle currency conversions

**Key Operations**:
- Get portfolio summary with current value
- List all positions with P&L calculations
- Generate portfolio value chart for specified time range
- Calculate performance metrics (day/week/month/year/all-time returns)

### Transaction Service

**Responsibilities**:
- Validate transaction data
- Create/update/delete transactions
- Update portfolio positions
- Trigger fetcher backfill for new assets
- Recalculate average buy price
- Handle FIFO/LIFO for sell transactions

**Key Operations**:
- Create transaction and update position
- Trigger backfill event for new assets
- Calculate realized gains on sell
- Update average cost basis

### Asset Service

**Responsibilities**:
- Search assets by symbol/name
- Get asset details with current price
- Generate asset chart data
- Check if asset is tracked

**Key Operations**:
- Full-text search across asset catalog
- Retrieve asset with latest price
- Generate OHLCV chart data for time range
- Check tracking status

### Analytics Service (Future)

**Responsibilities**:
- Calculate asset allocation
- Risk metrics (volatility, Sharpe ratio)
- Performance attribution
- Correlation analysis

## Authentication & Authorization

### JWT Token Strategy

**Access Token**:
- Lifetime: 1 hour
- Contains: user_id, email
- Storage: Frontend memory (not localStorage)

**Refresh Token**:
- Lifetime: 30 days
- Storage: httpOnly cookie
- Purpose: Obtain new access token

### Authorization Rules

- Users can only access their own portfolios
- Users can only create transactions in their portfolios
- Admin role (future): Access all data for support

### Middleware

**Authentication Middleware**:
- Extract JWT from Authorization header
- Validate token signature and expiration
- Inject user context into request

**Rate Limiting**:
- Per-user: 100 requests/minute
- Per-IP: 1000 requests/minute
- Auth endpoints: 5 login attempts/minute

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Portfolio with id 123 not found",
    "details": {},
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful GET/PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Duplicate resource
- `422 Validation Error`: Pydantic validation failed
- `429 Rate Limit Exceeded`: Too many requests
- `500 Internal Server Error`: Server error

### Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_FAILED`: Invalid credentials
- `UNAUTHORIZED`: Missing or invalid token
- `FORBIDDEN`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

## Integration with Fetcher

### Event-Driven Communication

**PostgreSQL LISTEN/NOTIFY** (MVP):

API publishes events via database trigger:
```sql
NOTIFY transaction_created, '{"transaction_id": 456, "asset_id": 123, "timestamp": "..."}'
```

Fetcher listens and processes:
- Receives transaction event
- Creates backfill job
- Starts historical data fetch

**Alternative** (Future): Message Queue (RabbitMQ/Redis Pub/Sub) for better scalability

### Backfill Status

Frontend can check backfill progress:
```
GET /api/transactions/:id/backfill-status

Response:
{
  "status": "pending" | "in_progress" | "completed" | "failed",
  "progress": 75,
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

## Caching Strategy

### Redis Cache (Optional)

**Cache Targets**:
- Asset metadata (symbol, name, type): 1 hour TTL
- Latest asset prices: 1 minute TTL
- Portfolio performance: 5 minutes TTL
- User sessions: 1 hour TTL

**Cache Invalidation**:
- Transaction create/update/delete → invalidate portfolio cache
- Price update from fetcher → invalidate asset price cache

**Cache-Aside Pattern**:
1. Check cache
2. If miss, query database
3. Store in cache
4. Return result

## Performance Optimization

### Database Optimization

- Eager loading with `joinedload` for related entities
- Proper indexing on frequently queried columns
- Pagination for large result sets (limit/offset)
- Connection pooling (SQLAlchemy default: 5-20 connections)

### Response Optimization

- Gzip compression for responses
- Partial responses (field selection)
- ETags for conditional requests
- HTTP/2 support

### Async Operations

- Use `async/await` for all I/O operations
- Background tasks for heavy computations
- Non-blocking database queries

## Security

### Input Validation

- Pydantic schemas validate all inputs
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitize outputs)
- File upload validation (type, size)

### Authentication Security

- Password hashing with bcrypt (cost factor: 12)
- JWT with short expiration (1 hour)
- Refresh token rotation
- Rate limiting on auth endpoints

### CORS Configuration

- Whitelist specific origins
- Allow credentials for cookies
- Preflight request caching

### HTTPS & Headers

- Enforce HTTPS in production
- HSTS headers
- Secure cookies (httpOnly, secure, sameSite)
- CSP headers

## Monitoring & Logging

### Structured Logging

- Format: JSON
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include: request_id, user_id, endpoint, duration, status_code

### Metrics

- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Active database connections
- Cache hit/miss ratio

### Health Checks

```
GET /health

Response: 200
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "uptime": 3600
}
```

## API Versioning

### URL Versioning (Recommended)

```
/api/v1/portfolios
/api/v2/portfolios  # Future breaking changes
```

**Benefits**:
- Clear and explicit
- Easy to route
- Simple for clients

### Header Versioning (Alternative)

```
Accept: application/vnd.portfolio.v1+json
```

## Testing Strategy

### Unit Tests

- Service layer business logic
- Calculation functions (P&L, returns)
- Validators and utilities
- Coverage target: >80%

### Integration Tests

- API endpoints with test database
- Authentication flow
- Transaction creation → position update
- Error handling

### Load Tests

- Concurrent users (100-1000)
- Rate limiting behavior
- Database connection pool limits
- Response time under load

## Deployment

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Production

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

### Environment Variables

```
# Database
DATABASE_URL=postgresql://user:pass@localhost/portfolio

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:5173,https://app.example.com

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development|staging|production
```

## Documentation

### Auto-Generated Docs

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

### Manual Documentation

- API design document (this file)
- Deployment guide
- Development setup guide
- Troubleshooting guide

## Future Enhancements

1. **GraphQL API**: Alternative to REST for flexible queries
2. **gRPC**: For internal service-to-service communication
3. **API Gateway**: Kong or AWS API Gateway for advanced routing
4. **Service Mesh**: Istio for microservices architecture
5. **Event Sourcing**: Full audit trail of all changes
6. **CQRS**: Separate read/write models for scalability
