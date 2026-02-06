"""
LogStore component for persisting fetcher daemon logs to PostgreSQL.

This module provides the LogStore class which handles:
- Writing log entries to the fetcher_logs table
- Retrieving recent logs with pagination
- Purging old logs based on retention policy
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class LogStore:
    """
    Manages persistent storage of fetcher daemon logs in PostgreSQL.
    
    The LogStore provides methods for writing log entries, retrieving logs
    with pagination, and managing log retention according to policy.
    """
    
    def __init__(self, db_url: str):
        """
        Initialize LogStore with database connection string.
        
        Args:
            db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
        """
        self.db_url = db_url
        self.conn = None
    
    def connect(self) -> None:
        """
        Establish database connection.
        
        Creates a new connection to PostgreSQL using the provided connection string.
        Should be called before any other operations.
        
        Raises:
            psycopg2.Error: If connection fails
        """
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.db_url)
    
    def close(self) -> None:
        """
        Close database connection.
        
        Safely closes the database connection if it exists and is open.
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def log(self, level: str, message: str, context: Optional[Dict] = None) -> None:
        """
        Write a log entry to the fetcher_logs table.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message text
            context: Optional dictionary with additional structured data
        
        Raises:
            RuntimeError: If database is not connected
            psycopg2.Error: If database operation fails
        """
        if not self.conn or self.conn.closed:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        # Validate log level
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")
        
        cursor = self.conn.cursor()
        try:
            # Convert context dict to JSON if provided
            context_json = json.dumps(context) if context else None
            
            cursor.execute(
                """
                INSERT INTO fetcher_logs (timestamp, level, message, context)
                VALUES (NOW(), %s, %s, %s)
                """,
                (level.upper(), message, context_json)
            )
            self.conn.commit()
        finally:
            cursor.close()
    
    def get_recent_logs(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        level: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve recent logs with pagination support.
        
        Args:
            limit: Maximum number of logs to return (default: 100)
            offset: Number of logs to skip for pagination (default: 0)
            level: Optional filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            List of log entries as dictionaries with keys:
            - id: Log entry ID
            - timestamp: When the log was created
            - level: Log level
            - message: Log message
            - context: Additional context data (dict or None)
            - created_at: Database insertion timestamp
        
        Raises:
            RuntimeError: If database is not connected
            psycopg2.Error: If database operation fails
        """
        if not self.conn or self.conn.closed:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Build query with optional level filter
            query = """
                SELECT id, timestamp, level, message, context, created_at
                FROM fetcher_logs
            """
            params = []
            
            if level:
                # Validate log level
                valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
                if level.upper() not in valid_levels:
                    raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")
                query += " WHERE level = %s"
                params.append(level.upper())
            
            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert RealDictRow to regular dict and parse JSON context
            logs = []
            for row in results:
                log_entry = dict(row)
                # Parse context JSON string back to dict if present
                if log_entry['context']:
                    try:
                        log_entry['context'] = json.loads(log_entry['context'])
                    except (json.JSONDecodeError, TypeError):
                        # Keep as string if parsing fails
                        pass
                logs.append(log_entry)
            
            return logs
        finally:
            cursor.close()
    
    def purge_old_logs(self, days: int = 30) -> int:
        """
        Delete logs older than specified number of days.
        
        Implements the log retention policy by removing entries that exceed
        the retention period.
        
        Args:
            days: Number of days to retain logs (default: 30)
        
        Returns:
            Number of log entries deleted
        
        Raises:
            RuntimeError: If database is not connected
            psycopg2.Error: If database operation fails
        """
        if not self.conn or self.conn.closed:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        cursor = self.conn.cursor()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute(
                """
                DELETE FROM fetcher_logs
                WHERE timestamp < %s
                """,
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            self.conn.commit()
            
            return deleted_count
        finally:
            cursor.close()
