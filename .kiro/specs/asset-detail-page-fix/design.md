# Design Document: Asset Detail Page Fix

## Overview

This design addresses the broken asset detail page by implementing symbol-based routing and adding comprehensive price change data display. The solution involves:

1. **Backend API Changes**: Add two new endpoints (`/api/assets/{asset_symbol}` and `/api/assets/{asset_symbol}/chart`) that accept asset symbols instead of numeric IDs
2. **Frontend Routing Updates**: Change the route parameter from `:id` to `:symbol` and update all navigation links
3. **Price Change Calculation**: Implement logic to calculate percentage changes across multiple time periods (1D, 1M, 3M, 6M, 1Y)
4. **UI Enhancement**: Replace the existing chart-focused display with a price change table

The design maintains backward compatibility with existing database schema and leverages the current AssetPrice table structure.

## Architecture

### Component Interaction Flow

```
User → Frontend (React Router) → Backend API (FastAPI) → Database (PostgreSQL)
  ↓                                      ↓
  URL: /assets/AAPL              GET /api/assets/AAPL
  ↓                                      ↓
  AssetDetail Component          Query Asset by symbol
  ↓                                      ↓
  Display price table            Calculate price changes
```

### Key Architectural Decisions

1. **Symbol-based routing**: Using symbols instead of IDs makes URLs more user-friendly and shareable
2. **Separate endpoints**: Keep asset details and chart data separate for better API organization
3. **Null handling**: Return null for missing data rather than errors, allowing graceful degradation
4. **Client-side formatting**: Handle "N/A" display logic in the frontend for better UX control

## Components and Interfaces

### Backend API Components

#### 1. Asset Detail Endpoint

**Endpoint**: `GET /api/assets/{asset_symbol}`

**Path Parameters**:
- `asset_symbol` (string): The asset's ticker symbol (e.g., "AAPL", "BTC")

**Response Schema**:
```python
{
    "id": int,
    "symbol": str,
    "name": str,
    "asset_type": str,
    "exchange": str,
    "current_price": float
}
```

**Implementation Logic**:
1. Query the Asset table for a record where `symbol` matches `asset_symbol` (case-insensitive)
2. If no asset found, raise HTTPException with 404 status
3. Query AssetPrice table for the most recent price record for this asset_id
4. Return asset data with current_price set to the latest close price (or 0.0 if no prices exist)

#### 2. Price Chart Endpoint

**Endpoint**: `GET /api/assets/{asset_symbol}/chart`

**Path Parameters**:
- `asset_symbol` (string): The asset's ticker symbol

**Response Schema**:
```python
{
    "symbol": str,
    "current_price": float,
    "price_changes": {
        "1D": float | null,
        "1M": float | null,
        "3M": float | null,
        "6M": float | null,
        "1Y": float | null
    }
}
```

**Implementation Logic**:
1. Look up asset by symbol (case-insensitive)
2. If not found, raise HTTPException with 404 status
3. Get current price (most recent AssetPrice record)
4. For each time period:
   - Calculate target timestamp (now - period duration)
   - Query for the closest price at or before target timestamp
   - If found, calculate percentage change: `((current - historical) / historical) * 100`
   - If not found, set to null
5. Return response with all calculated changes

**Time Period Mappings**:
- 1D: 1 day (24 hours)
- 1M: 30 days
- 3M: 90 days
- 6M: 180 days
- 1Y: 365 days

### Frontend Components

#### 1. Updated AssetDetail Component

**Route**: `/assets/:symbol`

**State Management**:
```javascript
{
    asset: {
        id: number,
        symbol: string,
        name: string,
        asset_type: string,
        exchange: string,
        current_price: number
    },
    priceChanges: {
        "1D": number | null,
        "1M": number | null,
        "3M": number | null,
        "6M": number | null,
        "1Y": number | null
    },
    loading: boolean,
    error: string | null
}
```

**Component Logic**:
1. Extract `symbol` from URL params (instead of `id`)
2. Fetch asset details from `/api/assets/{symbol}`
3. Fetch price changes from `/api/assets/{symbol}/chart`
4. Render asset header with basic information
5. Render price change table with formatted values

#### 2. Price Change Table Component

**Display Logic**:
- For each time period column (1D, 1M, 3M, 6M, 1Y):
  - If value is null: display "N/A" in gray
  - If value > 0: display "+X.XX%" in green
  - If value < 0: display "-X.XX%" in red
  - If value === 0: display "0.00%" in gray

#### 3. Updated AssetSearch Component

**Link Generation**:
- Change from: `<Link to={/assets/${asset.id}}>`
- Change to: `<Link to={/assets/${asset.symbol}}>`

### API Service Updates

**File**: `src/frontend/src/services/api.js`

**Changes**:
```javascript
export const assetApi = {
  search: (query, limit = 20) => apiClient.get(`/assets/search?q=${query}&limit=${limit}`),
  getAsset: (symbol) => apiClient.get(`/assets/${symbol}`),  // Changed parameter name
  getChart: (symbol) => apiClient.get(`/assets/${symbol}/chart`),  // Changed parameter name and endpoint
}
```

## Data Models

### Existing Database Schema (No Changes Required)

**Asset Table**:
```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50),
    name VARCHAR(255),
    asset_type VARCHAR(20),
    exchange VARCHAR(50),
    native_currency VARCHAR(3),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**AssetPrice Table**:
```sql
CREATE TABLE asset_prices (
    id BIGINT PRIMARY KEY,
    asset_id INTEGER,
    timestamp TIMESTAMP,
    open DECIMAL(18, 8),
    high DECIMAL(18, 8),
    low DECIMAL(18, 8),
    close DECIMAL(18, 8),
    volume BIGINT,
    source VARCHAR(50)
);
```

### Data Access Patterns

**Query 1: Get Asset by Symbol**
```python
asset = db.query(Asset).filter(
    func.lower(Asset.symbol) == asset_symbol.lower(),
    Asset.is_active == True
).first()
```

**Query 2: Get Latest Price**
```python
latest_price = db.query(AssetPrice).filter(
    AssetPrice.asset_id == asset_id
).order_by(desc(AssetPrice.timestamp)).first()
```

**Query 3: Get Historical Price for Time Period**
```python
target_timestamp = datetime.now() - timedelta(days=period_days)
historical_price = db.query(AssetPrice).filter(
    AssetPrice.asset_id == asset_id,
    AssetPrice.timestamp <= target_timestamp
).order_by(desc(AssetPrice.timestamp)).first()
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Asset Lookup by Symbol

*For any* valid asset symbol in the database, when the backend API receives a request to `/api/assets/{symbol}`, the response should contain the correct asset details including id, symbol, name, asset_type, exchange, and current_price fields.

**Validates: Requirements 1.2, 2.2**

### Property 2: Invalid Symbol Error Handling

*For any* string that does not correspond to an active asset symbol in the database, when the backend API receives a request to `/api/assets/{symbol}`, the response should return a 404 status code.

**Validates: Requirements 1.3, 2.4**

### Property 3: Symbol-Based Link Generation

*For any* asset displayed in the frontend, all generated links to the asset detail page should use the format `/assets/{symbol}` where {symbol} is the asset's symbol field, not its numeric ID.

**Validates: Requirements 1.4, 5.1, 5.2**

### Property 4: Chart Response Completeness

*For any* valid asset symbol, when the backend API receives a request to `/api/assets/{symbol}/chart`, the response should include the current_price field and all five time period keys (1D, 1M, 3M, 6M, 1Y) in the price_changes object, with each value being either a number or null.

**Validates: Requirements 3.2, 3.5**

### Property 5: Price Change Calculation Formula

*For any* asset with both current price and historical price data for a given time period, the calculated price change percentage should equal `((current_price - historical_price) / historical_price) * 100` within a tolerance of 0.01%.

**Validates: Requirements 3.3**

### Property 6: Time Period Offset Correctness

*For any* time period calculation (1D, 1M, 3M, 6M, 1Y), the target timestamp used to query historical prices should be within 1 hour of the expected offset from the current time (24 hours, 30 days, 90 days, 180 days, 365 days respectively).

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 7: Historical Price Selection

*For any* target timestamp when querying historical prices, if no exact timestamp match exists, the returned price should be from the most recent timestamp that is less than or equal to the target timestamp.

**Validates: Requirements 6.6**

### Property 8: Frontend Price Change Formatting

*For any* non-null price change value displayed in the frontend, the rendered text should include the percentage sign (%) and be formatted to two decimal places.

**Validates: Requirements 4.2**

### Property 9: Color Coding by Value Sign

*For any* price change value displayed in the frontend, the color should be green when the value is positive, red when the value is negative, and gray when the value is zero or null.

**Validates: Requirements 4.4, 4.5, 4.6**

## Error Handling

### Backend Error Scenarios

1. **Asset Not Found**
   - **Trigger**: Request to `/api/assets/{symbol}` or `/api/assets/{symbol}/chart` with non-existent symbol
   - **Response**: HTTP 404 with message "Asset not found"
   - **Handling**: Frontend displays user-friendly error message

2. **Database Connection Error**
   - **Trigger**: Database is unavailable during API request
   - **Response**: HTTP 500 with generic error message
   - **Handling**: Frontend displays "Service temporarily unavailable" message

3. **Invalid Symbol Format**
   - **Trigger**: Symbol contains invalid characters or is empty
   - **Response**: HTTP 400 with message "Invalid asset symbol"
   - **Handling**: Frontend validates input before making request

### Frontend Error Scenarios

1. **Network Error**
   - **Trigger**: API request fails due to network issues
   - **Handling**: Display error message with retry button

2. **Missing Price Data**
   - **Trigger**: API returns null for price change periods
   - **Handling**: Display "N/A" in table cells (graceful degradation)

3. **Invalid Route Parameter**
   - **Trigger**: User navigates to `/assets/` with no symbol
   - **Handling**: Redirect to asset search page or show 404 page

## Testing Strategy

### Unit Testing

Unit tests will focus on specific examples, edge cases, and integration points:

**Backend Unit Tests**:
- Test asset lookup with known symbols (e.g., "AAPL", "BTC")
- Test 404 response for non-existent symbols
- Test price change calculation with known price values
- Test null handling when no historical prices exist
- Test case-insensitive symbol matching
- Test response schema validation

**Frontend Unit Tests**:
- Test "N/A" display for null price changes
- Test color class application for positive/negative/zero values
- Test link generation with sample asset data
- Test error message display for failed API calls
- Test loading state transitions

### Property-Based Testing

Property tests will verify universal properties across randomized inputs (minimum 100 iterations per test):

**Backend Property Tests**:

1. **Test Property 1**: Generate random valid asset symbols from database, verify response contains all required fields
   - **Tag**: Feature: asset-detail-page-fix, Property 1: Asset Lookup by Symbol

2. **Test Property 2**: Generate random invalid symbols (strings not in database), verify all return 404
   - **Tag**: Feature: asset-detail-page-fix, Property 2: Invalid Symbol Error Handling

3. **Test Property 4**: Generate random valid symbols, verify chart response includes all time period keys
   - **Tag**: Feature: asset-detail-page-fix, Property 4: Chart Response Completeness

4. **Test Property 5**: Generate random price pairs (current and historical), verify calculation formula
   - **Tag**: Feature: asset-detail-page-fix, Property 5: Price Change Calculation Formula

5. **Test Property 6**: For random time periods, verify target timestamp is within expected range
   - **Tag**: Feature: asset-detail-page-fix, Property 6: Time Period Offset Correctness

6. **Test Property 7**: Generate random target timestamps, verify closest historical price is selected
   - **Tag**: Feature: asset-detail-page-fix, Property 7: Historical Price Selection

**Frontend Property Tests**:

1. **Test Property 3**: Generate random asset objects, verify all links use symbol format
   - **Tag**: Feature: asset-detail-page-fix, Property 3: Symbol-Based Link Generation

2. **Test Property 8**: Generate random price change values, verify formatting includes % and 2 decimals
   - **Tag**: Feature: asset-detail-page-fix, Property 8: Frontend Price Change Formatting

3. **Test Property 9**: Generate random price change values (positive, negative, zero), verify color mapping
   - **Tag**: Feature: asset-detail-page-fix, Property 9: Color Coding by Value Sign

### Integration Testing

- Test complete flow: search asset → click link → view detail page with price changes
- Test navigation from asset detail back to search
- Test API endpoint integration with real database queries
- Test frontend rendering with actual API responses

### Test Configuration

- All property-based tests must run minimum 100 iterations
- Use appropriate PBT library: pytest-hypothesis (Python), fast-check (JavaScript)
- Each test must reference its design document property in comments
- Tests should use test database with known seed data for reproducibility
