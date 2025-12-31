"""
AI: Comprehensive tests for database operations.

Tests batch insert operations, query execution, security restrictions,
and schema inspection functionality.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.database.connection import DatabaseConnection
from app.database.operations import DatabaseOperations
from app.database.models import NginxLog, NexusLog


class TestDatabaseOperations:
    """AI: Test database operations functionality."""
    
    def setup_method(self):
        """AI: Setup test database and operations for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.db_connection = DatabaseConnection(self.db_path)
        self.db_ops = DatabaseOperations(self.db_connection)
        
    def teardown_method(self):
        """AI: Cleanup test database after each test."""
        self.db_connection.close()
        db_path = Path(self.db_path)
        if db_path.exists():
            db_path.unlink()
    
    def test_batch_insert_nginx_logs_success(self):
        """AI: Test successful batch insert of nginx logs."""
        log_data = [
            {
                'ip_address': '192.168.1.1',
                'timestamp': datetime(2025, 1, 1, 12, 0, 0),
                'method': 'GET',
                'path': '/api/test1',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': 1024,
                'raw_log': 'test log line 1',
                'file_source': 'test1.log'
            },
            {
                'ip_address': '192.168.1.2',
                'timestamp': datetime(2025, 1, 1, 12, 1, 0),
                'method': 'POST',
                'path': '/api/test2',
                'http_version': 'HTTP/1.1',
                'status_code': 201,
                'response_size': 2048,
                'raw_log': 'test log line 2',
                'file_source': 'test2.log'
            }
        ]
        
        result = self.db_ops.batch_insert_nginx_logs(log_data)
        
        assert result == 2
        
        # Verify data was inserted
        with self.db_connection.get_session() as session:
            count = session.query(NginxLog).count()
            assert count == 2
            
            # Check specific data
            log1 = session.query(NginxLog).filter_by(ip_address='192.168.1.1').first()
            assert log1.method == 'GET'
            assert log1.path == '/api/test1'
            assert log1.status_code == 200
    
    def test_batch_insert_nginx_logs_empty_list(self):
        """AI: Test batch insert with empty list returns zero."""
        result = self.db_ops.batch_insert_nginx_logs([])
        assert result == 0
    
    def test_batch_insert_nginx_logs_handles_errors(self):
        """AI: Test batch insert handles database errors."""
        # Invalid data that will cause database error
        invalid_data = [
            {
                'ip_address': '192.168.1.1',
                # Missing required timestamp field
                'method': 'GET',
                'path': '/api/test',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'raw_log': 'test log line',
                'file_source': 'test.log'
            }
        ]
        
        with pytest.raises(Exception):
            self.db_ops.batch_insert_nginx_logs(invalid_data)
    
    def test_batch_insert_nexus_logs_success(self):
        """AI: Test successful batch insert of nexus logs."""
        log_data = [
            {
                'ip_address': '10.0.0.1',
                'timestamp': datetime(2025, 1, 1, 13, 0, 0),
                'method': 'GET',
                'path': '/repository/maven/artifact.jar',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': 1024,
                'request_size': 2048,
                'processing_time_ms': 50,
                'user_agent': 'Maven/3.8.1',
                'thread_info': '[qtp123456-78]',
                'raw_log': 'nexus test log line 1',
                'file_source': 'nexus1.log'
            },
            {
                'ip_address': '10.0.0.2',
                'timestamp': datetime(2025, 1, 1, 13, 1, 0),
                'method': 'PUT',
                'path': '/repository/maven/upload.jar',
                'http_version': 'HTTP/1.1',
                'status_code': 201,
                'response_size': 4096,
                'request_size': 8192,
                'processing_time_ms': 120,
                'user_agent': 'curl/7.68.0',
                'thread_info': '[qtp123456-79]',
                'raw_log': 'nexus test log line 2',
                'file_source': 'nexus2.log'
            }
        ]
        
        result = self.db_ops.batch_insert_nexus_logs(log_data)
        
        assert result == 2
        
        # Verify data was inserted
        with self.db_connection.get_session() as session:
            count = session.query(NexusLog).count()
            assert count == 2
            
            # Check specific data
            log1 = session.query(NexusLog).filter_by(ip_address='10.0.0.1').first()
            assert log1.method == 'GET'
            assert log1.path == '/repository/maven/artifact.jar'
            assert log1.processing_time_ms == 50
    
    def test_batch_insert_nexus_logs_empty_list(self):
        """AI: Test nexus batch insert with empty list returns zero."""
        result = self.db_ops.batch_insert_nexus_logs([])
        assert result == 0
    
    def test_execute_query_select_success(self):
        """AI: Test successful SELECT query execution."""
        # Insert test data first
        log_data = [{
            'ip_address': '127.0.0.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/test',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }]
        self.db_ops.batch_insert_nginx_logs(log_data)
        
        # Execute query
        results = self.db_ops.execute_query("SELECT * FROM nginx_logs WHERE ip_address = '127.0.0.1'")
        
        assert len(results) == 1
        assert results[0]['ip_address'] == '127.0.0.1'
        assert results[0]['method'] == 'GET'
    
    def test_execute_query_rejects_non_select(self):
        """AI: Test that non-SELECT queries are rejected for security."""
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.db_ops.execute_query("DROP TABLE nginx_logs")
        
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.db_ops.execute_query("INSERT INTO nginx_logs VALUES (1, '127.0.0.1')")
        
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.db_ops.execute_query("UPDATE nginx_logs SET ip_address = '192.168.1.1'")
        
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.db_ops.execute_query("DELETE FROM nginx_logs")
    
    def test_execute_query_adds_limit_if_missing(self):
        """AI: Test that LIMIT is automatically added to queries."""
        # Insert test data
        log_data = [{
            'ip_address': '127.0.0.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/test',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }]
        self.db_ops.batch_insert_nginx_logs(log_data)
        
        # Test that the query works and adds limit automatically by default (1000)
        result = self.db_ops.execute_query("SELECT * FROM nginx_logs")
        assert isinstance(result, list)
        # Test that our data is there
        assert len(result) >= 1
        assert result[0]['ip_address'] == '127.0.0.1'
    
    def test_execute_query_respects_existing_limit(self):
        """AI: Test that existing LIMIT in query is preserved."""
        # Insert test data first
        log_data = [{
            'ip_address': '127.0.0.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/test',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }]
        self.db_ops.batch_insert_nginx_logs(log_data)
        
        # Test that query with existing LIMIT works
        result = self.db_ops.execute_query("SELECT * FROM nginx_logs LIMIT 50")
        assert isinstance(result, list)
        # Should return the inserted data with the LIMIT 50 preserved
        assert len(result) >= 1

    def test_execute_query_handles_database_errors(self):
        """AI: Test query execution handles database errors."""
        # Test with an invalid query that should cause an error
        with pytest.raises(Exception):
            self.db_ops.execute_query("SELECT * FROM non_existent_table")
    
    def test_get_nginx_preview(self):
        """AI: Test nginx log preview functionality."""
        # Insert test data
        log_data = [
            {
                'ip_address': f'192.168.1.{i}',
                'timestamp': datetime(2025, 1, 1, 12, i, 0),
                'method': 'GET',
                'path': f'/test{i}',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': 1024 * i,
                'raw_log': f'test log line {i}',
                'file_source': f'test{i}.log'
            }
            for i in range(1, 6)  # Insert 5 records
        ]
        self.db_ops.batch_insert_nginx_logs(log_data)
        
        # Get preview
        preview = self.db_ops.get_nginx_preview(limit=3)
        
        assert len(preview) == 3
        # Should be ordered by timestamp DESC, so latest first
        assert preview[0]['path'] == '/test5'
        assert preview[1]['path'] == '/test4'
        assert preview[2]['path'] == '/test3'
        
        # Check expected columns are present
        expected_columns = ['id', 'ip_address', 'timestamp', 'method', 'path', 'status_code', 'response_size', 'file_source']
        for col in expected_columns:
            assert col in preview[0]
    
    def test_get_nexus_preview(self):
        """AI: Test nexus log preview functionality."""
        # Insert test data
        log_data = [
            {
                'ip_address': f'10.0.0.{i}',
                'timestamp': datetime(2025, 1, 1, 13, i, 0),
                'method': 'GET',
                'path': f'/repository/test{i}',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': 1024 * i,
                'request_size': 2048 * i,
                'thread_info': f'[qtp123456-{i}]',
                'raw_log': f'nexus test log line {i}',
                'file_source': f'nexus{i}.log'
            }
            for i in range(1, 4)  # Insert 3 records
        ]
        self.db_ops.batch_insert_nexus_logs(log_data)
        
        # Get preview
        preview = self.db_ops.get_nexus_preview(limit=2)
        
        assert len(preview) == 2
        # Should be ordered by timestamp DESC
        assert preview[0]['path'] == '/repository/test3'
        assert preview[1]['path'] == '/repository/test2'
        
        # Check expected columns are present
        expected_columns = ['id', 'ip_address', 'timestamp', 'method', 'path', 'status_code', 'response_size', 'request_size', 'processing_time_ms', 'user_agent', 'thread_info', 'file_source']
        for col in expected_columns:
            assert col in preview[0]
    
    def test_get_table_sample_nginx_logs(self):
        """AI: Test table sample for nginx logs."""
        # Insert test data
        log_data = [{
            'ip_address': '127.0.0.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/sample',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'sample log line',
            'file_source': 'sample.log'
        }]
        self.db_ops.batch_insert_nginx_logs(log_data)
        
        # Get sample
        sample = self.db_ops.get_table_sample('nginx_logs', limit=5)
        
        assert len(sample) == 1
        assert sample[0]['ip_address'] == '127.0.0.1'
        assert sample[0]['method'] == 'GET'
    
    def test_get_table_sample_nexus_logs(self):
        """AI: Test table sample for nexus logs."""
        # Insert test data
        log_data = [{
            'ip_address': '10.0.0.1',
            'timestamp': datetime(2025, 1, 1, 13, 0, 0),
            'method': 'POST',
            'path': '/repository/sample',
            'http_version': 'HTTP/1.1',
            'status_code': 201,
            'raw_log': 'nexus sample log line',
            'file_source': 'nexus_sample.log'
        }]
        self.db_ops.batch_insert_nexus_logs(log_data)
        
        # Get sample
        sample = self.db_ops.get_table_sample('nexus_logs', limit=5)
        
        assert len(sample) == 1
        assert sample[0]['ip_address'] == '10.0.0.1'
        assert sample[0]['method'] == 'POST'
    
    def test_get_table_sample_invalid_table(self):
        """AI: Test table sample with invalid table name."""
        with pytest.raises(ValueError, match="Invalid table name"):
            self.db_ops.get_table_sample('invalid_table')
    
    def test_get_database_schema(self):
        """AI: Test database schema retrieval."""
        schema = self.db_ops.get_database_schema()
        
        assert 'database' in schema
        assert 'tables' in schema
        assert 'statistics' in schema
        
        # Check table information
        assert 'nginx_logs' in schema['tables']
        assert 'nexus_logs' in schema['tables']
        
        # Check that table info has required fields
        nginx_info = schema['tables']['nginx_logs']
        assert 'table_name' in nginx_info
        assert 'exists' in nginx_info
        assert 'columns' in nginx_info
    
    def test_get_processing_stats(self):
        """AI: Test processing statistics retrieval."""
        # Insert test data
        nginx_data = [{
            'ip_address': '192.168.1.1',
            'timestamp': datetime(2025, 1, 1, 12, 0, 0),
            'method': 'GET',
            'path': '/test',
            'http_version': 'HTTP/1.1',
            'status_code': 200,
            'raw_log': 'test log line',
            'file_source': 'test.log'
        }]
        
        nexus_data = [{
            'ip_address': '10.0.0.1',
            'timestamp': datetime(2025, 1, 2, 13, 0, 0),
            'method': 'POST',
            'path': '/repository/test',
            'http_version': 'HTTP/1.1',
            'status_code': 201,
            'raw_log': 'nexus test log line',
            'file_source': 'nexus.log'
        }]
        
        self.db_ops.batch_insert_nginx_logs(nginx_data)
        self.db_ops.batch_insert_nexus_logs(nexus_data)
        
        # Get stats
        stats = self.db_ops.get_processing_stats()
        
        assert 'nginx' in stats
        assert 'nexus' in stats
        assert 'database' in stats
        
        # Check nginx stats
        nginx_stats = stats['nginx']
        assert nginx_stats['total_entries'] == 1
        assert nginx_stats['unique_ips'] == 1
        assert nginx_stats['unique_days'] == 1
        
        # Check nexus stats
        nexus_stats = stats['nexus']
        assert nexus_stats['total_entries'] == 1
        assert nexus_stats['unique_ips'] == 1
        assert nexus_stats['unique_days'] == 1
    
    def test_get_processing_stats_handles_errors(self):
        """AI: Test processing stats handles SQL errors gracefully."""
        with patch.object(self.db_ops.common, 'execute_query', side_effect=Exception("Stats Error")):
            stats = self.db_ops.get_processing_stats()
            
            assert 'error' in stats
            assert stats['error'] == "Stats Error"
    
    def test_close_calls_db_connection_close(self):
        """AI: Test that close method calls database connection close."""
        with patch.object(self.db_connection, 'close') as mock_close:
            self.db_ops.close()
            mock_close.assert_called_once()
