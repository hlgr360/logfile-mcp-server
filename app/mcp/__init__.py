"""
AI: MCP server package for LLM integration.

Provides Model Context Protocol server implementation with three core tools:
- list_database_schema: Database structure inspection
- execute_sql_query: Secure SELECT query execution
- get_table_sample: Sample data retrieval

Security features ensure only safe database operations are exposed to LLM clients.
"""

from .server import LogAnalysisMCPServer
from .tools import MCPTools
from .schemas import (
    DatabaseSchemaResponse,
    ExecuteSQLRequest,
    ExecuteSQLResponse, 
    TableSampleRequest,
    TableSampleResponse,
    MCPErrorResponse
)

__all__ = [
    "LogAnalysisMCPServer",
    "MCPTools", 
    "DatabaseSchemaResponse",
    "ExecuteSQLRequest",
    "ExecuteSQLResponse",
    "TableSampleRequest", 
    "TableSampleResponse",
    "MCPErrorResponse"
]
