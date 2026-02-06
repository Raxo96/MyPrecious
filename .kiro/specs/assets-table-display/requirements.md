# Requirements Document

## Introduction

This feature adds a comprehensive assets table to the Assets subpage (AssetSearch.jsx) that displays all available assets from the database. The table will show key asset information including name, symbol, current price, and 1-day percentage change, providing users with a quick overview of all tracked assets in the system.

## Glossary

- **Asset**: A financial instrument (stock, crypto, commodity, or bond) tracked in the system
- **Symbol**: The ticker symbol or identifier for an asset (e.g., AAPL, BTC)
- **Current_Price**: The most recent closing price for an asset from the asset_prices table
- **Day_Change_Pct**: The percentage change in price over the last 24 hours
- **Assets_Table**: The UI component displaying all assets in tabular format
- **API_Endpoint**: The backend REST endpoint that provides asset data
- **Frontend**: The React application running in the browser
- **Backend**: The FastAPI server providing data through REST endpoints

## Requirements

### Requirement 1: Display All Assets

**User Story:** As a user, I want to see all available assets in a table, so that I can browse and compare different investment options.

#### Acceptance Criteria

1. WHEN the Assets subpage loads, THE Assets_Table SHALL fetch and display all active assets from the database
2. THE Assets_Table SHALL display assets with the following columns: Asset Name, Symbol, Current Price, and 1D Change %
3. WHEN no assets exist in the database, THE Assets_Table SHALL display a message indicating no assets are available
4. THE Assets_Table SHALL maintain the existing search functionality alongside the table view

### Requirement 2: Asset Data Retrieval

**User Story:** As a developer, I want a dedicated API endpoint for fetching all assets with price data, so that the frontend can efficiently load the assets table.

#### Acceptance Criteria

1. THE Backend SHALL provide an API endpoint that returns all active assets with their current prices
2. WHEN the API endpoint is called, THE Backend SHALL join asset data with the latest price from asset_prices table
3. WHEN an asset has no price data, THE Backend SHALL return a current_price of 0.0 for that asset
4. THE Backend SHALL calculate the 1-day percentage change by comparing the current price with the price from 24 hours ago
5. WHEN no price exists from 24 hours ago, THE Backend SHALL return null for day_change_pct

### Requirement 3: Price Change Calculation

**User Story:** As a user, I want to see the 1-day percentage change for each asset, so that I can quickly identify which assets are gaining or losing value.

#### Acceptance Criteria

1. THE Backend SHALL calculate day_change_pct using the formula: ((current_price - price_24h_ago) / price_24h_ago) * 100
2. WHEN day_change_pct is positive, THE Frontend SHALL display it in green with a plus sign
3. WHEN day_change_pct is negative, THE Frontend SHALL display it in red
4. WHEN day_change_pct is zero or null, THE Frontend SHALL display it in gray
5. THE Frontend SHALL format day_change_pct to 2 decimal places with a percentage symbol

### Requirement 4: Table Presentation

**User Story:** As a user, I want the assets table to be well-formatted and easy to read, so that I can quickly scan through asset information.

#### Acceptance Criteria

1. THE Assets_Table SHALL use Tailwind CSS classes consistent with the existing application design
2. THE Assets_Table SHALL display column headers: "Asset Name", "Symbol", "Current Price", "1D Change %"
3. WHEN displaying prices, THE Frontend SHALL format them as USD currency with 2 decimal places
4. THE Assets_Table SHALL make each row clickable to navigate to the asset detail page
5. WHEN hovering over a row, THE Assets_Table SHALL provide visual feedback (e.g., background color change)

### Requirement 5: Loading and Error States

**User Story:** As a user, I want to see appropriate feedback when data is loading or if an error occurs, so that I understand the current state of the application.

#### Acceptance Criteria

1. WHEN the assets data is being fetched, THE Frontend SHALL display a loading indicator
2. WHEN an API error occurs, THE Frontend SHALL display an error message to the user
3. WHEN the API request fails, THE Frontend SHALL preserve any previously loaded data if available
4. THE Frontend SHALL use the existing Loading component for consistency
5. THE Frontend SHALL display error messages in a styled error container consistent with existing patterns

### Requirement 6: Integration with Existing Features

**User Story:** As a user, I want the new assets table to work seamlessly with existing search functionality, so that I can both browse all assets and search for specific ones.

#### Acceptance Criteria

1. THE Assets_Table SHALL be displayed below the existing search input field
2. WHEN a search query is entered, THE Assets_Table SHALL be hidden and search results SHALL be displayed instead
3. WHEN the search query is cleared, THE Assets_Table SHALL be displayed again
4. THE Frontend SHALL reuse existing API service patterns from services/api.js
5. THE Frontend SHALL reuse existing formatter utilities for currency and percentage display
