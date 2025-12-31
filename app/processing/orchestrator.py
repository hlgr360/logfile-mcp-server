"""
AI: Phase 2 log processing integration layer.

Connects file discovery, processors, and database operations:
- Orchestrates processing workflow
- Progress reporting and statistics
- Error handling and recovery
- Memory-efficient batch processing
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

from ..config import Settings
from ..database.operations import DatabaseOperations
from ..file_discovery import LogFileDiscovery, create_file_iterator_from_path
from ..processors.nginx_processor import NginxLogProcessor
from ..processors.nexus_processor import NexusLogProcessor


class ProcessingStatistics:
    """
    AI: Track processing statistics across all log types.
    
    Provides detailed metrics for monitoring and reporting.
    """
    
    def __init__(self):
        self.nginx_stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'entries_parsed': 0,
            'parse_errors': 0,
            'processing_time': 0.0
        }
        self.nexus_stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'entries_parsed': 0,
            'parse_errors': 0,
            'processing_time': 0.0
        }
        self.overall_start_time = None
        self.overall_end_time = None
    
    def start_processing(self):
        """AI: Mark start of overall processing."""
        self.overall_start_time = time.time()
    
    def end_processing(self):
        """AI: Mark end of overall processing."""
        self.overall_end_time = time.time()
    
    def get_total_processing_time(self) -> float:
        """AI: Get total processing time in seconds."""
        if self.overall_start_time and self.overall_end_time:
            return self.overall_end_time - self.overall_start_time
        return 0.0
    
    def get_summary(self) -> Dict:
        """AI: Get comprehensive processing summary."""
        return {
            'nginx': self.nginx_stats.copy(),
            'nexus': self.nexus_stats.copy(),
            'total_files': self.nginx_stats['files_processed'] + self.nexus_stats['files_processed'],
            'total_lines': self.nginx_stats['lines_processed'] + self.nexus_stats['lines_processed'],
            'total_entries': self.nginx_stats['entries_parsed'] + self.nexus_stats['entries_parsed'],
            'total_errors': self.nginx_stats['parse_errors'] + self.nexus_stats['parse_errors'],
            'total_processing_time': self.get_total_processing_time(),
            'start_time': datetime.fromtimestamp(self.overall_start_time) if self.overall_start_time else None,
            'end_time': datetime.fromtimestamp(self.overall_end_time) if self.overall_end_time else None
        }


class LogProcessingOrchestrator:
    """
    AI: Orchestrates the complete log processing workflow.
    
    Coordinates file discovery, processing, and database storage
    following Phase 2 requirements and coding guidelines.
    """
    
    def __init__(self, settings: Settings, db_ops: DatabaseOperations):
        """
        AI: Initialize orchestrator with settings and database operations.
        
        Args:
            settings: Application configuration
            db_ops: Database operations instance
        """
        self.settings = settings
        self.db_ops = db_ops
        self.file_discovery = LogFileDiscovery(settings)
        self.statistics = ProcessingStatistics()
        
        # Initialize processors with settings dependency injection
        self.nginx_processor = NginxLogProcessor(
            settings=settings,
            chunk_size=settings.chunk_size,
            batch_size=1000
        )
        self.nexus_processor = NexusLogProcessor(
            settings=settings,
            chunk_size=settings.chunk_size,
            batch_size=1000
        )
    
    def process_all_logs(self) -> ProcessingStatistics:
        """
        AI: Process all configured log files and archives.
        
        Main entry point for Phase 2 processing workflow.
        
        Returns:
            Processing statistics for reporting
        """
        print("=" * 80)
        print("PHASE 2: Starting log processing workflow")
        print("=" * 80)
        
        self.statistics.start_processing()
        
        try:
            # Process nginx logs
            print("\n--- Processing nginx logs ---")
            nginx_stats = self._process_nginx_logs()
            self.statistics.nginx_stats.update(nginx_stats)
            
            # Process Nexus logs
            print("\n--- Processing Nexus logs ---")
            nexus_stats = self._process_nexus_logs()
            self.statistics.nexus_stats.update(nexus_stats)
            
            self.statistics.end_processing()
            
            # Print final summary
            self._print_processing_summary()
            
            return self.statistics
            
        except Exception as e:
            print(f"CRITICAL ERROR: Processing failed: {e}")
            self.statistics.end_processing()
            raise
        
        finally:
            # Cleanup temporary files
            self.file_discovery.cleanup_temp_dirs()
    
    def _process_nginx_logs(self) -> Dict:
        """
        AI: Process all discovered nginx log files.
        
        Returns:
            Processing statistics for nginx logs
        """
        return self._process_logs_by_type(
            "nginx", 
            self.file_discovery.discover_nginx_files, 
            self.nginx_processor
        )
    
    def _process_nexus_logs(self) -> Dict:
        """
        AI: Process all discovered Nexus log files.
        
        Returns:
            Processing statistics for Nexus logs
        """
        return self._process_logs_by_type(
            "nexus", 
            self.file_discovery.discover_nexus_files, 
            self.nexus_processor
        )
    
    def _process_logs_by_type(self, log_type: str, discovery_method, processor) -> Dict:
        """
        AI: Generic method for processing logs of a specific type.
        
        Reduces code duplication between nginx and nexus processing methods.
        
        Args:
            log_type: Type of logs being processed ("nginx" or "nexus")
            discovery_method: Method to discover files of this type
            processor: Processor instance for this log type
            
        Returns:
            Processing statistics for this log type
        """
        stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'entries_parsed': 0,
            'parse_errors': 0,
            'processing_time': 0.0
        }
        
        start_time = time.time()
        
        try:
            # Discover files
            log_files = list(discovery_method())
            print(f"Found {len(log_files)} {log_type} log files/archives")
            
            if not log_files:
                print(f"No {log_type} log files found")
                return stats
            
            # Process each discovered file
            for file_path, source_description in log_files:
                print(f"Processing {log_type} file: {source_description}")
                
                try:
                    file_stats = self._process_single_file(
                        file_path, source_description, processor, log_type
                    )
                    
                    # Update cumulative stats
                    stats['files_processed'] += 1
                    stats['lines_processed'] += file_stats['lines_processed']
                    stats['entries_parsed'] += file_stats['entries_parsed']
                    stats['parse_errors'] += file_stats['parse_errors']
                    
                    print(f"  Lines: {file_stats['lines_processed']}, "
                          f"Parsed: {file_stats['entries_parsed']}, "
                          f"Errors: {file_stats['parse_errors']}")
                    
                except Exception as e:
                    print(f"ERROR: Failed to process {log_type} file {source_description}: {e}")
                    stats['parse_errors'] += 1
            
        except Exception as e:
            print(f"ERROR: {log_type} log discovery failed: {e}")
        
        stats['processing_time'] = time.time() - start_time
        print(f"{log_type} processing completed in {stats['processing_time']:.2f} seconds")
        
        return stats
    
    def _process_single_file(self, file_path: Path, source_description: str, processor, log_type: str) -> Dict:
        """
        AI: Process a single log file using the specified processor.
        
        Args:
            file_path: Path to file to process
            source_description: Description for tracking
            processor: Log processor instance (nginx or nexus)
            log_type: Type of log for database routing
            
        Returns:
            Processing statistics for this file
        """
        file_stats = {
            'lines_processed': 0,
            'entries_parsed': 0,
            'parse_errors': 0
        }
        
        try:
            # Create file iterator
            file_iterator = create_file_iterator_from_path(file_path, source_description)
            
            # Process using processor's file_to_database method
            for source_desc, file_handle in file_iterator:
                stats = processor.process_file_to_database(
                    file_handle, source_desc, self.db_ops
                )
                
                file_stats['lines_processed'] += stats['lines_processed']
                file_stats['entries_parsed'] += stats['entries_inserted']
                file_stats['parse_errors'] += stats['parse_errors']
        
        except Exception as e:
            print(f"ERROR: File processing failed for {source_description}: {e}")
            file_stats['parse_errors'] += 1
        
        return file_stats
    
    def _print_processing_summary(self):
        """AI: Print comprehensive processing summary."""
        summary = self.statistics.get_summary()
        
        print("\n" + "=" * 80)
        print("PHASE 2: Processing Summary")
        print("=" * 80)
        
        # Overall statistics
        print(f"Total files processed: {summary['total_files']}")
        print(f"Total lines processed: {summary['total_lines']:,}")
        print(f"Total entries parsed: {summary['total_entries']:,}")
        print(f"Total parse errors: {summary['total_errors']:,}")
        print(f"Total processing time: {summary['total_processing_time']:.2f} seconds")
        
        if summary['total_lines'] > 0:
            success_rate = (summary['total_entries'] / summary['total_lines']) * 100
            print(f"Overall success rate: {success_rate:.1f}%")
        
        # nginx statistics
        print(f"\nnginx logs:")
        print(f"  Files: {summary['nginx']['files_processed']}")
        print(f"  Lines: {summary['nginx']['lines_processed']:,}")
        print(f"  Parsed: {summary['nginx']['entries_parsed']:,}")
        print(f"  Errors: {summary['nginx']['parse_errors']:,}")
        print(f"  Time: {summary['nginx']['processing_time']:.2f}s")
        
        # Nexus statistics
        print(f"\nNexus logs:")
        print(f"  Files: {summary['nexus']['files_processed']}")
        print(f"  Lines: {summary['nexus']['lines_processed']:,}")
        print(f"  Parsed: {summary['nexus']['entries_parsed']:,}")
        print(f"  Errors: {summary['nexus']['parse_errors']:,}")
        print(f"  Time: {summary['nexus']['processing_time']:.2f}s")
        
        # Performance metrics
        if summary['total_processing_time'] > 0:
            lines_per_second = summary['total_lines'] / summary['total_processing_time']
            entries_per_second = summary['total_entries'] / summary['total_processing_time']
            print(f"\nPerformance:")
            print(f"  Lines/second: {lines_per_second:,.0f}")
            print(f"  Entries/second: {entries_per_second:,.0f}")
        
        print("=" * 80)
