"""
AI: Unit tests for MCP server implementation.

Tests the Model Context Protocol server functionality including:
- MCP tool registration and configuration
- Server startup and shutdown
- Status reporting and health checks
- Error handling and edge cases

Focuses on server management rather than tool functionality
(which is tested separately in test_mcp_tools.py).
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.mcp.server import LogAnalysisMCPServer
from app.database.operations import DatabaseOperations


class TestLogAnalysisMCPServer:
    """AI: Test MCP server management and configuration."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        # Mock database operations with proper nested structure
        self.mock_db_ops = Mock(spec=DatabaseOperations)
        self.mock_db_connection = Mock()
        self.mock_db_connection.db_path = "/test/mock.db"
        self.mock_db_ops.db_connection = self.mock_db_connection

        # Disable test mode detection to see INFO-level logger messages
        from app.utils.logger import logger
        self._original_is_test = logger._is_test_environment
        logger._is_test_environment = lambda: False

        # Create server instance with test configuration
        self.server = LogAnalysisMCPServer(
            db_ops=self.mock_db_ops,
            host="127.0.0.1",
            port=8999
        )

    def teardown_method(self):
        """AI: Restore logger test mode detection after each test."""
        from app.utils.logger import logger
        logger._is_test_environment = self._original_is_test
    
    def test_server_initialization(self):
        """AI: Test MCP server initializes with correct configuration."""
        assert self.server.db_ops == self.mock_db_ops
        assert self.server.host == "127.0.0.1"
        assert self.server.port == 8999
        assert not self.server.is_running()
        assert self.server.server is not None
        assert self.server.tools is not None
    
    def test_server_status_not_running(self):
        """AI: Test server status when not running."""
        status = self.server.get_status()
        
        assert status["running"] is False
        assert status["host"] == "127.0.0.1"
        assert status["port"] == 8999
        assert status["tools_registered"] == 3
        assert len(status["tools"]) == 3
        assert "list_database_schema" in status["tools"]
        assert "execute_sql_query" in status["tools"]
        assert "get_table_sample" in status["tools"]
        assert status["database_path"] == "/test/mock.db"
    
    @patch('threading.Thread')
    def test_server_start(self, mock_thread):
        """AI: Test MCP server startup process."""
        # Mock thread creation and starting
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Start server
        self.server.start()
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify server state
        assert self.server._server_thread == mock_thread_instance
    
    def test_server_start_already_running(self, capsys):
        """AI: Test starting server when already running."""
        # Simulate server already running
        self.server._running = True

        self.server.start()

        captured = capsys.readouterr()
        # Logger outputs to stderr, not stdout
        assert "MCP server is already running" in captured.err

    def test_server_stop_not_running(self, capsys):
        """AI: Test stopping server when not running."""
        self.server.stop()

        captured = capsys.readouterr()
        # Logger outputs to stderr, not stdout
        assert "MCP server is not running" in captured.err

    def test_server_stop_running(self, capsys):
        """AI: Test stopping running server."""
        # Simulate server running
        self.server._running = True
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        self.server._server_thread = mock_thread

        self.server.stop()

        # Verify server stopped
        assert not self.server._running
        mock_thread.join.assert_called_once_with(timeout=5)

        captured = capsys.readouterr()
        # Logger outputs to stderr, not stdout
        assert "Stopping MCP server" in captured.err
        assert "✓ MCP server stopped" in captured.err
    
    def test_format_json_response_valid_data(self):
        """AI: Test JSON response formatting with valid data."""
        test_data = {
            "tables": ["nginx_logs", "nexus_logs"],
            "count": 42,
            "status": "success"
        }
        
        result = self.server._format_json_response(test_data)
        
        # Verify JSON formatting
        import json
        parsed = json.loads(result)
        assert parsed == test_data
        assert "nginx_logs" in result
        assert "nexus_logs" in result
    
    def test_format_json_response_error_handling(self):
        """AI: Test JSON response formatting error handling."""
        # Create data that can't be JSON serialized even with default=str
        # Use a circular reference which will cause JSON encoding to fail
        test_data = {}
        test_data["circular"] = test_data  # Circular reference
        
        result = self.server._format_json_response(test_data)
        
        assert "Error formatting response" in result
    
    def test_server_configuration_defaults(self):
        """AI: Test server with default configuration."""
        server = LogAnalysisMCPServer(self.mock_db_ops)
        
        assert server.host == "0.0.0.0"
        assert server.port == 8001
        assert server.db_ops == self.mock_db_ops
    
    def test_tools_integration(self):
        """AI: Test that MCP tools are properly integrated."""
        # Verify tools instance is created
        assert self.server.tools is not None
        assert self.server.tools.db_ops == self.mock_db_ops
        
        # Test tool availability through status
        status = self.server.get_status()
        expected_tools = ["list_database_schema", "execute_sql_query", "get_table_sample"]
        assert status["tools"] == expected_tools
        assert status["tools_registered"] == 3
