# MyPrecious Frontend (React)

Portfolio tracking application frontend built with React, Vite, and Tailwind CSS.

## Features

- Portfolio overview with performance metrics
- Asset search and discovery
- Transaction management (buy/sell)
- Interactive charts using Lightweight Charts
- Responsive design with Tailwind CSS

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Lightweight Charts** - Financial charts
- **Axios** - HTTP client

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Setup

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
copy .env.example .env
```

3. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Header.jsx      # Navigation header
│   ├── Chart.jsx       # Chart component
│   └── Loading.jsx     # Loading spinner
├── pages/              # Page components
│   ├── PortfolioOverview.jsx
│   ├── AssetSearch.jsx
│   ├── AssetDetail.jsx
│   └── AddTransaction.jsx
├── services/           # API services
│   └── api.js         # API client
├── utils/             # Utility functions
│   └── formatters.js  # Currency/date formatters
├── App.jsx            # Main app component
└── main.jsx          # Entry point
```

## API Integration

The frontend communicates with the FastAPI backend through REST endpoints:

- `GET /api/portfolios/:id` - Portfolio summary
- `GET /api/portfolios/:id/positions` - Portfolio positions
- `GET /api/portfolios/:id/chart` - Portfolio chart data
- `GET /api/assets/search` - Asset search
- `GET /api/assets/:id` - Asset details
- `POST /api/transactions` - Create transaction

## Environment Variables

- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000/api)