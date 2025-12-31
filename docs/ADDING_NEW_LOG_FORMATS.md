# Adding New Log Formats - Technical Guide

## Overview

This guide provides a comprehensive step-by-step process for adding support for new log formats to the Log Analysis Application. The architecture is designed to make adding new formats straightforward while maintaining consistency and quality.

## Prerequisites

- Understanding of the log format structure and parsing requirements
- Familiarity with SQLAlchemy models and database design
- Knowledge of Python regex patterns for log parsing
- Understanding of the application's architecture (see `docs/SPEC.md`)

## Architecture Overview

The application uses a modular architecture with clear separation between:

- **Processors**: Parse log files and extract structured data
- **Database**: Store and query parsed log data  
- **Models**: SQLAlchemy ORM models for database tables
- **Configuration**: Settings and patterns for log discovery

## Step-by-Step Implementation

### Step 1: Analyze the Log Format

Before implementation, thoroughly analyze the new log format:

```bash
# Example log entries for analysis
2024-01-15 10:30:45 [INFO] user123 accessed /api/data - response_time: 250ms
2024-01-15 10:31:12 [ERROR] authentication_failed for user456 from 192.168.1.100
```

**Key Questions:**
- What is the timestamp format?
- What fields are consistently present?
- What fields are optional?
- Are there different log entry types/formats?
- What makes this format unique from existing ones?

### Step 2: Create SQLAlchemy Model

Add the new model to `app/database/models.py`:

```python
class CustomServiceLog(Base):
    """AI: SQLAlchemy model for Custom Service logs."""
    __tablename__ = 'custom_service_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String, nullable=False)
    user_id = Column(String)
    action = Column(String, nullable=False)
    endpoint = Column(Text)
    response_time_ms = Column(Integer)
    ip_address = Column(String)
    raw_log = Column(Text, nullable=False)
    file_source = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Define indexes for common queries
    __table_args__ = (
        Index('idx_custom_service_timestamp', 'timestamp'),
        Index('idx_custom_service_level', 'level'),
        Index('idx_custom_service_user_action', 'user_id', 'action'),
    )
```

### Step 3: Create Database Operations

Create `app/database/custom_service_database.py`:

```python
"""
AI: Custom Service-specific database operations.

This module handles all database operations specific to Custom Service logs,
including batch insertion, previews, and custom service-specific queries.
"""

from typing import List, Dict, Any
from datetime import datetime

from app.database.base import BaseLogDatabase
from app.database.models import CustomServiceLog


class CustomServiceLogDatabase(BaseLogDatabase):
    """AI: Database operations specifically for Custom Service logs."""
    
    def get_model_class(self):
        """AI: Return the CustomServiceLog SQLAlchemy model."""
        return CustomServiceLog
    
    def batch_insert(self, log_data: List[Dict]) -> int:
        """
        AI: Insert a batch of custom service log entries into the database.
        
        Args:
            log_data: List of dictionaries containing parsed log data
            
        Returns:
            Number of entries successfully inserted
        """
        if not log_data:
            return 0
        
        try:
            with self.get_session() as session:
                logs = []
                for entry in log_data:
                    try:
                        log = CustomServiceLog(
                            timestamp=entry.get('timestamp'),
                            level=entry.get('level', ''),
                            user_id=entry.get('user_id'),
                            action=entry.get('action', ''),
                            endpoint=entry.get('endpoint'),
                            response_time_ms=entry.get('response_time_ms'),
                            ip_address=entry.get('ip_address'),
                            raw_log=entry.get('raw_log', ''),
                            file_source=entry.get('file_source', '')
                        )
                        logs.append(log)
                    except Exception as e:
                        print(f"CUSTOM_SERVICE_INSERT_ERROR: Skipping invalid entry - {e}")
                        continue
                
                if logs:
                    session.add_all(logs)
                    session.flush()
                    return len(logs)
                else:
                    return 0
                    
        except Exception as e:
            print(f"CUSTOM_SERVICE_BATCH_INSERT_ERROR: Failed to insert logs - {e}")
            raise
    
    def get_preview(self, limit: int = 10) -> List[Dict]:
        """AI: Get a preview of custom service log entries."""
        try:
            with self.get_session() as session:
                logs = session.query(CustomServiceLog).order_by(
                    CustomServiceLog.id.desc()
                ).limit(limit).all()
                
                result = []
                for log in logs:
                    result.append({
                        'id': log.id,
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                        'level': log.level,
                        'user_id': log.user_id,
                        'action': log.action,
                        'endpoint': log.endpoint,
                        'response_time_ms': log.response_time_ms,
                        'ip_address': log.ip_address,
                        'file_source': log.file_source,
                        'created_at': log.created_at.isoformat() if log.created_at else None
                    })
                
                return result
                
        except Exception as e:
            print(f"CUSTOM_SERVICE_PREVIEW_ERROR: Failed to get preview - {e}")
            return []
    
    # Add format-specific query methods as needed
    def get_error_summary(self, limit: int = 100) -> List[Dict[str, Any]]:
        """AI: Get summary of error-level log entries."""
        try:
            with self.get_session() as session:
                query = """
                SELECT action, COUNT(*) as error_count
                FROM custom_service_logs 
                WHERE level = 'ERROR'
                GROUP BY action 
                ORDER BY error_count DESC 
                LIMIT :limit
                """
                result = session.execute(query, {'limit': limit})
                return [{'action': row[0], 'error_count': row[1]} for row in result.fetchall()]
        except Exception as e:
            print(f"CUSTOM_SERVICE_ERROR_SUMMARY_ERROR: Failed to get error summary - {e}")
            return []
```

### Step 4: Create Log Processor

Create `app/processors/custom_service_processor.py`:

```python
"""
AI: Custom Service log processor for parsing and processing log files.

Handles parsing of Custom Service log format with robust error handling
and efficient memory usage through chunked processing.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from app.processors.base import BaseLogProcessor
from app.config import Settings


class CustomServiceLogProcessor(BaseLogProcessor):
    """AI: Processor for Custom Service log format."""
    
    def __init__(self, settings: Settings, chunk_size: int = 1000, batch_size: int = 1000):
        """
        AI: Initialize Custom Service processor with configuration.
        
        Args:
            settings: Application settings containing log patterns
            chunk_size: Number of lines to read per chunk
            batch_size: Number of parsed entries per database batch
        """
        super().__init__(chunk_size, batch_size)
        self.settings = settings
        
        # Compile regex pattern for Custom Service logs
        self.log_pattern = re.compile(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
            r'\[(?P<level>\w+)\] '
            r'(?P<message>.*)'
        )
        
        # Additional patterns for specific message types
        self.user_action_pattern = re.compile(
            r'(?P<user_id>\w+) (?P<action>\w+) (?P<endpoint>/[\w/]*)'
            r'(?: - response_time: (?P<response_time>\d+)ms)?'
        )
        
        self.error_pattern = re.compile(
            r'(?P<action>\w+) for (?P<user_id>\w+) from (?P<ip_address>[\d.]+)'
        )
    
    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        """
        AI: Parse individual Custom Service log line into structured data.
        
        Args:
            line: Raw log line to parse
            line_number: Line number for error reporting
            source_file: Source file path for tracking
            
        Returns:
            Parsed log entry as dictionary, or None if parsing fails
        """
        try:
            # Parse main log structure
            match = self.log_pattern.match(line.strip())
            if not match:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid log format")
                return None
            
            # Extract basic fields
            timestamp_str = match.group('timestamp')
            level = match.group('level')
            message = match.group('message')
            
            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                print(f"PARSE_ERROR: {source_file}:{line_number} - Invalid timestamp: {e}")
                return None
            
            # Initialize result
            result = {
                'timestamp': timestamp,
                'level': level,
                'raw_log': line,
                'file_source': source_file
            }
            
            # Parse message content based on patterns
            if 'accessed' in message:
                # User action log
                user_match = self.user_action_pattern.search(message)
                if user_match:
                    result.update({
                        'user_id': user_match.group('user_id'),
                        'action': user_match.group('action'),
                        'endpoint': user_match.group('endpoint'),
                        'response_time_ms': (
                            int(user_match.group('response_time')) 
                            if user_match.group('response_time') else None
                        )
                    })
            elif 'failed' in message:
                # Error log
                error_match = self.error_pattern.search(message)
                if error_match:
                    result.update({
                        'action': error_match.group('action'),
                        'user_id': error_match.group('user_id'),
                        'ip_address': error_match.group('ip_address')
                    })
            
            return result
            
        except Exception as e:
            print(f"PARSE_ERROR: {source_file}:{line_number} - Unexpected error: {e}")
            return None
    
    def get_batch_insert_method(self, db_ops):
        """AI: Return the custom service batch insert method."""
        return db_ops.batch_insert_custom_service_logs
    
    def get_supported_patterns(self) -> List[str]:
        """AI: Get filename patterns for custom service logs from configuration."""
        return self.settings.custom_service_patterns
```

### Step 5: Update Configuration

Add configuration support in `app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Custom Service log patterns
    custom_service_pattern: str = "custom_service*.log,service_*.log"
    
    @property
    def custom_service_patterns(self) -> List[str]:
        """AI: Convert custom service pattern string to list for processing."""
        return [p.strip() for p in self.custom_service_pattern.split(',')]
```

Update `.env.example`:

```bash
# Custom Service Logs
CUSTOM_SERVICE_PATTERN=custom_service*.log,service_*.log
```

### Step 6: Update Unified Database Operations

Update `app/database/operations.py`:

```python
from app.database.custom_service_database import CustomServiceLogDatabase

class DatabaseOperations:
    def __init__(self, db_connection: DatabaseConnection):
        # ... existing initialization ...
        self.custom_service = CustomServiceLogDatabase(db_connection)
    
    def batch_insert_custom_service_logs(self, log_data: List[Dict]) -> int:
        """AI: Insert batch of custom service log entries."""
        return self.custom_service.batch_insert(log_data)
    
    def get_custom_service_preview(self, limit: int = 10) -> List[Dict]:
        """AI: Get custom service log preview."""
        return self.custom_service.get_preview(limit)
    
    def custom_service_operations(self) -> CustomServiceLogDatabase:
        """AI: Get custom service-specific database operations."""
        return self.custom_service
```

### Step 7: Update Processing Orchestrator

Update `app/processing/orchestrator.py`:

```python
from app.processors.custom_service_processor import CustomServiceLogProcessor

class LogProcessingOrchestrator:
    def __init__(self, settings: Settings, db_ops: DatabaseOperations):
        # ... existing initialization ...
        self.custom_service_processor = CustomServiceLogProcessor(settings)
    
    def process_custom_service_logs(self, discovered_files: List[Path]) -> ProcessingStatistics:
        """AI: Process custom service log files."""
        return self._process_files_with_processor(
            discovered_files, 
            self.custom_service_processor, 
            "Custom Service"
        )
    
    def process_all_logs(self, nexus_dir: Path, nginx_dir: Path, custom_service_dir: Path):
        """AI: Process all log types including custom service."""
        # ... existing processing ...
        
        # Process custom service logs
        custom_service_files = self.file_discovery.discover_files(
            custom_service_dir, 
            self.custom_service_processor.get_supported_patterns()
        )
        custom_service_stats = self.process_custom_service_logs(custom_service_files)
        
        # ... combine stats ...
```

### Step 8: Create Comprehensive Tests

Create `tests/unit/test_custom_service_processor.py`:

```python
"""AI: Unit tests for Custom Service log processor."""

import pytest
from datetime import datetime

from app.processors.custom_service_processor import CustomServiceLogProcessor
from app.config import Settings


class TestCustomServiceProcessor:
    """AI: Test Custom Service log processing functionality."""
    
    def setup_method(self):
        """AI: Setup test instance before each test."""
        settings = Settings()
        self.processor = CustomServiceLogProcessor(settings)
    
    def test_parse_user_action_log(self):
        """AI: Test parsing of user action log entry."""
        log_line = '2024-01-15 10:30:45 [INFO] user123 accessed /api/data - response_time: 250ms'
        
        result = self.processor.parse_log_line(log_line, 1, "test.log")
        
        assert result is not None
        assert result['timestamp'] == datetime(2024, 1, 15, 10, 30, 45)
        assert result['level'] == 'INFO'
        assert result['user_id'] == 'user123'
        assert result['action'] == 'accessed'
        assert result['endpoint'] == '/api/data'
        assert result['response_time_ms'] == 250
    
    def test_parse_error_log(self):
        """AI: Test parsing of error log entry."""
        log_line = '2024-01-15 10:31:12 [ERROR] authentication_failed for user456 from 192.168.1.100'
        
        result = self.processor.parse_log_line(log_line, 1, "test.log")
        
        assert result is not None
        assert result['timestamp'] == datetime(2024, 1, 15, 10, 31, 12)
        assert result['level'] == 'ERROR'
        assert result['action'] == 'authentication_failed'
        assert result['user_id'] == 'user456'
        assert result['ip_address'] == '192.168.1.100'
    
    def test_parse_malformed_log_returns_none(self):
        """AI: Test that malformed logs return None."""
        log_line = 'invalid log format'
        
        result = self.processor.parse_log_line(log_line, 1, "test.log")
        
        assert result is None
    
    def test_get_supported_patterns(self):
        """AI: Test that processor returns correct patterns."""
        patterns = self.processor.get_supported_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
```

### Step 9: Update Web Interface (Optional)

If you want web interface support, update `app/web/routes.py`:

```python
@app.get("/api/custom-service-preview")
async def get_custom_service_preview(
    limit: int = 10,
    db: DatabaseOperations = Depends(get_database)
) -> List[Dict[str, Any]]:
    """AI: Get preview of custom service log entries."""
    try:
        preview_data = db.get_custom_service_preview(limit)
        return preview_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 10: Update CLI Interface

Update `app/main.py` to support the new log format:

```python
@click.option('--custom-service-dir', help='Directory containing custom service logs')
def main(
    nexus_dir: str,
    nginx_dir: str, 
    custom_service_dir: str,
    # ... other options ...
):
    if process_logs:
        orchestrator.process_all_logs(
            Path(nexus_dir), 
            Path(nginx_dir),
            Path(custom_service_dir) if custom_service_dir else None
        )
```

## Testing Strategy

### Unit Tests
- Test all parsing scenarios (valid, invalid, edge cases)
- Test database operations (insert, query, error handling)
- Test configuration integration

### Integration Tests  
- Test end-to-end processing pipeline
- Test with real log file samples
- Test error handling and recovery

### Performance Tests
- Test with large log files
- Verify memory usage stays reasonable
- Test concurrent processing if applicable

## Best Practices

### Code Quality
- Follow existing code style and patterns exactly
- Use type hints consistently
- Add comprehensive docstrings with "AI:" prefix
- Handle errors gracefully with informative messages

### Performance
- Use chunked file reading for memory efficiency
- Implement efficient regex patterns
- Use database indexes for common query patterns
- Consider batch processing for large datasets

### Maintainability
- Follow established naming conventions
- Keep processors focused and single-responsibility
- Use dependency injection for configuration
- Write comprehensive tests

## Troubleshooting

### Common Issues

**Parsing Failures:**
- Verify regex patterns match actual log format
- Check timestamp format parsing
- Test with various log samples

**Database Issues:**
- Ensure model fields match parsed data structure
- Check for data type mismatches
- Verify database indexes are appropriate

**Performance Problems:**
- Monitor memory usage during processing
- Optimize regex patterns if needed
- Consider adjusting chunk/batch sizes

**Integration Issues:**
- Verify all imports and dependencies
- Check configuration property names
- Test with other log processors

## Example Complete Implementation

See the existing `nginx_processor.py` and `nginx_database.py` files for complete reference implementations that follow all established patterns and best practices.

## Conclusion

Following this guide ensures new log formats integrate seamlessly with the existing architecture while maintaining consistency, performance, and maintainability. The modular design makes adding new formats straightforward once you understand the patterns.

For additional help, review:
- `docs/SPEC.md` for architecture overview
- `docs/adr/` for architectural decisions
- `.github/copilot-instructions.md` for coding standards
- Existing implementations for reference patterns
