"""
AI: Shared test fixtures for all E2E and integration tests.

Provides consistent database setup, web server configuration,
and test data management across different test types.
"""

import pytest
import pytest_asyncio
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Generator

from tests.fixtures.test_database import TestDatabaseFactory
from app.database.operations import DatabaseOperations
from app.web.routes import create_web_app
from app.config import Settings


def wait_for_server(url: str, timeout: int = 10, interval: float = 0.1) -> bool:
    """AI: Wait for web server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass
        time.sleep(interval)
    return False


@pytest_asyncio.fixture(scope="session")
async def shared_test_database() -> Generator[DatabaseOperations, None, None]:
    """
    AI: Session-scoped shared test database for all E2E tests.

    Creates a single test database with comprehensive data that can be
    shared across multiple test files to improve performance and consistency.
    """
    db_ops, db_conn, db_path = TestDatabaseFactory.create_temporary_database()

    yield db_ops

    # Cleanup
    TestDatabaseFactory.cleanup_database(db_path, db_conn)


@pytest_asyncio.fixture
async def test_database() -> Generator[DatabaseOperations, None, None]:
    """
    AI: Function-scoped test database for tests that need isolation.

    Creates a fresh database for each test function that requires isolation.
    Use this when tests modify data and need to be independent.
    """
    db_ops, db_conn, db_path = TestDatabaseFactory.create_temporary_database()

    yield db_ops

    # Cleanup
    TestDatabaseFactory.cleanup_database(db_path, db_conn)


@pytest.fixture(scope="session")
def web_server_with_shared_db(shared_test_database):
    """
    AI: Web server with shared test database for Playwright tests.
    
    Starts a FastAPI web server using the shared test database,
    providing consistent data across all web interface tests.
    """
    # Get database path from shared database
    db_path = shared_test_database.db_connection.db_path
    
    # Create test settings pointing to shared database
    test_settings = Settings(
        nexus_dir="/tmp/test_nexus",
        nginx_dir="/tmp/test_nginx", 
        db_name=db_path,
        web_port=8001,  # Use different port for testing
        enable_mcp_server=False
    )
    
    # Create and start the FastAPI app
    app = create_web_app(test_settings)
    
    import uvicorn
    import multiprocessing
    
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")
    
    # Start server in separate process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    # Wait for server to be ready
    server_url = "http://127.0.0.1:8001"
    if not wait_for_server(server_url):
        server_process.terminate()
        pytest.fail("Failed to start test web server")
    
    yield server_url
    
    # Cleanup
    server_process.terminate()
    server_process.join(timeout=5)
    if server_process.is_alive():
        server_process.kill()


# Legacy fixtures for backward compatibility
@pytest_asyncio.fixture
async def populated_db_ops():
    """AI: Legacy fixture name for MCP tests compatibility."""
    async for db_ops in test_database():
        yield db_ops


@pytest.fixture(scope="session")
def web_server():
    """AI: Legacy fixture name for Playwright tests compatibility."""
    # For now, create its own database to maintain compatibility
    # Can be updated later to use shared database
    test_db_path = "/tmp/test_playwright_legacy.db"

    # Remove existing test database
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()

    # Create database with test data
    db_ops, db_conn = TestDatabaseFactory.create_test_database(test_db_path)

    # Create test settings
    test_settings = Settings(
        nexus_dir="/tmp/test_nexus",
        nginx_dir="/tmp/test_nginx",
        db_name=test_db_path,
        web_port=8002  # Different port to avoid conflicts
    )

    # Create and start the FastAPI app
    app = create_web_app(test_settings)

    import uvicorn
    import multiprocessing

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8002, log_level="critical")

    # Start server in separate process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()

    # Wait for server to be ready
    server_url = "http://127.0.0.1:8002"
    if not wait_for_server(server_url):
        server_process.terminate()
        pytest.fail("Failed to start test web server")

    yield server_url

    # Cleanup
    server_process.terminate()
    server_process.join(timeout=5)
    if server_process.is_alive():
        server_process.kill()

    # Close database connection and remove test database
    TestDatabaseFactory.cleanup_database(test_db_path, db_conn)
