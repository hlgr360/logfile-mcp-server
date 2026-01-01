"""
AI: Unit tests for configuration management.

Tests Phase 1 requirements:
- CLI argument parsing and validation
- Environment variable loading
- Configuration validation
- Error handling for invalid configurations
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import Settings, load_settings, validate_configuration


class TestSettings:
    """AI: Test Settings class validation and properties."""
    
    def test_valid_configuration(self, tmp_path):
        """AI: Test configuration with valid directories and settings."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir)
        )
        
        assert settings.nexus_dir == str(nexus_dir.absolute())
        assert settings.nginx_dir == str(nginx_dir.absolute())
        assert settings.db_name == "log_analysis.db"
        assert settings.web_port == 8000
        assert settings.mcp_port == 8001
        assert not settings.enable_mcp_server
    
    def test_nexus_patterns_property(self, tmp_path):
        """AI: Test nexus_patterns property converts comma-separated string to list."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            nexus_pattern="pattern1.log*, pattern2.tar, pattern3.gz"
        )
        
        expected = ["pattern1.log*", "pattern2.tar", "pattern3.gz"]
        assert settings.nexus_patterns == expected
    
    def test_nginx_patterns_property(self, tmp_path):
        """AI: Test nginx_patterns property converts comma-separated string to list."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            nginx_pattern="access.log*, old.log.gz"
        )
        
        expected = ["access.log*", "old.log.gz"]
        assert settings.nginx_patterns == expected
    
    def test_directory_validation_nonexistent(self):
        """AI: Test validation fails for non-existent directories."""
        with pytest.raises(ValueError, match="Directory does not exist"):
            Settings(
                nexus_dir="/nonexistent/directory",
                nginx_dir="/another/nonexistent"
            )
    
    def test_directory_validation_not_directory(self, tmp_path):
        """AI: Test validation fails when path is not a directory."""
        file_path = tmp_path / "notadir.txt"
        file_path.write_text("content")
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            Settings(
                nexus_dir=str(file_path),
                nginx_dir=str(tmp_path)
            )
    
    def test_port_validation_invalid_range(self, tmp_path):
        """AI: Test port validation for invalid port numbers."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        with pytest.raises(ValueError, match="Port must be between 1024 and 65535"):
            Settings(
                nexus_dir=str(nexus_dir),
                nginx_dir=str(nginx_dir),
                web_port=80  # Below minimum
            )
        
        with pytest.raises(ValueError, match="Port must be between 1024 and 65535"):
            Settings(
                nexus_dir=str(nexus_dir),
                nginx_dir=str(nginx_dir),
                mcp_port=70000  # Above maximum
            )
    
    def test_archive_depth_validation(self, tmp_path):
        """AI: Test archive depth validation limits."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        with pytest.raises(ValueError, match="Archive depth must be between 1 and 10"):
            Settings(
                nexus_dir=str(nexus_dir),
                nginx_dir=str(nginx_dir),
                max_archive_depth=0
            )
        
        with pytest.raises(ValueError, match="Archive depth must be between 1 and 10"):
            Settings(
                nexus_dir=str(nexus_dir),
                nginx_dir=str(nginx_dir),
                max_archive_depth=15
            )


class TestLoadSettings:
    """AI: Test load_settings function with CLI arguments."""
    
    def test_load_settings_with_cli_args(self, tmp_path):
        """AI: Test loading settings with CLI arguments override."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = load_settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            web_port=9000,
            enable_mcp_server=True
        )
        
        assert settings.nexus_dir == str(nexus_dir.absolute())
        assert settings.nginx_dir == str(nginx_dir.absolute())
        assert settings.web_port == 9000
        assert settings.enable_mcp_server is True
    
    def test_load_settings_none_values_ignored(self, tmp_path):
        """AI: Test that None CLI arguments don't override defaults."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = load_settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            web_port=None,  # Should use default
            enable_mcp_server=None  # Should use default
        )
        
        assert settings.web_port == 8000  # Default value
        assert settings.enable_mcp_server is False  # Default value
    
    def test_load_settings_validation_error(self):
        """AI: Test load_settings raises ValueError for invalid config."""
        with pytest.raises(ValueError, match="Configuration validation failed"):
            load_settings(
                nexus_dir="/nonexistent",
                nginx_dir="/another/nonexistent"
            )


class TestValidateConfiguration:
    """AI: Test validate_configuration function."""
    
    def test_validate_configuration_port_conflict(self, tmp_path):
        """AI: Test validation fails when web and MCP ports conflict."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            enable_mcp_server=True,
            web_port=8000,
            mcp_port=8000  # Same as web port
        )
        
        with pytest.raises(ValueError, match="Web server and MCP server cannot use the same port"):
            validate_configuration(settings)
    
    def test_validate_configuration_empty_patterns(self, tmp_path):
        """AI: Test validation fails for empty file patterns."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()
        
        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            nexus_pattern=""  # Empty pattern
        )
        
        with pytest.raises(ValueError, match="At least one nexus pattern must be specified"):
            validate_configuration(settings)
    
    def test_validate_configuration_success(self, tmp_path, capsys):
        """AI: Test successful configuration validation with output."""
        nexus_dir = tmp_path / "nexus"
        nginx_dir = tmp_path / "nginx"
        nexus_dir.mkdir()
        nginx_dir.mkdir()

        settings = Settings(
            nexus_dir=str(nexus_dir),
            nginx_dir=str(nginx_dir),
            enable_mcp_server=True
        )

        # Temporarily override test mode detection to see INFO messages
        from app.utils.logger import logger
        original_is_test = logger._is_test_environment
        logger._is_test_environment = lambda: False

        try:
            # Should not raise exception
            validate_configuration(settings)

            # Check output messages (logger outputs to stderr)
            captured = capsys.readouterr()
            assert "Configuration validated successfully" in captured.err
            assert f"Nexus directory: {nexus_dir.absolute()}" in captured.err
            assert f"nginx directory: {nginx_dir.absolute()}" in captured.err
            assert "MCP port: 8001" in captured.err
        finally:
            # Restore original test mode detection
            logger._is_test_environment = original_is_test
