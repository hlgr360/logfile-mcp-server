"""
AI: Base log processor with memory-efficient chunked processing.

Provides abstract base class for log file processors following coding guidelines:
- Chunked file reading for memory efficiency
- Error handling and reporting
- Batch processing capabilities
- Progress tracking for large files
"""

import re
import logging
import fnmatch
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, TextIO, Tuple

from ..database.operations import DatabaseOperations
from ..utils.logger import logger

logger = logging.getLogger(__name__)


class BaseLogProcessor(ABC):
    """
    AI: Abstract base class for log file processors.
    
    Provides common functionality for parsing log files including:
    - Chunked file reading for memory efficiency
    - Error handling and reporting
    - Batch processing capabilities
    - Progress tracking
    
    Subclasses must implement:
    - parse_log_line(): Parse individual log entries
    - get_batch_insert_method(): Return appropriate database method
    
    Attributes:
        chunk_size: Number of lines to read per chunk (default: 1000)
        batch_size: Number of entries to process in batches (default: 1000)
        error_count: Running count of parsing errors
    """
    
    def __init__(self, chunk_size: int = 1000, batch_size: int = 1000):
        """
        AI: Initialize base processor with configuration.
        
        Args:
            chunk_size: Number of lines to read per chunk
            batch_size: Number of parsed entries per database batch
        """
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.error_count = 0
        self.processed_count = 0
    
    @abstractmethod
    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        """
        AI: Parse individual log line into structured data.
        
        Args:
            line: Raw log line to parse
            line_number: Line number for error reporting
            source_file: Source file path for tracking
            
        Returns:
            Parsed log entry as dictionary, or None if parsing fails
        """
        pass
    
    @abstractmethod
    def get_batch_insert_method(self, db_ops: DatabaseOperations):
        """
        AI: Return the appropriate database batch insert method.
        
        Args:
            db_ops: Database operations instance
            
        Returns:
            Callable method for batch insertion
        """
        pass
    
    def process_file_lines(self, file_path: Path) -> Iterator[List[Dict]]:
        """
        AI: Process file in line-based chunks for memory efficiency.
        
        Reads file in chunks of lines rather than bytes to ensure
        complete log entries are processed.
        
        Args:
            file_path: Path to log file to process
            
        Yields:
            Batches of parsed log entries
        """
        batch = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines_read = 0
                
                while True:
                    # Read chunk_size lines at once
                    chunk_lines = []
                    for _ in range(self.chunk_size):
                        line = f.readline()
                        if not line:  # EOF
                            break
                        chunk_lines.append(line.rstrip('\\n\\r'))
                    
                    if not chunk_lines:
                        break
                    
                    # Process lines in this chunk
                    for line in chunk_lines:
                        lines_read += 1
                        if not line.strip():  # Skip empty lines
                            continue
                            
                        parsed = self.parse_log_line(line, lines_read, str(file_path))
                        if parsed:
                            batch.append(parsed)
                            self.processed_count += 1
                        else:
                            self.error_count += 1
                        
                        # Yield batch when it reaches batch_size
                        if len(batch) >= self.batch_size:
                            yield batch
                            batch = []
                
                # Yield final batch if it has entries
                if batch:
                    yield batch
                    
        except Exception as e:
            logger.error("ERROR: Failed to process file {file_path}: {e}")
            self.error_count += 1
    
    def process_file_content(self, file_obj: TextIO, source_name: str) -> Iterator[List[Dict]]:
        """
        AI: Process file content from file object (for archive extraction).
        
        Args:
            file_obj: Open file object to read from
            source_name: Source name for tracking (e.g., "archive.tar->log.txt")
            
        Yields:
            Batches of parsed log entries
        """
        batch = []
        line_number = 0
        
        try:
            lines_buffer = []
            
            # Read in chunks of lines
            for line in file_obj:
                line_number += 1
                line = line.rstrip('\\n\\r')
                
                if not line.strip():  # Skip empty lines
                    continue
                
                lines_buffer.append((line, line_number))
                
                # Process when buffer reaches chunk_size
                if len(lines_buffer) >= self.chunk_size:
                    for buffered_line, line_num in lines_buffer:
                        parsed = self.parse_log_line(buffered_line, line_num, source_name)
                        if parsed:
                            batch.append(parsed)
                            self.processed_count += 1
                        else:
                            self.error_count += 1
                        
                        # Yield batch when it reaches batch_size
                        if len(batch) >= self.batch_size:
                            yield batch
                            batch = []
                    
                    lines_buffer = []
            
            # Process remaining lines in buffer
            for buffered_line, line_num in lines_buffer:
                parsed = self.parse_log_line(buffered_line, line_num, source_name)
                if parsed:
                    batch.append(parsed)
                    self.processed_count += 1
                else:
                    self.error_count += 1
            
            # Yield final batch if it has entries
            if batch:
                yield batch
                
        except Exception as e:
            logger.error("ERROR: Failed to process file content from {source_name}: {e}")
            self.error_count += 1
    
    def process_file_to_database(self, file_handle, source_description: str, db_ops: DatabaseOperations) -> Dict:
        """
        AI: Process entire file and store entries in database.
        
        This method handles the complete processing workflow:
        1. Process file content from file handle for memory efficiency
        2. Use processor-specific batch insertion
        3. Return processing statistics
        
        Args:
            file_handle: Open file handle to process
            source_description: Description/path of source file
            db_ops: Database operations instance
            
        Returns:
            Dict with processing statistics
        """
        stats = {
            'lines_processed': 0,
            'entries_inserted': 0,
            'parse_errors': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'file_path': source_description
        }

        batch_insert_method = self.get_batch_insert_method(db_ops)
        
        # Reset counters to track this specific file
        initial_processed = self.processed_count
        initial_errors = self.error_count
        
        try:
            # Process file content from handle in chunks
            for entries_batch in self.process_file_content(file_handle, source_description):
                if entries_batch:
                    # Perform batch insert - call the method on the db_ops instance
                    batch_insert_method(entries_batch)
                    stats['entries_inserted'] += len(entries_batch)
                
        except Exception as e:
            logger.error(f"Error processing file {source_description}: {e}")
            # Database errors should be tracked as general processing errors, not parse errors
            # The parse errors are already tracked by the processor's error_count
        
        # Calculate final stats based on processor counters  
        final_entries = self.processed_count - initial_processed
        final_errors = self.error_count - initial_errors
        
        stats['entries_inserted'] = final_entries
        stats['parse_errors'] = final_errors  
        stats['lines_processed'] = final_entries + final_errors
            
        stats['end_time'] = datetime.now()
        return stats
    
    def get_processing_stats(self) -> Dict:
        """
        AI: Get current processing statistics.
        
        Returns:
            Dictionary with processing metrics
        """
        return {
            "processed_entries": self.processed_count,
            "parsing_errors": self.error_count,
            "success_rate": (
                (self.processed_count / (self.processed_count + self.error_count))
                if (self.processed_count + self.error_count) > 0 else 1.0
            )
        }

    # Common utility methods for reducing code duplication
    
    def _parse_size_field(self, size_str: Optional[str]) -> Optional[int]:
        """
        AI: Parse size field handling '-' and numeric values.
        
        Common utility for parsing size fields in log formats.
        
        Args:
            size_str: Size string from log (may be '-' or number)
            
        Returns:
            Parsed size as integer or None if invalid/missing
        """
        if not size_str or size_str == '-':
            return None
        
        try:
            return int(size_str)
        except ValueError:
            return None

    def _parse_status_code(self, status_str: str, source_file: str, line_number: int) -> Optional[int]:
        """
        AI: Parse HTTP status code with error reporting.
        
        Args:
            status_str: Status code string from log
            source_file: Source file for error reporting
            line_number: Line number for error reporting
            
        Returns:
            Parsed status code or None if invalid
        """
        try:
            return int(status_str)
        except ValueError:
            logger.error("PARSE_ERROR: %s:%d - Invalid status code: {status_str}", source_file, line_number)
            return None

    def _clean_optional_field(self, field_value: str, default_marker: str = '-') -> Optional[str]:
        """
        AI: Clean optional field, returning None for default markers.
        
        Args:
            field_value: Field value from log
            default_marker: Marker indicating no value (default: '-')
            
        Returns:
            Cleaned field value or None if default marker
        """
        return None if field_value == default_marker else field_value

    def matches_target_pattern(self, filename: str) -> bool:
        """
        AI: Check if filename matches configured log patterns.
        
        Uses patterns from Settings configuration following ADR_20250728_04.
        Subclasses should override get_supported_patterns() to provide patterns.
        
        Args:
            filename: Name of file to check
            
        Returns:
            True if file matches any configured pattern
        """
        patterns = self.get_supported_patterns()
        for pattern in patterns:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        return False

    @abstractmethod
    def get_supported_patterns(self) -> List[str]:
        """
        AI: Get list of filename patterns this processor supports.
        
        Returns:
            List of glob patterns for log files from configuration
        """
        pass
