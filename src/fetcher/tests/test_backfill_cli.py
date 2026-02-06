"""
Unit tests for backfill CLI argument parsing.

Tests the command-line interface argument parsing and validation
without actually running the backfill operation.
"""

import unittest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backfill_cli import parse_arguments, get_database_url, get_config_path, create_custom_config


class TestBackfillCLI(unittest.TestCase):
    """Test suite for backfill CLI."""
    
    def test_parse_arguments_once_mode(self):
        """Test parsing --once flag."""
        with patch('sys.argv', ['backfill_cli.py', '--once']):
            args = parse_arguments()
            self.assertTrue(args.once)
            self.assertFalse(args.scheduled)
            self.assertEqual(args.days, 365)
            self.assertFalse(args.force)
    
    def test_parse_arguments_with_symbols(self):
        """Test parsing --symbols parameter."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--symbols', 'AAPL', 'MSFT', 'GOOGL']):
            args = parse_arguments()
            self.assertEqual(args.symbols, ['AAPL', 'MSFT', 'GOOGL'])
    
    def test_parse_arguments_with_days(self):
        """Test parsing --days parameter."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--days', '180']):
            args = parse_arguments()
            self.assertEqual(args.days, 180)
    
    def test_parse_arguments_with_force(self):
        """Test parsing --force flag."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--force']):
            args = parse_arguments()
            self.assertTrue(args.force)
    
    def test_parse_arguments_with_config(self):
        """Test parsing --config parameter."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--config', '/path/to/config.json']):
            args = parse_arguments()
            self.assertEqual(args.config, '/path/to/config.json')
    
    def test_parse_arguments_with_db(self):
        """Test parsing --db parameter."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--db', 'postgresql://test:test@localhost/test']):
            args = parse_arguments()
            self.assertEqual(args.db, 'postgresql://test:test@localhost/test')
    
    def test_get_database_url_from_args(self):
        """Test database URL priority: args > env > default."""
        # Test with args.db set
        args = MagicMock()
        args.db = 'postgresql://from_args/db'
        url = get_database_url(args)
        self.assertEqual(url, 'postgresql://from_args/db')
    
    def test_get_database_url_from_env(self):
        """Test database URL from environment variable."""
        args = MagicMock()
        args.db = None
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://from_env/db'}):
            url = get_database_url(args)
            self.assertEqual(url, 'postgresql://from_env/db')
    
    def test_get_database_url_default(self):
        """Test default database URL."""
        args = MagicMock()
        args.db = None
        
        with patch.dict(os.environ, {}, clear=True):
            url = get_database_url(args)
            self.assertEqual(url, 'postgresql://postgres:postgres@localhost:5432/portfolio_tracker')
    
    def test_create_custom_config(self):
        """Test creating custom config file for symbol list."""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result_path = create_custom_config(symbols, temp_path)
            self.assertEqual(result_path, temp_path)
            
            # Verify file contents
            import json
            with open(temp_path, 'r') as f:
                config = json.load(f)
            
            self.assertEqual(config['name'], 'Custom Symbol List')
            self.assertEqual(config['symbols'], symbols)
            self.assertIn('last_updated', config)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_parse_arguments_requires_mode(self):
        """Test that either --once or --scheduled is required."""
        with patch('sys.argv', ['backfill_cli.py']):
            with self.assertRaises(SystemExit):
                parse_arguments()
    
    def test_parse_arguments_mutually_exclusive_modes(self):
        """Test that --once and --scheduled are mutually exclusive."""
        with patch('sys.argv', ['backfill_cli.py', '--once', '--scheduled']):
            with self.assertRaises(SystemExit):
                parse_arguments()


if __name__ == '__main__':
    unittest.main()
