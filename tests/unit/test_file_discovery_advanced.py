"""
AI: Advanced unit tests for file discovery system.

Tests advanced functionality, error scenarios, and edge cases to improve coverage
from 72% to 85%+. Focuses on untested paths and error handling scenarios.
"""

import pytest
import tempfile
import tarfile
import zipfile
import gzip
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from app.file_discovery.discovery import LogFileDiscovery, create_file_iterator_from_path
from app.config import Settings


class TestFileDiscoveryAdvanced:
    """AI: Test advanced file discovery functionality and error scenarios."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nginx_dir = "/test/nginx"
        self.mock_settings.nexus_dir = "/test/nexus"
        self.mock_settings.nginx_pattern = "access.log*,*.log"
        self.mock_settings.nexus_pattern = "request.log*,nexus_logs_*.tar"
        
        self.discovery = LogFileDiscovery(self.mock_settings, max_archive_depth=2)
    
    def test_discover_files_nonexistent_directory(self):
        """AI: Test file discovery with non-existent directory - covers lines 96-97."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:
                files = list(self.discovery.discover_nginx_files())
                
                assert len(files) == 0
                mock_logger_warn.assert_called_once()
                assert "does not exist" in mock_logger_warn.call_args[0][0]
    
    def test_discover_files_directory_is_file(self):
        """AI: Test file discovery when path is file not directory - covers lines 100-101."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            with patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:
                files = list(self.discovery.discover_nexus_files())
                
                assert len(files) == 0
                mock_logger_warn.assert_called_once()
                assert "is not a directory" in mock_logger_warn.call_args[0][0]
    
    def test_discover_files_duplicate_processing_prevention(self):
        """AI: Test that duplicate files are processed only once - covers line 119."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file
            test_file = temp_path / "access.log"
            test_file.write_text("test log line\n")
            
            # Mock os.walk to return the same file multiple times (simulating symlinks)
            mock_walk_data = [
                (str(temp_path), [], ["access.log"]),
                (str(temp_path), [], ["access.log"]),  # Duplicate
            ]
            
            self.mock_settings.nginx_dir = str(temp_path)
            self.mock_settings.nginx_pattern = "access.log*"
            
            with patch('os.walk', return_value=mock_walk_data):
                files = list(self.discovery.discover_nginx_files())
                
                # Should only process file once despite duplicate in walk
                assert len(files) == 1
    
    def test_process_archive_max_depth_reached(self):
        """AI: Test archive processing stops at max depth - covers lines 180-181."""
        archive_path = Path("/test/nested.tar")
        patterns = ["*.log"]
        
        with patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:
            # Test with depth at maximum
            results = list(self.discovery._process_archive_recursive(
                archive_path, patterns, "test", depth=2  # At max depth
            ))
            
            assert len(results) == 0
            mock_logger_warn.assert_called_once()
            assert "Maximum archive depth" in mock_logger_warn.call_args[0][0]
    
    def test_process_archive_extraction_failure(self):
        """AI: Test archive processing with extraction failure - covers lines 198-199."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a fake archive file
            fake_archive = temp_path / "fake.tar"
            fake_archive.write_text("not a real archive")
            
            patterns = ["*.log"]
            
            with patch('app.file_discovery.discovery.logger.error') as mock_logger_error:
                results = list(self.discovery._process_archive_recursive(
                    fake_archive, patterns, "test", depth=0
                ))
                
                assert len(results) == 0
                # Should have printed error message
                error_calls = [call for call in mock_logger_error.call_args_list 
                              if "ERROR" in str(call)]
                assert len(error_calls) > 0
    
    def test_extract_archive_unsupported_format(self):
        """AI: Test extraction with unsupported archive format - covers line 223."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extract"
            extract_to.mkdir()
            
            # Create unsupported archive file
            unsupported_archive = temp_path / "test.rar"
            unsupported_archive.write_text("unsupported format")
            
            with patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:
                result = self.discovery._extract_archive(unsupported_archive, extract_to)
                
                assert result is False
                mock_logger_warn.assert_called_once()
                assert "Unsupported archive format" in mock_logger_warn.call_args[0][0]
    
    def test_extract_archive_tarfile_unsafe_paths(self):
        """AI: Test tar extraction with unsafe paths - covers lines 226-230."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extract"
            extract_to.mkdir()
            
            # Create tar with unsafe member
            archive_path = temp_path / "unsafe.tar"
            
            # Mock tarfile member with unsafe path
            mock_member = Mock()
            mock_member.name = "../../../etc/passwd"  # Directory traversal
            
            mock_tar = Mock()
            mock_tar.getmembers.return_value = [mock_member]
            mock_tar.__enter__ = Mock(return_value=mock_tar)
            mock_tar.__exit__ = Mock(return_value=None)
            
            with patch('tarfile.open', return_value=mock_tar), \
                 patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:

                result = self.discovery._extract_archive(archive_path, extract_to)

                assert result is True
                # Should not extract unsafe member
                mock_tar.extract.assert_not_called()
                # Should print warning
                warning_calls = [call for call in mock_logger_warn.call_args_list
                               if "Unsafe path" in str(call)]
                assert len(warning_calls) > 0
    
    def test_extract_archive_zipfile_unsafe_paths(self):
        """AI: Test zip extraction with unsafe paths - covers lines 240-245."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extract"
            extract_to.mkdir()
            
            archive_path = temp_path / "unsafe.zip"
            
            # Mock zipfile with unsafe member
            mock_zip = Mock()
            mock_zip.namelist.return_value = ["../../../etc/passwd"]  # Directory traversal
            mock_zip.__enter__ = Mock(return_value=mock_zip)
            mock_zip.__exit__ = Mock(return_value=None)
            
            with patch('zipfile.ZipFile', return_value=mock_zip), \
                 patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:

                result = self.discovery._extract_archive(archive_path, extract_to)

                assert result is True
                # Should not extract unsafe member
                mock_zip.extract.assert_not_called()
                # Should print warning
                warning_calls = [call for call in mock_logger_warn.call_args_list
                               if "Unsafe path" in str(call)]
                assert len(warning_calls) > 0
    
    def test_extract_archive_gzip_single_file(self):
        """AI: Test gzip single file extraction - covers lines 247-256."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extract"
            extract_to.mkdir()
            
            # Create a real gzip file
            test_content = "test log content\nline 2\n"
            gzip_file = temp_path / "test.log.gz"
            
            with gzip.open(gzip_file, 'wb') as gz:
                gz.write(test_content.encode('utf-8'))
            
            result = self.discovery._extract_archive(gzip_file, extract_to)
            
            assert result is True
            
            # Check extracted file exists
            extracted_file = extract_to / "test.log"
            assert extracted_file.exists()
            
            # Check content
            with open(extracted_file, 'r') as f:
                content = f.read()
            assert content == test_content
    
    def test_extract_archive_exception_handling(self):
        """AI: Test extraction exception handling - covers lines 299-300."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_to = temp_path / "extract"
            extract_to.mkdir()
            
            archive_path = temp_path / "corrupt.tar"
            archive_path.write_text("corrupt archive")

            with patch('app.file_discovery.discovery.logger.error') as mock_logger_error:
                result = self.discovery._extract_archive(archive_path, extract_to)

                assert result is False
                # Should print error message
                error_calls = [call for call in mock_logger_error.call_args_list
                              if "ERROR" in str(call)]
                assert len(error_calls) > 0
    
    def test_process_extracted_contents_nested_archive(self):
        """AI: Test processing nested archives in extracted content - covers lines 322-323."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patterns = ["*.log", "*.tar"]
            
            # Create nested structure with archive
            subdir = temp_path / "subdir"
            subdir.mkdir()
            
            # Create a nested tar archive
            nested_archive = subdir / "nested.tar"
            test_log = temp_path / "temp.log"
            test_log.write_text("test content")
            
            with tarfile.open(nested_archive, 'w') as tar:
                tar.add(test_log, arcname="test.log")
            
            # Mock the recursive processing to avoid infinite recursion in test
            with patch.object(self.discovery, '_process_archive_recursive') as mock_recursive:
                mock_recursive.return_value = iter([])  # Return empty iterator
                
                results = list(self.discovery._process_extracted_contents(
                    temp_path, patterns, "test", "parent.tar", 0
                ))
                
                # Should call recursive processing for nested archive
                mock_recursive.assert_called_once()
                call_args = mock_recursive.call_args[0]
                assert call_args[0] == nested_archive  # archive path
                assert call_args[1] == patterns
                assert call_args[2] == "test"
                assert call_args[3] == 1  # depth + 1


class TestLogFileDiscoveryErrorHandling:
    """AI: Test error handling and edge cases in file discovery."""
    
    def setup_method(self):
        """AI: Setup test instance."""
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nginx_dir = "/test/nginx"
        self.mock_settings.nexus_dir = "/test/nexus"
        self.mock_settings.nginx_pattern = "*.log"
        self.mock_settings.nexus_pattern = "*.log"
        
        self.discovery = LogFileDiscovery(self.mock_settings)
    
    def test_cleanup_temp_dirs_with_exception(self):
        """AI: Test cleanup with removal exception."""
        self.discovery._temp_dirs = ["/fake/temp/dir"]

        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree', side_effect=OSError("Permission denied")), \
             patch('app.file_discovery.discovery.logger.warn') as mock_logger_warn:

            self.discovery.cleanup_temp_dirs()

            # Should print warning about cleanup failure
            warning_calls = [call for call in mock_logger_warn.call_args_list
                           if "WARNING" in str(call)]
            assert len(warning_calls) > 0
    
    def test_cleanup_temp_dirs_nonexistent_directory(self):
        """AI: Test cleanup with non-existent directory."""
        self.discovery._temp_dirs = ["/fake/temp/dir"]
        
        with patch('os.path.exists', return_value=False), \
             patch('shutil.rmtree') as mock_rmtree:
            
            self.discovery.cleanup_temp_dirs()
            
            # Should not attempt to remove non-existent directory
            mock_rmtree.assert_not_called()
    
    def test_destructor_calls_cleanup(self):
        """AI: Test that __del__ calls cleanup_temp_dirs."""
        with patch.object(self.discovery, 'cleanup_temp_dirs') as mock_cleanup:
            self.discovery.__del__()
            mock_cleanup.assert_called_once()
    
    def test_case_insensitive_pattern_matching(self):
        """AI: Test case-insensitive pattern matching."""
        patterns = ["ACCESS.LOG*", "*.LOG"]
        
        # Should match regardless of case
        assert self.discovery._matches_patterns("access.log", patterns)
        assert self.discovery._matches_patterns("ACCESS.LOG", patterns)
        assert self.discovery._matches_patterns("test.log", patterns)
        assert self.discovery._matches_patterns("TEST.LOG", patterns)
        
        # Mixed case should also work
        assert self.discovery._matches_patterns("Access.Log", patterns)
    
    def test_is_safe_path_edge_cases(self):
        """AI: Test path safety with various edge cases."""
        # Test backslash handling on Windows-style paths
        assert not self.discovery._is_safe_path("dir\\..\\file")
        
        # Test escaped backslashes (should be allowed)
        assert self.discovery._is_safe_path("dir\\\\file")  # Double backslash
        
        # Test various directory traversal attempts
        assert not self.discovery._is_safe_path("./../../etc/passwd")
        assert not self.discovery._is_safe_path("dir/../../../root")
        
        # Test absolute paths
        assert not self.discovery._is_safe_path("/etc/passwd")
        assert not self.discovery._is_safe_path("C:\\Windows\\System32")


class TestCreateFileIteratorAdvanced:
    """AI: Test advanced file iterator scenarios."""
    
    def test_create_file_iterator_encoding_error(self):
        """AI: Test file iterator with encoding issues."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write invalid UTF-8 bytes
            temp_file.write(b'\\xff\\xfe\\x00\\x00invalid utf-8')
            temp_path = Path(temp_file.name)
        
        try:
            # Should handle encoding errors gracefully with 'replace' mode
            iterator = create_file_iterator_from_path(temp_path, "encoding_error_test")
            results = list(iterator)
            
            # Should still yield result, just with replaced characters
            assert len(results) == 1
            source_desc, file_handle = results[0]
            assert source_desc == "encoding_error_test"
            
        finally:
            temp_path.unlink()
    
    def test_create_file_iterator_permission_error(self):
        """AI: Test file iterator with permission denied."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Mock permission error
            with patch('builtins.open', side_effect=PermissionError("Access denied")), \
                 patch('app.file_discovery.discovery.logger.error') as mock_logger_error:

                iterator = create_file_iterator_from_path(temp_path, "permission_test")
                results = list(iterator)

                # Should not yield any results
                assert len(results) == 0

                # Should print error message
                error_calls = [call for call in mock_logger_error.call_args_list
                              if "ERROR" in str(call)]
                assert len(error_calls) > 0
                
        finally:
            temp_path.unlink()


class TestLogFileDiscoveryIntegrationAdvanced:
    """AI: Advanced integration tests with real file systems."""
    
    def test_complex_nested_archive_processing(self):
        """AI: Test complex nested archive scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test directory
            test_dir = temp_path / "test_logs"
            test_dir.mkdir()
            
            # Create inner log file
            inner_log = temp_path / "inner.log"
            inner_log.write_text("inner log content\\n")
            
            # Create inner tar archive
            inner_tar = temp_path / "inner.tar"
            with tarfile.open(inner_tar, 'w') as tar:
                tar.add(inner_log, arcname="inner.log")
            
            # Create outer tar archive containing inner tar
            outer_tar = test_dir / "outer.tar"
            with tarfile.open(outer_tar, 'w') as tar:
                tar.add(inner_tar, arcname="inner.tar")
            
            # Configure discovery
            mock_settings = Mock(spec=Settings)
            mock_settings.nexus_dir = str(test_dir)
            mock_settings.nexus_pattern = "*.tar,*.log"
            
            discovery = LogFileDiscovery(mock_settings, max_archive_depth=3)
            
            try:
                # Discover files
                found_files = list(discovery.discover_nexus_files())
                
                # Should find nested log file
                assert len(found_files) > 0
                
                # Check for nested source descriptions
                descriptions = [desc for path, desc in found_files]
                nested_descriptions = [desc for desc in descriptions if "->" in desc]
                assert len(nested_descriptions) > 0
                
            finally:
                discovery.cleanup_temp_dirs()
    
    def test_mixed_archive_types_processing(self):
        """AI: Test processing different archive types in same directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            test_dir = temp_path / "mixed_archives"
            test_dir.mkdir()
            
            # Create test log content
            log_content = "test log line\\n"
            
            # Create tar.gz archive
            test_log1 = temp_path / "test1.log"
            test_log1.write_text(log_content)
            
            tar_gz_archive = test_dir / "logs.tar.gz"
            with tarfile.open(tar_gz_archive, 'w:gz') as tar:
                tar.add(test_log1, arcname="test1.log")
            
            # Create zip archive
            test_log2 = temp_path / "test2.log"
            test_log2.write_text(log_content)
            
            zip_archive = test_dir / "logs.zip"
            with zipfile.ZipFile(zip_archive, 'w') as zip_file:
                zip_file.write(test_log2, arcname="test2.log")
            
            # Create gzip single file
            gzip_file = test_dir / "test3.log.gz"
            with gzip.open(gzip_file, 'wb') as gz:
                gz.write(log_content.encode('utf-8'))
            
            # Configure discovery
            mock_settings = Mock(spec=Settings)
            mock_settings.nginx_dir = str(test_dir)
            mock_settings.nginx_pattern = "*.tar.gz,*.zip,*.gz,*.log"
            
            discovery = LogFileDiscovery(mock_settings, max_archive_depth=2)
            
            try:
                # Discover files
                found_files = list(discovery.discover_nginx_files())
                
                # Should find extracted log files from all archive types
                assert len(found_files) >= 3
                
                # Check that different archive types were processed
                descriptions = [desc for path, desc in found_files]
                archive_descriptions = [desc for desc in descriptions if "->" in desc]
                assert len(archive_descriptions) >= 3
                
            finally:
                discovery.cleanup_temp_dirs()
