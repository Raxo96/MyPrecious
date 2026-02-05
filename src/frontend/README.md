# Portfolio Tracker - Frontend

Minimal SvelteKit web UI for portfolio tracking.

## Features (MVP)

✅ Portfolio Overview
- Total portfolio value display
- 1D change percentage

✅ Positions List
- View all holdings
- Current value and P&L per position

✅ Asset Search
- Search stocks by symbol or name
- Real-time filtering

✅ Add Transaction Form
- Select asset
- Enter quantity, price, date
- Submit transaction

## Tech Stack

- **SvelteKit** - Web framework
- **Vite** - Build tool
- **Node 18** - Runtime (in Docker)

## Running

### With Docker (Recommended)

```bash
# Start frontend
docker-compose up -d frontend

# View logs
docker logs -f portfolio_tracker_frontend

# Access at: http://localhost:5173
```

### Local Development

```bash
cd src/frontend
npm install
npm run dev
```

## Current State

**Mock Data**: Currently using hardcoded data for demonstration
**Next Steps**: Connect to API backend

## Structure

```
src/frontend/
├── package.json
├── svelte.config.js
├── vite.config.js
└── src/
    ├── app.html          # HTML template
    └── routes/
        └── +page.svelte  # Main page
```

## Screenshots

The UI includes:
- Clean, modern design
- Responsive layout
- Color-coded gains/losses (green/red)
- Easy-to-use forms

## Next Steps

1. ✅ Basic UI created
2. ⏭️ Connect to API backend
3. ⏭️ Real data from database
4. ⏭️ Charts integration
5. ⏭️ Real-time updates
