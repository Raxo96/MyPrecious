-- Sample data for testing

-- Insert test user
INSERT INTO users (email, password_hash) VALUES
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIeWEgZWUu'); -- password: test123

-- Insert sample assets (10 popular stocks)
INSERT INTO assets (symbol, name, asset_type, exchange, native_currency) VALUES
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD'),
('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD'),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'USD'),
('AMZN', 'Amazon.com Inc.', 'stock', 'NASDAQ', 'USD'),
('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD'),
('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'USD'),
('META', 'Meta Platforms Inc.', 'stock', 'NASDAQ', 'USD'),
('BRK-B', 'Berkshire Hathaway Inc.', 'stock', 'NYSE', 'USD'),
('V', 'Visa Inc.', 'stock', 'NYSE', 'USD'),
('JPM', 'JPMorgan Chase & Co.', 'stock', 'NYSE', 'USD');

-- Insert USD exchange rate (base currency)
INSERT INTO exchange_rates (currency_code, rate_to_usd, timestamp, source) VALUES
('USD', 1.0, NOW(), 'base');

-- Create test portfolio
INSERT INTO portfolios (user_id, name, currency) VALUES
(1, 'My Portfolio', 'USD');
