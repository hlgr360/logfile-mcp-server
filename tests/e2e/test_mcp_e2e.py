"""
End-to-end test for MCP integration.

This test validates the complete MCP integration flow by:
1. Setting up the MCP server with a real database
2. Testing all MCP tools with actual data
3. Verifying protocol compliance and error handling
4. Testing concurrent operations
"""

import json
import threading
import time
import asyncio
from typing import Any, Dict

import pytest
import pytest_asyncio

from app.mcp.server import LogAnalysisMCPServer
from app.mcp.tools import MCPTools
from tests.fixtures.test_database import TestDatabaseFactory


class TestMCPEndToEnd:
    """End-to-end tests for MCP integration."""

    @pytest_asyncio.fixture
    async def populated_db_ops(self):
        """Create a temporary database with comprehensive test data."""
        # Use the shared test database factory for consistent data
        db_ops, db_path = TestDatabaseFactory.create_temporary_database()
        
        yield db_ops

        # Cleanup
        db_ops.db_connection.close()
        TestDatabaseFactory.cleanup_database(db_path)

    @pytest.mark.asyncio
    async def test_mcp_tools_direct(self, populated_db_ops):
        """Test MCP tools directly without server protocol overhead."""
        # Create tools instance
        tools = MCPTools(populated_db_ops)

        # Test list_database_schema
        schema_result = tools.list_database_schema()
        assert "tables" in schema_result
        table_names = [table["table_name"] for table in schema_result["tables"]]
        assert "nginx_logs" in table_names
        assert "nexus_logs" in table_names

        # Test execute_sql_query with valid query
        query_result = tools.execute_sql_query("SELECT COUNT(*) as total FROM nginx_logs")
        assert "results" in query_result
        assert len(query_result["results"]) == 1
        assert query_result["results"][0]["total"] == 5  # Updated for shared test data

        # Test get_table_sample
        sample_result = tools.get_table_sample("nginx_logs", 2)
        assert "sample_data" in sample_result
        assert len(sample_result["sample_data"]) == 2
        assert "ip_address" in sample_result["sample_data"][0]
        assert "method" in sample_result["sample_data"][0]

        # Test error handling with invalid SQL
        error_result = tools.execute_sql_query("INVALID SQL STATEMENT")
        assert "error" in error_result
        assert "security_violation" in error_result["error"]

        # Test security validation - prevent non-SELECT queries
        security_result = tools.execute_sql_query("DROP TABLE nginx_logs")
        assert "error" in security_result
        assert "security_violation" in security_result["error"]

    @pytest.mark.asyncio 
    async def test_mcp_server_initialization(self, populated_db_ops):
        """Test MCP server initialization and basic functionality."""
        # Initialize MCP server
        mcp_server = LogAnalysisMCPServer(populated_db_ops)
        
        # Test server status
        status = mcp_server.get_status()
        assert status["running"] is False
        assert status["tools_registered"] == 3
        assert "list_database_schema" in status["tools"]
        assert "execute_sql_query" in status["tools"]
        assert "get_table_sample" in status["tools"]

    @pytest.mark.asyncio
    async def test_mcp_concurrent_tools(self, populated_db_ops):
        """Test MCP tools with concurrent access."""
        tools = MCPTools(populated_db_ops)

        async def run_query(query_id: int) -> Dict[str, Any]:
            """Run a test query."""
            return tools.execute_sql_query(
                f"SELECT {query_id} as query_id, COUNT(*) as count FROM nginx_logs"
            )

        # Run multiple concurrent queries
        tasks = [run_query(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all queries completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Query {i} failed: {result}"
            assert "results" in result
            assert result["results"][0]["query_id"] == i
            assert result["results"][0]["count"] == 5  # Updated for shared test data

    @pytest.mark.asyncio
    async def test_mcp_complex_queries(self, populated_db_ops):
        """Test MCP tools with complex SQL queries."""
        tools = MCPTools(populated_db_ops)

        # Test JOIN-like query (using subqueries since we don't have foreign keys)
        complex_query = """
            SELECT
                method,
                status_code,
                COUNT(*) as count,
                AVG(response_size) as avg_bytes
            FROM nginx_logs
            WHERE status_code >= 200
            GROUP BY method, status_code
            ORDER BY count DESC
        """
        
        result = tools.execute_sql_query(complex_query)
        assert "results" in result
        assert len(result["results"]) > 0

        # Test aggregation query
        agg_query = """
            SELECT 
                status_code,
                COUNT(*) as count,
                MIN(response_size) as min_bytes,
                MAX(response_size) as max_bytes
            FROM nginx_logs 
            GROUP BY status_code
            ORDER BY status_code
        """
        
        result = tools.execute_sql_query(agg_query)
        assert "results" in result
        assert len(result["results"]) >= 2  # Should have multiple status codes

    @pytest.mark.asyncio
    async def test_mcp_table_validation(self, populated_db_ops):
        """Test MCP tools table validation."""
        tools = MCPTools(populated_db_ops)

        # Test valid table
        result = tools.get_table_sample("nginx_logs", 1)
        assert "sample_data" in result

        # Test invalid table
        result = tools.get_table_sample("nonexistent_table", 1)
        assert "error" in result
        assert "invalid_table" in result["error"]

    def test_mcp_tools_threading(self, populated_db_ops):
        """Test MCP tools in background thread (integration test pattern)."""
        tools = MCPTools(populated_db_ops)
        results = []
        errors = []

        def run_tools():
            """Run MCP tools in background thread."""
            try:
                # Run a test query
                result = tools.execute_sql_query("SELECT COUNT(*) as total FROM nginx_logs")
                results.append(result)
                
            except Exception as e:
                errors.append(str(e))

        # Start tools in background thread
        thread = threading.Thread(target=run_tools)
        thread.start()
        thread.join(timeout=10)  # 10 second timeout

        # Verify results
        assert not errors, f"Tools errors: {errors}"
        assert len(results) == 1
        assert results[0]["results"][0]["total"] == 5  # Updated for shared test data

    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, populated_db_ops):
        """Test MCP protocol compliance."""
        tools = MCPTools(populated_db_ops)

        # Test that all responses are valid JSON-serializable dictionaries
        test_operations = [
            ("list_database_schema", {}),
            ("execute_sql_query", {"query": "SELECT 1"}),
            ("get_table_sample", {"table_name": "nginx_logs", "limit": 1}),
        ]
        
        for op_name, params in test_operations:
            if op_name == "list_database_schema":
                result = tools.list_database_schema()
            elif op_name == "execute_sql_query":
                result = tools.execute_sql_query(params["query"])
            else:  # get_table_sample
                result = tools.get_table_sample(params["table_name"], params["limit"])
            
            # Verify result is a dictionary and JSON-serializable
            assert isinstance(result, dict)
            json_str = json.dumps(result)  # Should not raise an exception
            assert isinstance(json_str, str)
            
            # Verify we can round-trip the JSON
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)

    @pytest.mark.asyncio
    async def test_mcp_performance(self, populated_db_ops):
        """Test MCP tools performance with multiple operations."""
        tools = MCPTools(populated_db_ops)

        start_time = time.time()
        
        # Run multiple operations
        operations = [
            ("list_database_schema", {}),
            ("execute_sql_query", {"query": "SELECT COUNT(*) FROM nginx_logs"}),
            ("execute_sql_query", {"query": "SELECT COUNT(*) FROM nexus_logs"}),
            ("get_table_sample", {"table_name": "nginx_logs", "limit": 5}),
            ("get_table_sample", {"table_name": "nexus_logs", "limit": 5}),
        ]
        
        for op_name, params in operations:
            if op_name == "list_database_schema":
                result = tools.list_database_schema()
            elif op_name == "execute_sql_query":
                result = tools.execute_sql_query(params["query"])
            else:  # get_table_sample
                result = tools.get_table_sample(params["table_name"], params["limit"])
            
            assert isinstance(result, dict)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly (under 1 second for all operations)
        assert execution_time < 1.0, f"Performance test took {execution_time:.2f} seconds"
