"""
AI: Shared test database factory for all E2E and integration tests.

Provides consistent test data creation across Playwright E2E tests,
MCP E2E tests, and demo data population. Supports both processed
log files and direct data insertion for comprehensive testing.
"""

import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import sys

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.connection import DatabaseConnection
from app.database.operations import DatabaseOperations
from app.processing.orchestrator import LogProcessingOrchestrator
from app.config import Settings


class TestDatabaseFactory:
    """AI: Factory for creating consistent test databases across all test types."""
    
    @staticmethod
    def get_comprehensive_test_data() -> Dict[str, List[Dict[str, Any]]]:
        """
        AI: Get comprehensive test data including edge cases.
        
        Returns consistent test data that covers:
        - Normal HTTP requests (GET, POST, PUT, DELETE)
        - Different status codes (200, 201, 400, 404, 500)
        - Edge cases (SSH attempts, malformed requests)
        - Various IP addresses and user agents
        - Both nginx and nexus log formats
        """
        
        # Use consistent timestamp for all test data
        base_time = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        nginx_data = [
            {
                'ip_address': '192.168.1.1',
                'remote_user': None,
                'timestamp': base_time,
                'method': 'GET', 
                'path': '/api/health',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': 1024,
                'referer': None,
                'user_agent': 'TestAgent/1.0',
                'raw_log': '192.168.1.1 - - [15/Jan/2025:10:00:00 +0000] "GET /api/health HTTP/1.1" 200 1024 "-" "TestAgent/1.0"',
                'file_source': 'test_access.log'
            },
            {
                'ip_address': '192.168.1.2',
                'remote_user': 'testuser',
                'timestamp': base_time.replace(minute=1),
                'method': 'POST',
                'path': '/api/data',
                'http_version': 'HTTP/1.1',
                'status_code': 201,
                'response_size': 2048,
                'referer': 'https://example.com',
                'user_agent': 'TestAgent/2.0',
                'raw_log': '192.168.1.2 - testuser [15/Jan/2025:10:01:00 +0000] "POST /api/data HTTP/1.1" 201 2048 "https://example.com" "TestAgent/2.0"',
                'file_source': 'test_access.log'
            },
            {
                'ip_address': '192.168.1.3',
                'remote_user': None,
                'timestamp': base_time.replace(minute=2),
                'method': 'GET',
                'path': '/api/error',
                'http_version': 'HTTP/1.1',
                'status_code': 500,
                'response_size': 512,
                'referer': None,
                'user_agent': 'TestAgent/3.0',
                'raw_log': '192.168.1.3 - - [15/Jan/2025:10:02:00 +0000] "GET /api/error HTTP/1.1" 500 512 "-" "TestAgent/3.0"',
                'file_source': 'test_access.log'
            },
            {
                'ip_address': '10.0.0.1',
                'remote_user': None,
                'timestamp': base_time.replace(minute=3),
                'method': 'SSH-ATTEMPT',
                'path': 'SSH-2.0-OpenSSH_7.4',
                'http_version': 'NON-HTTP',
                'status_code': 400,
                'response_size': 0,
                'referer': None,
                'user_agent': '-',
                'raw_log': '10.0.0.1 - - [15/Jan/2025:10:03:00 +0000] "SSH-2.0-OpenSSH_7.4" 400 0 "-" "-"',
                'file_source': 'test_access.log'
            },
            {
                'ip_address': '172.16.0.100',
                'remote_user': None,
                'timestamp': base_time.replace(minute=4),
                'method': 'DELETE',
                'path': '/api/temp/456',
                'http_version': 'HTTP/1.1',
                'status_code': 404,
                'response_size': 142,
                'referer': None,
                'user_agent': 'curl/7.68.0',
                'raw_log': '172.16.0.100 - - [15/Jan/2025:10:04:00 +0000] "DELETE /api/temp/456 HTTP/1.1" 404 142 "-" "curl/7.68.0"',
                'file_source': 'test_access.log'
            }
        ]
        
        nexus_data = [
            {
                'ip_address': '192.168.1.1',
                'remote_user': None,
                'timestamp': base_time,
                'method': 'GET',
                'path': '/repository/test',
                'http_version': 'HTTP/1.1',
                'status_code': 200,
                'response_size': None,
                'processing_time_ms': 150,
                'raw_log': '192.168.1.1 - - [15/Jan/2025:10:00:00 +0000] "GET /repository/test HTTP/1.1" 200 - processing_time=150ms',
                'file_source': 'test_request.log'
            },
            {
                'ip_address': '192.168.1.2',
                'remote_user': 'admin',
                'timestamp': base_time.replace(minute=1),
                'method': 'PUT',
                'path': '/repository/upload',
                'http_version': 'HTTP/1.1',
                'status_code': 400,
                'response_size': None,
                'processing_time_ms': 300,
                'raw_log': '192.168.1.2 - admin [15/Jan/2025:10:01:00 +0000] "PUT /repository/upload HTTP/1.1" 400 - processing_time=300ms',
                'file_source': 'test_request.log'
            },
            {
                'ip_address': '192.168.1.3',
                'remote_user': None,
                'timestamp': base_time.replace(minute=2),
                'method': 'DELETE',
                'path': '/repository/item',
                'http_version': 'HTTP/1.1',
                'status_code': 500,
                'response_size': None,
                'processing_time_ms': 1000,
                'raw_log': '192.168.1.3 - - [15/Jan/2025:10:02:00 +0000] "DELETE /repository/item HTTP/1.1" 500 - processing_time=1000ms',
                'file_source': 'test_request.log'
            }
        ]
        
        return {
            'nginx_logs': nginx_data,
            'nexus_logs': nexus_data
        }
    
    @staticmethod
    def create_test_database(db_path: Optional[str] = None,
                           use_sample_logs: bool = False,
                           fresh_start: bool = True) -> tuple[DatabaseOperations, DatabaseConnection]:
        """
        AI: Create a test database with comprehensive data.

        Args:
            db_path: Path to database file (temporary if None)
            use_sample_logs: Whether to process actual log files or use test data
            fresh_start: Whether to recreate database from scratch

        Returns:
            Tuple of (DatabaseOperations, DatabaseConnection) - caller must close connection

        Example:
            db_ops, db_conn = TestDatabaseFactory.create_test_database()
            try:
                # Use db_ops for testing
                pass
            finally:
                db_conn.close()  # Ensure cleanup
        """

        if db_path is None:
            # Create temporary database file
            temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            db_path = temp_file.name
            temp_file.close()

        # Create database connection and operations
        db_connection = DatabaseConnection(db_path, fresh_start=fresh_start)
        db_ops = DatabaseOperations(db_connection)

        if use_sample_logs:
            # Use actual log file processing for realistic demo data
            TestDatabaseFactory._populate_from_sample_logs(db_ops, db_path)
        else:
            # Use predefined test data for consistent testing
            TestDatabaseFactory._populate_with_test_data(db_ops)

        return db_ops, db_connection
    
    @staticmethod
    def _populate_from_sample_logs(db_ops: DatabaseOperations, db_path: str):
        """AI: Populate database by processing actual sample log files."""
        base_dir = Path(__file__).parent.parent.parent
        
        settings = Settings(
            nexus_dir=str(base_dir / "sample_logs" / "nexus"),
            nginx_dir=str(base_dir / "sample_logs" / "nginx"),
            db_name=db_path,
            nexus_pattern="*.log",
            nginx_pattern="*.log"
        )
        
        orchestrator = LogProcessingOrchestrator(settings, db_ops)
        orchestrator.process_all_logs()
    
    @staticmethod
    def _populate_with_test_data(db_ops: DatabaseOperations):
        """AI: Populate database with predefined test data."""
        test_data = TestDatabaseFactory.get_comprehensive_test_data()
        
        # Insert nginx logs using batch operations
        nginx_logs = test_data['nginx_logs']
        db_ops.batch_insert_nginx_logs(nginx_logs)
        
        # Insert nexus logs using batch operations
        nexus_logs = test_data['nexus_logs']
        db_ops.batch_insert_nexus_logs(nexus_logs)
    
    @staticmethod
    def create_temporary_database() -> tuple[DatabaseOperations, DatabaseConnection, str]:
        """
        AI: Create a temporary database that will be cleaned up automatically.

        Returns:
            Tuple of (DatabaseOperations, DatabaseConnection, db_path) for cleanup

        Example:
            db_ops, db_conn, db_path = TestDatabaseFactory.create_temporary_database()
            try:
                # Use db_ops for testing
                pass
            finally:
                db_conn.close()
                TestDatabaseFactory.cleanup_database(db_path)
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()

        db_ops, db_conn = TestDatabaseFactory.create_test_database(db_path)
        return db_ops, db_conn, db_path

    @staticmethod
    def cleanup_database(db_path: str, db_connection: Optional[DatabaseConnection] = None):
        """
        AI: Clean up database resources.

        Args:
            db_path: Path to database file to delete
            db_connection: Optional connection to close before file deletion
        """
        if db_connection:
            db_connection.close()

        if Path(db_path).exists():
            Path(db_path).unlink()


# Convenience functions for direct usage
def create_test_db(use_sample_logs: bool = False) -> tuple[DatabaseOperations, DatabaseConnection]:
    """
    AI: Quick function to create test database with default settings.

    Returns:
        Tuple of (DatabaseOperations, DatabaseConnection) - caller must close connection
    """
    return TestDatabaseFactory.create_test_database(use_sample_logs=use_sample_logs)


def create_demo_db(db_path: str = "demo.db") -> tuple[DatabaseOperations, DatabaseConnection]:
    """
    AI: Create demo database with realistic data from sample logs.

    Returns:
        Tuple of (DatabaseOperations, DatabaseConnection) - caller must close connection
    """
    return TestDatabaseFactory.create_test_database(
        db_path=db_path,
        use_sample_logs=True,
        fresh_start=True
    )
