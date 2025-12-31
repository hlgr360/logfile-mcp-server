"""
AI: MCP request/response schemas for log analysis tools.

Defines the JSON schema structures for MCP tool inputs and outputs,
ensuring proper validation and type safety for LLM interactions.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TableSchema(BaseModel):
    """AI: Database table schema information for MCP responses."""
    table_name: str = Field(..., description="Name of the database table")
    columns: List[Dict[str, Any]] = Field(..., description="Column definitions with types")
    indexes: List[str] = Field(..., description="List of index names on the table")
    row_count: int = Field(..., description="Approximate number of rows in table")


class DatabaseSchemaResponse(BaseModel):
    """AI: Response for list_database_schema MCP tool."""
    tables: List[TableSchema] = Field(..., description="List of database tables and schemas")
    database_file: str = Field(..., description="SQLite database file path")
    total_tables: int = Field(..., description="Total number of tables in database")


class ExecuteSQLRequest(BaseModel):
    """AI: Request for execute_sql_query MCP tool."""
    query: str = Field(..., description="SQL SELECT query to execute")
    limit: Optional[int] = Field(100, description="Maximum number of rows to return")


class ExecuteSQLResponse(BaseModel):
    """AI: Response for execute_sql_query MCP tool."""
    results: List[Dict[str, Any]] = Field(..., description="Query result rows")
    columns: List[str] = Field(..., description="Column names in result set")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time: float = Field(..., description="Query execution time in seconds")
    query_text: str = Field(..., description="Original query that was executed")


class TableSampleRequest(BaseModel):
    """AI: Request for get_table_sample MCP tool."""
    table_name: str = Field(..., description="Name of table to sample")
    limit: Optional[int] = Field(10, description="Number of sample rows to return")


class TableSampleResponse(BaseModel):
    """AI: Response for get_table_sample MCP tool."""
    table_name: str = Field(..., description="Name of the sampled table")
    sample_data: List[Dict[str, Any]] = Field(..., description="Sample rows from table")
    columns: List[str] = Field(..., description="Column names in sample data")
    total_rows: int = Field(..., description="Total number of rows in table")
    sample_size: int = Field(..., description="Number of rows in sample")


class MCPErrorResponse(BaseModel):
    """AI: Error response structure for MCP tool failures."""
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
