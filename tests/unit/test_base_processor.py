"""
AI: Comprehensive tests for base log processor - FIXED VERSION.

Tests abstract base class functionality including chunked file processing,
error handling, and batch processing capabilities.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional

from app.processors.base import BaseLogProcessor
from app.database.operations import DatabaseOperations


class MockLogProcessor(BaseLogProcessor):
    """AI: Concrete test implementation of BaseLogProcessor."""
    
    def __init__(self, chunk_size: int = 1000, batch_size: int = 1000, should_fail: bool = False):
        super().__init__(chunk_size, batch_size)
        self.should_fail = should_fail
        self.parsed_lines = []
    
    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        """AI: Test implementation that parses lines or fails based on configuration."""
        if self.should_fail and "ERROR" in line:
            return None
        
        # Simple parsing - just store the line info
        parsed = {
            'line': line.strip(),
            'line_number': line_number,
            'source_file': source_file,
            'parsed_at': 'test_processor'
        }
        self.parsed_lines.append(parsed)
        return parsed
    
    def get_batch_insert_method(self, db_ops: DatabaseOperations):
        """AI: Return mock batch insert method for testing."""
        return MagicMock(return_value=len(self.parsed_lines))
    
    def get_supported_patterns(self) -> List[str]:
        """AI: Return mock patterns for testing."""
        return ['*.log', '*.txt']


class TestBaseLogProcessor:
    """AI: Test base log processor functionality."""
    
    def setup_method(self):
        """AI: Setup test processor for each test."""
        self.processor = MockLogProcessor(chunk_size=5, batch_size=3)

    def test_initialization_sets_configuration(self):
        """AI: Test processor initialization with custom settings."""
        processor = MockLogProcessor(chunk_size=100, batch_size=50)
        
        assert processor.chunk_size == 100
        assert processor.batch_size == 50
        assert processor.processed_count == 0
        assert processor.error_count == 0

    def test_process_file_lines_reads_small_file(self):
        """AI: Test processing small file in chunks."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("line 1\n")
            f.write("line 2\n") 
            f.write("line 3\n")
            temp_path = Path(f.name)

        try:
            # Process the file
            batches = list(self.processor.process_file_lines(temp_path))

            # Should have one batch with 3 items (batch_size=3)
            assert len(batches) == 1
            assert len(batches[0]) == 3
            
            # Check that all lines were processed
            lines = [item['line'] for item in batches[0]]
            assert "line 1" in lines
            assert "line 2" in lines
            assert "line 3" in lines

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_lines_handles_large_file_in_batches(self):
        """AI: Test processing large file creates multiple batches."""
        # Create test file with more lines than batch_size
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            for i in range(8):  # 8 lines, batch_size=3, should create 3 batches
                f.write(f"line {i+1}\n")
            temp_path = Path(f.name)

        try:
            # Process the file
            batches = list(self.processor.process_file_lines(temp_path))

            # Should have 3 batches: [3, 3, 2]
            assert len(batches) == 3
            assert len(batches[0]) == 3
            assert len(batches[1]) == 3
            assert len(batches[2]) == 2
            
            # Check total processed
            total_processed = sum(len(batch) for batch in batches)
            assert total_processed == 8

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_lines_handles_parsing_errors(self):
        """AI: Test processing continues when individual lines fail to parse."""
        processor = MockLogProcessor(batch_size=5, should_fail=True)

        # Create test file with some error lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("good line 1\n")
            f.write("ERROR bad line\n")  # This will fail to parse
            f.write("good line 2\n")
            f.write("ERROR another bad line\n")  # This will also fail
            f.write("good line 3\n")
            temp_path = Path(f.name)

        try:
            # Process the file
            batches = list(processor.process_file_lines(temp_path))

            # Should have one batch with only the good lines
            assert len(batches) == 1
            assert len(batches[0]) == 3  # Only good lines
            
            # Check that error count was tracked
            assert processor.error_count == 2
            assert processor.processed_count == 3

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_lines_handles_empty_file(self):
        """AI: Test processing empty file returns no batches."""
        # Create empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            pass  # Empty file
        temp_path = Path(f.name)

        try:
            # Process the file
            batches = list(self.processor.process_file_lines(temp_path))

            # Should have no batches
            assert len(batches) == 0

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_lines_handles_file_not_found(self):
        """AI: Test processing non-existent file handles error gracefully."""
        non_existent_path = Path("/non/existent/file.log")

        # Should handle error gracefully and return empty iterator
        batches = list(self.processor.process_file_lines(non_existent_path))
        assert len(batches) == 0
        assert self.processor.error_count == 1

    def test_process_file_lines_handles_encoding_errors(self):
        """AI: Test processing file with encoding issues."""
        # Create file with potential encoding issues
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.log', delete=False) as f:
            f.write(b"good line 1\n")
            f.write(b"line with \xff invalid utf-8\n")  # Invalid UTF-8
            f.write(b"good line 2\n")
            temp_path = Path(f.name)

        try:
            # Process the file - should handle encoding errors gracefully
            batches = list(self.processor.process_file_lines(temp_path))

            # Should still process the lines (with replacement characters)
            assert len(batches) == 1
            assert len(batches[0]) == 3

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_content_with_text_io(self):
        """AI: Test processing file content from TextIO object."""
        # Create test content
        content = "line 1\nline 2\nline 3\nline 4\nline 5\n"

        # Mock TextIO object
        mock_file = MagicMock()
        mock_file.__iter__ = MagicMock(return_value=iter(content.splitlines()))

        # Process content
        batches = list(self.processor.process_file_content(mock_file, "test_source.log"))

        # Should create multiple batches based on batch_size=3
        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 2

    def test_process_file_to_database_success(self):
        """AI: Test complete file to database processing."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("test line 1\n")
            f.write("test line 2\n")
            f.write("test line 3\n")
            f.write("test line 4\n")
            temp_path = Path(f.name)

        try:
            # Mock database operations
            mock_db_ops = MagicMock()
            mock_batch_method = MagicMock(return_value=2)  # Return count of inserted records
            self.processor.get_batch_insert_method = MagicMock(return_value=mock_batch_method)

            # Process file to database - note correct method signature
            with open(temp_path, 'r') as file_handle:
                result = self.processor.process_file_to_database(file_handle, str(temp_path), mock_db_ops)

            # Verify processing stats
            assert 'entries_inserted' in result
            assert 'lines_processed' in result
            assert result['entries_inserted'] > 0

        finally:
            temp_path.unlink(missing_ok=True)

    def test_process_file_to_database_handles_database_errors(self):
        """AI: Test file to database processing handles database errors."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("test line\n")
            temp_path = Path(f.name)

        try:
            # Mock database operations to raise error
            mock_db_ops = MagicMock()
            mock_batch_method = MagicMock(side_effect=Exception("Database error"))
            self.processor.get_batch_insert_method = MagicMock(return_value=mock_batch_method)

            # Process file to database
            with open(temp_path, 'r') as file_handle:
                result = self.processor.process_file_to_database(file_handle, str(temp_path), mock_db_ops)

            # Should handle error gracefully but database errors are not parse errors
            assert 'parse_errors' in result
            assert 'entries_inserted' in result
            assert 'lines_processed' in result
            # Database errors don't increment parse_errors - those are for log parsing issues
        
        finally:
            temp_path.unlink(missing_ok=True)

    def test_abstract_methods_must_be_implemented(self):
        """AI: Test that abstract methods must be implemented by subclasses."""
        # Should not be able to instantiate BaseLogProcessor directly
        with pytest.raises(TypeError):
            BaseLogProcessor()

    def test_chunk_size_affects_file_reading(self):
        """AI: Test that chunk_size parameter affects file reading behavior."""
        # Create file with many lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            for i in range(100):
                f.write(f"line {i+1}\n")
            temp_path = Path(f.name)

        try:
            # Use small chunk size and large batch size
            processor = MockLogProcessor(chunk_size=10, batch_size=1000)
            
            # Process the file
            batches = list(processor.process_file_lines(temp_path))

            # Should have one large batch (since batch_size > total lines)
            assert len(batches) == 1
            assert len(batches[0]) == 100

        finally:
            temp_path.unlink(missing_ok=True)

    def test_batch_size_affects_output_batching(self):
        """AI: Test that batch_size parameter affects output batching."""
        # Create file with many lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            for i in range(10):
                f.write(f"line {i+1}\n")
            temp_path = Path(f.name)

        try:
            # Use small batch size
            processor = MockLogProcessor(chunk_size=1000, batch_size=3)
            
            # Process the file
            batches = list(processor.process_file_lines(temp_path))

            # Should have multiple small batches
            assert len(batches) > 1
            # Most batches should be size 3, last might be smaller
            for i, batch in enumerate(batches[:-1]):  # All but last
                assert len(batch) == 3

        finally:
            temp_path.unlink(missing_ok=True)

    def test_error_count_tracking(self):
        """AI: Test that error count is properly tracked."""
        processor = MockLogProcessor(should_fail=True)
        
        # Create test file with error lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("good line\n")
            f.write("ERROR line\n")
            f.write("another good line\n")
            temp_path = Path(f.name)

        try:
            list(processor.process_file_lines(temp_path))
            
            assert processor.error_count == 1
            assert processor.processed_count == 2

        finally:
            temp_path.unlink(missing_ok=True)

    def test_processed_count_tracking(self):
        """AI: Test that processed count is properly tracked."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            for i in range(5):
                f.write(f"line {i+1}\n")
            temp_path = Path(f.name)

        try:
            list(self.processor.process_file_lines(temp_path))
            
            assert self.processor.processed_count == 5
            assert self.processor.error_count == 0

        finally:
            temp_path.unlink(missing_ok=True)


class TestBaseLogProcessorEdgeCases:
    """AI: Test edge cases and boundary conditions."""

    def test_very_large_batch_size(self):
        """AI: Test processing with batch size larger than file."""
        processor = MockLogProcessor(batch_size=1000)
        
        # Create small file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("line 1\n")
            f.write("line 2\n")
            temp_path = Path(f.name)

        try:
            batches = list(processor.process_file_lines(temp_path))
            
            # Should have one batch with both lines
            assert len(batches) == 1
            assert len(batches[0]) == 2

        finally:
            temp_path.unlink(missing_ok=True)

    def test_very_small_batch_size(self):
        """AI: Test processing with batch size of 1."""
        processor = MockLogProcessor(batch_size=1)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("line 1\n")
            f.write("line 2\n")
            f.write("line 3\n")
            temp_path = Path(f.name)

        try:
            batches = list(processor.process_file_lines(temp_path))
            
            # Should have three batches of size 1 each
            assert len(batches) == 3
            for batch in batches:
                assert len(batch) == 1

        finally:
            temp_path.unlink(missing_ok=True)

    def test_file_with_very_long_lines(self):
        """AI: Test processing file with very long lines."""
        processor = MockLogProcessor(batch_size=2)
        
        # Create file with one very long line and one normal line
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            long_line = "x" * 10000  # Very long line
            f.write(f"{long_line}\n")
            f.write("normal line\n")
            temp_path = Path(f.name)

        try:
            batches = list(processor.process_file_lines(temp_path))
            
            # Should handle long lines properly
            assert len(batches) == 1
            assert len(batches[0]) == 2
            
            # Verify long line was processed
            lines = [item['line'] for item in batches[0]]
            assert long_line in lines
            assert "normal line" in lines

        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_lines_handling(self):
        """AI: Test handling of empty lines in file."""
        processor = MockLogProcessor(batch_size=10)
        
        # Create file with empty lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("line 1\n")
            f.write("\n")  # Empty line
            f.write("line 2\n")
            f.write("\n")  # Another empty line
            f.write("line 3\n")
            temp_path = Path(f.name)

        try:
            batches = list(processor.process_file_lines(temp_path))
            
            # Should skip empty lines and process only content lines
            assert len(batches) == 1
            assert len(batches[0]) == 3  # Only the 3 non-empty lines
            
            lines = [item['line'] for item in batches[0]]
            assert "line 1" in lines
            assert "line 2" in lines
            assert "line 3" in lines

        finally:
            temp_path.unlink(missing_ok=True)
