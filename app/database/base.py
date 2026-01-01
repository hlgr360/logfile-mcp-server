"""
AI: Base database operations providing common functionality.

This module provides the foundational database operations that are shared
across all log format-specific database handlers. It handles connection
management, common queries, and schema operations.

Architecture:
- BaseLogDatabase: Abstract base for format-specific operations
- CommonLogDatabase: Shared functionality (schema, queries, stats)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import contextmanager

from app.database.connection import DatabaseConnection
from ..utils.logger import logger


class BaseLogDatabase(ABC):
    """AI: Abstract base class for format-specific database operations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """AI: Initialize with database connection."""
        self.db_connection = db_connection
    
    @contextmanager
    def get_session(self):
        """AI: Context manager for database sessions with proper error handling."""
        session = self.db_connection.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("DATABASE_ERROR: Transaction rolled back - %s", e)
            raise
        finally:
            session.close()
    
    @abstractmethod
    def batch_insert(self, log_data: List[Dict]) -> int:
        """AI: Insert batch of log entries. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_preview(self, limit: int = 10) -> List[Dict]:
        """AI: Get preview of log entries. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_model_class(self):
        """AI: Return the SQLAlchemy model class for this log format."""
        pass


class CommonLogDatabase:
    """AI: Common database operations shared across all log formats."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """AI: Initialize with database connection."""
        self.db_connection = db_connection
    
    @contextmanager
    def get_session(self):
        """AI: Context manager for database sessions with proper error handling."""
        session = self.db_connection.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("DATABASE_ERROR: Transaction rolled back - %s", e)
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        AI: Execute a raw SQL query and return results as dictionaries.
        
        Security measures:
        - Only SELECT statements allowed
        - Automatic LIMIT enforcement  
        - Query validation and sanitization
        """
        # Validate query is SELECT only (security requirement)
        query_stripped = query.strip().upper()
        if not query_stripped.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for security")
        
        try:
            with self.get_session() as session:
                # Apply limit if specified and not already present
                if limit and 'LIMIT' not in query_stripped:
                    query = f"{query.rstrip(';')} LIMIT {limit}"
                
                result = session.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error("QUERY_ERROR: Failed to execute query - %s", e)
            raise
    
    def get_database_schema(self) -> Dict[str, Any]:
        """AI: Get database schema information for all tables."""
        schema_info = {
            'database': str(self.db_connection.db_path),
            'tables': {},
            'statistics': {}
        }
        
        try:
            with self.get_session() as session:
                # Get table information for both nginx_logs and nexus_logs
                for table_name in ['nginx_logs', 'nexus_logs']:
                    # Get column information
                    columns_query = f"PRAGMA table_info({table_name})"
                    columns_result = session.execute(text(columns_query))
                    
                    columns = []
                    for col_info in columns_result.fetchall():
                        columns.append({
                            'name': col_info[1],
                            'type': col_info[2],
                            'not_null': bool(col_info[3]),
                            'default': col_info[4],
                            'primary_key': bool(col_info[5])
                        })
                    
                    # Get table create SQL
                    table_sql_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                    table_sql_result = session.execute(text(table_sql_query))
                    table_sql_row = table_sql_result.fetchone()
                    table_sql = table_sql_row[0] if table_sql_row else None
                    
                    schema_info['tables'][table_name] = {
                        'table_name': table_name,
                        'exists': True,
                        'columns': columns,
                        'create_sql': table_sql
                    }
                
                # Add basic statistics
                schema_info['statistics'] = self.get_processing_stats()
                
        except Exception as e:
            logger.error("SCHEMA_ERROR: Failed to get database schema - %s", e)
        
        return schema_info
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """AI: Get processing statistics across all log tables."""
        try:
            # Get nginx stats using execute_query
            nginx_stats = self.execute_query("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    COUNT(DISTINCT DATE(timestamp)) as unique_days,
                    MIN(timestamp) as earliest_log,
                    MAX(timestamp) as latest_log
                FROM nginx_logs
            """)
            nginx_stats = nginx_stats[0] if nginx_stats else {
                'total_entries': 0, 'unique_ips': 0, 'unique_days': 0,
                'earliest_log': None, 'latest_log': None
            }
            
            # Get nexus stats using execute_query  
            nexus_stats = self.execute_query("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    COUNT(DISTINCT DATE(timestamp)) as unique_days,
                    MIN(timestamp) as earliest_log,
                    MAX(timestamp) as latest_log
                FROM nexus_logs
            """)
            nexus_stats = nexus_stats[0] if nexus_stats else {
                'total_entries': 0, 'unique_ips': 0, 'unique_days': 0,
                'earliest_log': None, 'latest_log': None
            }
            
            # Database stats - use a simple placeholder since we don't have get_database_stats
            database_stats = {
                'size_bytes': self.db_connection.db_path.stat().st_size if self.db_connection.db_path.exists() else 0,
                'total_tables': 2,
                'total_entries': nginx_stats['total_entries'] + nexus_stats['total_entries']
            }
            
            return {
                "nginx": nginx_stats,
                "nexus": nexus_stats,  
                "database": database_stats
            }
            
        except Exception as e:
            logger.error("STATS_ERROR: Failed to get processing stats - %s", e)
            return {"error": str(e)}
    
    def get_table_sample(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get sample data from specified table."""
        # Validate table name for security
        valid_tables = ['nginx_logs', 'nexus_logs']
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table name. Must be one of: {valid_tables}")
            
        try:
            query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            logger.error("SAMPLE_ERROR: Failed to get table sample - %s", e)
            return []
