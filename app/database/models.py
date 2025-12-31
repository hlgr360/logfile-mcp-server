"""
AI: SQLAlchemy database models for nginx and Nexus log storage.

Implements separate models per ADR decision:
- NginxLog and NexusLog as distinct models
- Optimized schemas for each log format
- Performance indexes for common query patterns
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NginxLog(Base):
    """
    AI: SQLAlchemy model for nginx access logs.
    
    Schema follows specification with performance indexes for common queries.
    Tracks complete nginx access log format including original raw log for debugging.
    """
    __tablename__ = 'nginx_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core nginx log fields
    ip_address = Column(String, nullable=False, doc="Client IP address")
    remote_user = Column(String, doc="Authenticated user (typically '-')")
    timestamp = Column(DateTime, nullable=False, doc="Request timestamp")
    method = Column(String, nullable=False, doc="HTTP method (GET, POST, etc.)")
    path = Column(Text, nullable=False, doc="URL path")
    http_version = Column(String, nullable=False, doc="HTTP version (HTTP/1.1, etc.)")
    status_code = Column(Integer, nullable=False, doc="HTTP status code")
    response_size = Column(Integer, doc="Response size in bytes")
    referer = Column(Text, doc="HTTP referer header")
    user_agent = Column(Text, doc="User agent string")
    
    # Metadata fields
    raw_log = Column(Text, nullable=False, doc="Original log line for debugging")
    file_source = Column(String, nullable=False, doc="Source file path")
    created_at = Column(DateTime, default=func.now(), doc="Record creation timestamp")
    
    # Performance indexes as table arguments
    __table_args__ = (
        Index('idx_nginx_timestamp', 'timestamp'),
        Index('idx_nginx_ip', 'ip_address'),
        Index('idx_nginx_method', 'method'),
        Index('idx_nginx_path', 'path'),
        Index('idx_nginx_status', 'status_code'),
        Index('idx_nginx_method_path', 'method', 'path'),
        Index('idx_nginx_file_source', 'file_source'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<NginxLog(id={self.id}, ip={self.ip_address}, "
            f"method={self.method}, path={self.path[:50]}...)>"
        )


class NexusLog(Base):
    """
    AI: SQLAlchemy model for Nexus access logs.
    
    Schema follows specification with Nexus-specific fields:
    - Dual response size fields (response_size_1, response_size_2)
    - Thread pool information from [qtp...] format
    - Same core HTTP fields as nginx for correlation queries
    """
    __tablename__ = 'nexus_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core HTTP log fields (similar to nginx)
    ip_address = Column(String, nullable=False, doc="Client IP address")
    remote_user = Column(String, doc="Authenticated user (typically '-')")
    timestamp = Column(DateTime, nullable=False, doc="Request timestamp")
    method = Column(String, nullable=False, doc="HTTP method (GET, POST, etc.)")
    path = Column(Text, nullable=False, doc="URL path")
    http_version = Column(String, nullable=False, doc="HTTP version")
    status_code = Column(Integer, nullable=False, doc="HTTP status code")
    
    # Nexus-specific fields
    response_size = Column(Integer, doc="Response size in bytes (Apache-style)")
    request_size = Column(Integer, doc="Request size in bytes (Apache-style)")
    processing_time_ms = Column(Integer, doc="Request processing time in milliseconds")
    user_agent = Column(Text, doc="User agent string")
    thread_info = Column(String, doc="Thread pool information [qtp...]")
    
    # Metadata fields
    raw_log = Column(Text, nullable=False, doc="Original log line for debugging")
    file_source = Column(String, nullable=False, doc="Source file path")
    created_at = Column(DateTime, default=func.now(), doc="Record creation timestamp")
    
    # Performance indexes as table arguments
    __table_args__ = (
        Index('idx_nexus_timestamp', 'timestamp'),
        Index('idx_nexus_ip', 'ip_address'),
        Index('idx_nexus_method', 'method'),
        Index('idx_nexus_path', 'path'),
        Index('idx_nexus_status', 'status_code'),
        Index('idx_nexus_method_path', 'method', 'path'),
        Index('idx_nexus_file_source', 'file_source'),
        Index('idx_nexus_thread', 'thread_info'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<NexusLog(id={self.id}, ip={self.ip_address}, "
            f"method={self.method}, path={self.path[:50]}...)>"
        )
