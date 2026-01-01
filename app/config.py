"""
AI: Configuration management with CLI arguments and environment variable support.

This module provides comprehensive configuration management following the ADR decisions:
- Pydantic-based settings with validation
- CLI argument parsing with Click
- Environment file support with python-dotenv
- Configuration validation with meaningful error messages
"""

import os
from pathlib import Path
from typing import List, Optional

import click
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings

from .utils.logger import logger


class Settings(BaseSettings):
    """
    AI: Application configuration with validation and environment support.
    
    Follows ADR decisions for configuration management including:
    - Default values from DEFAULT_VALUES
    - Environment variable and CLI override support
    - Path validation for directories
    - Port availability checking
    """
    
    # Directory paths
    nexus_dir: str = Field(..., description="Path to directory containing Nexus logs")
    nginx_dir: str = Field(..., description="Path to directory containing nginx logs")
    
    # Database configuration
    db_name: str = Field(default="log_analysis.db", description="SQLite database filename")
    
    # File patterns (comma-separated strings)
    nexus_pattern: str = Field(
        default="request*.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz",
        description="Comma-separated patterns for Nexus log files"
    )
    nginx_pattern: str = Field(
        default="access.log*",
        description="Comma-separated patterns for nginx log files"
    )
    
    # Processing configuration
    chunk_size: int = Field(default=1000, description="Number of lines to read per chunk during log parsing")
    line_buffer_size: int = Field(default=1000, description="Line processing batch size")
    max_archive_depth: int = Field(default=3, description="Maximum nested archive depth")
    
    # Server configuration
    enable_mcp_server: bool = Field(default=False, description="Enable MCP server")
    mcp_port: int = Field(default=8001, description="MCP server port")
    web_port: int = Field(default=8000, description="Web server port")
    
    # Processing mode
    process_only: bool = Field(default=False, description="Process logs and exit without starting web server")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix=""
    )

    @field_validator('nexus_dir', 'nginx_dir')
    @classmethod
    def validate_directories(cls, v: str) -> str:
        """AI: Validate that directories exist and are readable."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        if not os.access(path, os.R_OK):
            raise ValueError(f"Directory is not readable: {v}")
        return str(path.absolute())

    @field_validator('db_name')
    @classmethod
    def validate_db_path(cls, v: str) -> str:
        """AI: Validate that database directory is writable."""
        db_path = Path(v)
        parent_dir = db_path.parent if db_path.parent != Path('.') else Path.cwd()
        
        if not parent_dir.exists():
            raise ValueError(f"Database directory does not exist: {parent_dir}")
        if not os.access(parent_dir, os.W_OK):
            raise ValueError(f"Database directory is not writable: {parent_dir}")
        return v

    @field_validator('mcp_port', 'web_port')
    @classmethod
    def validate_ports(cls, v: int) -> int:
        """AI: Validate port ranges."""
        if not (1024 <= v <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got: {v}")
        return v

    @field_validator('max_archive_depth')
    @classmethod
    def validate_archive_depth(cls, v: int) -> int:
        """AI: Validate archive depth limits."""
        if v < 1 or v > 10:
            raise ValueError(f"Archive depth must be between 1 and 10, got: {v}")
        return v

    @property
    def nexus_patterns(self) -> List[str]:
        """AI: Convert nexus pattern string to list for processing."""
        return [p.strip() for p in self.nexus_pattern.split(',') if p.strip()]

    @property
    def nginx_patterns(self) -> List[str]:
        """AI: Convert nginx pattern string to list for processing."""
        return [p.strip() for p in self.nginx_pattern.split(',') if p.strip()]


def load_settings(
    nexus_dir: Optional[str] = None,
    nginx_dir: Optional[str] = None,
    db_name: Optional[str] = None,
    nexus_pattern: Optional[str] = None,
    nginx_pattern: Optional[str] = None,
    enable_mcp_server: Optional[bool] = None,
    mcp_port: Optional[int] = None,
    web_port: Optional[int] = None,
    chunk_size: Optional[int] = None,
    line_buffer_size: Optional[int] = None,
    max_archive_depth: Optional[int] = None,
    process_only: Optional[bool] = None,
) -> Settings:
    """
    AI: Load configuration from CLI arguments, environment, and .env file.
    
    Priority order:
    1. CLI arguments (highest priority)
    2. Environment variables
    3. .env file
    4. Default values (lowest priority)
    
    Args:
        All CLI arguments as optional parameters
        
    Returns:
        Validated Settings instance
        
    Raises:
        ValueError: When configuration validation fails
    """
    # Build kwargs from non-None CLI arguments
    kwargs = {}
    if nexus_dir is not None:
        kwargs['nexus_dir'] = nexus_dir
    if nginx_dir is not None:
        kwargs['nginx_dir'] = nginx_dir
    if db_name is not None:
        kwargs['db_name'] = db_name
    if nexus_pattern is not None:
        kwargs['nexus_pattern'] = nexus_pattern
    if nginx_pattern is not None:
        kwargs['nginx_pattern'] = nginx_pattern
    if enable_mcp_server is not None:
        kwargs['enable_mcp_server'] = enable_mcp_server
    if mcp_port is not None:
        kwargs['mcp_port'] = mcp_port
    if web_port is not None:
        kwargs['web_port'] = web_port
    if chunk_size is not None:
        kwargs['chunk_size'] = chunk_size
    if line_buffer_size is not None:
        kwargs['line_buffer_size'] = line_buffer_size
    if max_archive_depth is not None:
        kwargs['max_archive_depth'] = max_archive_depth
    if process_only is not None:
        kwargs['process_only'] = process_only
    
    try:
        return Settings(**kwargs)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")


def validate_configuration(settings: Settings) -> None:
    """
    AI: Perform additional configuration validation checks.
    
    Validates:
    - Port conflicts between web and MCP servers
    - Directory accessibility
    - File pattern validity
    
    Args:
        settings: Settings instance to validate
        
    Raises:
        ValueError: When validation fails
    """
    # Check for port conflicts
    if settings.enable_mcp_server and settings.web_port == settings.mcp_port:
        raise ValueError(
            f"Web server and MCP server cannot use the same port: {settings.web_port}"
        )
    
    # Validate patterns contain at least one pattern
    if not settings.nexus_patterns:
        raise ValueError("At least one nexus pattern must be specified")
    if not settings.nginx_patterns:
        raise ValueError("At least one nginx pattern must be specified")
    
    # Additional directory checks
    nexus_path = Path(settings.nexus_dir)
    nginx_path = Path(settings.nginx_dir)

    if nexus_path == nginx_path:
        logger.warn("WARNING: Nexus and nginx directories are the same: %s", nexus_path)

    logger.info("Configuration validated successfully:")
    logger.info("  Nexus directory: %s", settings.nexus_dir)
    logger.info("  nginx directory: %s", settings.nginx_dir)
    logger.info("  Database: %s", settings.db_name)
    logger.info("  Web port: %d", settings.web_port)
    if settings.enable_mcp_server:
        logger.info("  MCP port: %d", settings.mcp_port)
    logger.info("  Max archive depth: %d", settings.max_archive_depth)
