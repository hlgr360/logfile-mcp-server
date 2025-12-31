"""
AI: Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for all test modules.
Ensures proper resource cleanup to maintain zero warnings requirement.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dirs():
    """
    AI: Create temporary directories for testing.

    Returns:
        Tuple of (nexus_dir, nginx_dir) as Path objects
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        nexus_dir = temp_path / "nexus"
        nginx_dir = temp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        yield nexus_dir, nginx_dir


@pytest.fixture
def sample_nginx_log_line():
    """AI: Sample nginx log line for testing."""
    return '127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /api/test HTTP/1.1" 200 1234 "-" "test-agent"'


@pytest.fixture
def sample_nexus_log_line():
    """AI: Sample nexus log line for testing."""
    return '10.1.6.4 - - [12/Jun/2025:06:06:02 +0000] "GET / HTTP/1.0" 200 - 7927 93 "Mozilla/5.0..." [qtp1399093517-103]'


@pytest.fixture(autouse=True)
def cleanup_database_connections():
    """
    AI: Ensure all database connections are properly closed after each test.

    This fixture runs automatically for all tests to prevent ResourceWarnings
    from unclosed database connections, maintaining the zero warnings requirement
    from best-practices/DEVELOPMENT.md.
    """
    # Setup: nothing needed before test
    yield

    # Teardown: Force garbage collection to close any lingering connections
    import gc
    gc.collect()
