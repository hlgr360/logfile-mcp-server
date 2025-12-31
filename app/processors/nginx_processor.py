"""
AI: nginx access log processor with Common Log Format parsing.

Implements nginx-specific log parsing following coding guidelines:
- Regex-based parsing for nginx Common Log Format
- Comprehensive error handling with detailed reporting
- Timestamp parsing with timezone support
- Robust field extraction and validation
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..database.operations import DatabaseOperations
from ..config import Settings
from .base import BaseLogProcessor


class NginxLogProcessor(BaseLogProcessor):
    """
    AI: Processor specifically for nginx access log format.
    
    Supports nginx Common Log Format:
    IP - - [timestamp] "METHOD path HTTP/version" status size "referer" "user-agent"
    
    Example log line:
    127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /api/test HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
    
    AI: Nginx log processor with configurable pattern matching.
    
    Following ADR_20250728_04: Configuration dependencies are injected via Settings instance.
    Processes nginx access log files with support for gzip compression and archives.
    """
    
    def __init__(self, settings: Settings, chunk_size: int = 1000, batch_size: int = 1000):
        """
        AI: Initialize nginx processor with configuration dependency injection.
        
        Args:
            settings: Settings instance containing configuration including nginx_patterns
            chunk_size: Number of lines to read per chunk
            batch_size: Number of parsed entries per database batch
        """
        super().__init__(chunk_size, batch_size)
        self.settings = settings
        self.regex_pattern = self._compile_nginx_regex()
    
    def _compile_nginx_regex(self) -> re.Pattern:
        """
        AI: Compile regex pattern for nginx Combined Log Format.
        
        Pattern captures:
        - IP address
        - Remote user (usually -)
        - Timestamp with timezone
        - HTTP method, path, and version (or malformed request)
        - Status code
        - Response size
        - Referer
        - User agent
        
        Updated to handle malformed requests like SSH attempts, binary data, etc.
        
        Returns:
            Compiled regex pattern
        """
        pattern = (
            r'^(?P<ip>\S+) '                          # IP address
            r'(?P<remote_user>\S+) '                  # Remote user (usually -)
            r'(?P<auth_user>\S+) '                    # Auth user (usually -)
            r'\[(?P<timestamp>[^\]]+)\] '           # Timestamp in brackets
            r'"(?P<request>[^"]*)" '                  # Full request (may be malformed)
            r'(?P<status_code>\d+) '                 # Status code
            r'(?P<response_size>\S+) '               # Response size (- if none)
            r'"(?P<referer>[^"]*)" '                  # Referer
            r'"(?P<user_agent>[^"]*)"'                # User agent
        )
        return re.compile(pattern)
    
    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        """
        AI: Parse nginx log line into structured data.
        
        Handles both valid HTTP requests and malformed requests (SSH attempts, 
        binary data, etc.) by capturing the full request string and attempting
        to parse it as HTTP format.
        
        Args:
            line: Raw nginx log line
            line_number: Line number for error reporting
            source_file: Source file path for tracking
            
        Returns:
            Parsed log entry dictionary or None if parsing fails
        """
        try:
            match = self.regex_pattern.match(line)
            if not match:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid nginx log format")
                return None
            
            groups = match.groupdict()
            
            # Parse timestamp
            timestamp = self._parse_timestamp(groups['timestamp'])
            if not timestamp:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid timestamp format")
                return None
            
            # Parse the request field to extract method, path, and HTTP version
            method, path, http_version = self._parse_request_field(groups['request'])
            
            # Parse response size (handle '-' case)
            response_size = self._parse_size_field(groups['response_size'])
            
            # Parse status code
            status_code = self._parse_status_code(groups['status_code'], source_file, line_number)
            if status_code is None:
                return None
            
            # Clean up special fields
            remote_user = self._clean_optional_field(groups['remote_user'])
            referer = self._clean_optional_field(groups['referer'])
            
            return {
                'ip_address': groups['ip'],
                'remote_user': remote_user,
                'timestamp': timestamp,
                'method': method,
                'path': path,
                'http_version': http_version,
                'status_code': status_code,
                'response_size': response_size,
                'referer': referer,
                'user_agent': groups['user_agent'],
                'raw_log': line,
                'file_source': source_file
            }
            
        except Exception as e:
            print(f"UNEXPECTED_ERROR: {source_file}:{line_number} - {e}")
            return None
    
    def _parse_request_field(self, request_str: str) -> Tuple[str, str, str]:
        """
        AI: Parse the request field to extract HTTP method, path, and version.
        
        Handles both valid HTTP requests and malformed requests by attempting
        to parse as standard HTTP format and falling back to safe defaults
        for malformed requests.
        
        Args:
            request_str: The full request string from nginx log
            
        Returns:
            Tuple of (method, path, http_version). For malformed requests,
            returns safe defaults with the original request preserved in path.
        """
        try:
            # Try to parse as standard HTTP request: "METHOD /path HTTP/version"
            parts = request_str.split(' ', 2)
            
            if len(parts) == 3:
                method, path, version = parts
                # Validate this looks like HTTP
                if version.startswith('HTTP/'):
                    return method, path, version
            
            # Handle malformed requests (SSH, binary data, JSON, etc.)
            # These are legitimate log entries but not HTTP requests
            if request_str.startswith('SSH-'):
                return 'SSH-ATTEMPT', request_str, 'NON-HTTP'
            elif request_str.startswith('{') or 'method' in request_str:
                return 'JSON-RPC', request_str[:50] + '...' if len(request_str) > 50 else request_str, 'NON-HTTP'
            elif any(ord(c) < 32 or ord(c) > 126 for c in request_str):
                # Contains binary/non-printable characters
                return 'BINARY-DATA', '[BINARY]', 'NON-HTTP'
            else:
                # Other malformed requests
                return 'MALFORMED', request_str[:50] + '...' if len(request_str) > 50 else request_str, 'NON-HTTP'
                
        except Exception:
            # Fallback for any parsing errors
            return 'PARSE-ERROR', request_str[:50] + '...' if len(request_str) > 50 else request_str, 'NON-HTTP'
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        AI: Parse nginx timestamp format to datetime object.
        
        nginx uses format: 29/May/2025:00:00:09 -0400
        
        Args:
            timestamp_str: Raw timestamp string from log
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # nginx format: 29/May/2025:00:00:09 -0400
            # Convert to format Python can parse
            # Remove timezone for simplicity (store as UTC)
            if ' ' in timestamp_str:
                date_part = timestamp_str.split(' ')[0]
            else:
                date_part = timestamp_str
            
            # Parse the date part: 29/May/2025:00:00:09
            return datetime.strptime(date_part, "%d/%b/%Y:%H:%M:%S")
            
        except ValueError as e:
            return None
    
    def get_batch_insert_method(self, db_ops: DatabaseOperations):
        """
        AI: Return nginx-specific database batch insert method.
        
        Uses the nginx-specific database operations for optimized performance
        and better separation of concerns.
        
        Args:
            db_ops: Database operations instance
            
        Returns:
            Bound method for batch inserting nginx logs
        """
        # Use the specialized nginx operations directly
        return db_ops.nginx.batch_insert
    
    def get_supported_patterns(self) -> List[str]:
        """
        AI: Get list of filename patterns this processor supports.
        
        Returns configured patterns from Settings instead of hardcoded list
        following ADR_20250728_04 architectural consistency requirements.
        
        Returns:
            List of glob patterns for nginx log files from configuration
        """
        return self.settings.nginx_patterns
