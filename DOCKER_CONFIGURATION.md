# Docker Configuration Guide

## Overview

This document describes the Docker Compose configuration for the Portfolio Tracker application, with a focus on the fetcher daemon service.

## Services

### Fetcher Service

The fetcher service runs as a background daemon that continuously updates stock prices and monitors system health.

#### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | **Required** | PostgreSQL connection string. Format: `postgresql://user:password@host:port/database` |
| `UPDATE_INTERVAL_MINUTES` | integer | `10` | Interval between price update cycles in minutes. Minimum recommended: 5 minutes |
| `LOG_RETENTION_DAYS` | integer | `30` | Number of days to retain fetcher logs before automatic purging |
| `STATS_PERSIST_INTERVAL` | integer | `300` | Interval in seconds to persist statistics to database (5 minutes) |

#### Resource Limits

The fetcher service is configured with resource constraints to ensure stable operation:

**CPU:**
- Limit: 0.5 cores (50% of one CPU core)
- Reservation: 0.25 cores (25% of one CPU core)

**Memory:**
- Limit: 512MB
- Reservation: 256MB

These limits can be adjusted in `docker-compose.yml` under the `deploy.resources` section if your workload requires different constraints.

#### Restart Policy

**Policy:** `unless-stopped`

This policy ensures:
- The fetcher automatically restarts if it crashes or exits unexpectedly
- The fetcher restarts on system reboot (unless manually stopped)
- The fetcher does not restart if explicitly stopped using `docker-compose stop fetcher`

#### Health Check

The fetcher includes a health check that verifies database connectivity:

- **Test Command:** Attempts to connect to PostgreSQL database
- **Interval:** 30 seconds between checks
- **Timeout:** 10 seconds per check
- **Retries:** 3 attempts before marking as unhealthy
- **Start Period:** 40 seconds grace period on startup

#### Dependencies

The fetcher service depends on the `postgres` service with a health check condition, ensuring:
- The fetcher only starts after PostgreSQL is healthy and ready
- Automatic restart if database connection is lost

## Configuration Examples

### Development Configuration

For development with more frequent updates and verbose logging:

```yaml
fetcher:
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/portfolio_tracker
    - UPDATE_INTERVAL_MINUTES=5
    - LOG_RETENTION_DAYS=7
    - STATS_PERSIST_INTERVAL=60
```

### Production Configuration

For production with conservative resource usage:

```yaml
fetcher:
  environment:
    - DATABASE_URL=postgresql://user:secure_password@postgres:5432/portfolio_tracker
    - UPDATE_INTERVAL_MINUTES=15
    - LOG_RETENTION_DAYS=90
    - STATS_PERSIST_INTERVAL=600
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
```

## Common Operations

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start only fetcher
docker-compose up -d fetcher
```

### Viewing Logs

```bash
# Follow fetcher logs
docker-compose logs -f fetcher

# View last 100 lines
docker-compose logs --tail=100 fetcher
```

### Restarting Services

```bash
# Restart fetcher
docker-compose restart fetcher

# Restart all services
docker-compose restart
```

### Stopping Services

```bash
# Stop fetcher
docker-compose stop fetcher

# Stop all services
docker-compose down
```

### Checking Service Health

```bash
# Check service status
docker-compose ps

# Inspect fetcher health
docker inspect portfolio_tracker_fetcher --format='{{.State.Health.Status}}'
```

## Troubleshooting

### Fetcher Not Starting

1. Check database health:
   ```bash
   docker-compose ps postgres
   ```

2. View fetcher logs:
   ```bash
   docker-compose logs fetcher
   ```

3. Verify database connection:
   ```bash
   docker-compose exec postgres psql -U postgres -d portfolio_tracker -c "SELECT 1;"
   ```

### High Resource Usage

If the fetcher is consuming too many resources:

1. Reduce update frequency:
   - Increase `UPDATE_INTERVAL_MINUTES` to 15 or 20

2. Adjust resource limits in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.25'
         memory: 256M
   ```

3. Restart the service:
   ```bash
   docker-compose restart fetcher
   ```

### Database Connection Issues

If the fetcher cannot connect to the database:

1. Verify the `DATABASE_URL` is correct
2. Ensure the postgres service is healthy
3. Check network connectivity between containers
4. Review postgres logs for connection errors

## Monitoring

Access the Fetcher Monitoring Dashboard at http://localhost:5173 to view:
- Real-time daemon status
- Update cycle statistics
- Recent price updates
- Operational logs and errors
- Performance metrics

## Security Considerations

### Production Deployment

For production environments:

1. **Change default passwords:**
   ```yaml
   postgres:
     environment:
       POSTGRES_PASSWORD: <strong-password>
   
   fetcher:
     environment:
       - DATABASE_URL=postgresql://postgres:<strong-password>@postgres:5432/portfolio_tracker
   ```

2. **Use secrets management:**
   - Consider using Docker secrets or environment files
   - Never commit credentials to version control

3. **Restrict network access:**
   - Remove port mappings for internal services
   - Use Docker networks for service isolation

4. **Enable TLS/SSL:**
   - Configure PostgreSQL to use SSL connections
   - Update DATABASE_URL to use `sslmode=require`

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Fetcher Module Documentation](src/fetcher/README.md)
