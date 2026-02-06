# Fetcher Monitoring Verification Script
# Run this to quickly verify all components are working

Write-Host "=== Service Status ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n=== Fetcher Health ===" -ForegroundColor Cyan
docker inspect portfolio_tracker_fetcher --format='{{.State.Health.Status}}'

Write-Host "`n=== API Status ===" -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/fetcher/status"
    $status | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n=== Recent Logs ===" -ForegroundColor Cyan
try {
    $logs = Invoke-RestMethod -Uri "http://localhost:8000/api/fetcher/logs?limit=3"
    $logs | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n=== Statistics ===" -ForegroundColor Cyan
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/fetcher/statistics"
    $stats | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n=== Recent Updates ===" -ForegroundColor Cyan
try {
    $updates = Invoke-RestMethod -Uri "http://localhost:8000/api/fetcher/recent-updates?limit=3"
    $updates | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n=== Database Tables ===" -ForegroundColor Cyan
docker-compose exec -T postgres psql -U postgres -d portfolio_tracker -c "\dt fetcher*"

Write-Host "`n=== Log Count ===" -ForegroundColor Cyan
docker-compose exec -T postgres psql -U postgres -d portfolio_tracker -c "SELECT COUNT(*) as log_count FROM fetcher_logs;"

Write-Host "`n=== Recent Price Updates ===" -ForegroundColor Cyan
docker-compose exec -T postgres psql -U postgres -d portfolio_tracker -c "SELECT a.symbol, p.timestamp, p.price, p.success FROM price_update_log p JOIN assets a ON p.asset_id = a.id ORDER BY p.timestamp DESC LIMIT 5;"

Write-Host "`n✅ All checks complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:5173 in your browser"
Write-Host "2. Click 'Fetcher' in the navigation menu"
Write-Host "3. Verify the monitoring dashboard displays correctly"
Write-Host "4. Wait 15 seconds and verify auto-refresh works"
