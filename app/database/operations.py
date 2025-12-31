"""
AI: Unified database operations interface.

This module provides a single interface that combines common database operations
with format-specific operations, maintaining backward compatibility while
providing the benefits of separated architecture.

This replaces the monolithic DatabaseOperations class with a composition-based
approach that maintains clean separation between different log format operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database.connection import DatabaseConnection
from app.database.base import CommonLogDatabase
from app.database.nginx_database import NginxLogDatabase
from app.database.nexus_database import NexusLogDatabase


class DatabaseOperations:
    """
    AI: Unified database operations interface.
    
    Provides a single entry point for all database operations while maintaining
    clean separation between format-specific operations internally. This design
    allows for easy extension when adding new log formats.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """AI: Initialize with database connection and create specialized operation handlers."""
        self.db_connection = db_connection
        
        # Common operations (schema, stats, queries)
        self.common = CommonLogDatabase(db_connection)
        
        # Format-specific operations
        self.nginx = NginxLogDatabase(db_connection)
        self.nexus = NexusLogDatabase(db_connection)
    
    # =============================================================================
    # Backward Compatibility Methods (delegate to appropriate specialized classes)
    # =============================================================================
    
    def batch_insert_nginx_logs(self, log_data: List[Dict]) -> int:
        """AI: Insert batch of nginx log entries. Delegates to nginx operations."""
        return self.nginx.batch_insert(log_data)
    
    def batch_insert_nexus_logs(self, log_data: List[Dict]) -> int:
        """AI: Insert batch of nexus log entries. Delegates to nexus operations."""
        return self.nexus.batch_insert(log_data)
    
    def get_nginx_preview(self, limit: int = 10) -> List[Dict]:
        """AI: Get nginx log preview. Delegates to nginx operations."""
        return self.nginx.get_preview(limit)
    
    def get_nexus_preview(self, limit: int = 10) -> List[Dict]:
        """AI: Get nexus log preview. Delegates to nexus operations."""
        return self.nexus.get_preview(limit)
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """AI: Execute raw SQL query. Delegates to common operations."""
        return self.common.execute_query(query, limit)
    
    def get_database_schema(self) -> Dict[str, Any]:
        """AI: Get database schema information. Delegates to common operations."""
        return self.common.get_database_schema()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """AI: Get processing statistics. Delegates to common operations."""
        return self.common.get_processing_stats()
    
    def get_table_sample(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get table sample. Delegates to common operations."""
        return self.common.get_table_sample(table_name, limit)
    
    # =============================================================================
    # Enhanced Methods (expose format-specific functionality)
    # =============================================================================
    
    def get_nginx_top_paths(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most frequently accessed nginx paths."""
        return self.nginx.get_top_paths(limit)
    
    def get_nginx_status_distribution(self) -> List[Dict[str, Any]]:
        """AI: Get nginx HTTP status code distribution."""
        return self.nginx.get_status_code_distribution()
    
    def get_nginx_logs_by_timerange(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """AI: Get nginx logs within time range."""
        return self.nginx.get_logs_by_timerange(start_time, end_time, limit)
    
    def get_nexus_top_repositories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most active nexus repositories."""
        return self.nexus.get_top_repositories(limit)
    
    def get_nexus_user_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most active nexus users."""
        return self.nexus.get_user_activity(limit)
    
    def get_nexus_action_distribution(self) -> List[Dict[str, Any]]:
        """AI: Get nexus action distribution."""
        return self.nexus.get_action_distribution()
    
    def get_nexus_logs_by_timerange(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """AI: Get nexus logs within time range."""
        return self.nexus.get_logs_by_timerange(start_time, end_time, limit)
    
    # =============================================================================
    # Direct Access Properties (for advanced usage)
    # =============================================================================
    
    def nginx_operations(self) -> NginxLogDatabase:
        """AI: Get nginx-specific database operations."""
        return self.nginx
    
    def nexus_operations(self) -> NexusLogDatabase:
        """AI: Get nexus-specific database operations."""
        return self.nexus
    
    def common_operations(self) -> CommonLogDatabase:
        """AI: Get common database operations."""
        return self.common
    
    def close(self):
        """AI: Close database connection and cleanup resources."""
        if hasattr(self.db_connection, 'close'):
            self.db_connection.close()
