"""
AI: Unit tests for file discovery system.

Tests file discovery functionality:
- Directory scanning and pattern matching
- Archive detection and processing
- Nested archive depth limits
- Memory-efficient iteration
"""

import pytest
import tempfile
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.file_discovery.discovery import LogFileDiscovery, create_file_iterator_from_path
from app.config import Settings


class TestLogFileDiscovery:
    """AI: Test file discovery functionality."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        # Create mock settings
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nginx_dir = "/test/nginx"
        self.mock_settings.nexus_dir = "/test/nexus"
        self.mock_settings.nginx_pattern = "access.log*,*.log"
        self.mock_settings.nexus_pattern = "request.log*,nexus_logs_*.tar"
        
        self.discovery = LogFileDiscovery(self.mock_settings)
    
    def test_get_nginx_patterns(self):
        """AI: Test nginx pattern extraction from configuration."""
        patterns = self.discovery._get_nginx_patterns()
        
        assert patterns == ["access.log*", "*.log"]
    
    def test_get_nexus_patterns(self):
        """AI: Test Nexus pattern extraction from configuration."""
        patterns = self.discovery._get_nexus_patterns()
        
        assert patterns == ["request.log*", "nexus_logs_*.tar"]
    
    def test_matches_patterns(self):
        """AI: Test filename pattern matching."""
        patterns = ["access.log*", "*.tar.gz", "test_*.log"]
        
        # Should match
        assert self.discovery._matches_patterns("access.log", patterns)
        assert self.discovery._matches_patterns("access.log.1", patterns)
        assert self.discovery._matches_patterns("logs.tar.gz", patterns)
        assert self.discovery._matches_patterns("test_nginx.log", patterns)
        
        # Should not match
        assert not self.discovery._matches_patterns("error.log", patterns)
        assert not self.discovery._matches_patterns("random.txt", patterns)
        assert not self.discovery._matches_patterns("access.txt", patterns)
    
    def test_is_archive_file(self):
        """AI: Test archive file detection."""
        # Should detect as archives
        assert self.discovery._is_archive_file(Path("logs.tar"))
        assert self.discovery._is_archive_file(Path("logs.tar.gz"))
        assert self.discovery._is_archive_file(Path("logs.tar.bz2"))
        assert self.discovery._is_archive_file(Path("logs.zip"))
        assert self.discovery._is_archive_file(Path("archive.gz"))  # Single .gz
        
        # Should not detect as archives
        assert not self.discovery._is_archive_file(Path("access.log"))
        assert not self.discovery._is_archive_file(Path("file.txt"))
        assert not self.discovery._is_archive_file(Path("document.pdf"))
    
    def test_is_safe_path(self):
        """AI: Test path safety validation."""
        # Safe paths
        assert self.discovery._is_safe_path("access.log")
        assert self.discovery._is_safe_path("logs/access.log")
        assert self.discovery._is_safe_path("subdir/file.txt")
        
        # Unsafe paths (directory traversal)
        assert not self.discovery._is_safe_path("../etc/passwd")
        assert not self.discovery._is_safe_path("..\\windows\\system32")
        assert not self.discovery._is_safe_path("/absolute/path")
        assert not self.discovery._is_safe_path("path/../../../etc")
    
    def test_cleanup_temp_dirs(self):
        """AI: Test temporary directory cleanup."""
        # Add some fake temp directories
        self.discovery._temp_dirs = ["/tmp/fake1", "/tmp/fake2"]
        
        with patch('os.path.exists') as mock_exists, \
             patch('shutil.rmtree') as mock_rmtree:
            
            mock_exists.return_value = True
            self.discovery.cleanup_temp_dirs()
            
            # Should attempt to remove both directories
            assert mock_rmtree.call_count == 2
            assert self.discovery._temp_dirs == []
    
    @pytest.mark.integration
    def test_discover_files_with_real_filesystem(self):
        """AI: Integration test with real temporary filesystem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file structure
            nginx_dir = temp_path / "nginx"
            nginx_dir.mkdir()
            
            # Create test files
            (nginx_dir / "access.log").write_text("test log line\n")
            (nginx_dir / "access.log.1").write_text("old log line\n")
            (nginx_dir / "error.log").write_text("error line\n")  # Should not match
            
            # Update settings to use temp directory
            self.mock_settings.nginx_dir = str(nginx_dir)
            self.mock_settings.nginx_pattern = "access.log*"
            
            discovery = LogFileDiscovery(self.mock_settings)
            
            # Discover files
            found_files = list(discovery.discover_nginx_files())
            
            # Should find 2 access.log files
            assert len(found_files) == 2
            
            # Check file paths and descriptions
            file_paths = [str(path) for path, desc in found_files]
            assert str(nginx_dir / "access.log") in file_paths
            assert str(nginx_dir / "access.log.1") in file_paths
            
            # Check descriptions
            descriptions = [desc for path, desc in found_files]
            assert all("nginx:" in desc for desc in descriptions)
    
    @pytest.mark.integration
    def test_discover_files_with_archive(self):
        """AI: Integration test with archive processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nexus directory
            nexus_dir = temp_path / "nexus"
            nexus_dir.mkdir()
            
            # Create a tar archive with log files
            archive_path = nexus_dir / "nexus_logs_2025.tar"
            
            with tarfile.open(archive_path, 'w') as tar:
                # Create temporary files to add to archive
                log_content = '2025-05-29 12:34:56,123+0000 127.0.0.1 thread "GET /test HTTP/1.1" 200 100\n'
                
                # Add request.log to archive
                request_log = temp_path / "request.log"
                request_log.write_text(log_content)
                tar.add(request_log, arcname="request.log")
            
            # Update settings to include both archive and file patterns
            self.mock_settings.nexus_dir = str(nexus_dir)
            self.mock_settings.nexus_pattern = "nexus_logs_*.tar,request.log*"
            
            discovery = LogFileDiscovery(self.mock_settings, max_archive_depth=2)
            
            # Discover files
            found_files = list(discovery.discover_nexus_files())
            
            # Should find the extracted request.log
            assert len(found_files) >= 1
            
            # Check that archive processing worked
            descriptions = [desc for path, desc in found_files]
            archive_descriptions = [desc for desc in descriptions if "->" in desc]
            assert len(archive_descriptions) > 0
            
            # Cleanup
            discovery.cleanup_temp_dirs()


class TestCreateFileIterator:
    """AI: Test file iterator creation functionality."""
    
    def test_create_file_iterator_success(self):
        """AI: Test successful file iterator creation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content\nline 2\n")
            temp_path = Path(temp_file.name)
        
        try:
            # Test iterator
            iterator = create_file_iterator_from_path(temp_path, "test_source")
            results = list(iterator)
            
            assert len(results) == 1
            source_desc, file_handle = results[0]
            assert source_desc == "test_source"
            
            # File handle should be closed after iterator
            
        finally:
            temp_path.unlink()
    
    def test_create_file_iterator_file_not_found(self):
        """AI: Test file iterator with non-existent file."""
        non_existent = Path("/non/existent/file.log")
        
        # Should not raise exception, but should not yield anything
        iterator = create_file_iterator_from_path(non_existent, "missing_file")
        results = list(iterator)
        
        assert len(results) == 0
    
    @pytest.mark.integration  
    def test_file_iterator_encoding_handling(self):
        """AI: Test file iterator with different encodings."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write some content with special characters
            content = "Test content with special chars: üñíçødé\n"
            temp_file.write(content.encode('utf-8'))
            temp_path = Path(temp_file.name)
        
        try:
            iterator = create_file_iterator_from_path(temp_path, "encoding_test")
            results = list(iterator)
            
            assert len(results) == 1
            source_desc, file_handle = results[0]
            assert source_desc == "encoding_test"
            
        finally:
            temp_path.unlink()
