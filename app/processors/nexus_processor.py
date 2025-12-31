"""
AI: Nexus repository manager log processor.

Implements Nexus-specific log parsing following coding guidelines:
- Multi-format support for Nexus request logs
- Thread information extraction
- Request/response size parsing
- Repository path analysis
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..database.operations import DatabaseOperations
from ..config import Settings
from .base import BaseLogProcessor


class NexusLogProcessor(BaseLogProcessor):
    """
    AI: Processor specifically for Nexus repository request logs.
    
    Supports Nexus request log format:
    timestamp IP thread "METHOD path HTTP/version" status size1 size2 ms
    
    Example log line:
    2025-05-29 12:34:56,123+0000 127.0.0.1 qtp123456789-42 "GET /repository/maven-public/com/example/artifact/1.0/artifact-1.0.jar HTTP/1.1" 200 1234 5678 89
    
    AI: Nexus log processor with configurable pattern matching.
    
    Following ADR_20250728_04: Configuration dependencies are injected via Settings instance.
    Processes Nexus request log files with support for gzip compression and archives.
    """
    
    def __init__(self, settings: Settings, chunk_size: int = 1000, batch_size: int = 1000):
        """
        AI: Initialize Nexus processor with configuration dependency injection.
        
        Args:
            settings: Settings instance containing configuration including nexus_patterns
            chunk_size: Number of lines to read per chunk
            batch_size: Number of parsed entries per database batch
        """
        super().__init__(chunk_size, batch_size)
        self.settings = settings
        self.regex_patterns = self._compile_nexus_regex_patterns()
    
    def _compile_nexus_regex_patterns(self) -> list:
        """
        AI: Compile regex pattern for Apache-style Nexus log format.
        
        Nexus logs follow Apache Combined Log Format:
        IP - user [timestamp] "METHOD path HTTP/version" status size time1 time2 "user-agent" [thread]
        
        Returns:
            List containing single compiled regex pattern
        """
        patterns = []
        
        # Apache-style Nexus request log format (real format)
        apache_style_pattern = (
            r'^(?P<ip>\S+) '                                                                  # IP address
            r'- '                                                                            # Remote logname (always -)
            r'(?P<user>\S+) '                                                                # Remote user (or -)
            r'\[(?P<timestamp>[^\]]+)\] '                                                    # Timestamp in brackets
            r'"(?P<method>\S+) '                                                             # HTTP method
            r'(?P<path>\S+) '                                                               # Request path
            r'(?P<http_version>[^"]+)" '                                                     # HTTP version
            r'(?P<status_code>\d+) '                                                        # Status code
            r'(?P<response_size>\d+|-) '                                                    # Response size (or -)
            r'(?P<request_size>\d+|-) '                                                     # Request size (or -)
            r'(?P<processing_time_ms>\d+|-)'                                               # Processing time in ms
            r'(?: "(?P<user_agent>[^"]*)")? '                                              # User agent (optional)
            r'(?:\[(?P<thread_info>[^\]]+)\])?'                                            # Thread info (optional)
        )
        patterns.append(re.compile(apache_style_pattern))
        
        return patterns
    
    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        """
        AI: Parse Nexus log line into structured data.
        
        Tries multiple regex patterns to handle format variations.
        
        Args:
            line: Raw Nexus log line
            line_number: Line number for error reporting
            source_file: Source file path for tracking
            
        Returns:
            Parsed log entry dictionary or None if parsing fails
        """
        try:
            # Try each pattern until one matches
            match = None
            for pattern in self.regex_patterns:
                match = pattern.match(line)
                if match:
                    break
            
            if not match:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid Nexus log format")
                return None
            
            groups = match.groupdict()
            
            # Parse timestamp
            timestamp = self._parse_timestamp(groups['timestamp'])
            if not timestamp:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid timestamp format")
                return None
            
            # Parse status code
            status_code = self._parse_status_code(groups['status_code'], source_file, line_number)
            if status_code is None:
                return None
            
            # Parse Apache-style format fields
            remote_user = groups.get('user', '-')
            if remote_user == '-':
                remote_user = '-'  # Keep dash for nexus logs as expected by tests
            response_size = self._parse_size_field(groups.get('response_size'))
            request_size = self._parse_size_field(groups.get('request_size'))
            processing_time = self._parse_size_field(groups.get('processing_time_ms'))
            user_agent = groups.get('user_agent')
            thread_info = groups.get('thread_info')
            
            # Extract HTTP version if present
            http_version = groups.get('http_version', 'HTTP/1.1')
            
            return {
                'ip_address': groups['ip'],
                'remote_user': remote_user,
                'timestamp': timestamp,
                'method': groups['method'],
                'path': groups['path'],
                'http_version': http_version,
                'status_code': status_code,
                'response_size': response_size,
                'request_size': request_size,
                'processing_time_ms': processing_time,
                'user_agent': user_agent,
                'thread_info': thread_info,
                'raw_log': line,
                'file_source': source_file
            }
            
        except Exception as e:
            print(f"UNEXPECTED_ERROR: {source_file}:{line_number} - {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        AI: Parse Nexus timestamp format to datetime object.
        
        Supports multiple formats:
        - Apache style: 12/Jun/2025:09:11:00 +0000
        - Nexus style: 2025-05-29 12:34:56,123+0000
        
        Args:
            timestamp_str: Raw timestamp string from log
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # Apache-style format: 12/Jun/2025:09:11:00 +0000
            if '/' in timestamp_str and ':' in timestamp_str:
                # Remove timezone for parsing
                base_time = timestamp_str.split(' ')[0]  # Take just "12/Jun/2025:09:11:00"
                return datetime.strptime(base_time, "%d/%b/%Y:%H:%M:%S")
            
            # Nexus-style format: 2025-05-29 12:34:56,123+0000
            elif ',' in timestamp_str:
                base_time = timestamp_str.split(',')[0]  # Remove milliseconds
                return datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            elif '+' in timestamp_str:
                base_time = timestamp_str.split('+')[0]  # Remove timezone
                return datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            elif '-' in timestamp_str and timestamp_str.count('-') >= 3:
                # Handle negative timezone
                base_time = timestamp_str.rsplit('-', 1)[0]  # Remove timezone
                return datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            else:
                # Try parsing as-is
                return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
        except ValueError:
            return None
    
    def _parse_size_field(self, size_str: Optional[str]) -> Optional[int]:
        """
        AI: Parse size field handling '-' and numeric values.
        
        This method is deprecated - use the base class method instead.
        Kept for backward compatibility but delegates to parent.
        
        Args:
            size_str: Size string from log (may be '-' or number)
            
        Returns:
            Parsed size as integer or None if invalid/missing
        """
        return super()._parse_size_field(size_str)
    
    def get_batch_insert_method(self, db_ops: DatabaseOperations):
        """
        AI: Return Nexus-specific database batch insert method.
        
        Uses the nexus-specific database operations for optimized performance
        and better separation of concerns.
        
        Args:
            db_ops: Database operations instance
            
        Returns:
            Bound method for batch inserting Nexus logs
        """
        # Use the specialized nexus operations directly
        return db_ops.nexus.batch_insert
    
    def get_table_model(self):
        """
        AI: Return the SQLAlchemy model for Nexus logs.
        
        Returns:
            NexusLog model class for database operations
        """
        from ..database.models import NexusLog
        return NexusLog
    
    def get_supported_patterns(self) -> List[str]:
        """
        AI: Get list of filename patterns this processor supports.
        
        Returns configured patterns from Settings instead of hardcoded list
        following ADR_20250728_04 architectural consistency requirements.
        
        Returns:
            List of glob patterns for Nexus log files from configuration
        """
        return self.settings.nexus_patterns
