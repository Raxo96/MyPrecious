# Requirements Document

## Introduction

This specification addresses the asset detail page feature that currently returns a 404 error. The feature needs to be fixed to properly display asset information and price history using asset symbols in URLs instead of numeric IDs, and to show price changes across multiple time periods.

## Glossary

- **Asset**: A financial instrument (stock, cryptocurrency, etc.) tracked in the system
- **Asset_Symbol**: The ticker symbol or short identifier for an asset (e.g., "AAPL", "BTC")
- **Asset_ID**: The numeric database identifier for an asset
- **Price_Change**: The percentage change in asset price over a specified time period
- **Time_Period**: A duration for measuring price changes (1D, 1M, 3M, 6M, 1Y)
- **Backend_API**: The FastAPI server that provides data endpoints
- **Frontend**: The React application that displays the user interface
- **Asset_Detail_Page**: The page that displays comprehensive information about a single asset

## Requirements

### Requirement 1: URL Routing with Asset Symbols

**User Story:** As a user, I want to access asset detail pages using readable asset symbols in the URL, so that I can easily share and bookmark specific assets.

#### Acceptance Criteria

1. WHEN a user navigates to `/assets/<asset_symbol>`, THE Frontend SHALL display the asset detail page for that asset
2. WHEN an asset symbol is provided in the URL, THE Backend_API SHALL look up the asset by symbol and return its details
3. WHEN an invalid asset symbol is provided, THE System SHALL return a 404 error with a clear message
4. WHEN links to asset detail pages are generated, THE Frontend SHALL use asset symbols instead of asset IDs

### Requirement 2: Asset Detail Endpoint

**User Story:** As a frontend developer, I want a backend endpoint that returns asset details by symbol, so that I can display comprehensive asset information.

#### Acceptance Criteria

1. THE Backend_API SHALL provide an endpoint at `/api/assets/{asset_symbol}`
2. WHEN a valid asset symbol is requested, THE Backend_API SHALL return the asset's id, symbol, name, asset_type, exchange, and current_price
3. WHEN the asset has no price data, THE Backend_API SHALL return current_price as 0.0
4. WHEN an asset symbol does not exist, THE Backend_API SHALL return a 404 status code

### Requirement 3: Price Change Data Endpoint

**User Story:** As a user, I want to see how an asset's price has changed over different time periods, so that I can understand its performance trends.

#### Acceptance Criteria

1. THE Backend_API SHALL provide an endpoint at `/api/assets/{asset_symbol}/chart`
2. WHEN price data is requested, THE Backend_API SHALL calculate price changes for 1D, 1M, 3M, 6M, and 1Y periods
3. WHEN calculating price change, THE Backend_API SHALL use the formula: ((current_price - period_start_price) / period_start_price) * 100
4. WHEN no price data exists for a time period, THE Backend_API SHALL return null for that period's price change
5. THE Backend_API SHALL return the current price along with all price change data

### Requirement 4: Price Change Display Table

**User Story:** As a user, I want to see a table of price changes across multiple time periods, so that I can quickly assess the asset's performance.

#### Acceptance Criteria

1. THE Frontend SHALL display a table with columns for each time period: 1D, 1M, 3M, 6M, 1Y
2. WHEN price change data is available, THE Frontend SHALL display the percentage change with appropriate formatting
3. WHEN price change data is null, THE Frontend SHALL display "N/A" in the table cell
4. WHEN price change is positive, THE Frontend SHALL display it in green color
5. WHEN price change is negative, THE Frontend SHALL display it in red color
6. WHEN price change is zero, THE Frontend SHALL display it in gray color

### Requirement 5: Asset Search Link Updates

**User Story:** As a user, I want asset search results to link to the correct detail pages, so that I can navigate to asset details without errors.

#### Acceptance Criteria

1. WHEN displaying asset search results, THE Frontend SHALL generate links using asset symbols
2. THE Frontend SHALL use the format `/assets/{asset_symbol}` for all asset detail links
3. WHEN a user clicks an asset in search results, THE System SHALL navigate to the asset detail page using the symbol

### Requirement 6: Price Data Calculation

**User Story:** As a system, I need to accurately calculate price changes over time periods, so that users see correct performance data.

#### Acceptance Criteria

1. WHEN calculating 1D price change, THE Backend_API SHALL use the price from 24 hours ago
2. WHEN calculating 1M price change, THE Backend_API SHALL use the price from 30 days ago
3. WHEN calculating 3M price change, THE Backend_API SHALL use the price from 90 days ago
4. WHEN calculating 6M price change, THE Backend_API SHALL use the price from 180 days ago
5. WHEN calculating 1Y price change, THE Backend_API SHALL use the price from 365 days ago
6. WHEN no exact timestamp match exists, THE Backend_API SHALL use the closest available price before the target timestamp
7. WHEN no historical price exists for a period, THE Backend_API SHALL return null for that period
