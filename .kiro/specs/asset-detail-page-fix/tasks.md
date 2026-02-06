# Implementation Plan: Asset Detail Page Fix

## Overview

This implementation plan fixes the broken asset detail page by adding symbol-based routing and price change display functionality. The work is organized into backend API development, frontend updates, and testing tasks.

## Tasks

- [x] 1. Implement backend API endpoints for asset details and price changes
  - [x] 1.1 Add GET `/api/assets/{asset_symbol}` endpoint
    - Implement asset lookup by symbol (case-insensitive)
    - Query latest price from AssetPrice table
    - Return asset details with current_price
    - Handle 404 for non-existent symbols
    - _Requirements: 1.2, 2.1, 2.2, 2.4_
  
  - [ ]* 1.2 Write property test for asset lookup by symbol
    - **Property 1: Asset Lookup by Symbol**
    - **Validates: Requirements 1.2, 2.2**
  
  - [ ]* 1.3 Write property test for invalid symbol error handling
    - **Property 2: Invalid Symbol Error Handling**
    - **Validates: Requirements 1.3, 2.4**
  
  - [ ]* 1.4 Write unit test for asset with no price data
    - Test that current_price returns 0.0 when no prices exist
    - _Requirements: 2.3_
  
  - [x] 1.5 Add GET `/api/assets/{asset_symbol}/chart` endpoint
    - Implement asset lookup by symbol
    - Calculate price changes for all time periods (1D, 1M, 3M, 6M, 1Y)
    - Query historical prices using appropriate time offsets
    - Apply percentage change formula
    - Return null for periods with no data
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1-6.7_
  
  - [ ]* 1.6 Write property test for chart response completeness
    - **Property 4: Chart Response Completeness**
    - **Validates: Requirements 3.2, 3.5**
  
  - [ ]* 1.7 Write property test for price change calculation formula
    - **Property 5: Price Change Calculation Formula**
    - **Validates: Requirements 3.3**
  
  - [ ]* 1.8 Write property test for time period offset correctness
    - **Property 6: Time Period Offset Correctness**
    - **Validates: Requirements 6.1-6.5**
  
  - [ ]* 1.9 Write property test for historical price selection
    - **Property 7: Historical Price Selection**
    - **Validates: Requirements 6.6**
  
  - [ ]* 1.10 Write unit test for null handling when no historical prices exist
    - Test that periods return null when no data available
    - _Requirements: 3.4, 6.7_

- [x] 2. Checkpoint - Test backend endpoints
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 3. Update frontend API service and routing
  - [x] 3.1 Update API service methods to use symbols
    - Change `assetApi.getAsset(id)` to accept symbol parameter
    - Change `assetApi.getChart(id, range)` to accept symbol and remove range parameter
    - Update API endpoint paths to use symbol
    - _Requirements: 1.2, 3.1_
  
  - [x] 3.2 Update App.jsx route definition
    - Change route from `/assets/:id` to `/assets/:symbol`
    - _Requirements: 1.1_
  
  - [x] 3.3 Update AssetDetail component to use symbol parameter
    - Extract `symbol` from useParams instead of `id`
    - Update API calls to pass symbol
    - _Requirements: 1.1, 1.2_
  
  - [x] 3.4 Update AssetSearch component link generation
    - Change links from `/assets/${asset.id}` to `/assets/${asset.symbol}`
    - _Requirements: 1.4, 5.1, 5.2, 5.3_
  
  - [ ]* 3.5 Write property test for symbol-based link generation
    - **Property 3: Symbol-Based Link Generation**
    - **Validates: Requirements 1.4, 5.1, 5.2**

- [x] 4. Implement price change table display
  - [x] 4.1 Create price change table component
    - Display table with columns for 1D, 1M, 3M, 6M, 1Y
    - Implement formatting logic for percentage values
    - Handle null values by displaying "N/A"
    - Apply color coding: green for positive, red for negative, gray for zero/null
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 4.2 Integrate price change table into AssetDetail page
    - Fetch data from `/api/assets/{symbol}/chart`
    - Pass price change data to table component
    - Replace or supplement existing chart display
    - _Requirements: 3.1, 4.1_
  
  - [ ]* 4.3 Write property test for price change formatting
    - **Property 8: Frontend Price Change Formatting**
    - **Validates: Requirements 4.2**
  
  - [ ]* 4.4 Write property test for color coding by value sign
    - **Property 9: Color Coding by Value Sign**
    - **Validates: Requirements 4.4, 4.5, 4.6**
  
  - [ ]* 4.5 Write unit test for "N/A" display
    - Test that null values render as "N/A"
    - _Requirements: 4.3_

- [x] 5. Add error handling and edge cases
  - [x] 5.1 Add frontend error handling for 404 responses
    - Display user-friendly message when asset not found
    - Provide link back to asset search
    - _Requirements: 1.3_
  
  - [x] 5.2 Add frontend error handling for network errors
    - Display error message with retry option
    - Handle loading states appropriately
  
  - [ ]* 5.3 Write unit tests for error scenarios
    - Test 404 error display
    - Test network error handling
    - Test loading state transitions

- [x] 6. Final checkpoint - Integration testing
  - [-]* 6.1 Test complete user flow
    - Search for asset → click link → view detail page with price changes
    - Verify symbol appears in URL
    - Verify price change table displays correctly
    - Test navigation back to search
  
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Backend tasks use Python with FastAPI and pytest-hypothesis for property testing
- Frontend tasks use JavaScript/React with fast-check for property testing
- Property tests should run minimum 100 iterations each
- Integration testing verifies end-to-end functionality
