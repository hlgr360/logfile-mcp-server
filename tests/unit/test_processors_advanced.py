"""
AI: Advanced unit tests for processor modules.

Tests advanced functionality, error scenarios, and edge cases to improve coverage
for both nexus and nginx processors. Targets specific uncovered lines.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.processors.nexus_processor import NexusLogProcessor
from app.processors.nginx_processor import NginxLogProcessor
from app.config import Settings
from app.database.operations import DatabaseOperations


class TestProcessorsAdvanced:
    """AI: Test advanced processor functionality and error scenarios."""
    
    def setup_method(self):
        """AI: Setup test instance."""
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nexus_patterns = ["request.log*", "*.log"]
        self.processor = NexusLogProcessor(self.mock_settings, chunk_size=100, batch_size=100)
    
    def test_parse_log_invalid_timestamp_returns_none(self):
        """AI: Test parse_log with invalid timestamp format - covers lines 113-114."""
        # Valid Apache-style log line format but with invalid timestamp that triggers timestamp parsing error
        # Format: IP - user [timestamp] "METHOD path HTTP/version" status size1 size2 time "user-agent" [thread]
        valid_format_log = '127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /test HTTP/1.1" 200 1234 5678 89 "Mozilla" [thread]'
        
        # Mock the timestamp parsing to return None to trigger the specific error
        with patch.object(self.processor, '_parse_timestamp', return_value=None), \
             patch('builtins.print') as mock_print:
            
            result = self.processor.parse_log_line(valid_format_log, 1, "test.log")
            
            assert result is None
            # Should print parse error with timestamp format message
            mock_print.assert_called_once()
            assert "PARSE_ERROR" in mock_print.call_args[0][0]
            assert "Invalid timestamp format" in mock_print.call_args[0][0]
    
    def test_parse_log_invalid_status_code_returns_none(self):
        """AI: Test parse_log with invalid status code - covers line 119."""
        # Valid log line but with invalid status code
        invalid_status_log = '2025-05-29 12:34:56,123+0000 127.0.0.1 qtp123456789-42 "GET /test HTTP/1.1" invalid_status 1234 5678 89'
        
        # Mock _parse_status_code to return None (invalid status)
        with patch.object(self.processor, '_parse_status_code', return_value=None):
            result = self.processor.parse_log_line(invalid_status_log, 1, "test.log")
            
            assert result is None
    
    def test_parse_log_unexpected_exception_handling(self):
        """AI: Test parse_log with unexpected exception - covers lines 151-153."""
        valid_log = '2025-05-29 12:34:56,123+0000 127.0.0.1 qtp123456789-42 "GET /test HTTP/1.1" 200 1234 5678 89'
        
        # Mock the regex matching to succeed but cause an exception in the processing
        # This will trigger the exception handling in the try/except block
        with patch.object(self.processor, 'regex_patterns') as mock_patterns:
            # Create a mock pattern that matches but then raises an exception when accessing groups
            mock_pattern = Mock()
            mock_match = Mock()
            mock_match.groupdict.side_effect = RuntimeError("Unexpected error")
            mock_pattern.match.return_value = mock_match
            mock_patterns.__iter__ = Mock(return_value=iter([mock_pattern]))
            
            with patch('builtins.print') as mock_print:
                result = self.processor.parse_log_line(valid_log, 1, "test.log")
                
                assert result is None
                # Should print unexpected error
                mock_print.assert_called_once()
                assert "UNEXPECTED_ERROR" in mock_print.call_args[0][0]
                assert "Unexpected error" in mock_print.call_args[0][0]
    
    def test_parse_timestamp_apache_style_format(self):
        """AI: Test timestamp parsing for Apache-style format - covers lines 177-179."""
        apache_timestamp = "12/Jun/2025:09:11:00 +0000"
        
        result = self.processor._parse_timestamp(apache_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 12
        assert result.hour == 9
        assert result.minute == 11
        assert result.second == 0
    
    def test_parse_timestamp_nexus_style_with_comma(self):
        """AI: Test timestamp parsing for Nexus format with comma - covers lines 180-181."""
        nexus_timestamp = "2025-05-29 12:34:56,123+0000"
        
        result = self.processor._parse_timestamp(nexus_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 29
        assert result.hour == 12
        assert result.minute == 34
        assert result.second == 56
    
    def test_parse_timestamp_positive_timezone_format(self):
        """AI: Test timestamp parsing with positive timezone - covers lines 182-183."""
        timezone_timestamp = "2025-05-29 12:34:56+0400"
        
        result = self.processor._parse_timestamp(timezone_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 29
    
    def test_parse_timestamp_negative_timezone_format(self):
        """AI: Test timestamp parsing with negative timezone - covers lines 184-186."""
        negative_timezone_timestamp = "2025-05-29 12:34:56-0500"
        
        result = self.processor._parse_timestamp(negative_timezone_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 29
    
    def test_parse_timestamp_as_is_format(self):
        """AI: Test timestamp parsing as-is without timezone - covers lines 187-188."""
        simple_timestamp = "2025-05-29 12:34:56"
        
        result = self.processor._parse_timestamp(simple_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 29
    
    def test_parse_timestamp_invalid_format_returns_none(self):
        """AI: Test timestamp parsing with invalid format - covers lines 190-191."""
        invalid_timestamp = "not-a-valid-timestamp"
        
        result = self.processor._parse_timestamp(invalid_timestamp)
        
        assert result is None
    
    def test_parse_size_field_delegates_to_parent(self):
        """AI: Test deprecated _parse_size_field method - covers line 223."""
        # Test that the method delegates to parent
        with patch.object(self.processor.__class__.__bases__[0], '_parse_size_field', return_value=1234) as mock_parent:
            result = self.processor._parse_size_field("1234")
            
            assert result == 1234
            mock_parent.assert_called_once_with("1234")
    
    def test_get_supported_patterns_returns_settings_patterns(self):
        """AI: Test get_supported_patterns returns from settings."""
        patterns = self.processor.get_supported_patterns()
        
        assert patterns == ["request.log*", "*.log"]
        assert patterns is self.mock_settings.nexus_patterns


class TestNginxProcessorAdvanced:
    """AI: Test advanced Nginx processor functionality and error scenarios."""
    
    def setup_method(self):
        """AI: Setup test instance."""
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nginx_patterns = ["access.log*", "*.log"]
        self.processor = NginxLogProcessor(self.mock_settings, chunk_size=100, batch_size=100)
    
    def test_parse_log_invalid_status_code_returns_none(self):
        """AI: Test parse_log with invalid status code - covers line 121."""
        # Valid log line but with invalid status code
        invalid_status_log = '127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /test HTTP/1.1" invalid_status 1234 "-" "Mozilla/5.0"'
        
        # Mock _parse_status_code to return None (invalid status)
        with patch.object(self.processor, '_parse_status_code', return_value=None):
            result = self.processor.parse_log_line(invalid_status_log, 1, "test.log")
            
            assert result is None
    
    def test_parse_log_unexpected_exception_handling(self):
        """AI: Test parse_log with unexpected exception - covers lines 142-144."""
        valid_log = '127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /test HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        
        # Mock the regex matching to succeed but cause an exception in the processing
        # This will trigger the exception handling in the try/except block
        with patch.object(self.processor, 'regex_pattern') as mock_pattern:
            mock_match = Mock()
            mock_match.groupdict.side_effect = RuntimeError("Unexpected error")
            mock_pattern.match.return_value = mock_match
            
            with patch('builtins.print') as mock_print:
                result = self.processor.parse_log_line(valid_log, 1, "test.log")
                
                assert result is None
                # Should print unexpected error
                mock_print.assert_called_once()
                assert "UNEXPECTED_ERROR" in mock_print.call_args[0][0]
                assert "Unexpected error" in mock_print.call_args[0][0]
    
    def test_parse_request_field_json_rpc_request(self):
        """AI: Test parsing JSON-RPC style request - covers lines 179-180."""
        json_rpc_request = '{"method": "getData", "params": [], "id": 1}'
        
        method, path, version = self.processor._parse_request_field(json_rpc_request)
        
        assert method == "JSON-RPC"
        assert "method" in path
        assert version == "NON-HTTP"
    
    def test_parse_request_field_binary_data(self):
        """AI: Test parsing request with binary data - covers lines 181-183."""
        # Request with actual non-printable characters that doesn't parse as valid HTTP
        # Make it look like it could be 3 parts but the version is invalid, then check for binary
        binary_request = "GET /test" + chr(0) + chr(1) + chr(2) + "INVALID"
        
        method, path, version = self.processor._parse_request_field(binary_request)
        
        assert method == "BINARY-DATA"
        assert path == "[BINARY]"
        assert version == "NON-HTTP"
    
    def test_parse_request_field_malformed_request(self):
        """AI: Test parsing malformed request - covers lines 184-185."""
        malformed_request = "INVALID REQUEST FORMAT"
        
        method, path, version = self.processor._parse_request_field(malformed_request)
        
        assert method == "MALFORMED"
        assert "INVALID REQUEST FORMAT" in path
        assert version == "NON-HTTP"
    
    def test_parse_request_field_exception_handling(self):
        """AI: Test parsing request with exception - covers lines 186-188."""
        # Create a string that will cause an exception during the binary character check
        # by raising an exception in the any() loop with ord()
        with patch('builtins.any') as mock_any:
            mock_any.side_effect = Exception("Any function error")
            
            result = self.processor._parse_request_field("GET /test INVALID")
            
            method, path, version = result
            assert method == "PARSE-ERROR"
            assert "GET /test INVALID" in path
            assert version == "NON-HTTP"


class TestProcessorIntegration:
    """AI: Test advanced integration scenarios for processors."""
    
    def test_nexus_processor_with_database_operations(self):
        """AI: Test Nexus processor integration with database operations."""
        mock_settings = Mock(spec=Settings)
        mock_settings.nexus_patterns = ["*.log"]
        processor = NexusLogProcessor(mock_settings)
        
        # Mock database operations
        mock_db_ops = Mock(spec=DatabaseOperations)
        mock_nexus_ops = Mock()
        mock_nexus_ops.batch_insert = Mock()
        mock_db_ops.nexus = mock_nexus_ops
        
        batch_insert_method = processor.get_batch_insert_method(mock_db_ops)
        
        assert batch_insert_method is mock_nexus_ops.batch_insert
    
    def test_nexus_processor_get_table_model(self):
        """AI: Test Nexus processor table model retrieval."""
        mock_settings = Mock(spec=Settings)
        processor = NexusLogProcessor(mock_settings)
        
        model = processor.get_table_model()
        
        # Should import and return NexusLog model
        from app.database.models import NexusLog
        assert model is NexusLog
    
    def test_nginx_processor_with_database_operations(self):
        """AI: Test Nginx processor integration with database operations."""
        mock_settings = Mock(spec=Settings)
        mock_settings.nginx_patterns = ["*.log"]
        processor = NginxLogProcessor(mock_settings)
        
        # Mock database operations
        mock_db_ops = Mock(spec=DatabaseOperations)
        mock_nginx_ops = Mock()
        mock_nginx_ops.batch_insert = Mock()
        mock_db_ops.nginx = mock_nginx_ops
        
        batch_insert_method = processor.get_batch_insert_method(mock_db_ops)
        
        assert batch_insert_method is mock_nginx_ops.batch_insert
    
    def test_nginx_processor_get_supported_patterns(self):
        """AI: Test Nginx processor supported patterns."""
        mock_settings = Mock(spec=Settings)
        mock_settings.nginx_patterns = ["access.log*", "error.log*"]
        processor = NginxLogProcessor(mock_settings)
        
        patterns = processor.get_supported_patterns()
        
        assert patterns == ["access.log*", "error.log*"]
        assert patterns is mock_settings.nginx_patterns
    
    def test_nginx_processor_matches_target_pattern(self):
        """AI: Test Nginx processor pattern matching."""
        mock_settings = Mock(spec=Settings)
        mock_settings.nginx_patterns = ["access.log*"]
        processor = NginxLogProcessor(mock_settings)
        
        assert processor.matches_target_pattern("access.log")
        assert processor.matches_target_pattern("access.log.1")
        assert not processor.matches_target_pattern("error.log")


class TestProcessorErrorHandling:
    """AI: Test edge cases and error handling scenarios."""
    
    def test_nexus_processor_large_timestamp_variations(self):
        """AI: Test various timestamp edge cases in Nexus processor."""
        mock_settings = Mock(spec=Settings)
        processor = NexusLogProcessor(mock_settings)
        
        # Test timestamp with multiple dashes (negative timezone with date separators)
        complex_timestamp = "2025-12-31 23:59:59-1200"  # 4 dashes total
        result = processor._parse_timestamp(complex_timestamp)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31
    
    def test_nginx_processor_long_request_truncation(self):
        """AI: Test request field truncation for very long requests."""
        mock_settings = Mock(spec=Settings)
        processor = NginxLogProcessor(mock_settings)
        
        # Create a very long malformed request
        long_request = "MALFORMED " + "X" * 100 + " REQUEST"
        
        method, path, version = processor._parse_request_field(long_request)
        
        assert method == "MALFORMED"
        assert len(path) <= 53  # 50 chars + "..."
        assert path.endswith("...")
        assert version == "NON-HTTP"
    
    def test_processor_configuration_consistency(self):
        """AI: Test that processors maintain configuration consistency."""
        mock_settings = Mock(spec=Settings)
        mock_settings.nexus_patterns = ["nexus*.log"]
        mock_settings.nginx_patterns = ["nginx*.log"]
        
        nexus_processor = NexusLogProcessor(mock_settings)
        nginx_processor = NginxLogProcessor(mock_settings)
        
        # Both processors should reference the same settings instance
        assert nexus_processor.settings is mock_settings
        assert nginx_processor.settings is mock_settings
        
        # Pattern methods should return correct patterns
        assert nexus_processor.get_supported_patterns() == ["nexus*.log"]
        assert nginx_processor.get_supported_patterns() == ["nginx*.log"]
