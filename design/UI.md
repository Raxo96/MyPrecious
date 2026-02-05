# User Interface - Design Document

## Overview

Web-based user interface for portfolio tracking application. Provides portfolio overview, asset management, transaction handling, and performance analytics.

## Technology Stack

### Frontend Framework
- **SvelteKit**: Lightweight (~3KB runtime), fast compilation, built-in routing and SSR
- **Alternative**: Vue 3 + Vite (if team prefers Options API)

### UI Components
- **shadcn-svelte** or **DaisyUI**: Pre-built component library
- **TailwindCSS**: Utility-first styling

### Charts
- **Lightweight Charts** (TradingView): Financial charts, 40KB
- **Alternative**: Chart.js (general purpose, 60KB)

### State Management
- **Svelte Stores**: Built-in, no external library needed
- **Optional**: TanStack Query for server state caching

### HTTP Client
- Native `fetch` API
- **Optional**: axios for interceptors

## MVP (Minimum Viable Product)

### Goal
Test integration with Fetcher + Database, establish basic functionality for development.

### Core Features - Phase 1

#### 1. Portfolio Overview (Read-only)
- Single portfolio view
- Total value in USD
- 1D change percentage
- List of positions (symbol, quantity, current value, P&L)

#### 2. Asset List (Read-only)
- Search assets by symbol/name
- Display: symbol, name, current price, 24h change

#### 3. Simple Line Chart
- Portfolio value over time (1M fixed range)
- Single asset price chart (1M fixed range)

#### 4. Basic Transaction Form
- Add buy transaction (asset, date, quantity, price)
- No validation, no sell functionality yet

#### 5. Authentication (Stub)
- Hardcoded user (no login form)
- Single user mode

### MVP Architecture

```
frontend/
├── src/
│   ├── routes/
│   │   ├── +page.svelte              # Portfolio overview
│   │   ├── portfolio/
│   │   │   └── +page.svelte          # Portfolio detail
│   │   ├── assets/
│   │   │   ├── +page.svelte          # Asset search/list
│   │   │   └── [id]/+page.svelte     # Asset detail
│   │   └── transactions/
│   │       └── new/+page.svelte      # Add transaction
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts             # API wrapper
│   │   ├── components/
│   │   │   ├── PortfolioCard.svelte
│   │   │   ├── AssetCard.svelte
│   │   │   ├── SimpleChart.svelte
│   │   │   └── TransactionForm.svelte
│   │   └── stores/
│   │       └── portfolio.ts          # Svelte store
│   └── app.css                       # Tailwind imports
├── package.json
└── svelte.config.js
```

### MVP Pages

**Portfolio Overview** (`/`)
- Total portfolio value
- 1D change ($ and %)
- List of positions with basic metrics
- "Add Transaction" button

**Asset Search** (`/assets`)
- Search input
- List of matching assets
- Current price and 24h change per asset
- Click to view detail

**Asset Detail** (`/assets/[id]`)
- Asset name and symbol
- Current price
- Simple line chart (1M fixed)
- "Add to Portfolio" button

**Add Transaction** (`/transactions/new`)
- Asset selector (dropdown)
- Transaction type (buy only)
- Date picker
- Quantity input
- Price input
- Fee input (optional)
- Submit button

### MVP Data Flow

```
User opens app
    ↓
Fetch portfolio summary (API)
    ↓
Display total value + positions
    ↓
User clicks asset
    ↓
Fetch asset detail + chart (API)
    ↓
Display chart (1M fixed)
    ↓
User clicks "Add Transaction"
    ↓
Fill form, submit
    ↓
POST to API
    ↓
Trigger fetcher backfill (backend)
    ↓
Redirect to portfolio
```

### MVP API Endpoints

```
GET  /api/portfolios/:id              # Portfolio summary
GET  /api/portfolios/:id/positions    # List positions
GET  /api/portfolios/:id/chart?range=1M  # Chart data
GET  /api/assets/search?q=apple       # Search assets
GET  /api/assets/:id                  # Asset detail
GET  /api/assets/:id/chart?range=1M   # Asset chart
POST /api/transactions                # Create transaction
```

## Full Version - Feature Roadmap

### Phase 2: Core Features

#### 1. Portfolio Overview - Enhanced
- Multiple portfolios support
- All time ranges: 1D, 1W, 1M, 3M, 6M, 1Y, 3Y, 5Y, All
- Detailed metrics:
  - Total invested
  - Total return ($ and %)
  - Best/worst performer
  - Asset allocation pie chart
  - Sector breakdown (for stocks)

#### 2. Portfolio Detail - Per Asset
- Individual asset performance within portfolio
- Cost basis tracking
- Realized vs unrealized gains
- Transaction history per asset
- Average buy price calculation

#### 3. Advanced Charts
- Candlestick charts (OHLC)
- Volume bars
- Multiple indicators (MA, RSI, MACD)
- Comparison mode (overlay multiple assets)
- Zoom and pan
- Export chart as image

#### 4. Asset Management
- Buy/Sell transactions
- Edit existing transactions
- Delete transactions
- Bulk import (CSV)
- Transaction notes/tags

#### 5. Asset Discovery - Enhanced
- Advanced filters:
  - Asset type (stock, crypto, commodity, bond)
  - Exchange
  - Price range
  - Volume
  - Market cap
- Sorting options
- Watchlist (track without buying)
- Price alerts

### Phase 3: Advanced Features

#### 6. Dashboard & Analytics
- Portfolio diversification score
- Risk metrics (volatility, beta)
- Correlation matrix
- Performance attribution
- Tax lot tracking (FIFO/LIFO)

#### 7. User Management
- Login/Register
- Multi-user support
- User settings
- Currency preference
- Theme (light/dark)

### Phase 4: Real-time & Polish

#### 8. Real-time Updates
- WebSocket for live prices
- Auto-refresh portfolio value
- Push notifications for alerts

#### 9. Progressive Web App
- Offline mode
- Install prompt
- Background sync

## Full Architecture

```
frontend/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte            # App shell
│   │   ├── +page.svelte              # Dashboard
│   │   ├── auth/
│   │   │   ├── login/+page.svelte
│   │   │   └── register/+page.svelte
│   │   ├── portfolios/
│   │   │   ├── +page.svelte          # Portfolio list
│   │   │   ├── [id]/+page.svelte     # Portfolio detail
│   │   │   └── [id]/assets/[assetId]/+page.svelte
│   │   ├── assets/
│   │   │   ├── +page.svelte          # Asset search
│   │   │   ├── [id]/+page.svelte     # Asset detail
│   │   │   └── watchlist/+page.svelte
│   │   ├── transactions/
│   │   │   ├── +page.svelte          # Transaction history
│   │   │   ├── new/+page.svelte      # Add transaction
│   │   │   └── [id]/edit/+page.svelte
│   │   ├── analytics/
│   │   │   └── +page.svelte          # Advanced analytics
│   │   └── settings/
│   │       └── +page.svelte
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── portfolios.ts
│   │   │   ├── assets.ts
│   │   │   ├── transactions.ts
│   │   │   └── auth.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.svelte
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   └── Footer.svelte
│   │   │   ├── portfolio/
│   │   │   │   ├── PortfolioCard.svelte
│   │   │   │   ├── PortfolioChart.svelte
│   │   │   │   ├── PositionList.svelte
│   │   │   │   └── AllocationPie.svelte
│   │   │   ├── assets/
│   │   │   │   ├── AssetCard.svelte
│   │   │   │   ├── AssetSearch.svelte
│   │   │   │   ├── AssetChart.svelte
│   │   │   │   └── AssetFilters.svelte
│   │   │   ├── transactions/
│   │   │   │   ├── TransactionForm.svelte
│   │   │   │   ├── TransactionList.svelte
│   │   │   │   └── TransactionModal.svelte
│   │   │   └── common/
│   │   │       ├── Button.svelte
│   │   │       ├── Input.svelte
│   │   │       ├── Select.svelte
│   │   │       ├── Modal.svelte
│   │   │       ├── Loading.svelte
│   │   │       └── ErrorBoundary.svelte
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── portfolio.ts
│   │   │   ├── assets.ts
│   │   │   └── ui.ts
│   │   ├── utils/
│   │   │   ├── formatters.ts         # Currency, date, percent
│   │   │   ├── calculations.ts       # P&L, returns
│   │   │   └── validators.ts
│   │   └── types/
│   │       ├── portfolio.ts
│   │       ├── asset.ts
│   │       └── transaction.ts
│   └── app.css
├── static/
│   └── favicon.png
├── tests/
│   ├── unit/
│   └── e2e/
├── package.json
├── svelte.config.js
├── tailwind.config.js
└── vite.config.js
```

## Implementation Phases

### Phase 1: MVP (2-3 weeks)
- Setup SvelteKit project
- Basic routing (3 pages)
- API client wrapper
- Portfolio overview (read-only)
- Asset search (read-only)
- Simple line chart (fixed 1M range)
- Add transaction form (buy only)
- Basic styling (Tailwind)

**Deliverable**: Functional app to test DB + Fetcher integration

### Phase 2: Core Features (3-4 weeks)
- Multiple portfolios
- Time range selector (1D, 1W, 1M, 3M, 6M, 1Y, All)
- Sell transactions
- Edit/delete transactions
- Per-asset detail view
- Enhanced charts (candlestick, volume)
- Portfolio metrics (total return, P&L)
- Responsive design (mobile)

**Deliverable**: Fully functional portfolio tracker

### Phase 3: Advanced Features (4-6 weeks)
- User authentication
- Multi-user support
- Advanced analytics dashboard
- Asset allocation charts
- Watchlist
- Price alerts
- Transaction history filters
- CSV import/export
- Dark mode

**Deliverable**: Production-ready application

### Phase 4: Real-time & Polish (2-3 weeks)
- WebSocket integration
- Live price updates
- Push notifications
- Performance optimization
- E2E testing
- Accessibility (WCAG 2.1)
- PWA support (offline mode)

**Deliverable**: Enterprise-grade application

## Design System

### Color Palette
- **Primary**: Blue (#3B82F6)
- **Success/Gain**: Green (#10B981)
- **Danger/Loss**: Red (#EF4444)
- **Neutral**: Gray scale (#F3F4F6 to #111827)
- **Background**: White (#FFFFFF) / Dark (#1F2937)

### Typography
- **Font Family**: Inter or System fonts
- **Sizes**: 
  - xs: 12px
  - sm: 14px
  - base: 16px
  - lg: 18px
  - xl: 20px
  - 2xl: 24px
  - 3xl: 30px

### Spacing
- Base unit: 4px (Tailwind default)
- Scale: 4, 8, 12, 16, 24, 32, 48, 64px

### Responsive Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

## Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 200KB (gzipped)

## Accessibility

- Keyboard navigation support
- Screen reader compatibility (ARIA labels)
- Color contrast ratio: WCAG AA (4.5:1 minimum)
- Focus indicators
- Skip navigation links

## API Contract

### Portfolio Endpoints

**GET /api/portfolios/:id**
```typescript
Response: {
  id: number
  name: string
  currency: string
  total_value_usd: number
  day_change_pct: number
  month_change_pct: number
  year_change_pct: number
  all_time_return_pct: number
}
```

**GET /api/portfolios/:id/positions**
```typescript
Response: {
  positions: [{
    asset_id: number
    symbol: string
    name: string
    quantity: number
    current_price: number
    current_value: number
    cost_basis: number
    unrealized_gain: number
    unrealized_gain_pct: number
  }]
}
```

**GET /api/portfolios/:id/chart?range=1M**
```typescript
Response: {
  data: [{
    timestamp: string  // ISO 8601
    value: number
  }]
}
```

### Asset Endpoints

**GET /api/assets/search?q=apple&limit=20**
```typescript
Response: {
  assets: [{
    id: number
    symbol: string
    name: string
    asset_type: string
    exchange: string
    current_price: number
    day_change_pct: number
  }]
}
```

**GET /api/assets/:id**
```typescript
Response: {
  id: number
  symbol: string
  name: string
  asset_type: string
  exchange: string
  native_currency: string
  current_price: number
  day_change_pct: number
  volume: number
  market_cap: number
}
```

**GET /api/assets/:id/chart?range=1M**
```typescript
Response: {
  data: [{
    timestamp: string  // ISO 8601
    open: number
    high: number
    low: number
    close: number
    volume: number
  }]
}
```

### Transaction Endpoints

**POST /api/transactions**
```typescript
Body: {
  portfolio_id: number
  asset_id: number
  transaction_type: "buy" | "sell"
  quantity: number
  price: number
  fee: number
  timestamp: string  // ISO 8601
  notes: string
}

Response: {
  id: number
  status: "pending" | "completed"
  backfill_job_id: number  // If new asset
}
```

**GET /api/transactions?portfolio_id=1**
```typescript
Response: {
  transactions: [{
    id: number
    asset_id: number
    symbol: string
    transaction_type: string
    quantity: number
    price: number
    fee: number
    timestamp: string
    notes: string
  }]
}
```

## Testing Strategy

### Unit Tests
- Component rendering
- Store logic
- Utility functions (formatters, calculations)
- API client methods

### Integration Tests
- API mocking (MSW - Mock Service Worker)
- User flows
- Form validation
- Error handling

### E2E Tests (Playwright)
Critical paths:
- Add buy transaction
- View portfolio overview
- Search and view asset
- View charts with different time ranges
- Edit/delete transaction

## Deployment

### Development
```bash
npm install
npm run dev
# http://localhost:5173
```

### Production Build
```bash
npm run build
npm run preview
```

### Hosting Options
- **Vercel** (recommended for SvelteKit)
- **Netlify**
- **AWS Amplify**
- **Self-hosted** (Node.js + Nginx)

### Environment Variables
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

## Security Considerations

### Frontend Security
- Sanitize user inputs
- XSS prevention (Svelte auto-escapes)
- CSRF tokens for mutations
- Secure cookie handling
- Content Security Policy headers

### API Communication
- HTTPS only in production
- JWT token storage (httpOnly cookies)
- Token refresh mechanism
- Rate limiting awareness

## Future Enhancements

1. **Mobile App**: React Native or Flutter version
2. **Desktop App**: Electron wrapper
3. **Browser Extension**: Quick portfolio view
4. **API for Third-party**: Public API for integrations
5. **Social Features**: Share portfolios, compare with friends
6. **AI Insights**: ML-powered recommendations
7. **News Integration**: Asset-specific news feed
8. **Tax Reports**: Automated tax document generation
