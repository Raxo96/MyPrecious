# MyPrecious
App to track stock portfolio

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Running the Application

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Start all services:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Database: localhost:5432

### Services

The application consists of four services:

- **postgres**: PostgreSQL database (port 5432)
- **api**: FastAPI backend (port 8000)
- **frontend**: React frontend (port 5173)
- **fetcher**: Background daemon for continuous price updates

### Fetcher Configuration

The fetcher daemon runs continuously and updates stock prices every 10 minutes by default. You can configure it by modifying environment variables in `docker-compose.yml`:

- `UPDATE_INTERVAL_MINUTES`: Update frequency (default: 10)
- `LOG_RETENTION_DAYS`: Log retention period (default: 30)
- `STATS_PERSIST_INTERVAL`: Statistics persistence interval in seconds (default: 300)

For detailed fetcher documentation, see [src/fetcher/README.md](src/fetcher/README.md).

### Monitoring

Access the Fetcher Monitoring Dashboard at http://localhost:5173 to view:
- Daemon status and uptime
- Recent price updates
- Operational logs
- Performance statistics

### Stopping the Application

```bash
docker-compose down
```

To remove all data including the database:
```bash
docker-compose down -v
```
