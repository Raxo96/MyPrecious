# Implementation Plan: Assets Table Display

## Overview

This implementation plan breaks down the assets table display feature into discrete coding tasks. The approach follows a backend-first strategy: first implementing the API endpoint with data retrieval and calculation logic, then enhancing the frontend component to consume and display the data, and finally adding comprehensive testing.

## Tasks

- [ ] 1. Implement backend API endpoint for all assets
  - [x] 1.1 Create GET /api/assets endpoint in main.py
    - Add new route handler function `get_all_assets()`
    - Query all active assets from database (WHERE is_active = true)
    - Order results by symbol for consistent display
    - _Requirements: 2.1_
  
  - [x] 1.2 Implement price data retrieval and joining
    - For each asset, query latest price from asset_prices table
    - Handle assets with no price data (return 0.0)
    - Join asset metadata with price information
    - _Requirements: 2.2, 2.3_
  
  - [x] 1.3 Implement 1-day percentage change calculation
    - Get current price (most recent timestamp)
    - Get price from 24 hours ago (closest to current_time - 24h)
    - Calculate percentage: ((current - previous) / previous) * 100
    - Handle edge cases: no historical price (return null), zero previous price (return null)
    - Round result to 2 decimal places
    - _Requirements: 2.4, 2.5, 3.1_
  
  - [ ]* 1.4 Write property test for day change calculation
    - **Property 1: Day Change Calculation Correctness**
    - **Validates: Requirements 2.4, 3.1**
    - Generate random price pairs using Hypothesis
    - Verify calculation matches formula for all valid inputs
    - Test edge cases: zero prices, equal prices, large differences
  
  - [ ]* 1.5 Write unit tests for API endpoint
    - Test endpoint returns correct response structure
    - Test with empty database (returns empty array)
    - Test with assets having no price data
    - Test with assets having no 24h historical data
    - Test error handling for database failures

- [x] 2. Checkpoint - Verify backend implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Enhance frontend API service
  - [x] 3.1 Add getAll method to assetApi in services/api.js
    - Add new method: `getAll: () => apiClient.get('/assets')`
    - Follow existing pattern from search and getAsset methods
    - _Requirements: 6.4_

- [ ] 4. Implement assets table in AssetSearch component
  - [x] 4.1 Add state management for all assets
    - Add state variables: allAssets, loadingAll, errorAll
    - Create fetchAllAssets function to call API
    - Call fetchAllAssets on component mount using useEffect
    - _Requirements: 1.1_
  
  - [x] 4.2 Implement table rendering logic
    - Create table structure with Tailwind CSS classes
    - Add column headers: Asset Name, Symbol, Current Price, 1D Change %
    - Map over allAssets to render table rows
    - Apply formatCurrency to current_price
    - Apply formatPercent to day_change_pct
    - Apply getChangeColor to day_change_pct for color coding
    - _Requirements: 1.2, 3.2, 3.3, 3.5, 4.2, 4.3, 6.5_
  
  - [x] 4.3 Implement conditional rendering
    - Show table only when query is empty
    - Hide table when search query has value
    - Show existing search results when query has value
    - _Requirements: 1.4, 6.2, 6.3_
  
  - [x] 4.4 Add loading and error states
    - Display Loading component when loadingAll is true
    - Display error message when errorAll is set
    - Display "No assets available" when allAssets is empty
    - _Requirements: 1.3, 5.1, 5.2, 5.4_
  
  - [x] 4.5 Implement row click navigation
    - Make each table row clickable using onClick or Link wrapper
    - Navigate to /assets/{symbol} on row click
    - Add hover effect using Tailwind CSS (hover:bg-gray-50)
    - _Requirements: 4.4_
  
  - [ ]* 4.6 Write property test for percentage formatting
    - **Property 2: Percentage Display Formatting**
    - **Validates: Requirements 3.2, 3.3, 3.5**
    - Generate random percentage values using fast-check
    - Verify formatting includes 2 decimals, %, and correct sign
    - Verify color class is correct based on value
  
  - [ ]* 4.7 Write property test for currency formatting
    - **Property 3: Currency Formatting Consistency**
    - **Validates: Requirements 4.3**
    - Generate random price values using fast-check
    - Verify formatCurrency produces valid USD format
    - Verify 2 decimal places and dollar sign
  
  - [ ]* 4.8 Write property test for row navigation
    - **Property 4: Row Click Navigation**
    - **Validates: Requirements 4.4**
    - Generate random asset data using fast-check
    - Render table and simulate row clicks
    - Verify navigation is triggered with correct symbol
  
  - [ ]* 4.9 Write property test for error display
    - **Property 5: Error Display Behavior**
    - **Validates: Requirements 5.2**
    - Generate random error scenarios using fast-check
    - Mock API to throw errors
    - Verify error message is displayed and state is set
  
  - [ ]* 4.10 Write unit tests for component behavior
    - Test component fetches data on mount
    - Test table is displayed when query is empty
    - Test table is hidden when query has value
    - Test loading state is displayed during fetch
    - Test error state is displayed on API failure
    - Test empty state message when no assets
    - Test table displays correct column headers
    - Test row click triggers navigation

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Backend implementation comes first to ensure data availability
- Frontend implementation builds on existing patterns and utilities
- Property tests validate universal correctness across randomized inputs
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation of functionality
