FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy fetcher code
COPY fetcher.py .
COPY db_loader.py .
COPY backfill_daemon.py .
COPY __init__.py .

# Run daemon with unbuffered output
CMD ["python", "-u", "backfill_daemon.py"]
