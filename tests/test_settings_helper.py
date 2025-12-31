"""
AI: Test settings helper for unit tests.

Provides standardized test Settings instances following ADR_20250728_04
architectural consistency requirements.
"""

from pathlib import Path
from app.config import Settings


def create_test_settings(**overrides) -> Settings:
    """
    AI: Create test Settings instance with sensible defaults.
    
    Args:
        **overrides: Override any default setting values
        
    Returns:
        Settings instance configured for testing
    """
    defaults = {
        'nexus_dir': '/tmp/test_nexus',
        'nginx_dir': '/tmp/test_nginx',
        'db_name': ':memory:',  # Use in-memory database for tests
        'nexus_pattern': 'request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz',
        'nginx_pattern': 'access.log*',
        'chunk_size': 100,
        'line_buffer_size': 100,
        'max_archive_depth': 3,
        'enable_mcp_server': False,
        'mcp_port': 8001,
        'web_port': 8000
    }
    
    # Apply overrides
    for key, value in overrides.items():
        defaults[key] = value
    
    # Ensure test directories exist for validation
    for dir_key in ['nexus_dir', 'nginx_dir']:
        test_dir = Path(defaults[dir_key])
        test_dir.mkdir(parents=True, exist_ok=True)
    
    return Settings(**defaults)


def create_mock_settings_with_patterns(nexus_patterns: list = None, nginx_patterns: list = None) -> Settings:
    """
    AI: Create test Settings with specific pattern configurations.
    
    Args:
        nexus_patterns: List of nexus patterns (or None for defaults)
        nginx_patterns: List of nginx patterns (or None for defaults)
        
    Returns:
        Settings instance with specified patterns
    """
    overrides = {}
    
    if nexus_patterns:
        overrides['nexus_pattern'] = ','.join(nexus_patterns)
    
    if nginx_patterns:
        overrides['nginx_pattern'] = ','.join(nginx_patterns)
    
    return create_test_settings(**overrides)
