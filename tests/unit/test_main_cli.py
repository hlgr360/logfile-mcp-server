"""
AI: Comprehensive tests for main CLI module to improve coverage.

Tests target missing coverage areas in app/main.py:
- CLI argument validation and error handling
- MCP stdio mode activation and error scenarios
- Web server startup logic
- Log processing workflow 
- Configuration validation errors
- Server startup and error handling
"""

import pytest
import sys
import threading
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from click.testing import CliRunner

from app.main import cli, start_web_server, start_mcp_server
from app.config import Settings


class TestMainCLI:
    """AI: Test CLI argument parsing and validation."""

    def setup_method(self):
        """AI: Setup test runner before each test."""
        self.runner = CliRunner()
        # Patch logger to disable test mode suppression for CLI tests
        # so we can see INFO-level messages in test output
        from app.utils.logger import logger
        self._original_is_test = logger._is_test_environment
        logger._is_test_environment = lambda: False

    def teardown_method(self):
        """AI: Restore logger test mode detection after each test."""
        from app.utils.logger import logger
        logger._is_test_environment = self._original_is_test
    
    def test_cli_argument_parsing_basic_success(self):
        """AI: Test basic CLI argument parsing with valid arguments."""
        # Test that CLI can parse arguments without errors
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration') as mock_validate, \
             patch('app.main.DatabaseConnection') as mock_db_conn, \
             patch('app.main.DatabaseOperations') as mock_db_ops, \
             patch('app.main.start_web_server') as mock_web, \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx',
                '--db-name', 'test.db'
            ])
            
            # Should reach the main loop and handle KeyboardInterrupt gracefully
            assert mock_load.called
            assert mock_validate.called
    
    def test_cli_validation_prevents_invalid_configurations(self):
        """AI: Test CLI validation prevents invalid directory configurations."""
        # Test process-logs flag requires both directories (lines 168-169)
        result = self.runner.invoke(cli, [
            '--process-logs'
            # Missing --nexus-dir and --nginx-dir
        ])
        
        assert result.exit_code == 1
        assert "❌ Error: --nexus-dir and --nginx-dir are required when using --process-logs" in result.output
    
    def test_mcp_stdio_mode_activation_success(self):
        """AI: Test MCP stdio mode activation with existing database."""
        with patch('app.main.Path') as mock_path, \
             patch('app.main.DatabaseConnection') as mock_db_conn, \
             patch('app.main.DatabaseOperations') as mock_db_ops, \
             patch('app.mcp.server.create_stdio_server') as mock_stdio_server, \
             patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'):
            
            # Mock database exists (lines 200-202)
            mock_path.return_value.exists.return_value = True
            mock_settings = MagicMock()
            mock_settings.db_name = 'test.db'
            mock_load.return_value = mock_settings
            
            # Mock stdio server
            mock_server = MagicMock()
            mock_stdio_server.return_value = mock_server
            
            result = self.runner.invoke(cli, [
                '--mcp-stdio',
                '--db-name', 'test.db'
            ])
            
            # Should start stdio server and exit (lines 203-217)
            assert mock_stdio_server.called
            assert mock_server.start.called
            assert "🚀 Starting MCP server in stdio mode for VS Code Copilot..." in result.output
    
    def test_mcp_stdio_mode_database_not_found(self):
        """AI: Test MCP stdio mode with missing database."""
        with patch('app.main.Path') as mock_path, \
             patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'):
            
            # Mock database does not exist (lines 200-202)
            mock_path.return_value.exists.return_value = False
            mock_settings = MagicMock()
            mock_settings.db_name = 'missing.db'
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, ['--mcp-stdio'])
            
            assert result.exit_code == 1
            assert "❌ Database not found: missing.db" in result.output
            assert "💡 Run with --process-logs first to create and populate the database" in result.output
    
    def test_mcp_stdio_dummy_directories_assignment(self):
        """AI: Test MCP stdio mode assigns dummy directories when not provided."""
        with patch('app.main.Path') as mock_path, \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.mcp.server.create_stdio_server') as mock_stdio_server, \
             patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'):
            
            mock_path.return_value.exists.return_value = True
            mock_settings = MagicMock()
            mock_settings.db_name = 'test.db'
            mock_load.return_value = mock_settings
            
            # Mock stdio server
            mock_server = MagicMock()
            mock_stdio_server.return_value = mock_server
            
            result = self.runner.invoke(cli, ['--mcp-stdio'])
            
            # Check that load_settings was called with dummy directories (lines 173, 175)
            call_args = mock_load.call_args[1]
            assert call_args['nexus_dir'] == '/tmp'
            assert call_args['nginx_dir'] == '/tmp'
    
    def test_log_processing_workflow_success(self):
        """AI: Test complete log processing workflow."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations') as mock_db_ops, \
             patch('app.main.LogProcessingOrchestrator') as mock_orchestrator, \
             patch('app.main.start_web_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            # Mock orchestrator
            mock_orch_instance = MagicMock()
            mock_orchestrator.return_value = mock_orch_instance
            mock_orch_instance.process_all_logs.return_value = {'processed': 100}
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx', 
                '--process-logs'
            ])
            
            # Should process logs (lines 238-242)
            assert mock_orchestrator.called
            assert mock_orch_instance.process_all_logs.called
            assert "=== Starting Phase 2: Log Processing ===" in result.output
            assert "=== Phase 2 Complete: Log Processing Finished ===" in result.output
    
    def test_process_only_flag_exits_after_processing(self):
        """AI: Test process-only flag exits after log processing."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations') as mock_db_ops, \
             patch('app.main.LogProcessingOrchestrator') as mock_orchestrator:
            
            mock_settings = MagicMock()
            mock_settings.process_only = True
            mock_load.return_value = mock_settings
            
            # Mock database operations
            mock_db_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_db_ops_instance
            
            # Mock orchestrator  
            mock_orch_instance = MagicMock()
            mock_orchestrator.return_value = mock_orch_instance
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx',
                '--process-logs',
                '--process-only'
            ])
            
            # Should exit after processing (lines 246-249)
            assert "--process-only flag specified, exiting after log processing..." in result.output
            assert mock_db_ops_instance.close.called
    
    def test_web_server_startup_logic(self):
        """AI: Test web server startup logic."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server') as mock_web_server, \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx'
            ])
            
            # Should start web server (lines 251-252)
            assert mock_web_server.called
            assert "=== Starting Phase 3: Web Interface ===" in result.output
    
    def test_mcp_server_startup_when_enabled(self):
        """AI: Test MCP server startup when enabled."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server'), \
             patch('app.main.start_mcp_server') as mock_mcp_server, \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = True
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx',
                '--enable-mcp-server'
            ])
            
            # Should start MCP server (lines 254-256)
            assert mock_mcp_server.called
            assert "=== Starting Phase 4: MCP Server ===" in result.output
    
    def test_application_running_status_display(self):
        """AI: Test application running status display."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server'), \
             patch('app.main.start_mcp_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = True
            mock_settings.process_only = False
            mock_settings.web_port = 8000
            mock_settings.mcp_port = 8001
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx',
                '--enable-mcp-server'
            ])
            
            # Should display running status (lines 259-265)
            assert "✓ Application running:" in result.output
            assert "- Web interface: http://localhost:8000" in result.output
            assert "- MCP server: http://localhost:8001" in result.output
            assert "Press Ctrl+C to exit..." in result.output
    
    def test_keyboard_interrupt_graceful_shutdown(self):
        """AI: Test graceful shutdown on keyboard interrupt."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations') as mock_db_ops, \
             patch('app.main.start_web_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Trigger KeyboardInterrupt immediately
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            # Mock database operations
            mock_db_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_db_ops_instance
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx'
            ])
            
            # Should handle shutdown gracefully (lines 269-274)
            assert "Shutting down..." in result.output
            assert mock_db_ops_instance.close.called
    
    def test_application_startup_exception_handling(self):
        """AI: Test application startup exception handling."""
        with patch('app.main.load_settings', side_effect=Exception("Configuration error")):
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx'
            ])
            
            # Should handle startup errors (lines 276-278)
            assert result.exit_code == 1
            assert "ERROR: Application startup failed: Configuration error" in result.output


class TestWebServerStartup:
    """AI: Test web server startup functionality."""
    
    def test_start_web_server_success(self):
        """AI: Test successful web server startup."""
        with patch('app.main.create_web_app') as mock_create_app, \
             patch('app.main.uvicorn.Config') as mock_config, \
             patch('app.main.uvicorn.Server') as mock_server, \
             patch('app.main.threading.Thread') as mock_thread, \
             patch('time.sleep'):
            
            # Mock settings and db_ops
            mock_settings = MagicMock()
            mock_settings.web_port = 8000
            mock_db_ops = MagicMock()
            
            # Mock FastAPI app
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            
            # Mock uvicorn server
            mock_server_instance = MagicMock()
            mock_server.return_value = mock_server_instance
            
            # Mock thread
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            # Test server startup (lines 289-320)
            start_web_server(mock_settings, mock_db_ops)

            # Verify server configuration
            mock_create_app.assert_called_with(mock_settings)
            assert mock_config.called
            assert mock_server.called
            assert mock_thread.called
            assert mock_thread_instance.start.called
    
    def test_start_web_server_exception_handling(self):
        """AI: Test web server startup exception handling."""
        with patch('app.main.create_web_app', side_effect=Exception("App creation failed")):
            
            mock_settings = MagicMock()
            mock_settings.web_port = 8000
            mock_db_ops = MagicMock()
            
            # Should raise exception with error message (lines 319-320)
            with pytest.raises(Exception) as exc_info:
                start_web_server(mock_settings, mock_db_ops)
            
            assert "App creation failed" in str(exc_info.value)


class TestMCPServerStartup:
    """AI: Test MCP server startup functionality."""
    
    def test_start_mcp_server_success(self):
        """AI: Test successful MCP server startup."""
        with patch('app.mcp.server.create_network_server') as mock_create_server:
            
            # Mock settings and db_ops
            mock_settings = MagicMock()
            mock_settings.mcp_port = 8001
            mock_db_ops = MagicMock()
            
            # Mock MCP server
            mock_server = MagicMock()
            mock_server.get_status.return_value = {'tools': ['execute_sql_query', 'list_database_schema']}
            mock_create_server.return_value = mock_server
            
            # Test server startup (lines 331-354)
            start_mcp_server(mock_settings, mock_db_ops)

            # Verify server creation and startup
            mock_create_server.assert_called_with(
                db_ops=mock_db_ops,
                host="0.0.0.0",
                port=8001
            )
            assert mock_server.start.called
            assert hasattr(mock_settings, '_mcp_server')
            assert mock_settings._mcp_server == mock_server
    
    def test_start_mcp_server_exception_handling(self):
        """AI: Test MCP server startup exception handling."""
        with patch('app.mcp.server.create_network_server', side_effect=Exception("MCP server failed")):
            
            mock_settings = MagicMock()
            mock_settings.mcp_port = 8001
            mock_db_ops = MagicMock()
            
            # Should raise exception with error message (lines 353-354)
            with pytest.raises(Exception) as exc_info:
                start_mcp_server(mock_settings, mock_db_ops)
            
            assert "MCP server failed" in str(exc_info.value)


class TestCLIConfigurationConsistency:
    """AI: Test CLI configuration consistency and edge cases."""

    def setup_method(self):
        """AI: Setup test runner before each test."""
        self.runner = CliRunner()
        # Patch logger to disable test mode suppression for CLI tests
        from app.utils.logger import logger
        self._original_is_test = logger._is_test_environment
        logger._is_test_environment = lambda: False

    def teardown_method(self):
        """AI: Restore logger test mode detection after each test."""
        from app.utils.logger import logger
        logger._is_test_environment = self._original_is_test

    def test_mcp_server_port_configuration(self):
        """AI: Test MCP server port configuration displays correctly."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = True
            mock_settings.process_only = False
            mock_settings.nexus_dir = '/tmp/nexus'
            mock_settings.nginx_dir = '/tmp/nginx'
            mock_settings.nexus_patterns = ['*.log']
            mock_settings.nginx_patterns = ['access.log*']
            mock_settings.db_name = 'test.db'
            mock_settings.web_port = 9000
            mock_settings.mcp_port = 9001
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx',
                '--enable-mcp-server',
                '--web-port', '9000',
                '--mcp-port', '9001'
            ])
            
            # Should display MCP server port in configuration (line 234)
            assert "✓ MCP server will start on port 9001" in result.output
    
    def test_skip_log_processing_message(self):
        """AI: Test skip log processing message display."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/tmp/nexus',
                '--nginx-dir', '/tmp/nginx'
                # No --process-logs flag
            ])
            
            # Should display skip message (line 244)
            assert "Skipping log processing (use --process-logs to process logs)" in result.output
    
    def test_configuration_status_display(self):
        """AI: Test detailed configuration status display."""
        with patch('app.main.load_settings') as mock_load, \
             patch('app.main.validate_configuration'), \
             patch('app.main.DatabaseConnection'), \
             patch('app.main.DatabaseOperations'), \
             patch('app.main.start_web_server'), \
             patch('time.sleep', side_effect=KeyboardInterrupt):  # Immediately interrupt the loop
            
            mock_settings = MagicMock()
            mock_settings.enable_mcp_server = False
            mock_settings.process_only = False
            mock_settings.nexus_dir = '/custom/nexus'
            mock_settings.nginx_dir = '/custom/nginx'
            mock_settings.nexus_patterns = ['request*.log', '*.tar.gz']
            mock_settings.nginx_patterns = ['access.log*', 'error.log*']
            mock_settings.db_name = 'custom.db'
            mock_settings.web_port = 7000
            mock_load.return_value = mock_settings
            
            result = self.runner.invoke(cli, [
                '--nexus-dir', '/custom/nexus',
                '--nginx-dir', '/custom/nginx',
                '--db-name', 'custom.db',
                '--web-port', '7000'
            ])
            
            # Should display detailed configuration (lines 227-232)
            assert "✓ Ready to process logs from:" in result.output
            assert "- Nexus: /custom/nexus (patterns: ['request*.log', '*.tar.gz'])" in result.output
            assert "- nginx: /custom/nginx (patterns: ['access.log*', 'error.log*'])" in result.output
            assert "✓ Database: custom.db" in result.output
            assert "✓ Web server will start on port 7000" in result.output
