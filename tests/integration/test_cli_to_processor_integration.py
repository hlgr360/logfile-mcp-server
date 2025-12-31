"""
AI: Integration tests for CLI to processor configuration flow.

Tests the critical path mandated by ADR_20250728_04:
- CLI arguments → Settings → LogProcessingOrchestrator → Processors
- Configuration dependency injection validation
- End-to-end pattern matching consistency
- File discovery to processing pipeline integration
"""

import tempfile
import pytest
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from app.main import cli
from app.config import load_settings
from app.processing.orchestrator import LogProcessingOrchestrator
from app.processors.nginx_processor import NginxLogProcessor
from app.processors.nexus_processor import NexusLogProcessor
from app.database.operations import DatabaseOperations


class TestCLIToProcessorIntegration:
    """AI: Test CLI arguments flow through to processors via dependency injection."""

    def setup_method(self):
        """AI: Setup temporary directories and mock database for integration tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.nexus_dir = Path(self.temp_dir) / "nexus"
        self.nginx_dir = Path(self.temp_dir) / "nginx"
        self.nexus_dir.mkdir()
        self.nginx_dir.mkdir()

    def test_cli_arguments_flow_to_processor_patterns(self):
        """
        AI: Test that CLI arguments for patterns reach processors via Settings.
        
        This test verifies ADR_20250728_04 requirement that configuration
        dependencies are properly injected from CLI to processors.
        """
        # Custom patterns from CLI
        custom_nexus_pattern = "custom_nexus*.log,nexus_archive*.tar"
        custom_nginx_pattern = "custom_access*.log"
        
        # Load settings as if from CLI
        settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
            nexus_pattern=custom_nexus_pattern,
            nginx_pattern=custom_nginx_pattern,
        )
        
        # Create processors via orchestrator (simulating real application flow)
        mock_db_ops = Mock(spec=DatabaseOperations)
        orchestrator = LogProcessingOrchestrator(settings, mock_db_ops)
        
        # Verify processors received correct patterns from CLI
        assert orchestrator.nginx_processor.settings.nginx_patterns == ["custom_access*.log"]
        assert orchestrator.nexus_processor.settings.nexus_patterns == ["custom_nexus*.log", "nexus_archive*.tar"]
        
        # Verify pattern matching uses injected configuration
        assert orchestrator.nginx_processor.matches_target_pattern("custom_access.log") == True
        assert orchestrator.nginx_processor.matches_target_pattern("regular_access.log") == False
        
        assert orchestrator.nexus_processor.matches_target_pattern("custom_nexus_req.log") == True
        assert orchestrator.nexus_processor.matches_target_pattern("request.log") == False

    def test_cli_chunk_size_flows_to_processors(self):
        """
        AI: Test that CLI chunk_size parameter reaches processors.
        
        Verifies dependency injection of processing parameters from CLI.
        """
        custom_chunk_size = 16384
        
        settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
            chunk_size=custom_chunk_size,
        )
        
        mock_db_ops = Mock(spec=DatabaseOperations)
        orchestrator = LogProcessingOrchestrator(settings, mock_db_ops)
        
        # Verify chunk size propagated to processors
        assert orchestrator.nginx_processor.chunk_size == custom_chunk_size
        assert orchestrator.nexus_processor.chunk_size == custom_chunk_size

    def test_orchestrator_creates_processors_with_settings_dependency_injection(self):
        """
        AI: Test orchestrator properly injects Settings into processors.
        
        Validates ADR_20250728_04 requirement for dependency injection pattern.
        """
        settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
        )
        
        mock_db_ops = Mock(spec=DatabaseOperations)
        orchestrator = LogProcessingOrchestrator(settings, mock_db_ops)
        
        # Verify processors have Settings dependency injected
        assert isinstance(orchestrator.nginx_processor, NginxLogProcessor)
        assert isinstance(orchestrator.nexus_processor, NexusLogProcessor)
        assert orchestrator.nginx_processor.settings is settings
        assert orchestrator.nexus_processor.settings is settings

    def test_file_discovery_and_processor_pattern_consistency(self):
        """
        AI: Test file discovery and processor patterns are consistent.
        
        Critical integration test for ADR_20250728_04: ensures files discovered
        by LogFileDiscovery can actually be processed by their intended processors.
        """
        # Create test files matching custom patterns
        custom_nginx_pattern = "webapp*.log"
        custom_nexus_pattern = "repo*.log"
        
        test_nginx_file = self.nginx_dir / "webapp_access.log"
        test_nexus_file = self.nexus_dir / "repo_request.log"
        test_nginx_file.write_text("test nginx log")
        test_nexus_file.write_text("test nexus log")
        
        settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
            nginx_pattern=custom_nginx_pattern,
            nexus_pattern=custom_nexus_pattern,
        )
        
        mock_db_ops = Mock(spec=DatabaseOperations)
        orchestrator = LogProcessingOrchestrator(settings, mock_db_ops)
        
        # Test file discovery uses same patterns as processors
        nginx_files = list(orchestrator.file_discovery.discover_nginx_files())
        nexus_files = list(orchestrator.file_discovery.discover_nexus_files())
        
        # Verify discovered files can be processed by their intended processors
        for file_path, _ in nginx_files:
            filename = Path(file_path).name
            assert orchestrator.nginx_processor.matches_target_pattern(filename) == True
            
        for file_path, _ in nexus_files:
            filename = Path(file_path).name
            assert orchestrator.nexus_processor.matches_target_pattern(filename) == True

    def test_configuration_changes_affect_processing_behavior(self):
        """
        AI: Test that configuration changes actually affect processing behavior.
        
        Validates that the system responds correctly to configuration updates,
        preventing the architectural disconnect identified in ADR_20250728_04.
        """
        # Test with restrictive patterns
        restrictive_settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
            nginx_pattern="very_specific*.log",
            nexus_pattern="very_specific*.log",
        )
        
        # Test with permissive patterns  
        permissive_settings = load_settings(
            nexus_dir=str(self.nexus_dir),
            nginx_dir=str(self.nginx_dir),
            nginx_pattern="*.log",
            nexus_pattern="*.log",
        )
        
        mock_db_ops = Mock(spec=DatabaseOperations)
        
        restrictive_orchestrator = LogProcessingOrchestrator(restrictive_settings, mock_db_ops)
        permissive_orchestrator = LogProcessingOrchestrator(permissive_settings, mock_db_ops)
        
        test_filename = "access.log"
        
        # Verify different configurations produce different behaviors
        assert restrictive_orchestrator.nginx_processor.matches_target_pattern(test_filename) == False
        assert permissive_orchestrator.nginx_processor.matches_target_pattern(test_filename) == True
        
        assert restrictive_orchestrator.nexus_processor.matches_target_pattern(test_filename) == False
        assert permissive_orchestrator.nexus_processor.matches_target_pattern(test_filename) == True


class TestCLIIntegrationWithMocks:
    """AI: Test CLI integration using Click testing framework."""

    def setup_method(self):
        """AI: Setup CLI test runner and temporary directories."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.nexus_dir = Path(self.temp_dir) / "nexus"
        self.nginx_dir = Path(self.temp_dir) / "nginx" 
        self.nexus_dir.mkdir()
        self.nginx_dir.mkdir()

    @patch('app.main.LogProcessingOrchestrator')
    @patch('app.main.DatabaseOperations')
    @patch('app.main.DatabaseConnection')
    def test_cli_creates_orchestrator_with_correct_settings(
        self, mock_db_conn, mock_db_ops, mock_orchestrator
    ):
        """
        AI: Test CLI command creates orchestrator with properly loaded settings.
        
        Validates end-to-end CLI argument processing and dependency injection.
        Uses --process-logs to trigger orchestrator creation and --process-only 
        to avoid infinite loop during testing.
        """
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_orchestrator_instance.process_all_logs.return_value = Mock()
        
        # For this test, we'll use --process-only to avoid the infinite loop
        # and include --process-logs to trigger orchestrator creation
        result = self.runner.invoke(cli, [
            '--nexus-dir', str(self.nexus_dir),
            '--nginx-dir', str(self.nginx_dir),
            '--nexus-pattern', 'custom_nexus*.log',
            '--nginx-pattern', 'custom_nginx*.log',
            '--chunk-size', '16384',
            '--process-logs',            # Trigger orchestrator creation
            '--process-only'             # Exit immediately after processing
        ])
        
        # Verify CLI executed successfully
        assert result.exit_code == 0
        
        # Verify orchestrator was created with settings from CLI
        mock_orchestrator.assert_called_once()
        settings_arg = mock_orchestrator.call_args[0][0]  # First argument to orchestrator
        
        assert settings_arg.nexus_dir == str(self.nexus_dir)
        assert settings_arg.nginx_dir == str(self.nginx_dir)
        assert settings_arg.nexus_patterns == ['custom_nexus*.log']
        assert settings_arg.nginx_patterns == ['custom_nginx*.log']
        assert settings_arg.chunk_size == 16384
        
        # Verify processing was triggered
        mock_orchestrator_instance.process_all_logs.assert_called_once()

    def test_cli_validation_prevents_invalid_configurations(self):
        """
        AI: Test CLI validation catches configuration issues early.
        
        Ensures architectural consistency by validating configuration
        before it reaches processors.
        """
        # Test with non-existent directories
        result = self.runner.invoke(cli, [
            '--nexus-dir', '/nonexistent/nexus',
            '--nginx-dir', '/nonexistent/nginx',
        ])
        
        # CLI should fail with validation error
        assert result.exit_code == 1
        assert "Application startup failed" in result.output


class TestProcessorConfigurationContract:
    """AI: Test processor configuration contracts as required by ADR_20250728_04."""

    def test_processors_implement_required_configuration_interface(self):
        """
        AI: Test processors implement required configuration interface.
        
        Validates that processors properly accept and use Settings dependency.
        """
        from tests.test_settings_helper import create_test_settings
        
        settings = create_test_settings()
        
        # Test processors can be instantiated with Settings
        nginx_processor = NginxLogProcessor(settings)
        nexus_processor = NexusLogProcessor(settings)
        
        # Verify processors store settings reference
        assert nginx_processor.settings is settings
        assert nexus_processor.settings is settings
        
        # Verify processors use settings for pattern matching
        assert hasattr(nginx_processor, 'matches_target_pattern')
        assert hasattr(nexus_processor, 'matches_target_pattern')
        
        # Verify processors use configuration-driven patterns
        nginx_patterns = nginx_processor.get_supported_patterns()
        nexus_patterns = nexus_processor.get_supported_patterns()
        
        assert nginx_patterns == settings.nginx_patterns
        assert nexus_patterns == settings.nexus_patterns

    def test_processor_pattern_matching_consistency(self):
        """
        AI: Test processor pattern matching is consistent with file discovery.
        
        Critical test ensuring architectural consistency between discovery and processing.
        """
        from tests.test_settings_helper import create_test_settings
        from app.file_discovery.discovery import LogFileDiscovery
        
        # Create settings with specific patterns
        custom_settings = create_test_settings()
        custom_settings.nginx_pattern = "webapp*.log,api*.log"
        custom_settings.nexus_pattern = "repo*.log,artifact*.log"
        
        # Create processors and discovery with same settings
        nginx_processor = NginxLogProcessor(custom_settings)
        nexus_processor = NexusLogProcessor(custom_settings)
        file_discovery = LogFileDiscovery(custom_settings)
        
        # Test files that should match
        test_files = [
            ("webapp_access.log", "nginx"),
            ("api_requests.log", "nginx"),
            ("repo_requests.log", "nexus"),
            ("artifact_download.log", "nexus"),
            ("other.log", "none")  # Should not match either
        ]
        
        for filename, expected_type in test_files:
            nginx_matches = nginx_processor.matches_target_pattern(filename)
            nexus_matches = nexus_processor.matches_target_pattern(filename)
            nginx_discovery_matches = file_discovery._matches_patterns(filename, custom_settings.nginx_patterns)
            nexus_discovery_matches = file_discovery._matches_patterns(filename, custom_settings.nexus_patterns)
            
            if expected_type == "nginx":
                assert nginx_matches == True, f"Nginx processor should match {filename}"
                assert nginx_discovery_matches == True, f"Nginx discovery should match {filename}"
                assert nexus_matches == False, f"Nexus processor should not match {filename}"
                assert nexus_discovery_matches == False, f"Nexus discovery should not match {filename}"
            elif expected_type == "nexus":
                assert nexus_matches == True, f"Nexus processor should match {filename}"
                assert nexus_discovery_matches == True, f"Nexus discovery should match {filename}"
                assert nginx_matches == False, f"Nginx processor should not match {filename}"
                assert nginx_discovery_matches == False, f"Nginx discovery should not match {filename}"
            else:
                assert nginx_matches == False, f"No processor should match {filename}"
                assert nexus_matches == False, f"No processor should match {filename}"
                assert nginx_discovery_matches == False, f"No discovery should match {filename}"
                assert nexus_discovery_matches == False, f"No discovery should match {filename}"
