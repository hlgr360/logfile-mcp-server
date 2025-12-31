"""
AI: MCP tool definitions for log analysis database operations.

Implements the three core MCP tools specified in the requirements:
1. list_database_schema - Inspect database structure
2. execute_sql_query - Execute SELECT queries  
3. get_table_sample - Get sample data from tables

Each tool includes proper error handling, security validation,
and JSON formatting for LLM consumption.
"""

import time
import sqlparse
from typing import Dict, Any, List, Optional

from ..database.operations import DatabaseOperations
from .schemas import (
    DatabaseSchemaResponse, TableSchema,
    ExecuteSQLResponse, ExecuteSQLRequest,
    TableSampleResponse, TableSampleRequest,
    MCPErrorResponse
)


class MCPTools:
    """
    AI: MCP tool implementations for database operations.
    
    Provides secure, validated access to the log analysis database
    for LLM clients through the Model Context Protocol.
    """
    
    def __init__(self, db_ops: DatabaseOperations):
        """
        AI: Initialize MCP tools with database operations.
        
        Args:
            db_ops: Database operations instance for query execution
        """
        self.db_ops = db_ops
    
    def list_database_schema(self) -> Dict[str, Any]:
        """
        AI: List all database tables and their complete schemas.
        
        Returns comprehensive schema information including column types,
        indexes, and row counts for all tables in the database.
        
        Returns:
            Dictionary containing database schema information
            
        Raises:
            Exception: When database access fails
        """
        try:
            # Use the new get_database_schema method
            schema_info = self.db_ops.get_database_schema()
            
            tables = []
            
            # Convert schema info to the expected format
            for table_name, table_info in schema_info.get('tables', {}).items():
                # Get row count from execute_query
                try:
                    row_count_result = self.db_ops.execute_query(
                        f"SELECT COUNT(*) as count FROM {table_name}",
                        limit=1
                    )
                    row_count = row_count_result[0]['count'] if row_count_result else 0
                except Exception:
                    row_count = 0
                
                # Convert column format for compatibility
                columns = []
                for col in table_info.get('columns', []):
                    columns.append({
                        'name': col['name'],
                        'type': col['type'],
                        'notnull': int(col['not_null']),
                        'pk': int(col['primary_key'])
                    })
                
                table_schema = TableSchema(
                    table_name=table_name,
                    columns=columns,
                    indexes=[],  # For now, we'll leave indexes empty as they're not in our schema
                    row_count=row_count
                )
                tables.append(table_schema)
            
            response = DatabaseSchemaResponse(
                tables=tables,
                database_file=schema_info.get('database', ''),
                total_tables=len(tables)
            )
            
            return response.model_dump()
            
        except Exception as e:
            error_response = MCPErrorResponse(
                error="database_access_error",
                message=f"Failed to retrieve database schema: {str(e)}",
                details={"operation": "list_database_schema"}
            )
            return error_response.model_dump()
    
    def execute_sql_query(self, query: str, limit: Optional[int] = 100) -> Dict[str, Any]:
        """
        AI: Execute a SELECT SQL query against the database.
        
        Only SELECT statements are allowed for security. Results are
        limited to prevent memory issues and include execution timing.
        
        Args:
            query: SQL SELECT query to execute
            limit: Maximum number of rows to return (default: 100)
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Validate request
            request = ExecuteSQLRequest(query=query, limit=limit)
            
            # Security validation - only allow SELECT statements
            if not self._is_select_query(request.query):
                error_response = MCPErrorResponse(
                    error="security_violation",
                    message="Only SELECT queries are allowed for security reasons",
                    details={"query": request.query[:100]}  # Truncate for security
                )
                return error_response.model_dump()
            
            # Execute query with timing
            start_time = time.time()
            results = self.db_ops.execute_query(request.query, limit=request.limit)
            execution_time = time.time() - start_time
            
            # Extract column names from first result row
            columns = list(results[0].keys()) if results else []
            
            response = ExecuteSQLResponse(
                results=results,
                columns=columns,
                row_count=len(results),
                execution_time=round(execution_time, 4),
                query_text=request.query
            )
            
            return response.model_dump()
            
        except Exception as e:
            error_response = MCPErrorResponse(
                error="query_execution_error", 
                message=f"Failed to execute query: {str(e)}",
                details={
                    "query": query[:100] if query else "",
                    "limit": limit
                }
            )
            return error_response.model_dump()
    
    def get_table_sample(self, table_name: str, limit: Optional[int] = 10) -> Dict[str, Any]:
        """
        AI: Get sample rows from a specific table.
        
        Returns a small sample of data from the specified table
        along with metadata about the table structure.
        
        Args:
            table_name: Name of table to sample (must be 'nginx_logs' or 'nexus_logs')
            limit: Number of sample rows to return (default: 10)
            
        Returns:
            Dictionary containing sample data and table metadata
        """
        try:
            # Validate request
            request = TableSampleRequest(table_name=table_name, limit=limit)
            
            # Validate table name for security
            allowed_tables = ["nginx_logs", "nexus_logs"]
            if request.table_name not in allowed_tables:
                error_response = MCPErrorResponse(
                    error="invalid_table",
                    message=f"Table '{request.table_name}' not found. Available tables: {allowed_tables}",
                    details={"requested_table": request.table_name, "available_tables": allowed_tables}
                )
                return error_response.model_dump()
            
            # Get sample data
            query = f"SELECT * FROM {request.table_name} ORDER BY created_at DESC LIMIT {request.limit}"
            sample_data = self.db_ops.execute_query(query, limit=request.limit)
            
            # Get total row count
            count_query = f"SELECT COUNT(*) as total FROM {request.table_name}"
            count_result = self.db_ops.execute_query(count_query, limit=1)
            total_rows = count_result[0]['total'] if count_result else 0
            
            # Extract column names
            columns = list(sample_data[0].keys()) if sample_data else []
            
            response = TableSampleResponse(
                table_name=request.table_name,
                sample_data=sample_data,
                columns=columns,
                total_rows=total_rows,
                sample_size=len(sample_data)
            )
            
            return response.model_dump()
            
        except Exception as e:
            error_response = MCPErrorResponse(
                error="table_sample_error",
                message=f"Failed to get table sample: {str(e)}",
                details={
                    "table_name": table_name,
                    "limit": limit
                }
            )
            return error_response.model_dump()
    
    def _is_select_query(self, query: str) -> bool:
        """
        AI: Validate that query contains only SELECT statements.
        
        Uses sqlparse to analyze SQL structure and reject any
        non-SELECT operations for security.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            True if query contains only SELECT statements, False otherwise
        """
        try:
            # Handle empty or whitespace-only queries
            if not query or not query.strip():
                return False
            
            # Parse the SQL query
            parsed = sqlparse.parse(query)
            
            for statement in parsed:
                # Skip empty statements
                if not statement.tokens:
                    continue
                
                # Get the first meaningful token
                first_token = None
                for token in statement.tokens:
                    if not token.is_whitespace:
                        first_token = token
                        break
                
                if first_token is None:
                    continue
                
                # Check if it's a SELECT statement
                if (first_token.ttype is sqlparse.tokens.Keyword.DML and 
                    first_token.value.upper() == 'SELECT'):
                    continue
                elif (hasattr(first_token, 'tokens') and first_token.tokens and
                      first_token.tokens[0].ttype is sqlparse.tokens.Keyword.DML and
                      first_token.tokens[0].value.upper() == 'SELECT'):
                    continue
                else:
                    return False
            
            return True
            
        except Exception:
            # If parsing fails, err on the side of caution
            return False
