"""
AI: Playwright test configuration and fixtures.

Provides browser setup, web server management, and test database configuration
for comprehensive E2E testing of the log analysis web interface.
Uses shared test database factory for consistency with other test types.
"""

import pytest
import threading
import time
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import urllib.error

from app.web.routes import create_web_app
from app.config import Settings
from tests.fixtures.test_database import TestDatabaseFactory


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


@pytest.fixture(scope="session")
def web_server():
    """AI: Start FastAPI web server for testing using shared database factory."""
    # Create test database using shared factory
    test_db_path = "/tmp/test_playwright.db"
    
    # Remove existing test database
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
    
    # Setup test database with comprehensive test data
    db_ops = TestDatabaseFactory.create_test_database(test_db_path, use_sample_logs=False)
    
    # Create test settings
    test_settings = Settings(
        nexus_dir="/tmp/test_nexus",
        nginx_dir="/tmp/test_nginx", 
        db_name=test_db_path,
        web_port=8001  # Use different port for testing
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
    
    # Close database and remove test database
    db_ops.db_connection.close()
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
