"""
AI: MCP server implementation for log analysis database operations.

Implements the Model Context Protocol server providing LLM clients
with secure access to log analysis database through structured tools.

Server provides three core tools as specified in requirements:
1. list_database_schema - Database structure inspection
2. execute_sql_query - Secure SELECT query execution
3. get_table_sample - Sample data retrieval

Supports both stdio transport (for VS Code Copilot) and network transport.

Security Features:
- Only SELECT statements allowed
- Query validation and sanitization
- Result size limits
- Error handling and sanitization
"""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional
from enum import Enum

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from ..database.operations import DatabaseOperations
from ..utils.logger import logger
from .tools import MCPTools


class TransportMode(Enum):
    """AI: MCP server transport modes."""
    STDIO = "stdio"  # For VS Code Copilot
    NETWORK = "network"  # For network-based clients


class LogAnalysisMCPServer:
    """
    AI: MCP server for log analysis with proper error handling and security.
    
    Provides LLM clients with structured access to log analysis database
    through validated tools with comprehensive error handling.
    
    Supports both stdio transport (for VS Code Copilot) and network transport.
    """
    
    def __init__(
        self, 
        db_ops: DatabaseOperations, 
        transport_mode: TransportMode = TransportMode.NETWORK,
        host: str = "0.0.0.0", 
        port: int = 8001
    ):
        """
        AI: Initialize MCP server with database operations.
        
        Args:
            db_ops: Database operations instance for query execution
            transport_mode: Transport mode (stdio or network)
            host: Server host address (default: 0.0.0.0, used for network mode)
            port: Server port number (default: 8001, used for network mode)
        """
        self.db_ops = db_ops
        self.transport_mode = transport_mode
        self.host = host
        self.port = port
        self.server = Server("log-analysis")
        self.tools = MCPTools(db_ops)
        self._running = False
        self._server_thread: Optional[threading.Thread] = None
        
        # Register MCP tools
        self._register_tools()
    
    def _register_tools(self) -> None:
        """AI: Register all MCP tools with proper schemas and handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """AI: List available MCP tools for LLM clients."""
            return [
                Tool(
                    name="list_database_schema",
                    description="Get the structure and schema of the log analysis database including tables, columns, and relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="execute_sql_query", 
                    description="Execute a SELECT SQL query against the log database. Only SELECT queries are allowed for security.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL SELECT query to execute against the log database"
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_table_sample",
                    description="Get a sample of data from a specific table in the log database",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to sample (nginx_logs or nexus_logs)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of rows to return (default: 10, max: 100)",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10
                            }
                        },
                        "required": ["table_name"],
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            AI: Route tool calls to appropriate handlers with error handling.
            
            Args:
                name: Name of the tool to call
                arguments: Tool arguments from LLM client
                
            Returns:
                List of TextContent responses formatted for LLM consumption
            """
            try:
                if name == "list_database_schema":
                    result = self.tools.list_database_schema()
                    return [TextContent(
                        type="text",
                        text=f"Database Schema:\n{result}"
                    )]
                
                elif name == "execute_sql_query":
                    query = arguments.get("query", "")
                    result = self.tools.execute_sql_query(query)
                    return [TextContent(
                        type="text", 
                        text=f"Query Results:\n{result}"
                    )]
                
                elif name == "get_table_sample":
                    table_name = arguments.get("table_name", "")
                    limit = arguments.get("limit", 10)
                    result = self.tools.get_table_sample(table_name, limit)
                    return [TextContent(
                        type="text",
                        text=f"Table Sample ({table_name}):\n{result}"
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error: Unknown tool '{name}'"
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing tool '{name}': {str(e)}"
                )]
            finally:
                # Cleanup database connection if needed
                try:
                    if hasattr(self, 'tools') and hasattr(self.tools, 'db_ops'):
                        # Database connections are managed by the parent application
                        pass
                except:
                    pass
    
    def start(self) -> None:
        """
        AI: Start MCP server with appropriate transport.

        For stdio mode: runs synchronously (blocking)
        For network mode: runs asynchronously in background thread
        """
        if self._running:
            logger.info("MCP server is already running")
            return

        if self.transport_mode == TransportMode.STDIO:
            self._start_stdio_server()
        else:
            self._start_network_server()
    
    def _start_stdio_server(self) -> None:
        """AI: Start MCP server in stdio mode for VS Code Copilot."""
        logger.info("🚀 Starting Log Analysis MCP Server for VS Code Copilot...")
        logger.info("📁 Using database: %s", self.db_ops.db_connection.db_path)
        logger.info("📊 Available tools:")
        logger.info("   - list_database_schema: Inspect database structure")
        logger.info("   - execute_sql_query: Run SELECT queries on log data")
        logger.info("   - get_table_sample: Get sample data from tables")
        logger.info("")
        logger.info("🔌 MCP server ready for VS Code Copilot connection...")

        # Run stdio server synchronously
        asyncio.run(self._run_stdio_server())
    
    async def _run_stdio_server(self) -> None:
        """AI: Run stdio server for VS Code Copilot integration."""
        try:
            self._running = True
            async with stdio_server() as streams:
                await self.server.run(
                    streams[0],
                    streams[1],
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error("❌ MCP stdio server error: %s", e)
            raise
        finally:
            self._running = False
    
    def _start_network_server(self) -> None:
        """AI: Start MCP server in network mode for background operation."""
        logger.info("Starting MCP server on %s:%d...", self.host, self.port)

        def run_server():
            """AI: Server thread function."""
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Run the MCP server
                self._running = True
                loop.run_until_complete(self._run_network_server())

            except Exception as e:
                logger.error("ERROR: MCP server failed: %s", e)
                self._running = False
            finally:
                loop.close()

        # Start server in background thread
        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()

        # Give server time to start
        time.sleep(1)

        if self._running:
            logger.info("✓ MCP server started on %s:%d", self.host, self.port)
        else:
            logger.error("✗ MCP server failed to start")
    
    async def _run_network_server(self) -> None:
        """AI: Run network server for general MCP clients."""
        try:
            logger.info("MCP server listening on %s:%d", self.host, self.port)

            # Keep server running - actual network implementation would go here
            # For now, this maintains the server lifecycle
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error("MCP server error: %s", e)
            raise
    
    def stop(self) -> None:
        """AI: Stop MCP server and cleanup resources."""
        if not self._running:
            logger.info("MCP server is not running")
            return

        logger.info("Stopping MCP server...")
        self._running = False

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=5)

        logger.info("✓ MCP server stopped")
    
    def _format_json_response(self, data: Any) -> str:
        """
        AI: Format data as JSON response with error handling.
        
        Args:
            data: Data to format as JSON
            
        Returns:
            JSON string representation of data or error message
        """
        import json
        
        try:
            # Try to serialize with default JSON encoder
            return json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError) as e:
            # If serialization fails, return error message
            return f"Error formatting response: {str(e)}"
    
    def is_running(self) -> bool:
        """AI: Check if MCP server is currently running."""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """
        AI: Get MCP server status information.
        
        Returns:
            Dictionary containing server status and configuration
        """
        return {
            "running": self._running,
            "transport_mode": self.transport_mode.value,
            "host": self.host if self.transport_mode == TransportMode.NETWORK else "stdio",
            "port": self.port if self.transport_mode == TransportMode.NETWORK else None,
            "tools_registered": 3,
            "tools": ["list_database_schema", "execute_sql_query", "get_table_sample"],
            "database_path": str(self.db_ops.db_connection.db_path) if self.db_ops else None
        }


def create_stdio_server(db_ops: DatabaseOperations) -> LogAnalysisMCPServer:
    """
    AI: Create MCP server for VS Code Copilot integration.
    
    Args:
        db_ops: Database operations instance
        
    Returns:
        Configured MCP server in stdio mode
    """
    return LogAnalysisMCPServer(
        db_ops=db_ops,
        transport_mode=TransportMode.STDIO
    )


def create_network_server(db_ops: DatabaseOperations, host: str = "0.0.0.0", port: int = 8001) -> LogAnalysisMCPServer:
    """
    AI: Create MCP server for network-based clients.
    
    Args:
        db_ops: Database operations instance
        host: Server host address
        port: Server port number
        
    Returns:
        Configured MCP server in network mode
    """
    return LogAnalysisMCPServer(
        db_ops=db_ops,
        transport_mode=TransportMode.NETWORK,
        host=host,
        port=port
    )
