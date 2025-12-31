"""
AI: File discovery system for log analysis application.

Implements file finding with pattern matching and archive support:
- Recursive directory scanning
- Glob pattern matching
- Archive file detection
- Nested archive depth limits
- Memory-efficient file iteration
"""

import fnmatch
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Iterator, List, Set, Tuple, TextIO
import tempfile

from ..config import Settings


class LogFileDiscovery:
    """
    AI: Discovers log files matching configured patterns in directories and archives.
    
    Supports:
    - Recursive directory scanning
    - Multiple file patterns per processor
    - Archive extraction (tar, tar.gz, zip)
    - Nested archive processing with depth limits
    - Memory-efficient file iteration
    """
    
    def __init__(self, settings: Settings, max_archive_depth: int = 3):
        """
        AI: Initialize file discovery with configuration.
        
        Args:
            settings: Application settings with directories and patterns
            max_archive_depth: Maximum depth for nested archive extraction
        """
        self.settings = settings
        self.max_archive_depth = max_archive_depth
        self._temp_dirs: List[str] = []  # Track temp dirs for cleanup
    
    def discover_nginx_files(self) -> Iterator[Tuple[Path, str]]:
        """
        AI: Discover nginx log files in configured directory.
        
        Yields:
            Tuple of (file_path, source_description) for each nginx log file
        """
        nginx_patterns = self._get_nginx_patterns()
        yield from self._discover_files_by_patterns(
            Path(self.settings.nginx_dir),
            nginx_patterns,
            "nginx"
        )
    
    def discover_nexus_files(self) -> Iterator[Tuple[Path, str]]:
        """
        AI: Discover Nexus log files in configured directory.
        
        Yields:
            Tuple of (file_path, source_description) for each Nexus log file
        """
        nexus_patterns = self._get_nexus_patterns()
        yield from self._discover_files_by_patterns(
            Path(self.settings.nexus_dir),
            nexus_patterns,
            "nexus"
        )
    
    def _get_nginx_patterns(self) -> List[str]:
        """AI: Get nginx filename patterns from configuration."""
        return [p.strip() for p in self.settings.nginx_pattern.split(',')]
    
    def _get_nexus_patterns(self) -> List[str]:
        """AI: Get Nexus filename patterns from configuration."""
        return [p.strip() for p in self.settings.nexus_pattern.split(',')]
    
    def _discover_files_by_patterns(self, base_dir: Path, patterns: List[str], log_type: str) -> Iterator[Tuple[Path, str]]:
        """
        AI: Discover files matching patterns in directory tree.
        
        Args:
            base_dir: Base directory to search
            patterns: List of glob patterns to match
            log_type: Type of logs for source tracking
            
        Yields:
            Tuple of (file_path, source_description) for matching files
        """
        if not base_dir.exists():
            print(f"WARNING: {log_type} directory does not exist: {base_dir}")
            return
        
        if not base_dir.is_dir():
            print(f"WARNING: {log_type} path is not a directory: {base_dir}")
            return
        
        print(f"Scanning {log_type} directory: {base_dir}")
        
        # Track processed files to avoid duplicates
        processed_files: Set[str] = set()
        
        # Walk directory tree
        for root, dirs, files in os.walk(base_dir):
            root_path = Path(root)
            
            # Check each file against patterns
            for filename in files:
                file_path = root_path / filename
                
                # Avoid processing same file multiple times
                file_key = str(file_path.resolve())
                if file_key in processed_files:
                    continue
                
                # Check if file matches any pattern
                if self._matches_patterns(filename, patterns):
                    processed_files.add(file_key)
                    
                    if self._is_archive_file(file_path):
                        # Process archive contents
                        yield from self._process_archive_recursive(
                            file_path, patterns, log_type, depth=0
                        )
                    else:
                        # Direct file match
                        source_desc = f"{log_type}:{file_path.name}"
                        yield (file_path, source_desc)
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """
        AI: Check if filename matches any of the provided patterns.
        
        Args:
            filename: Name of file to check
            patterns: List of glob patterns
            
        Returns:
            True if filename matches at least one pattern
        """
        return any(fnmatch.fnmatch(filename.lower(), pattern.lower()) for pattern in patterns)
    
    def _is_archive_file(self, file_path: Path) -> bool:
        """
        AI: Check if file is a supported archive format.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is a supported archive
        """
        suffix = file_path.suffix.lower()
        suffixes = ''.join(file_path.suffixes).lower()
        
        return (
            suffix in ['.tar', '.zip', '.gz'] or
            suffixes in ['.tar.gz', '.tar.bz2']
        )
    
    def _process_archive_recursive(self, archive_path: Path, patterns: List[str], log_type: str, depth: int) -> Iterator[Tuple[Path, str]]:
        """
        AI: Process archive recursively with depth limits.
        
        Args:
            archive_path: Path to archive file
            patterns: Patterns to match within archive
            log_type: Type of logs for source tracking
            depth: Current nesting depth
            
        Yields:
            Tuple of (extracted_file_path, source_description) for matching files
        """
        if depth >= self.max_archive_depth:
            print(f"WARNING: Maximum archive depth ({self.max_archive_depth}) reached for {archive_path}")
            return
        
        print(f"Processing archive (depth {depth}): {archive_path}")
        
        try:
            # Create temporary directory for extraction
            temp_dir = tempfile.mkdtemp(prefix=f"logminer_archive_{depth}_")
            self._temp_dirs.append(temp_dir)
            temp_path = Path(temp_dir)
            
            # Extract archive based on type
            if self._extract_archive(archive_path, temp_path):
                # Process extracted contents
                yield from self._process_extracted_contents(
                    temp_path, patterns, log_type, archive_path.name, depth
                )
            
        except Exception as e:
            print(f"ERROR: Failed to process archive {archive_path}: {e}")
    
    def _extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """
        AI: Extract archive to temporary directory.
        
        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to
            
        Returns:
            True if extraction succeeded, False otherwise
        """
        try:
            suffixes = ''.join(archive_path.suffixes).lower()
            
            if suffixes in ['.tar.gz', '.tar.bz2'] or archive_path.suffix == '.tar':
                # Handle tar archives
                with tarfile.open(archive_path, 'r:*') as tar:
                    # Extract safely, checking for path traversal
                    for member in tar.getmembers():
                        if self._is_safe_path(member.name):
                            tar.extract(member, extract_to)
                        else:
                            print(f"WARNING: Unsafe path in archive: {member.name}")
                return True
                
            elif archive_path.suffix == '.zip':
                # Handle zip archives
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    for member in zip_file.namelist():
                        if self._is_safe_path(member):
                            zip_file.extract(member, extract_to)
                        else:
                            print(f"WARNING: Unsafe path in archive: {member}")
                return True
                
            elif archive_path.suffix == '.gz' and not archive_path.name.endswith('.tar.gz'):
                # Handle single gzip files
                import gzip
                import shutil
                
                # Create output filename by removing .gz extension
                output_name = archive_path.stem
                output_path = extract_to / output_name
                
                with gzip.open(archive_path, 'rb') as gz_file:
                    with open(output_path, 'wb') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                return True
                
            else:
                print(f"WARNING: Unsupported archive format: {archive_path}")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to extract {archive_path}: {e}")
            return False
    
    def _is_safe_path(self, path: str) -> bool:
        """
        AI: Check if extracted path is safe (no directory traversal).
        
        Args:
            path: Path from archive member
            
        Returns:
            True if path is safe to extract
        """
        return not (
            os.path.isabs(path) or
            '..' in path or
            path.startswith('/') or
            '\\' in path.replace('\\\\', '')  # Allow escaped backslashes
        )
    
    def _process_extracted_contents(self, extract_path: Path, patterns: List[str], log_type: str, archive_name: str, depth: int) -> Iterator[Tuple[Path, str]]:
        """
        AI: Process contents of extracted archive.
        
        Args:
            extract_path: Path where archive was extracted
            patterns: Patterns to match
            log_type: Type of logs for source tracking
            archive_name: Original archive filename
            depth: Current nesting depth
            
        Yields:
            Tuple of (file_path, source_description) for matching files
        """
        # Walk extracted directory
        for root, dirs, files in os.walk(extract_path):
            root_path = Path(root)
            
            for filename in files:
                file_path = root_path / filename
                
                if self._matches_patterns(filename, patterns):
                    if self._is_archive_file(file_path):
                        # Nested archive - process recursively
                        nested_source = f"{archive_name}->{filename}"
                        yield from self._process_archive_recursive(
                            file_path, patterns, log_type, depth + 1
                        )
                    else:
                        # Direct file match
                        relative_path = file_path.relative_to(extract_path)
                        source_desc = f"{log_type}:{archive_name}->{relative_path}"
                        yield (file_path, source_desc)
    
    def cleanup_temp_dirs(self):
        """
        AI: Clean up temporary directories created during archive processing.
        
        Should be called when file discovery is complete to free disk space.
        """
        import shutil
        
        for temp_dir in self._temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"WARNING: Failed to cleanup temp directory {temp_dir}: {e}")
        
        self._temp_dirs.clear()
    
    def __del__(self):
        """AI: Ensure cleanup on object destruction."""
        self.cleanup_temp_dirs()


def create_file_iterator_from_path(file_path: Path, source_description: str) -> Iterator[Tuple[str, TextIO]]:
    """
    AI: Create file iterator for processing discovered files.
    
    Provides consistent interface for processors to handle both direct files
    and extracted archive contents.
    
    Args:
        file_path: Path to file to process
        source_description: Description for tracking file source
        
    Yields:
        Tuple of (source_description, file_handle) for processing
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file_handle:
            yield (source_description, file_handle)
    except Exception as e:
        print(f"ERROR: Failed to open file {file_path}: {e}")
