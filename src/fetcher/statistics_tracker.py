"""
StatisticsTracker component for tracking fetcher daemon performance metrics.

This module provides the StatisticsTracker class which handles:
- Recording update cycle start and completion
- Calculating rolling averages for cycle duration
- Tracking success rates and uptime
- Persisting statistics to the database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional
from datetime import datetime
import uuid
from collections import deque


class StatisticsTracker:
    """
    Manages performance statistics for the fetcher daemon.
    
    The StatisticsTracker tracks update cycles, calculates success rates,
    maintains rolling averages, and persists statistics to PostgreSQL.
    """
    
    def __init__(self, db_url: str):
        """
        Initialize StatisticsTracker with database connection string.
        
        Args:
            db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
        """
        self.db_url = db_url
        self.conn = None
        self.cycle_durations = deque(maxlen=100)  # Last 100 cycle durations
        self.total_cycles = 0
        self.successful_cycles = 0
        self.start_time = datetime.now()
        self._active_cycles = {}  # Track cycle start times by cycle_id
    
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
    
    def record_cycle_start(self) -> str:
        """
        Record the start of an update cycle.
        
        Generates a unique cycle ID and records the start timestamp.
        This cycle ID should be passed to record_cycle_end() when the cycle completes.
        
        Returns:
            Unique cycle identifier (UUID string)
        """
        cycle_id = str(uuid.uuid4())
        self._active_cycles[cycle_id] = datetime.now()
        return cycle_id
    
    def record_cycle_end(self, cycle_id: str, success: bool, duration: float) -> None:
        """
        Record the completion of an update cycle.
        
        Updates internal statistics including total cycles, successful cycles,
        and rolling average duration.
        
        Args:
            cycle_id: The cycle identifier returned by record_cycle_start()
            success: Whether the cycle completed successfully
            duration: Duration of the cycle in seconds
        
        Raises:
            ValueError: If cycle_id is not found in active cycles
        """
        if cycle_id not in self._active_cycles:
            raise ValueError(f"Unknown cycle_id: {cycle_id}. Call record_cycle_start() first.")
        
        # Remove from active cycles
        del self._active_cycles[cycle_id]
        
        # Update counters
        self.total_cycles += 1
        if success:
            self.successful_cycles += 1
        
        # Add duration to rolling window
        self.cycle_durations.append(duration)
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics summary.
        
        Returns a dictionary containing all current performance metrics including
        uptime, cycle counts, success rate, and average duration.
        
        Returns:
            Dictionary with keys:
            - uptime_seconds: Time elapsed since daemon start (int)
            - total_cycles: Total number of cycles executed (int)
            - successful_cycles: Number of successful cycles (int)
            - failed_cycles: Number of failed cycles (int)
            - success_rate: Percentage of successful cycles (float, 0-100)
            - average_cycle_duration: Average duration over last 100 cycles in seconds (float)
            - last_cycle_duration: Duration of most recent cycle in seconds (float or None)
            - assets_tracked: Number of assets being tracked (int, requires database query)
        """
        # Calculate uptime
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        # Calculate success rate
        if self.total_cycles > 0:
            success_rate = round((self.successful_cycles / self.total_cycles) * 100, 2)
        else:
            success_rate = 0.0
        
        # Calculate average cycle duration
        if self.cycle_durations:
            average_duration = round(sum(self.cycle_durations) / len(self.cycle_durations), 2)
            last_duration = round(self.cycle_durations[-1], 2)
        else:
            average_duration = 0.0
            last_duration = None
        
        # Get tracked assets count from database
        assets_tracked = self._get_tracked_assets_count()
        
        return {
            'uptime_seconds': uptime_seconds,
            'total_cycles': self.total_cycles,
            'successful_cycles': self.successful_cycles,
            'failed_cycles': self.total_cycles - self.successful_cycles,
            'success_rate': success_rate,
            'average_cycle_duration': average_duration,
            'last_cycle_duration': last_duration,
            'assets_tracked': assets_tracked
        }
    
    def persist_statistics(self) -> None:
        """
        Save current statistics to the database.
        
        Inserts a new row into the fetcher_statistics table with the current
        statistics snapshot. This should be called periodically to maintain
        historical statistics data.
        
        Raises:
            RuntimeError: If database is not connected
            psycopg2.Error: If database operation fails
        """
        if not self.conn or self.conn.closed:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        stats = self.get_statistics()
        
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO fetcher_statistics (
                    timestamp,
                    uptime_seconds,
                    total_cycles,
                    successful_cycles,
                    failed_cycles,
                    success_rate,
                    average_cycle_duration,
                    assets_tracked
                )
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    stats['uptime_seconds'],
                    stats['total_cycles'],
                    stats['successful_cycles'],
                    stats['failed_cycles'],
                    stats['success_rate'],
                    stats['average_cycle_duration'],
                    stats['assets_tracked']
                )
            )
            self.conn.commit()
        finally:
            cursor.close()
    
    def _get_tracked_assets_count(self) -> int:
        """
        Query the database for the number of tracked assets.
        
        Returns:
            Number of assets in the tracked_assets table, or 0 if database not connected
        """
        if not self.conn or self.conn.closed:
            return 0
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM tracked_assets")
            result = cursor.fetchone()
            return result[0] if result else 0
        except psycopg2.Error:
            # If query fails (e.g., table doesn't exist), return 0
            return 0
        finally:
            cursor.close()
