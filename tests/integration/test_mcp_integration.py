"""
AI: Integration tests for MCP server with real database operations.

Tests the complete MCP server integration including:
- End-to-end tool execution with real database
- MCP server startup with database connections
- Tool integration with actual data processing
- Error handling with real database errors

Uses temporary database to ensure test isolation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.database.connection import DatabaseConnection
from app.database.operations import DatabaseOperations
from app.mcp.server import LogAnalysisMCPServer
from app.mcp.tools import MCPTools


class TestMCPServerIntegration:
    """AI: Test MCP server integration with real database operations."""
    
    @pytest.fixture
    def temp_db(self):
        """AI: Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_connection = DatabaseConnection(db_path, fresh_start=True)
        db_ops = DatabaseOperations(db_connection)
        
        yield db_ops
        
        # Cleanup
        db_ops.close()
        Path(db_path).unlink(missing_ok=True)
    
    def test_mcp_server_with_real_database(self, temp_db):
        """AI: Test MCP server initialization with real database."""
        server = LogAnalysisMCPServer(temp_db, host="127.0.0.1", port=9999)
        
        # Verify server created successfully
        assert server.db_ops == temp_db
        assert server.host == "127.0.0.1"
        assert server.port == 9999
        assert not server.is_running()
        
        # Test status with real database
        status = server.get_status()
        assert status["database_path"] is not None
        assert Path(status["database_path"]).exists()
    
    def test_mcp_tools_with_real_database(self, temp_db):
        """AI: Test MCP tools with real database operations."""
        tools = MCPTools(temp_db)
        
        # Test database schema inspection
        schema_result = tools.list_database_schema()
        
        # Verify schema structure
        assert "tables" in schema_result
        assert "database_file" in schema_result
        assert "total_tables" in schema_result
        
        # Verify tables exist (even if empty)
        tables = schema_result["tables"]
        table_names = [table["table_name"] for table in tables]
        assert "nginx_logs" in table_names
        assert "nexus_logs" in table_names
    
    def test_mcp_tools_empty_database_queries(self, temp_db):
        """AI: Test MCP tools with empty database."""
        tools = MCPTools(temp_db)
        
        # Test table sampling on empty tables
        nginx_sample = tools.get_table_sample("nginx_logs", 10)
        assert nginx_sample["table_name"] == "nginx_logs"
        assert nginx_sample["sample_data"] == []
        assert nginx_sample["total_rows"] == 0
        
        nexus_sample = tools.get_table_sample("nexus_logs", 10)
        assert nexus_sample["table_name"] == "nexus_logs"
        assert nexus_sample["sample_data"] == []
        assert nexus_sample["total_rows"] == 0
        
        # Test SQL queries on empty tables
        count_result = tools.execute_sql_query("SELECT COUNT(*) as count FROM nginx_logs", 100)
        assert count_result["row_count"] == 1
        assert count_result["results"][0]["count"] == 0
    
    def test_mcp_tools_with_sample_data(self, temp_db):
        """AI: Test MCP tools with actual log data."""
        from datetime import datetime
        
        # Insert sample nginx log data
        nginx_data = [
            {
                "ip_address": "192.168.1.1",
                "remote_user": "-",
                "timestamp": datetime(2025, 7, 30, 10, 0, 0),
                "method": "GET",
                "path": "/api/test",
                "http_version": "HTTP/1.1",
                "status_code": 200,
                "response_size": 1024,
                "referer": "-",
                "user_agent": "test-agent",
                "raw_log": "test log line",
                "file_source": "test.log"
            }
        ]
        
        # Insert sample nexus log data
        nexus_data = [
            {
                "ip_address": "10.1.1.1",
                "remote_user": "testuser",
                "timestamp": datetime(2025, 7, 30, 10, 5, 0),
                "method": "GET",
                "path": "/repository/maven/",
                "http_version": "HTTP/1.1", 
                "status_code": 200,
                "response_size": 2048,
                "request_size": 512,
                "processing_time_ms": 150,
                "user_agent": "Maven/3.8.1",
                "thread_info": "[qtp123-45]",
                "raw_log": "test nexus log line",
                "file_source": "nexus.log"
            }
        ]
        
        # Insert data into database
        temp_db.batch_insert_nginx_logs(nginx_data)
        temp_db.batch_insert_nexus_logs(nexus_data)
        
        # Test MCP tools with real data
        tools = MCPTools(temp_db)
        
        # Test table sampling
        nginx_sample = tools.get_table_sample("nginx_logs", 5)
        assert nginx_sample["total_rows"] == 1
        assert nginx_sample["sample_size"] == 1
        assert nginx_sample["sample_data"][0]["ip_address"] == "192.168.1.1"
        
        nexus_sample = tools.get_table_sample("nexus_logs", 5)
        assert nexus_sample["total_rows"] == 1
        assert nexus_sample["sample_size"] == 1
        assert nexus_sample["sample_data"][0]["remote_user"] == "testuser"
        
        # Test SQL queries
        query_result = tools.execute_sql_query(
            "SELECT ip_address, method, status_code FROM nginx_logs WHERE status_code = 200",
            100
        )
        assert query_result["row_count"] == 1
        assert query_result["results"][0]["method"] == "GET"
        
        # Test cross-table query
        cross_query = tools.execute_sql_query(
            """
            SELECT 'nginx' as source, COUNT(*) as count FROM nginx_logs
            UNION ALL
            SELECT 'nexus' as source, COUNT(*) as count FROM nexus_logs
            """,
            100
        )
        assert cross_query["row_count"] == 2
        assert cross_query["columns"] == ["source", "count"]
    
    def test_mcp_server_tool_error_handling(self, temp_db):
        """AI: Test MCP server error handling with real database."""
        server = LogAnalysisMCPServer(temp_db)
        tools = server.tools
        
        # Test invalid table name
        invalid_table_result = tools.get_table_sample("nonexistent_table", 10)
        assert "error" in invalid_table_result
        assert invalid_table_result["error"] == "invalid_table"
        
        # Test invalid SQL query
        invalid_sql_result = tools.execute_sql_query("SELECT * FROM nonexistent_table", 100)
        assert "error" in invalid_sql_result
        assert invalid_sql_result["error"] == "query_execution_error"
        
        # Test security violation
        security_violation_result = tools.execute_sql_query("DROP TABLE nginx_logs", 100)
        assert "error" in security_violation_result
        assert security_violation_result["error"] == "security_violation"
    
    @patch('threading.Thread')
    def test_mcp_server_startup_with_database(self, mock_thread, temp_db):
        """AI: Test MCP server startup process with real database."""
        mock_thread_instance = mock_thread.return_value
        
        server = LogAnalysisMCPServer(temp_db, host="127.0.0.1", port=9998)
        
        # Start server
        server.start()
        
        # Verify thread creation
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify server configuration
        status = server.get_status()
        assert status["running"] is False  # Thread is mocked, so server won't actually be running
        assert status["host"] == "127.0.0.1"
        assert status["port"] == 9998
        assert status["tools_registered"] == 3
    
    def test_database_schema_inspection_integration(self, temp_db):
        """AI: Test comprehensive database schema inspection."""
        tools = MCPTools(temp_db)
        
        # Get complete schema
        schema_result = tools.list_database_schema()
        
        # Verify comprehensive schema information
        assert "tables" in schema_result
        tables = schema_result["tables"]
        
        # Find nginx_logs table
        nginx_table = next((t for t in tables if t["table_name"] == "nginx_logs"), None)
        assert nginx_table is not None
        
        # Verify column information
        assert "columns" in nginx_table
        columns = nginx_table["columns"]
        column_names = [col["name"] for col in columns]
        
        # Check for expected columns
        expected_columns = ["id", "ip_address", "timestamp", "method", "path", "status_code"]
        for col in expected_columns:
            assert col in column_names
        
        # Verify index information
        assert "indexes" in nginx_table
        assert "row_count" in nginx_table
        assert isinstance(nginx_table["row_count"], int)
    
    def test_mcp_security_enforcement(self, temp_db):
        """AI: Test MCP security measures with real database."""
        tools = MCPTools(temp_db)
        
        # Test various SQL injection attempts
        malicious_queries = [
            "SELECT * FROM nginx_logs; DROP TABLE nexus_logs;",
            "SELECT * FROM nginx_logs UNION SELECT 'hack' as id;",
            "'; DROP TABLE nginx_logs; --",
            "SELECT * FROM sqlite_master",  # System table access
        ]
        
        for query in malicious_queries:
            result = tools.execute_sql_query(query, 100)
            # Should either be blocked by security or fail safely
            if "error" in result:
                assert result["error"] in ["security_violation", "query_execution_error"]
            else:
                # If not blocked by security, should at least not cause damage
                # Verify tables still exist
                schema_check = tools.list_database_schema()
                assert "tables" in schema_check
                table_names = [t["table_name"] for t in schema_check["tables"]]
                assert "nginx_logs" in table_names
                assert "nexus_logs" in table_names
