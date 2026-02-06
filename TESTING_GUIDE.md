# Fetcher Monitoring Feature - Testing Guide

## Overview

This guide will help you test all the new fetcher monitoring features that have been implemented.

## Prerequisites

All services should be running:
```bash
docker-compose ps
```

Expected output:
- ✅ portfolio_tracker_db (healthy)
- ✅ portfolio_tracker_api (up)
- ✅ portfolio_tracker_frontend (up)
- ✅ portfolio_tracker_fetcher (healthy)

## Access Points

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **Database**: localhost:5432

## Feature Testing Checklist

### 1. Database Schema ✅

**Test**: Verify monitoring tables exist

```bash
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "\dt fetcher*"
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "\dt price_update_log"
```

**Expected**: Should see 3 tables:
- `fetcher_logs`
- `fetcher_statistics`
- `price_update_log`

**Status**: ✅ Verified - All tables created

### 2. Fetcher Daemon Operation ✅

**Test**: Check fetcher is running and logging

```bash
docker-compose logs --tail=50 fetcher
```

**Expected Output**:
- "🎧 Backfill daemon listening for new transactions..."
- "⏰ Price update scheduler started (10 min interval)"
- No error messages

**Status**: ✅ Verified - Daemon running successfully

### 3. API Endpoints

#### 3.1 Status Endpoint ✅

**Test**:
```bash
curl http://localhost:8000/api/fetcher/status
```

**Expected Response**:
```json
{
  "status": "running",
  "uptime_seconds": <number>,
  "last_update": "<timestamp>",
  "next_update_in_seconds": <number>,
  "tracked_assets_count": 10,
  "update_interval_minutes": 10
}
```

**Status**: ✅ Verified - Returns correct data

#### 3.2 Statistics Endpoint ✅

**Test**:
```bash
curl http://localhost:8000/api/fetcher/statistics
```

**Expected Response**:
```json
{
  "uptime_seconds": <number>,
  "total_cycles": <number>,
  "successful_cycles": <number>,
  "failed_cycles": <number>,
  "success_rate": <percentage>,
  "average_cycle_duration_seconds": <number>,
  "last_cycle_duration_seconds": <number>,
  "assets_tracked": <number>
}
```

**Status**: ✅ Verified - Returns statistics (99.02% success rate observed)

#### 3.3 Logs Endpoint ✅

**Test**:
```bash
curl "http://localhost:8000/api/fetcher/logs?limit=5"
```

**Expected Response**:
```json
{
  "logs": [
    {
      "id": <number>,
      "timestamp": "<timestamp>",
      "level": "INFO|WARNING|ERROR",
      "message": "<message>",
      "context": {<optional context data>}
    }
  ],
  "total": <number>,
  "limit": 5,
  "offset": 0
}
```

**Status**: ✅ Verified - Returns paginated logs

#### 3.4 Recent Updates Endpoint ✅

**Test**:
```bash
curl "http://localhost:8000/api/fetcher/recent-updates?limit=5"
```

**Expected Response**:
```json
{
  "updates": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "timestamp": "<timestamp>",
      "price": 275.91,
      "success": true,
      "error": null
    }
  ]
}
```

**Status**: ✅ Verified - Returns recent price updates (AAPL, GOOGL, NVDA observed)

### 4. Frontend Monitoring Dashboard

#### 4.1 Access Dashboard

**Test**: 
1. Open browser to http://localhost:5173
2. Click "Fetcher" in the navigation menu
3. Verify dashboard loads

**Expected**:
- Dashboard page loads without errors
- Multiple cards displayed (Status, Statistics, Recent Updates, Logs)

#### 4.2 Status Card

**Test**: Verify Status Card displays:
- Daemon status indicator (green = running, red = error, gray = stopped)
- Last update timestamp
- Next update countdown
- Tracked assets count
- Update interval

**Expected Values**:
- Status: Running (green indicator)
- Tracked Assets: 10
- Update Interval: 10 minutes

#### 4.3 Statistics Card

**Test**: Verify Statistics Card displays:
- Uptime (human-readable format)
- Total cycles count
- Success rate (with visual indicator)
- Average cycle duration

**Expected**:
- Success rate should be > 95%
- Average duration should be < 30 seconds

#### 4.4 Recent Updates Card

**Test**: Verify Recent Updates Card displays:
- Table with columns: Symbol, Name, Timestamp, Price, Status
- Success/failure indicators
- At least 3 recent updates visible
- Scrollable list

**Expected Assets**:
- AAPL (Apple Inc.)
- GOOGL (Alphabet Inc.)
- NVDA (NVIDIA Corporation)

#### 4.5 Logs Card

**Test**: Verify Logs Card displays:
- Table with columns: Timestamp, Level, Message
- Log level filter dropdown
- Color-coded log levels (INFO=blue, WARNING=yellow, ERROR=red)
- Expandable rows for context details

**Expected Log Types**:
- "Price update cycle complete"
- "Starting portfolio value recalculation"
- "Portfolio value recalculation complete"

#### 4.6 Auto-Refresh

**Test**: 
1. Open dashboard
2. Wait 15 seconds
3. Observe if data refreshes automatically

**Expected**:
- Dashboard should refresh every 15 seconds
- New logs should appear
- Statistics should update
- No page reload required

### 5. Error Handling

#### 5.1 Network Error Resilience

**Test**: Simulate network error by stopping API temporarily
```bash
docker-compose stop api
# Wait 30 seconds
docker-compose start api
```

**Expected**:
- Fetcher continues running
- Error logged in fetcher_logs
- Dashboard shows error state gracefully
- System recovers when API restarts

#### 5.2 Database Connection

**Test**: Check fetcher health
```bash
docker inspect portfolio_tracker_fetcher --format='{{.State.Health.Status}}'
```

**Expected**: `healthy`

### 6. Resource Usage

**Test**: Check resource consumption
```bash
docker stats portfolio_tracker_fetcher --no-stream
```

**Expected**:
- CPU: < 50% (0.5 cores limit)
- Memory: < 512MB (limit)
- Should be well within configured limits

### 7. Configuration

**Test**: Verify environment variables are set
```bash
docker-compose exec fetcher env | grep -E "(UPDATE_INTERVAL|LOG_RETENTION|STATS_PERSIST)"
```

**Expected**:
```
UPDATE_INTERVAL_MINUTES=10
LOG_RETENTION_DAYS=30
STATS_PERSIST_INTERVAL=300
```

### 8. Data Persistence

#### 8.1 Logs Retention

**Test**: Check log count
```bash
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "SELECT COUNT(*) FROM fetcher_logs;"
```

**Expected**: Should have logs from recent operations

#### 8.2 Statistics History

**Test**: Check statistics records
```bash
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "SELECT COUNT(*) FROM fetcher_statistics;"
```

**Expected**: Should have statistics records

#### 8.3 Price Update Log

**Test**: Check price update history
```bash
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "SELECT symbol, timestamp, success FROM price_update_log JOIN assets ON price_update_log.asset_id = assets.id ORDER BY timestamp DESC LIMIT 5;"
```

**Expected**: Should show recent price updates with timestamps

## Manual Testing Scenarios

### Scenario 1: Fresh Start
1. Stop all services: `docker-compose down`
2. Start services: `docker-compose up -d`
3. Wait for database to be healthy (6 seconds)
4. Verify fetcher starts successfully
5. Check dashboard loads correctly

### Scenario 2: Price Update Cycle
1. Note current time
2. Wait for next 10-minute mark (e.g., 10:00, 10:10, 10:20)
3. Watch fetcher logs: `docker-compose logs -f fetcher`
4. Verify cycle completes successfully
5. Check dashboard shows new updates

### Scenario 3: Portfolio Recalculation
1. Add a new transaction via frontend
2. Wait for next price update cycle
3. Verify portfolio values are recalculated
4. Check logs for "Portfolio value recalculation complete"

### Scenario 4: Error Recovery
1. Temporarily block network access to Yahoo Finance (if possible)
2. Wait for update cycle
3. Verify errors are logged
4. Restore network access
5. Verify next cycle succeeds

## Performance Benchmarks

### API Response Times
- `/api/fetcher/status`: < 100ms
- `/api/fetcher/logs`: < 200ms
- `/api/fetcher/statistics`: < 100ms
- `/api/fetcher/recent-updates`: < 200ms

### Update Cycle Performance
- Cycle duration: 5-15 seconds (for 3-10 assets)
- Portfolio recalculation: < 5 seconds
- Success rate: > 95%

## Troubleshooting

### Fetcher Not Starting
```bash
# Check logs
docker-compose logs fetcher

# Common issues:
# - Missing Python modules → Rebuild: docker-compose build fetcher
# - Database not ready → Wait for postgres health check
# - Port conflicts → Check if ports are available
```

### Dashboard Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Check if API is accessible
curl http://localhost:8000/api/fetcher/status

# Verify frontend is running
docker-compose ps frontend
```

### No Data in Dashboard
```bash
# Check if fetcher has run at least one cycle
docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "SELECT COUNT(*) FROM fetcher_logs;"

# If count is 0, wait for first update cycle (up to 10 minutes)
# Or trigger manually by restarting fetcher
docker-compose restart fetcher
```

## Success Criteria

✅ All services running and healthy
✅ All API endpoints responding correctly
✅ Dashboard accessible and displaying data
✅ Auto-refresh working (15-second interval)
✅ Logs being persisted to database
✅ Statistics being calculated correctly
✅ Price updates happening every 10 minutes
✅ Portfolio values being recalculated
✅ Error handling working (daemon continues on errors)
✅ Resource usage within limits

## Next Steps

After verifying all features work:

1. **Monitor for 1 hour**: Ensure stability over multiple update cycles
2. **Check log retention**: Verify old logs are purged after 30 days (long-term test)
3. **Load testing**: Add more tracked assets to test scalability
4. **Custom configuration**: Try different UPDATE_INTERVAL_MINUTES values
5. **Production deployment**: Review security settings in DOCKER_CONFIGURATION.md

## Quick Verification Script

Run this to quickly verify all components:

```bash
echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Fetcher Health ==="
docker inspect portfolio_tracker_fetcher --format='{{.State.Health.Status}}'

echo -e "\n=== API Status ==="
curl -s http://localhost:8000/api/fetcher/status | python -m json.tool

echo -e "\n=== Recent Logs ==="
curl -s "http://localhost:8000/api/fetcher/logs?limit=3" | python -m json.tool

echo -e "\n=== Statistics ==="
curl -s http://localhost:8000/api/fetcher/statistics | python -m json.tool

echo -e "\n=== Recent Updates ==="
curl -s "http://localhost:8000/api/fetcher/recent-updates?limit=3" | python -m json.tool

echo -e "\n=== Database Tables ==="
docker-compose exec -T postgres psql -U postgres -d portfolio_tracker -c "\dt fetcher*"

echo -e "\n✅ All checks complete!"
```

Save this as `verify.sh` and run with `bash verify.sh` (or adapt for Windows PowerShell).
