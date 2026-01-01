"""
AI: Unit tests for log processing orchestrator.

Tests orchestration functionality:
- Processing workflow coordination
- Statistics tracking and reporting
- Error handling during processing
- Integration with processors and database
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.processing.orchestrator import LogProcessingOrchestrator, ProcessingStatistics
from app.config import Settings
from app.database.operations import DatabaseOperations


class TestProcessingStatistics:
    """AI: Test processing statistics tracking."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        self.stats = ProcessingStatistics()
    
    def test_initial_state(self):
        """AI: Test initial statistics state."""
        assert self.stats.nginx_stats['files_processed'] == 0
        assert self.stats.nginx_stats['lines_processed'] == 0
        assert self.stats.nginx_stats['entries_parsed'] == 0
        assert self.stats.nginx_stats['parse_errors'] == 0
        assert self.stats.nginx_stats['processing_time'] == 0.0
        
        assert self.stats.nexus_stats['files_processed'] == 0
        assert self.stats.overall_start_time is None
        assert self.stats.overall_end_time is None
    
    def test_processing_time_tracking(self):
        """AI: Test processing time measurement."""
        import time
        
        self.stats.start_processing()
        assert self.stats.overall_start_time is not None
        
        # Small delay
        time.sleep(0.01)
        
        self.stats.end_processing()
        assert self.stats.overall_end_time is not None
        assert self.stats.overall_end_time > self.stats.overall_start_time
        
        total_time = self.stats.get_total_processing_time()
        assert total_time > 0
        assert total_time < 1.0  # Should be very small
    
    def test_get_summary(self):
        """AI: Test comprehensive summary generation."""
        # Simulate some processing
        self.stats.nginx_stats.update({
            'files_processed': 5,
            'lines_processed': 1000,
            'entries_parsed': 950,
            'parse_errors': 50,
            'processing_time': 1.5
        })
        
        self.stats.nexus_stats.update({
            'files_processed': 3,
            'lines_processed': 750,
            'entries_parsed': 700,
            'parse_errors': 50,
            'processing_time': 1.2
        })
        
        self.stats.start_processing()
        self.stats.end_processing()
        
        summary = self.stats.get_summary()
        
        # Check totals
        assert summary['total_files'] == 8
        assert summary['total_lines'] == 1750
        assert summary['total_entries'] == 1650
        assert summary['total_errors'] == 100
        
        # Check individual stats preserved
        assert summary['nginx']['files_processed'] == 5
        assert summary['nexus']['files_processed'] == 3
        
        # Check timestamps
        assert summary['start_time'] is not None
        assert summary['end_time'] is not None


class TestLogProcessingOrchestrator:
    """AI: Test log processing orchestration."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        # Create mock settings
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.nginx_dir = "/test/nginx"
        self.mock_settings.nexus_dir = "/test/nexus"
        self.mock_settings.chunk_size = 100
        
        # Create mock database operations
        self.mock_db_ops = Mock(spec=DatabaseOperations)
        
        # Create orchestrator
        self.orchestrator = LogProcessingOrchestrator(
            self.mock_settings, 
            self.mock_db_ops
        )
    
    def test_initialization(self):
        """AI: Test orchestrator initialization."""
        assert self.orchestrator.settings == self.mock_settings
        assert self.orchestrator.db_ops == self.mock_db_ops
        assert self.orchestrator.file_discovery is not None
        assert self.orchestrator.statistics is not None
        assert self.orchestrator.nginx_processor is not None
        assert self.orchestrator.nexus_processor is not None
    
    @patch('app.processing.orchestrator.LogFileDiscovery')
    def test_process_nginx_logs_no_files(self, mock_discovery_class):
        """AI: Test nginx processing when no files are found."""
        # Mock empty file list
        mock_discovery = Mock()
        mock_discovery.discover_nginx_files.return_value = []
        self.orchestrator.file_discovery = mock_discovery
        
        stats = self.orchestrator._process_nginx_logs()
        
        assert stats['files_processed'] == 0
        assert stats['lines_processed'] == 0
        assert stats['entries_parsed'] == 0
        assert stats['parse_errors'] == 0
        assert stats['processing_time'] >= 0
    
    @patch('app.processing.orchestrator.create_file_iterator_from_path')
    def test_process_single_file_success(self, mock_file_iterator):
        """AI: Test successful single file processing."""
        # Mock file iterator
        mock_file_handle = Mock()
        mock_file_iterator.return_value = [("test_source", mock_file_handle)]
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.process_file_to_database.return_value = {
            'lines_processed': 100,
            'entries_inserted': 95,
            'parse_errors': 5
        }
        
        file_path = Path("/test/access.log")
        source_desc = "nginx:access.log"
        
        stats = self.orchestrator._process_single_file(
            file_path, source_desc, mock_processor, "nginx"
        )
        
        assert stats['lines_processed'] == 100
        assert stats['entries_parsed'] == 95
        assert stats['parse_errors'] == 5
        
        # Verify processor was called correctly
        mock_processor.process_file_to_database.assert_called_once_with(
            mock_file_handle, "test_source", self.mock_db_ops
        )
    
    @patch('app.processing.orchestrator.create_file_iterator_from_path')
    def test_process_single_file_error_handling(self, mock_file_iterator):
        """AI: Test error handling during single file processing."""
        # Mock file iterator to raise exception
        mock_file_iterator.side_effect = Exception("File read error")
        
        mock_processor = Mock()
        file_path = Path("/test/broken.log")
        source_desc = "nginx:broken.log"
        
        stats = self.orchestrator._process_single_file(
            file_path, source_desc, mock_processor, "nginx"
        )
        
        # Should handle error gracefully
        assert stats['lines_processed'] == 0
        assert stats['entries_parsed'] == 0
        assert stats['parse_errors'] == 1
    
    @patch('app.processing.orchestrator.LogFileDiscovery')
    def test_process_nginx_logs_with_files(self, mock_discovery_class):
        """AI: Test nginx processing with discovered files."""
        # Mock file discovery
        mock_discovery = Mock()
        test_files = [
            (Path("/test/access.log"), "nginx:access.log"),
            (Path("/test/access.log.1"), "nginx:access.log.1")
        ]
        mock_discovery.discover_nginx_files.return_value = test_files
        self.orchestrator.file_discovery = mock_discovery
        
        # Mock _process_single_file method
        with patch.object(self.orchestrator, '_process_single_file') as mock_process:
            mock_process.return_value = {
                'lines_processed': 50,
                'entries_parsed': 45,
                'parse_errors': 5
            }
            
            stats = self.orchestrator._process_nginx_logs()
            
            # Should process both files
            assert stats['files_processed'] == 2
            assert stats['lines_processed'] == 100  # 50 * 2
            assert stats['entries_parsed'] == 90   # 45 * 2
            assert stats['parse_errors'] == 10     # 5 * 2
            assert mock_process.call_count == 2
    
    @patch('app.processing.orchestrator.LogFileDiscovery')
    def test_process_all_logs_integration(self, mock_discovery_class):
        """AI: Test complete processing workflow integration."""
        # Mock file discovery
        mock_discovery = Mock()
        mock_discovery.discover_nginx_files.return_value = [
            (Path("/test/access.log"), "nginx:access.log")
        ]
        mock_discovery.discover_nexus_files.return_value = [
            (Path("/test/request.log"), "nexus:request.log")
        ]
        mock_discovery.cleanup_temp_dirs = Mock()
        self.orchestrator.file_discovery = mock_discovery
        
        # Mock single file processing
        with patch.object(self.orchestrator, '_process_single_file') as mock_process:
            mock_process.return_value = {
                'lines_processed': 100,
                'entries_parsed': 95,
                'parse_errors': 5
            }
            
            # Mock _print_processing_summary to avoid output during test
            with patch.object(self.orchestrator, '_print_processing_summary'):
                result_stats = self.orchestrator.process_all_logs()
            
            # Check that both nginx and nexus processing were called
            assert mock_process.call_count == 2
            
            # Check final statistics
            summary = result_stats.get_summary()
            assert summary['total_files'] == 2
            assert summary['total_lines'] == 200
            assert summary['total_entries'] == 190
            assert summary['total_errors'] == 10
            
            # Verify cleanup was called
            mock_discovery.cleanup_temp_dirs.assert_called_once()
    
    def test_print_processing_summary(self, capsys):
        """AI: Test processing summary output formatting."""
        # Setup some statistics
        self.orchestrator.statistics.nginx_stats.update({
            'files_processed': 3,
            'lines_processed': 500,
            'entries_parsed': 475,
            'parse_errors': 25,
            'processing_time': 1.5
        })

        self.orchestrator.statistics.nexus_stats.update({
            'files_processed': 2,
            'lines_processed': 300,
            'entries_parsed': 290,
            'parse_errors': 10,
            'processing_time': 1.0
        })

        self.orchestrator.statistics.start_processing()
        self.orchestrator.statistics.end_processing()

        # Temporarily override test mode detection to see INFO messages
        from app.utils.logger import logger
        original_level = logger.current_level
        from app.utils.logger import LogLevel
        logger.set_level(LogLevel.INFO)

        # Patch _is_test_environment to return False for this test
        original_method = logger._is_test_environment
        logger._is_test_environment = lambda: False

        try:
            # Call summary print
            self.orchestrator._print_processing_summary()

            # Capture output
            captured = capsys.readouterr()

            # Check key information is present (now in stderr, not stdout)
            assert "PHASE 2: Processing Summary" in captured.err
            assert "Total files processed: 5" in captured.err
            assert "Total lines processed: 800" in captured.err
            assert "Total entries parsed: 765" in captured.err
            assert "Total parse errors: 35" in captured.err
            assert "nginx logs:" in captured.err
            assert "Nexus logs:" in captured.err
            # Note: Performance section removed from implementation - timing shown per log type instead
        finally:
            # Restore original state
            logger.set_level(original_level)
            logger._is_test_environment = original_method
