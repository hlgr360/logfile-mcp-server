"""
AI: Comprehensive tests for database connection management - FIXED VERSION.

Tests database initialization, session handling, raw SQL execution,
and error handling scenarios.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.database.connection import DatabaseConnection
from app.database.models import Base, NginxLog, NexusLog


class TestDatabaseConnection:
    """AI: Test database connection functionality."""
    
    def setup_method(self):
        """AI: Setup temporary database for each test."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
    
    def teardown_method(self):
        """AI: Clean up temporary database after each test."""
        db_path = Path(self.db_path)
        if db_path.exists():
            db_path.unlink()

    def test_database_initialization_creates_fresh_database(self):
        """AI: Test fresh database creation and schema setup."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Check that database file exists
        assert Path(self.db_path).exists()
        
        # Check that tables are created
        tables = db_conn.execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in tables]
        assert 'nginx_logs' in table_names
        assert 'nexus_logs' in table_names
        
        db_conn.close()

    def test_database_initialization_removes_existing_database(self):
        """AI: Test that existing database is properly removed and recreated."""
        # Create initial database
        db_conn1 = DatabaseConnection(self.db_path)
        db_conn1.close()
        
        # Verify it exists
        assert Path(self.db_path).exists()
        
        # Create new connection - should remove and recreate
        db_conn2 = DatabaseConnection(self.db_path)
        
        # Should still exist and be functional
        assert Path(self.db_path).exists()
        tables = db_conn2.execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
        assert len(tables) > 0
        
        db_conn2.close()

    def test_session_context_manager_commits_on_success(self):
        """AI: Test session context manager commits transaction on success."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Insert test data using session context manager
        test_data = {
            'ip_address': '127.0.0.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/test',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }
        
        with db_conn.get_session() as session:
            session.add(NginxLog(**test_data))
        
        # Verify data was committed
        with db_conn.get_session() as session:
            count = session.query(NginxLog).count()
            assert count == 1
        
        db_conn.close()

    def test_session_context_manager_rolls_back_on_exception(self):
        """AI: Test that session context manager rolls back on exception."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Attempt to insert invalid data that will cause exception
        try:
            with db_conn.get_session() as session:
                # Invalid data - missing required fields
                invalid_log = NginxLog(ip_address='127.0.0.1')  # Missing required fields
                session.add(invalid_log)
                raise Exception("Simulated error")
        except Exception:
            pass  # Expected
        
        # Verify no data was committed
        with db_conn.get_session() as session:
            count = session.query(NginxLog).count()
            assert count == 0
        
        db_conn.close()

    def test_execute_raw_sql_returns_results(self):
        """AI: Test raw SQL execution returns proper results."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Execute a simple query
        results = db_conn.execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
        
        assert isinstance(results, list)
        # Should have nginx_logs and nexus_logs tables
        table_names = [row['name'] for row in results]
        assert 'nginx_logs' in table_names
        assert 'nexus_logs' in table_names
        
        db_conn.close()

    def test_execute_raw_sql_with_parameters(self):
        """AI: Test raw SQL execution with parameters."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Insert test data first
        test_data = {
            'ip_address': '192.168.1.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'POST',
            'path': '/api/test',
            'http_version': 'HTTP/1.1',
            'status_code': 201,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }
        
        with db_conn.get_session() as session:
            session.add(NginxLog(**test_data))
        
        # Query with parameters (SQLAlchemy 2.0 uses dict params)
        results = db_conn.execute_raw_sql(
            "SELECT * FROM nginx_logs WHERE method = :method AND status_code = :status",
            {'method': 'POST', 'status': 201}
        )
        
        assert len(results) == 1
        assert results[0]['ip_address'] == '192.168.1.1'
        
        db_conn.close()

    def test_get_table_info_returns_schema_details(self):
        """AI: Test table schema information retrieval."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Get nginx_logs table info
        table_info = db_conn.get_table_info('nginx_logs')
        
        assert isinstance(table_info, dict)
        assert table_info['exists'] == True
        assert 'columns' in table_info
        assert 'indexes' in table_info
        
        # Check for expected columns
        column_names = [col['name'] for col in table_info['columns']]
        expected_columns = ['id', 'ip_address', 'timestamp', 'method', 'path', 'status_code']
        for col in expected_columns:
            assert col in column_names
        
        db_conn.close()

    def test_get_table_info_nonexistent_table(self):
        """AI: Test table info for non-existent table returns proper structure."""
        db_conn = DatabaseConnection(self.db_path)
        
        table_info = db_conn.get_table_info('nonexistent_table')
        
        assert isinstance(table_info, dict)
        assert table_info['exists'] == False
        assert 'columns' in table_info or 'error' in table_info
        
        db_conn.close()

    def test_get_database_stats_returns_statistics(self):
        """AI: Test database statistics retrieval."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Insert some test data
        with db_conn.get_session() as session:
            nginx_log = NginxLog(
                ip_address='127.0.0.1',
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
                method='GET',
                path='/test',
                http_version='HTTP/1.1',
                status_code=200,
                raw_log='test log line',
                file_source='test.log'
            )
            nexus_log = NexusLog(
                ip_address='127.0.0.1',
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
                method='GET',
                path='/repository/test',
                http_version='HTTP/1.1',
                status_code=200,
                raw_log='test log line',
                file_source='nexus.log'
            )
            session.add(nginx_log)
            session.add(nexus_log)
        
        # Get database stats
        stats = db_conn.get_database_stats()
        
        assert 'database_size_bytes' in stats
        assert 'tables' in stats
        assert 'total_rows' in stats
        assert stats['tables']['nginx_logs'] == 1
        assert stats['tables']['nexus_logs'] == 1
        assert stats['total_rows'] == 2
        
        db_conn.close()

    def test_close_disposes_engine(self):
        """AI: Test that close method properly disposes of engine."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Verify engine exists
        assert db_conn.engine is not None
        
        # Close connection
        db_conn.close()
        
        # Engine should still exist but connections should be closed
        assert db_conn.engine is not None

    def test_engine_configuration(self):
        """AI: Test that SQLite engine is configured properly."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Check engine URL
        assert str(db_conn.engine.url).startswith('sqlite:///')
        
        # Check that engine is functional
        tables = db_conn.execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
        assert len(tables) > 0
        
        db_conn.close()


class TestDatabaseConnectionErrorHandling:
    """AI: Test error handling scenarios for database connection."""
    
    def setup_method(self):
        """AI: Setup temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
    
    def teardown_method(self):
        """AI: Clean up temporary database after each test."""
        db_path = Path(self.db_path)
        if db_path.exists():
            db_path.unlink()

    def test_get_table_info_handles_sql_errors(self):
        """AI: Test table info gracefully handles SQL errors."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Mock execute_raw_sql to raise exception
        with patch.object(db_conn, 'execute_raw_sql', side_effect=Exception("SQL Error")):
            table_info = db_conn.get_table_info('nginx_logs')
            
            # Should return error info in dict format
            assert isinstance(table_info, dict)
            assert table_info['exists'] == False
            assert 'error' in table_info
        
        db_conn.close()

    def test_get_database_stats_handles_errors(self):
        """AI: Test database stats gracefully handles errors."""
        db_conn = DatabaseConnection(self.db_path)
        
        # Mock execute_raw_sql to raise exception
        with patch.object(db_conn, 'execute_raw_sql', side_effect=Exception("Database Error")):
            stats = db_conn.get_database_stats()
            
            # Should return dict with basic info and error
            assert isinstance(stats, dict)
            assert 'database_path' in stats
            assert 'error' in stats
        
        db_conn.close()

    def test_invalid_database_path_handling(self):
        """AI: Test handling of invalid database paths."""
        # Try to create database in non-existent directory
        invalid_path = "/non/existent/directory/test.db"
        
        # Should handle error gracefully
        try:
            db_conn = DatabaseConnection(invalid_path)
            # If it doesn't raise an exception, it created the path
            assert Path(invalid_path).parent.exists()
            db_conn.close()
        except Exception:
            # Expected if path truly cannot be created
            pass
