"""
AI: Unit tests for Nexus log processor (Apache-style format only).

Tests the simplified NexusLogProcessor that handles only Apache-style
Nexus repository log format.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from app.processors.nexus_processor import NexusLogProcessor
from app.config import Settings


class TestNexusProcessor:
    """AI: Test Nexus log processing functionality with Apache-style format."""
    
    def setup_method(self):
        """AI: Set up test instance before each test."""
        # Create mock settings with required pattern configuration
        mock_settings = Mock(spec=Settings)
        mock_settings.nexus_patterns = ['request.log*', 'nexus_logs_*.tar']
        
        self.processor = NexusLogProcessor(mock_settings)
    
    def test_parse_apache_style_get_request(self):
        """AI: Test parsing Apache-style GET request log entry."""
        log_line = '10.0.0.1 - testuser [28/May/2025:14:30:45 +0000] "GET /repository/maven-public/org/springframework/spring-core/5.3.21/spring-core-5.3.21.jar HTTP/1.1" 200 1234567 152 89 "Maven/3.8.1" [qtp123456789-42]'
        
        result = self.processor.parse_log_line(log_line, 1, "test.log")
        
        assert result is not None
        assert result['ip_address'] == '10.0.0.1'
        assert result['remote_user'] == 'testuser'
        assert result['method'] == 'GET'
        assert result['path'] == '/repository/maven-public/org/springframework/spring-core/5.3.21/spring-core-5.3.21.jar'
        assert result['http_version'] == 'HTTP/1.1'
        assert result['status_code'] == 200
        assert result['response_size'] == 1234567
        assert result['request_size'] == 152
        assert result['processing_time_ms'] == 89
        assert result['user_agent'] == 'Maven/3.8.1'
        assert result['thread_info'] == 'qtp123456789-42'
        assert result['file_source'] == 'test.log'
        assert isinstance(result['timestamp'], datetime)
    
    def test_parse_apache_style_post_request(self):
        """AI: Test parsing Apache-style POST request log entry."""
        log_line = '192.168.1.100 - admin [28/May/2025:15:45:30 +0000] "POST /repository/maven-releases/com/example/artifact/1.0.0/artifact-1.0.0.jar HTTP/1.1" 201 2048576 512 234 "curl/7.68.0" [qtp987654321-15]'
        
        result = self.processor.parse_log_line(log_line, 1, "nexus.log")
        
        assert result is not None
        assert result['ip_address'] == '192.168.1.100'
        assert result['remote_user'] == 'admin'
        assert result['method'] == 'POST'
        assert result['path'] == '/repository/maven-releases/com/example/artifact/1.0.0/artifact-1.0.0.jar'
        assert result['status_code'] == 201
        assert result['response_size'] == 2048576
        assert result['request_size'] == 512
        assert result['processing_time_ms'] == 234
        assert result['user_agent'] == 'curl/7.68.0'
        assert result['thread_info'] == 'qtp987654321-15'
    
    def test_parse_with_anonymous_user(self):
        """AI: Test parsing log entry with anonymous user (dash)."""
        log_line = '172.16.0.50 - - [28/May/2025:16:00:15 +0000] "GET /repository/npm-proxy/@angular/core/-/core-12.2.0.tgz HTTP/1.1" 200 98765 64 45 "npm/8.1.0" [qtp456789123-8]'
        
        result = self.processor.parse_log_line(log_line, 1, "access.log")
        
        assert result is not None
        assert result['ip_address'] == '172.16.0.50'
        assert result['remote_user'] == '-'
        assert result['method'] == 'GET'
        assert result['path'] == '/repository/npm-proxy/@angular/core/-/core-12.2.0.tgz'
        assert result['status_code'] == 200
        assert result['user_agent'] == 'npm/8.1.0'
        assert result['thread_info'] == 'qtp456789123-8'
    
    def test_parse_with_complex_user_agent(self):
        """AI: Test parsing log entry with complex user agent string."""
        log_line = '10.1.1.1 - devuser [28/May/2025:17:30:00 +0000] "GET /repository/docker-proxy/v2/library/ubuntu/manifests/20.04 HTTP/1.1" 200 4567 128 67 "Docker-Client/20.10.7 (linux)" [qtp111222333-99]'
        
        result = self.processor.parse_log_line(log_line, 1, "docker.log")
        
        assert result is not None
        assert result['ip_address'] == '10.1.1.1'
        assert result['remote_user'] == 'devuser'
        assert result['method'] == 'GET'
        assert result['path'] == '/repository/docker-proxy/v2/library/ubuntu/manifests/20.04'
        assert result['status_code'] == 200
        assert result['response_size'] == 4567
        assert result['request_size'] == 128
        assert result['processing_time_ms'] == 67
        assert result['user_agent'] == 'Docker-Client/20.10.7 (linux)'
        assert result['thread_info'] == 'qtp111222333-99'
    
    def test_parse_head_request(self):
        """AI: Test parsing Apache-style HEAD request."""
        log_line = '203.0.113.42 - ciuser [28/May/2025:18:15:45 +0000] "HEAD /repository/maven-public/junit/junit/4.13.2/junit-4.13.2.pom HTTP/1.1" 200 0 32 12 "Jenkins/2.401.3" [qtp777888999-3]'
        
        result = self.processor.parse_log_line(log_line, 1, "ci.log")
        
        assert result is not None
        assert result['method'] == 'HEAD'
        assert result['status_code'] == 200
        assert result['response_size'] == 0  # HEAD requests typically have no body
        assert result['request_size'] == 32
        assert result['processing_time_ms'] == 12
        assert result['user_agent'] == 'Jenkins/2.401.3'
    
    def test_parse_put_request(self):
        """AI: Test parsing Apache-style PUT request."""
        log_line = '198.51.100.10 - publisher [28/May/2025:19:00:30 +0000] "PUT /repository/maven-releases/com/mycompany/myapp/2.1.0/myapp-2.1.0.jar HTTP/1.1" 201 15728640 1024 456 "Gradle/7.4.2" [qtp333444555-21]'
        
        result = self.processor.parse_log_line(log_line, 1, "upload.log")
        
        assert result is not None
        assert result['method'] == 'PUT'
        assert result['status_code'] == 201
        assert result['response_size'] == 15728640  # Large artifact upload
        assert result['request_size'] == 1024
        assert result['processing_time_ms'] == 456
        assert result['user_agent'] == 'Gradle/7.4.2'
    
    def test_parse_delete_request(self):
        """AI: Test parsing Apache-style DELETE request."""
        log_line = '172.20.0.100 - admin [28/May/2025:20:45:15 +0000] "DELETE /repository/maven-snapshots/com/test/snapshot/1.0-SNAPSHOT/snapshot-1.0-20250528.204515-1.jar HTTP/1.1" 204 0 0 89 "Nexus-Cleanup/3.38.1" [qtp666777888-7]'
        
        result = self.processor.parse_log_line(log_line, 1, "cleanup.log")
        
        assert result is not None
        assert result['method'] == 'DELETE'
        assert result['status_code'] == 204
        assert result['response_size'] == 0
        assert result['request_size'] == 0
        assert result['processing_time_ms'] == 89
        assert result['user_agent'] == 'Nexus-Cleanup/3.38.1'
    
    def test_parse_error_status_codes(self):
        """AI: Test parsing log entries with various error status codes."""
        test_cases = [
            ('10.0.0.1 - user [28/May/2025:21:00:00 +0000] "GET /repository/missing/path HTTP/1.1" 404 1024 64 25 "Browser/1.0" [qtp123-1]', 404),
            ('10.0.0.2 - user [28/May/2025:21:01:00 +0000] "GET /repository/forbidden HTTP/1.1" 403 512 32 15 "Browser/1.0" [qtp123-2]', 403),
            ('10.0.0.3 - user [28/May/2025:21:02:00 +0000] "POST /repository/error HTTP/1.1" 500 2048 128 500 "Browser/1.0" [qtp123-3]', 500),
        ]
        
        for log_line, expected_status in test_cases:
            result = self.processor.parse_log_line(log_line, 1, "error.log")
            assert result is not None
            assert result['status_code'] == expected_status
    
    def test_parse_timestamp_formats(self):
        """AI: Test parsing different timestamp formats in Apache logs."""
        log_line = '10.0.0.1 - user [28/May/2025:14:30:45 +0000] "GET /test HTTP/1.1" 200 1234 64 25 "Test" [qtp123-1]'
        
        result = self.processor.parse_log_line(log_line, 1, "timestamp.log")
        
        assert result is not None
        assert isinstance(result['timestamp'], datetime)
        assert result['timestamp'].day == 28
        assert result['timestamp'].month == 5
        assert result['timestamp'].year == 2025
        assert result['timestamp'].hour == 14
        assert result['timestamp'].minute == 30
        assert result['timestamp'].second == 45
    
    def test_parse_with_zero_sizes(self):
        """AI: Test parsing log entries with zero request/response sizes."""
        log_line = '10.0.0.1 - user [28/May/2025:22:00:00 +0000] "HEAD /repository/test HTTP/1.1" 200 0 0 5 "Test-Agent" [qtp999-1]'
        
        result = self.processor.parse_log_line(log_line, 1, "zero.log")
        
        assert result is not None
        assert result['response_size'] == 0
        assert result['request_size'] == 0
        assert result['processing_time_ms'] == 5
    
    def test_parse_malformed_log_returns_none(self):
        """AI: Test that malformed logs return None and handle gracefully."""
        malformed_logs = [
            'completely invalid log format',
            '10.0.0.1 incomplete log',
            'missing timestamp and everything else',
            '10.0.0.1 - user [invalid timestamp] "GET /test" 200',
            '',  # Empty line
        ]
        
        for log_line in malformed_logs:
            result = self.processor.parse_log_line(log_line, 1, "malformed.log")
            assert result is None
    
    def test_parse_with_special_characters_in_path(self):
        """AI: Test parsing paths with special characters and encoding."""
        log_line = '10.0.0.1 - user [28/May/2025:23:00:00 +0000] "GET /repository/npm/@angular%2Fcore/-/core-12.2.0.tgz HTTP/1.1" 200 54321 256 78 "npm/8.1.0" [qtp888-5]'
        
        result = self.processor.parse_log_line(log_line, 1, "special.log")
        
        assert result is not None
        assert result['path'] == '/repository/npm/@angular%2Fcore/-/core-12.2.0.tgz'
        assert result['status_code'] == 200
        assert result['response_size'] == 54321
    
    def test_parse_large_file_sizes(self):
        """AI: Test parsing log entries with large file sizes."""
        log_line = '10.0.0.1 - user [28/May/2025:23:30:00 +0000] "GET /repository/docker/large-image.tar HTTP/1.1" 200 1073741824 2048 15000 "Docker/20.10" [qtp777-9]'
        
        result = self.processor.parse_log_line(log_line, 1, "large.log")
        
        assert result is not None
        assert result['response_size'] == 1073741824  # 1GB
        assert result['request_size'] == 2048
        assert result['processing_time_ms'] == 15000  # 15 seconds
    
    def test_get_table_model(self):
        """AI: Test that processor returns correct table model."""
        from app.database.models import NexusLog
        
        model = self.processor.get_table_model()
        assert model == NexusLog
