-- Migration: Add Fetcher Daemon Monitoring Tables
-- Date: 2026-02-05
-- Description: Adds tables for fetcher daemon monitoring, logging, and statistics tracking

-- ============================================================================
-- 1. Fetcher Logs Table
-- ============================================================================
-- Stores operational logs from the fetcher daemon
CREATE TABLE IF NOT EXISTS fetcher_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for efficient log queries
CREATE INDEX idx_fetcher_logs_timestamp ON fetcher_logs(timestamp DESC);
CREATE INDEX idx_fetcher_logs_level ON fetcher_logs(level);
CREATE INDEX idx_fetcher_logs_created_at ON fetcher_logs(created_at DESC);

-- ============================================================================
-- 2. Fetcher Statistics Table
-- ============================================================================
-- Stores aggregated statistics about fetcher daemon performance
CREATE TABLE IF NOT EXISTS fetcher_statistics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    uptime_seconds INTEGER NOT NULL,
    total_cycles INTEGER NOT NULL,
    successful_cycles INTEGER NOT NULL,
    failed_cycles INTEGER NOT NULL,
    success_rate DECIMAL(5,2) NOT NULL,
    average_cycle_duration DECIMAL(10,2) NOT NULL,
    assets_tracked INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for retrieving latest statistics
CREATE INDEX idx_fetcher_statistics_timestamp ON fetcher_statistics(timestamp DESC);
CREATE INDEX idx_fetcher_statistics_created_at ON fetcher_statistics(created_at DESC);

-- ============================================================================
-- 3. Price Update Log Table
-- ============================================================================
-- Tracks individual price update attempts for each asset
CREATE TABLE IF NOT EXISTS price_update_log (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    price DECIMAL(20,8),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX idx_price_update_log_timestamp ON price_update_log(timestamp DESC);
CREATE INDEX idx_price_update_log_asset ON price_update_log(asset_id);
CREATE INDEX idx_price_update_log_success ON price_update_log(success);
CREATE INDEX idx_price_update_log_asset_timestamp ON price_update_log(asset_id, timestamp DESC);

-- ============================================================================
-- 4. Portfolio Performance Cache Table (Modification)
-- ============================================================================
-- The portfolio_performance_cache table already exists in schema.sql
-- This section adds additional fields if needed for monitoring

-- Check if we need to add timestamp tracking for monitoring
-- The existing table has last_updated, which is sufficient
-- No modifications needed - table already exists with required fields

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- These comments document how to verify the migration

-- Verify fetcher_logs table
-- SELECT COUNT(*) FROM fetcher_logs;

-- Verify fetcher_statistics table
-- SELECT COUNT(*) FROM fetcher_statistics;

-- Verify price_update_log table
-- SELECT COUNT(*) FROM price_update_log;

-- Verify portfolio_performance_cache table
-- SELECT COUNT(*) FROM portfolio_performance_cache;

-- List all indexes on monitoring tables
-- SELECT tablename, indexname FROM pg_indexes 
-- WHERE tablename IN ('fetcher_logs', 'fetcher_statistics', 'price_update_log')
-- ORDER BY tablename, indexname;
