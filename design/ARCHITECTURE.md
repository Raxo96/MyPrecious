# System Architecture Overview

## Executive Summary

Portfolio Tracker is a web-based application for monitoring investment portfolios across multiple asset classes (stocks, cryptocurrencies, commodities, bonds). The system uses an on-demand data fetching strategy to minimize storage and API costs while providing real-time portfolio analytics.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Browser    │  │    Mobile    │  │   Desktop    │         │
│  │  (SvelteKit) │  │   (Future)   │  │   (Future)   │         │
│  └──────┬───────┘  └──────────────┘  └──────────────┘         │
└─────────┼──────────────────────────────────────────────────────┘
          │ HTTPS / WebSocket
┌─────────▼──────────────────────────────────────────────────────┐
│                      Application Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Service (FastAPI)                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │   Auth     │  │ Portfolio  │  │   Asset    │        │  │
│  │  │  Service   │  │  Service   │  │  Service   │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │  ┌────────────┐  ┌────────────┐                        │  │
│  │  │Transaction │  │ Analytics  │                        │  │
│  │  │  Service   │  │  Service   │                        │  │
│  │  └────────────┘  └────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                       Data Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           PostgreSQL Database                            │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │  │
│  │  │Users │ │Assets│ │Prices│ │Trans │ │Cache │          │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Redis Cache (Optional)                         │  │
│  │  - Session storage                                       │  │
│  │  - Price cache                                           │  │
│  │  - Rate limiting                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │ PostgreSQL LISTEN/NOTIFY
┌─────────▼──────────────────────────────────────────────────────┐
│                    Background Services                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Data Fetcher Service (Python)                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │ Orchestrator│  │  Backfill  │  │   Daemon   │        │  │
│  │  │             │  │   Worker   │  │ Scheduler  │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │   Stock    │  │   Crypto   │  │   Forex    │        │  │
│  │  │  Fetcher   │  │  Fetcher   │  │  Fetcher   │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │ HTTPS
┌─────────▼──────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Yahoo Finance │  │   Binance    │  │  CoinGecko   │         │
│  │  (yfinance)  │  │    (ccxt)    │  │     API      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Overview

### 1. Frontend (SvelteKit)

**Purpose**: User interface for portfolio management

**Responsibilities**:
- Display portfolio overview and analytics
- Asset search and discovery
- Transaction management (buy/sell)
- Real-time price updates via WebSocket
- Chart visualization

**Technology**: SvelteKit, TailwindCSS, Lightweight Charts

**Communication**: REST API (HTTPS), WebSocket for real-time updates

### 2. API Service (FastAPI)

**Purpose**: Backend business logic and data orchestration

**Responsibilities**:
- User authentication and authorization (JWT)
- Portfolio CRUD operations
- Transaction processing
- Performance calculations (P&L, returns)
- Asset search and filtering
- Chart data aggregation
- Event publishing to Fetcher

**Technology**: FastAPI, SQLAlchemy, Pydantic

**Communication**: 
- Inbound: HTTPS from Frontend
- Outbound: PostgreSQL queries, pg_notify events

### 3. Data Fetcher Service (Python)

**Purpose**: Market data collection and management

**Responsibilities**:
- On-demand historical data backfill (1 year)
- Real-time price updates (daemon mode)
- Rate limit handling with retry logic
- Multi-source data fetching (stocks, crypto, forex)
- Data validation and quality checks

**Technology**: Python, asyncio, yfinance, ccxt, SQLAlchemy

**Communication**:
- Inbound: PostgreSQL LISTEN (transaction events)
- Outbound: External APIs, PostgreSQL writes

### 4. PostgreSQL Database

**Purpose**: Persistent data storage

**Responsibilities**:
- User accounts and authentication
- Portfolio and position data
- Transaction history
- Asset catalog (metadata)
- Price history (on-demand)
- Performance cache
- Backfill job queue

**Technology**: PostgreSQL 14+, partitioned tables

### 5. Redis Cache (Optional)

**Purpose**: Performance optimization

**Responsibilities**:
- Session storage
- Price data caching (1-minute TTL)
- Rate limiting counters
- API response caching

**Technology**: Redis 6+

## Data Flow Diagrams

### User Adds Asset to Portfolio

```
User (Frontend)
    │
    │ 1. POST /api/transactions
    │    {asset_id, quantity, price, date}
    ▼
API Service
    │
    │ 2. Validate transaction
    │ 3. Insert into transactions table
    │ 4. Update portfolio_positions
    │ 5. Trigger: NOTIFY transaction_created
    │
    ▼
PostgreSQL
    │
    │ 6. LISTEN transaction_created
    │
    ▼
Fetcher Service
    │
    │ 7. Check if asset tracked
    │ 8. Create backfill job (date - 1 year to now)
    │ 9. Add to tracked_assets
    │
    ▼
Backfill Worker
    │
    │ 10. Fetch historical data from Yahoo/Binance
    │ 11. Handle rate limits (retry if needed)
    │ 12. Bulk insert to asset_prices
    │ 13. Mark job completed
    │
    ▼
PostgreSQL
    │
    │ 14. Historical data available
    │
    ▼
Frontend
    │
    │ 15. Poll backfill status
    │ 16. Display chart when ready
```

### Real-Time Price Updates

```
Daemon Scheduler (every 15 min)
    │
    │ 1. Query tracked_assets
    │
    ▼
Fetcher Service
    │
    │ 2. Group by asset type
    │ 3. Batch fetch current prices
    │
    ▼
External APIs (Yahoo/Binance)
    │
    │ 4. Return current prices
    │
    ▼
Fetcher Service
    │
    │ 5. Validate data
    │ 6. Bulk update asset_prices
    │ 7. Invalidate cache
    │
    ▼
PostgreSQL
    │
    │ 8. Updated prices available
    │
    ▼
WebSocket (optional)
    │
    │ 9. Push updates to connected clients
    │
    ▼
Frontend
    │
    │ 10. Update UI in real-time
```

### Portfolio Value Calculation

```
User requests portfolio view
    │
    │ 1. GET /api/portfolios/:id
    │
    ▼
API Service
    │
    │ 2. Check cache (Redis)
    │
    ├─ Cache Hit ──────────┐
    │                      │
    │ 3. Cache Miss        │
    │                      │
    ▼                      │
Portfolio Service          │
    │                      │
    │ 4. Query positions   │
    │ 5. Get latest prices │
    │ 6. Calculate:        │
    │    - Total value     │
    │    - P&L             │
    │    - Returns         │
    │ 7. Store in cache    │
    │                      │
    ▼                      │
    └──────────────────────┘
    │
    │ 8. Return response
    │
    ▼
Frontend
    │
    │ 9. Display portfolio
```

## Deployment Architecture

### Development Environment

```
Developer Machine
├── Frontend (localhost:5173)
├── API Service (localhost:8000)
├── Fetcher Service (background process)
├── PostgreSQL (localhost:5432)
└── Redis (localhost:6379) [optional]
```

### Production Environment (Single Server)

```
Server (EC2 / VPS)
├── Nginx (Reverse Proxy)
│   ├── Frontend (static files)
│   └── API Service (proxy to :8000)
├── API Service (Gunicorn + Uvicorn)
├── Fetcher Service (systemd service)
├── PostgreSQL (managed or self-hosted)
└── Redis (managed or self-hosted)
```

### Production Environment (Scalable)

```
┌─────────────────────────────────────────┐
│         Load Balancer (ALB)             │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Web 1 │ │ Web 2 │  (Frontend + API)
└───┬───┘ └──┬────┘
    │        │
    └────┬───┘
         │
┌────────▼────────────────────────────────┐
│      RDS PostgreSQL (Multi-AZ)          │
└─────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│    ElastiCache Redis (Cluster)          │
└─────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│  Fetcher Service (ECS/EC2 Auto Scaling) │
└─────────────────────────────────────────┘
```

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | SvelteKit | Web UI |
| API | FastAPI | REST API |
| Fetcher | Python + asyncio | Data collection |
| Database | PostgreSQL 14+ | Persistent storage |
| Cache | Redis 6+ | Performance |
| Charts | Lightweight Charts | Visualization |
| Auth | JWT | Authentication |
| ORM | SQLAlchemy 2.0 | Database access |
| Validation | Pydantic | Data validation |
| Server | Uvicorn/Gunicorn | ASGI server |

## Communication Patterns

### Synchronous Communication

**Frontend ↔ API**:
- Protocol: HTTPS (REST)
- Format: JSON
- Authentication: JWT Bearer token
- Rate limiting: 100 req/min per user

**API ↔ Database**:
- Protocol: PostgreSQL wire protocol
- Connection pooling: 5-20 connections
- Transactions: ACID guarantees

**Fetcher ↔ External APIs**:
- Protocol: HTTPS
- Rate limiting: Per-source limits
- Retry: Exponential backoff

### Asynchronous Communication

**API → Fetcher**:
- Method: PostgreSQL LISTEN/NOTIFY
- Event: `transaction_created`
- Payload: JSON with transaction details
- Alternative: Message queue (RabbitMQ/Redis)

**Fetcher → Frontend** (Future):
- Method: WebSocket
- Purpose: Real-time price updates
- Protocol: WSS (WebSocket Secure)

## Data Storage Strategy

### On-Demand Data Collection

**Principle**: Only fetch and store data for assets in user portfolios

**Benefits**:
- 99.8% storage reduction (500 MB vs 250 GB)
- 90% API call reduction
- Faster queries (smaller dataset)
- Cost-effective scaling

**Implementation**:
1. User adds asset → trigger backfill (1 year)
2. Asset added to tracking list
3. Daemon fetches real-time updates
4. User removes asset → stop tracking (keep historical data)

### Data Retention

- **Asset prices**: Indefinite (for historical analysis)
- **Transactions**: Indefinite (audit trail)
- **Backfill queue**: 30 days (completed jobs)
- **Cache**: 1-60 minutes (depending on data type)
- **Logs**: 90 days

## Security Architecture

### Authentication Flow

```
User
  │ 1. POST /auth/login (email, password)
  ▼
API
  │ 2. Verify password (bcrypt)
  │ 3. Generate JWT (1 hour expiry)
  │ 4. Generate refresh token (30 days)
  │ 5. Set httpOnly cookie (refresh token)
  ▼
User
  │ 6. Store access token in memory
  │ 7. Include in Authorization header
  │
  │ ... after 1 hour ...
  │
  │ 8. POST /auth/refresh (with cookie)
  ▼
API
  │ 9. Validate refresh token
  │ 10. Generate new access token
  ▼
User
  │ 11. Continue with new token
```

### Security Layers

1. **Transport**: HTTPS/TLS 1.3
2. **Authentication**: JWT with short expiry
3. **Authorization**: User-scoped data access
4. **Input Validation**: Pydantic schemas
5. **SQL Injection**: Parameterized queries
6. **XSS**: Auto-escaping (Svelte)
7. **CSRF**: SameSite cookies
8. **Rate Limiting**: Per-user and per-IP

## Scalability Considerations

### Current Design (MVP)

**Capacity**:
- Users: 1,000-10,000
- Portfolios: 10,000-100,000
- Tracked assets: 100-1,000
- API requests: 100,000/day
- Database size: 1-10 GB

**Bottlenecks**:
- Single API server
- Single Fetcher worker
- Database on single instance

### Scaling Strategy

**Horizontal Scaling**:
- Multiple API servers behind load balancer
- Multiple Fetcher workers (distributed queue)
- Read replicas for database

**Vertical Scaling**:
- Larger database instance
- More CPU/RAM for API servers

**Caching**:
- Redis for frequently accessed data
- CDN for static assets

**Database Optimization**:
- Partitioning (already implemented)
- Indexing (already implemented)
- Connection pooling
- Query optimization

## Monitoring & Observability

### Metrics to Track

**Application Metrics**:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users

**Business Metrics**:
- Portfolios created
- Transactions per day
- Assets tracked
- Backfill jobs completed

**Infrastructure Metrics**:
- CPU usage
- Memory usage
- Database connections
- Disk I/O
- Network throughput

### Logging Strategy

**Structured Logging** (JSON format):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "request_id": "abc-123",
  "user_id": 456,
  "endpoint": "/api/portfolios/1",
  "method": "GET",
  "status": 200,
  "duration_ms": 45
}
```

**Log Aggregation**:
- CloudWatch Logs (AWS)
- ELK Stack (self-hosted)
- Datadog / New Relic (SaaS)

### Alerting

**Critical Alerts**:
- API error rate > 5%
- Database connection pool exhausted
- Fetcher service down
- Disk space > 90%

**Warning Alerts**:
- Response time p95 > 1s
- Backfill queue size > 100
- Rate limit hits increasing

## Disaster Recovery

### Backup Strategy

**Database Backups**:
- Automated daily backups
- Point-in-time recovery (7 days)
- Cross-region replication (production)

**Application State**:
- Infrastructure as Code (Terraform/CloudFormation)
- Configuration in version control
- Docker images in registry

### Recovery Procedures

**Database Failure**:
1. Promote read replica to primary
2. Update API connection string
3. Verify data integrity

**API Service Failure**:
1. Auto-scaling launches new instances
2. Load balancer routes traffic
3. Health checks verify readiness

**Fetcher Service Failure**:
1. Restart service (systemd/ECS)
2. Resume from backfill queue
3. No data loss (queue persisted)

## Development Workflow

### Local Development

```bash
# 1. Start database
docker-compose up -d postgres redis

# 2. Run migrations
cd api && alembic upgrade head

# 3. Start API
cd api && uvicorn app.main:app --reload

# 4. Start Fetcher
cd fetcher && python main.py worker

# 5. Start Frontend
cd frontend && npm run dev
```

### CI/CD Pipeline

```
Git Push
    │
    ▼
GitHub Actions / GitLab CI
    │
    ├─ Run Tests (unit, integration)
    ├─ Lint Code (pylint, eslint)
    ├─ Build Docker Images
    ├─ Push to Registry
    │
    ▼
Staging Environment
    │
    ├─ Deploy API
    ├─ Deploy Fetcher
    ├─ Deploy Frontend
    ├─ Run E2E Tests
    │
    ▼
Production Environment (manual approval)
    │
    ├─ Blue/Green Deployment
    ├─ Health Checks
    └─ Rollback if needed
```

## Future Enhancements

### Phase 1 (Current)
- ✅ On-demand data fetching
- ✅ Basic portfolio tracking
- ✅ Transaction management
- ✅ Simple charts

### Phase 2 (3-6 months)
- Multiple portfolios per user
- Advanced analytics
- Real-time WebSocket updates
- Mobile responsive design

### Phase 3 (6-12 months)
- Mobile apps (iOS/Android)
- Social features (share portfolios)
- Price alerts and notifications
- Tax reporting

### Phase 4 (12+ months)
- AI-powered insights
- Automated trading integration
- Multi-currency support
- API for third-party integrations

## Conclusion

The Portfolio Tracker architecture is designed for:

- **Efficiency**: On-demand data fetching minimizes costs
- **Scalability**: Modular design allows independent scaling
- **Reliability**: Event-driven architecture with retry logic
- **Maintainability**: Clear separation of concerns
- **Performance**: Caching and optimization at every layer

The system can start small (single server) and scale horizontally as user base grows, with minimal architectural changes required.
