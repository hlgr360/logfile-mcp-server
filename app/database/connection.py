"""
AI: Database connection management with proper SQLite setup.

Implements:
- Fresh database creation on each application start (per ADR)
- Connection management with context managers
- Schema creation with proper indexes
- Transaction management for batch operations
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class DatabaseConnection:
    """
    AI: Database connection manager with SQLite optimization.
    
    Handles:
    - Fresh database creation per ADR requirement
    - Connection pooling and session management
    - Schema creation with indexes
    - Proper resource cleanup
    """
    
    def __init__(self, db_path: str, fresh_start: bool = True):
        """
        AI: Initialize database connection with optional fresh database creation.
        
        Args:
            db_path: Path to SQLite database file
            fresh_start: If True, drop/recreate database on start (per ADR)
                        If False, use existing database if available
        """
        self.db_path = Path(db_path)
        self.fresh_start = fresh_start
        self.engine: Engine = None
        self.SessionLocal: sessionmaker = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """
        AI: Initialize database with optional fresh creation.
        
        Creates new database file and applies schema with indexes.
        """
        # Remove existing database for fresh start (per ADR) only if fresh_start=True
        if self.fresh_start and self.db_path.exists():
            os.remove(self.db_path)
            print(f"Removed existing database: {self.db_path}")
        
        # Create SQLite engine with optimizations
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,  # Set to True for SQL debugging
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # 30-second timeout for database locks
            },
            pool_pre_ping=True,  # Verify connections before use
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Create all tables with indexes (this is safe if tables already exist)
        Base.metadata.create_all(self.engine)
        
        if self.fresh_start:
            print(f"Created fresh database with schema: {self.db_path}")
        else:
            print(f"Connected to existing database: {self.db_path}")
        print(f"Database size: {self.db_path.stat().st_size} bytes")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        AI: Context manager for database sessions with transaction management.
        
        Provides automatic commit/rollback and proper resource cleanup.
        
        Yields:
            SQLAlchemy session instance
            
        Example:
            with db.get_session() as session:
                session.add(log_entry)
                # Automatic commit on success, rollback on exception
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """
        AI: Execute raw SQL with proper connection management.
        
        Used for custom queries and schema inspection.
        
        Args:
            sql: SQL statement to execute
            params: Optional parameters for parameterized queries
            
        Returns:
            List of result rows as dictionaries
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            return [dict(row._mapping) for row in result]
    
    def execute_raw_sql_with_params(self, sql: str, params: list) -> list:
        """
        AI: Execute raw SQL with positional parameters.
        
        Used for prepared statements with positional parameters.
        
        Args:
            sql: SQL statement to execute with ? placeholders
            params: List of parameters for parameterized queries
            
        Returns:
            List of result rows as dictionaries
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(sql), params)
            return [dict(row._mapping) for row in result]
    
    def get_table_info(self, table_name: str) -> dict:
        """
        AI: Get table schema information for MCP server.
        
        Args:
            table_name: Name of table to inspect
            
        Returns:
            Dictionary with table schema details
        """
        try:
            # Get column information
            columns_sql = f"PRAGMA table_info({table_name})"
            columns = self.execute_raw_sql(columns_sql)
            
            # Get index information
            indexes_sql = f"PRAGMA index_list({table_name})"
            indexes = self.execute_raw_sql(indexes_sql)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "exists": len(columns) > 0
            }
        except Exception as e:
            return {
                "table_name": table_name,
                "error": str(e),
                "exists": False
            }
    
    def get_database_stats(self) -> dict:
        """
        AI: Get database statistics for monitoring.
        
        Returns:
            Dictionary with database size and table counts
        """
        stats = {
            "database_path": str(self.db_path),
            "database_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "tables": {}
        }
        
        try:
            # Get row counts for each table
            nginx_count = self.execute_raw_sql("SELECT COUNT(*) as count FROM nginx_logs")[0]['count']
            nexus_count = self.execute_raw_sql("SELECT COUNT(*) as count FROM nexus_logs")[0]['count']
            
            stats["tables"]["nginx_logs"] = nginx_count
            stats["tables"]["nexus_logs"] = nexus_count
            stats["total_rows"] = nginx_count + nexus_count
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def close(self) -> None:
        """AI: Close database connections and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            print("Database connections closed")
