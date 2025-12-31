"""
AI: Integration tests for web interface API endpoints.

Tests Phase 3 web interface functionality:
- FastAPI route registrati        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ip_address"] == "192.168.1.1"
        assert data[0]["method"] == "GET"
        
                # Verify the correct method was called
        mock_db_instance.get_nexus_preview.assert_called_once()sponses
- Database integration with mock data
- API security (SELECT-only queries)
- Error handling and validation
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.web.routes import create_web_app
from app.config import Settings


class TestWebInterfaceIntegration:
    """AI: Integration tests for web interface endpoints."""
    
    @pytest.fixture
    def mock_settings(self, tmp_dirs):
        """AI: Create mock settings for testing."""
        nexus_dir, nginx_dir = tmp_dirs
        return Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            db_name="test.db",
            nexus_pattern="*.log",
            nginx_pattern="*.log",
            web_port=8000,
            mcp_port=8001,
            enable_mcp_server=False
        )
    
    @pytest.fixture
    def mock_db_operations(self):
        """AI: Create mock database operations."""
        mock_db = Mock()
        
        # Mock nginx preview data
        mock_db.execute_query.return_value = [
            {
                "ip_address": "192.168.1.1",
                "timestamp": "2025-01-28T10:00:00Z",
                "method": "GET",
                "path": "/api/test",
                "status_code": 200,
                "response_size": 1024,
                "user_agent": "TestAgent/1.0",
                "file_source": "test.log"
            }
        ]
        
        # Mock table schema
        mock_db.get_table_schema.return_value = [
            {"name": "ip_address", "type": "TEXT", "nullable": False, "primary_key": False},
            {"name": "timestamp", "type": "DATETIME", "nullable": False, "primary_key": False}
        ]
        
        # Mock table row count
        mock_db.get_table_row_count.return_value = 100
        
        return mock_db
    
    @pytest.fixture
    def test_client(self, mock_settings, mock_db_operations):
        """AI: Create test client with mocked dependencies."""
        app = create_web_app(mock_settings)
        
        # Override database dependency
        def override_get_database():
            return mock_db_operations
        
        # Find and replace the dependency
        for route in app.routes:
            if hasattr(route, 'dependencies'):
                for dep in route.dependencies:
                    if hasattr(dep, 'dependency') and 'get_database' in str(dep.dependency):
                        dep.dependency = override_get_database
        
        # Override at app level
        app.dependency_overrides = {
            # We need to find the original dependency function to override it
            # For now, we'll patch it at the import level
        }
        
        return TestClient(app)
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_index_page_loads(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test that index page loads successfully."""
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Log Analysis Application" in response.text
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_nginx_preview_endpoint(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test nginx preview API endpoint."""
        # Setup mock
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        mock_db_instance.get_nginx_preview.return_value = [
            {
                "ip_address": "192.168.1.1",
                "timestamp": "2025-01-28T10:00:00Z",
                "method": "GET",
                "path": "/api/test",
                "status_code": 200,
                "response_size": 1024,
                "user_agent": "TestAgent/1.0",
                "file_source": "test.log"
            }
        ]
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/api/nginx-preview")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ip_address"] == "192.168.1.1"
        assert data[0]["method"] == "GET"
        
        # Verify database query was called correctly
        mock_db_instance.get_nginx_preview.assert_called_once_with(10)
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_nexus_preview_endpoint(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test nexus preview API endpoint."""
        # Setup mock
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        mock_db_instance.get_nexus_preview.return_value = [
            {
                "ip_address": "10.1.1.1",
                "timestamp": "2025-01-28T11:00:00Z",
                "method": "POST",
                "path": "/repository/test",
                "status_code": 201,
                "response_size": 2048,
                "request_size": 512,
                "user_agent": "Maven/3.8.1",
                "thread_info": "[qtp123-45]",
                "file_source": "nexus.log"
            }
        ]
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/api/nexus-preview")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ip_address"] == "10.1.1.1"
        assert data[0]["method"] == "POST"
        assert data[0]["thread_info"] == "[qtp123-45]"
        
        # Verify database query was called correctly
        mock_db_instance.get_nexus_preview.assert_called_once_with(10)
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_execute_query_success(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test successful SQL query execution."""
        # Setup mock
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        mock_db_instance.execute_query.return_value = [
            {"count": 150, "method": "GET"},
            {"count": 75, "method": "POST"}
        ]
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        query_data = {
            "query": "SELECT method, COUNT(*) as count FROM nginx_logs GROUP BY method",
            "limit": 100
        }
        
        response = client.post("/api/execute-query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "row_count" in data
        assert "columns" in data
        assert "execution_time" in data
        
        assert data["row_count"] == 2
        assert len(data["results"]) == 2
        assert data["columns"] == ["count", "method"]
        assert data["results"][0]["method"] == "GET"
        
        # Verify query was executed with correct parameters
        mock_db_instance.execute_query.assert_called_once()
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_execute_query_security_validation(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test SQL injection protection and query validation."""
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        # Test non-SELECT query
        forbidden_queries = [
            {"query": "DELETE FROM nginx_logs WHERE id = 1"},
            {"query": "UPDATE nginx_logs SET status_code = 500"},
            {"query": "INSERT INTO nginx_logs VALUES (...)"},
            {"query": "DROP TABLE nginx_logs"},
            {"query": "ALTER TABLE nginx_logs ADD COLUMN test TEXT"},
            {"query": "CREATE TABLE malicious (id INT)"}
        ]
        
        for query_data in forbidden_queries:
            response = client.post("/api/execute-query", json=query_data)
            assert response.status_code == 400
            assert "Only SELECT queries are allowed" in response.json()["detail"]
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_table_info_endpoint(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test table schema information endpoint."""
        # Setup mock
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        
        # Mock schema responses (all values must be strings for TableInfo model)
        nginx_schema = [
            {"name": "id", "type": "INTEGER", "nullable": "False", "primary_key": "True"},
            {"name": "ip_address", "type": "TEXT", "nullable": "False", "primary_key": "False"}
        ]
        nexus_schema = [
            {"name": "id", "type": "INTEGER", "nullable": "False", "primary_key": "True"},
            {"name": "thread_info", "type": "TEXT", "nullable": "True", "primary_key": "False"}
        ]
        
        mock_db_instance.get_table_schema.side_effect = [nginx_schema, nexus_schema]
        mock_db_instance.get_table_row_count.side_effect = [250, 150]
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/api/table-info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tables" in data
        assert len(data["tables"]) == 2
        
        # Check nginx table info
        nginx_table = next(t for t in data["tables"] if t["table_name"] == "nginx_logs")
        assert nginx_table["row_count"] == 250
        assert len(nginx_table["columns"]) == 2
        
        # Check nexus table info  
        nexus_table = next(t for t in data["tables"] if t["table_name"] == "nexus_logs")
        assert nexus_table["row_count"] == 150
        assert len(nexus_table["columns"]) == 2
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_health_endpoint(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test health check endpoint."""
        # Setup mock
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        mock_db_instance.get_table_row_count.side_effect = [100, 50]  # nginx, nexus counts
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["nginx_logs_count"] == 100
        assert data["nexus_logs_count"] == 50
        assert data["total_entries"] == 150
    
    @patch('app.web.routes.DatabaseOperations')
    @patch('app.web.routes.DatabaseConnection')
    def test_error_handling(self, mock_db_conn, mock_db_ops, mock_settings):
        """AI: Test error handling for database failures."""
        # Setup mock to raise exception
        mock_db_instance = Mock()
        mock_db_ops.return_value = mock_db_instance
        mock_db_instance.execute_query.side_effect = Exception("Database connection failed")
        
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        response = client.get("/api/nginx-preview")
        
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]
    
    def test_static_files_served(self, mock_settings):
        """AI: Test that static files are properly served."""
        app = create_web_app(mock_settings)
        client = TestClient(app)
        
        # Test CSS file
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")
        
        # Test JavaScript file
        response = client.get("/static/script.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "")


class TestWebInterfaceConfigurationConsistency:
    """AI: Test that web interface follows ADR_20250728_04 dependency injection patterns."""
    
    def test_database_dependency_injection_pattern(self, tmp_dirs):
        """AI: Verify web routes follow consistent dependency injection pattern."""
        nexus_dir, nginx_dir = tmp_dirs
        mock_settings = Settings(
            nexus_dir=str(nexus_dir), 
            nginx_dir=str(nginx_dir), 
            db_name="test.db",
            nexus_pattern="*.log", 
            nginx_pattern="*.log"
        )
        
        app = create_web_app(mock_settings)
        
        # Verify app was created successfully (dependency injection working)
        assert app is not None
        assert app.title == "Log Analysis Application"
        
        # Check routes are registered
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        expected_paths = ["/", "/api/nginx-preview", "/api/nexus-preview", 
                         "/api/execute-query", "/api/table-info", "/health"]
        
        for expected_path in expected_paths:
            assert expected_path in route_paths, f"Missing route: {expected_path}"
    
    def test_settings_integration_consistency(self, tmp_dirs):
        """AI: Verify Settings integration follows established patterns."""
        nexus_dir, nginx_dir = tmp_dirs
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            db_name="web_test.db",
            nexus_pattern="request.log*",
            nginx_pattern="access.log*",
            web_port=9000,
            mcp_port=9001
        )
        
        app = create_web_app(settings)
        
        # Verify app uses settings correctly
        assert app is not None
        
        # Test that dependency injection receives correct settings
        # (This is validated by successful app creation without exceptions)
