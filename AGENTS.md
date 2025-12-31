# AGENTS.md

This file provides comprehensive guidance to AI coding assistants (Claude Code, GitHub Copilot, Cursor, etc.) when working with code in this repository.

## Required Reading Before Development

**MANDATORY:** Review these documents for complete project context:
- `docs/SPEC.md` - Complete technical specification, system architecture, database schemas, and API design
- `docs/adr/` - Architectural Decision Records for all design decisions and project context

## Project Overview

This is a Python FastAPI application for loading, parsing, correlating, and analyzing access logs from Nexus Repository and nginx reverse proxy. The application provides both a web interface and MCP (Model Context Protocol) server for LLM integration.

## Essential Commands

### Setup and Installation
```bash
# Install uv (Python package manager) if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install development dependencies
uv sync --dev
```

### Running the Application
```bash
# Create demo database with sample data
uv run python scripts/create_demo_db.py

# Process logs and start web interface
uv run python -m app.main --nexus-dir ./sample_logs/nexus --nginx-dir ./sample_logs/nginx --process-logs

# Start MCP server for VS Code Copilot integration (stdio mode)
uv run python -m app.main --db-name log_analysis.db --mcp-stdio

# Full stack: process logs, web server, and MCP server
uv run python -m app.main --nexus-dir /path/to/nexus --nginx-dir /path/to/nginx --process-logs --enable-mcp-server
```

### Testing
```bash
# Run all unit and integration tests
uv run pytest tests/unit tests/integration -v

# Run specific test file
uv run pytest tests/unit/test_nginx_processor.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term

# Run E2E tests with Playwright
./run_playwright_e2e.sh

# Run tests by category
uv run pytest -m unit           # Unit tests only
uv run pytest -m integration    # Integration tests only
uv run pytest -m e2e            # E2E tests only
```

### Code Quality
```bash
# Format code with black
uv run black app/ tests/

# Sort imports
uv run isort app/ tests/

# Type checking
uv run mypy app/

# Linting
uv run flake8 app/ tests/
```

## Architecture Overview

### Core Components

**Processing Pipeline:**
- `file_discovery/` - Archive extraction and file pattern matching with support for nested archives (tar, zip, tar.gz) up to configurable depth
- `processors/` - Abstract base class (`BaseLogProcessor`) with format-specific implementations (`NginxLogProcessor`, `NexusLogProcessor`) using regex parsing
- `processing/orchestrator.py` - Coordinates file discovery and processing with statistics tracking

**Database Layer:**
- `database/models.py` - SQLAlchemy models for `nginx_logs` and `nexus_logs` tables with comprehensive indexes
- `database/operations.py` - Unified database operations interface with batch insertion
- `database/connection.py` - SQLite connection management with fresh database creation on startup

**Web Interface:**
- `web/routes.py` - FastAPI endpoints for table previews and SQL query execution
- Security: Only SELECT queries allowed, results limited to prevent memory issues

**MCP Server:**
- `mcp/server.py` - Dual transport support (stdio for VS Code Copilot, network for other clients)
- `mcp/tools.py` - Three core tools: `list_database_schema`, `execute_sql_query`, `get_table_sample`
- Single entry point through `app.main` (no separate MCP scripts)

### Key Architectural Patterns

**Memory-Efficient Processing:**
- Chunked file reading (default: 1000 lines per chunk)
- Generator-based processing to avoid loading entire files into memory
- Batch database inserts (default: 1000 entries per batch)
- Stream processing through archives

**Configuration Management:**
- Pydantic-based `Settings` class with `.env` file support
- CLI arguments override environment variables
- Dependency injection pattern - all components accept Settings instance

**Error Handling:**
- Malformed log lines are logged but processing continues
- Format: `PARSE_ERROR: {file_path}:{line_number} - {error_message}`
- Statistics tracking for errors and successful entries

**Nested Archive Support:**
- Recursive extraction with configurable depth limit (default: 3 levels)
- File source tracking through nesting chains (e.g., `backup.zip->daily.tar.gz->access.log`)
- Temporary directory cleanup after extraction

### Database Schema

**nginx_logs table:**
- Key fields: ip_address, timestamp, method, path, status_code, response_size, user_agent
- Indexes on: timestamp, ip_address, method, path, status_code, (method, path) composite

**nexus_logs table:**
- Key fields: ip_address, timestamp, method, path, status_code, response_size_1, response_size_2, user_agent, thread_info
- Similar index structure to nginx_logs for performance

Both tables include `raw_log` (original line) and `file_source` (tracking) fields.

---

## Python Coding Standards

### Dependency Management with UV

**MANDATORY:** Always use UV for Python package management:

```bash
# Project setup and dependency installation
uv sync                          # Install all dependencies from lock file
uv add package_name             # Add new dependency
uv add --dev pytest             # Add development dependency
uv remove package_name          # Remove dependency

# Running commands in UV environment
uv run python -m app.main       # Run application
uv run pytest                   # Run tests
uv run python -m app.main --mcp-stdio  # Run MCP server

# Environment management
uv venv                         # Create virtual environment (if needed)
uv pip list                     # List installed packages
```

**Dependency Guidelines:**
- Always use `uv add` instead of `pip install` for adding dependencies
- Use `uv run` prefix for all Python commands to ensure correct environment
- Keep `pyproject.toml` and `uv.lock` files updated and committed
- Use `--dev` flag for development-only dependencies (pytest, black, etc.)

### Documentation Standards

**MANDATORY:** All docstrings must use "AI:" prefix to indicate AI-generated/maintained code:

```python
def process_log_file(file_path: Path, patterns: List[str]) -> Iterator[Dict[str, Any]]:
    """
    AI: Process log file and yield parsed entries.

    Args:
        file_path: Path to log file
        patterns: List of filename patterns to match

    Yields:
        Parsed log entry dictionaries

    Raises:
        ProcessingError: When file cannot be processed
    """
    pass

class NginxLogProcessor(BaseLogProcessor):
    """AI: Processor specifically for nginx access log format."""
    pass
```

### Code Style and Structure

**Type Hints Required:**
```python
from typing import List, Dict, Optional, Iterator, Tuple
from pathlib import Path

def parse_log_line(line: str, line_number: int, source_file: str) -> Optional[Dict]:
    """AI: Parse individual log line with detailed error reporting."""
    try:
        return self._apply_regex_parsing(line)
    except LogParsingError as e:
        print(f"PARSE_ERROR: {source_file}:{line_number} - {e}")
        return None
```

### Error Handling Patterns

**Comprehensive Error Handling:**
```python
# Always use specific exception types
class LogParsingError(Exception):
    """AI: Raised when log entry cannot be parsed."""
    pass

class ArchiveExtractionError(Exception):
    """AI: Raised when archive cannot be extracted."""
    pass

# Error handling with context
def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
    """AI: Parse individual log line with detailed error reporting."""
    try:
        return self._apply_regex_parsing(line)
    except LogParsingError as e:
        print(f"PARSE_ERROR: {source_file}:{line_number} - {e}")
        return None  # Continue processing
    except Exception as e:
        print(f"UNEXPECTED_ERROR: {source_file}:{line_number} - {e}")
        return None
```

### Resource Management

**Always Use Context Managers:**
```python
# Always use context managers and handle nested archives
def process_archive_recursive(self, archive_path: Path, max_depth: int = 3) -> Iterator[Dict]:
    """AI: Process archive with nested archive support and proper resource cleanup."""
    if max_depth <= 0:
        print(f"WARNING: Maximum nesting depth reached for {archive_path}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(archive_path, 'r:gz') as archive:
            for member in archive.getmembers():
                if member.isfile():
                    # Extract to temporary location
                    archive.extract(member, temp_dir)
                    extracted_path = Path(temp_dir) / member.name

                    if self.matches_target_pattern(member.name):
                        with open(extracted_path, 'r') as file_obj:
                            yield from self.process_file_content(file_obj, f"{archive_path.name}->{member.name}")
                    elif self.is_archive_file(extracted_path):
                        # Recursively process nested archive
                        yield from self.process_archive_recursive(extracted_path, max_depth - 1)
                # Temporary directory automatically cleaned up
```

### Clean Code with Zero Warnings

**MANDATORY:** All code must execute without warnings in both development and test environments:

- **Test Output:** All pytest runs must complete without warning messages
- **Dependencies:** No deprecation warnings from imported libraries
- **Code Quality:** No unused imports, variables, or unreachable code
- **Resource Management:** Proper cleanup to prevent ResourceWarnings
- **Mock Configuration:** Test mocks properly configured to avoid warnings
- **Async Operations:** Proper async handling to prevent runtime warnings

---

## Architectural Consistency Requirements

### Configuration Dependency Injection

**MANDATORY:** All processors must accept Settings instance in constructor:

```python
# CORRECT
class NginxLogProcessor(BaseLogProcessor):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.patterns = settings.nginx_patterns  # Use from config

# INCORRECT - Never hardcode patterns
class NginxLogProcessor(BaseLogProcessor):
    def __init__(self):
        self.patterns = ["access.log*"]  # Don't do this
```

**Never hardcode configuration values** (patterns, paths, limits) in component classes. Use `settings.nexus_patterns` and `settings.nginx_patterns` properties for pattern matching.

### Module Naming Consistency

**Perfect Parallel Structure Required:**

```
app/processors/                     app/database/
├── base.py                         ├── base.py
│   └── BaseLogProcessor               └── BaseLogDatabase
│                                      └── CommonLogDatabase
├── nginx_processor.py              ├── nginx_database.py
│   └── NginxLogProcessor              └── NginxLogDatabase
└── nexus_processor.py              └── nexus_database.py
    └── NexusLogProcessor              └── NexusLogDatabase
```

**Naming Convention Rules:**

**File Naming:**
- Base files: `base.py` (not `base_operations.py` or `base_processor.py`)
- Format-specific files: `{format}_{module_type}.py`
  - Examples: `nginx_processor.py`, `nginx_database.py`
- Avoid verbose suffixes: Use `database` not `database_operations`

**Class Naming:**
- Base classes: `BaseLog{ModuleType}`
  - Examples: `BaseLogProcessor`, `BaseLogDatabase`
- Format-specific classes: `{Format}Log{ModuleType}`
  - Examples: `NginxLogProcessor`, `NginxLogDatabase`
- Common/shared classes: `CommonLog{ModuleType}`
  - Examples: `CommonLogDatabase`

### Adding New Log Formats

**File Creation Pattern:**
1. **Processor:** Create `{format}_processor.py` with `{Format}LogProcessor` class
2. **Database:** Create `{format}_database.py` with `{Format}LogDatabase` class
3. **Model:** Add `{Format}Log` SQLAlchemy model to `models.py`
4. **Tests:** Create corresponding test files following the same pattern

**Implementation Checklist:**
- [ ] Follow exact naming patterns of existing nginx/nexus implementations
- [ ] Inherit from appropriate base classes (`BaseLogProcessor`, `BaseLogDatabase`)
- [ ] Update unified interfaces (`DatabaseOperations`, orchestrator)
- [ ] Add configuration patterns to Settings class
- [ ] Create comprehensive tests following established patterns
- [ ] Update documentation to include new format

---

## FastAPI Implementation Guidelines

### Application Structure

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="Log Analysis Application",
    description="Nexus and nginx log correlation and analysis",
    version="1.0.0"
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency injection for database
def get_database():
    """AI: Dependency injection for database connections."""
    return DatabaseOperations(settings.db_name)
```

### Route Implementation

```python
@app.post("/api/execute-query")
async def execute_query(
    query_request: QueryRequest,
    db: DatabaseOperations = Depends(get_database)
) -> QueryResponse:
    """
    AI: Execute SQL query with security validation.

    Only SELECT statements allowed for security.
    Results limited to prevent memory issues.
    """
    try:
        # Validate query is SELECT only
        if not query_request.query.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )

        results = db.execute_query(query_request.query, limit=1000)
        return QueryResponse(results=results, row_count=len(results))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Request/Response Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """AI: Request model for SQL query execution."""
    query: str = Field(..., description="SQL SELECT query to execute")
    limit: Optional[int] = Field(100, description="Maximum rows to return")

class QueryResponse(BaseModel):
    """AI: Response model for query results."""
    results: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time: float
```

---

## Database Implementation Guidelines

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class NginxLog(Base):
    """AI: SQLAlchemy model for nginx access logs."""
    __tablename__ = 'nginx_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String, nullable=False)
    remote_user = Column(String)
    timestamp = Column(DateTime, nullable=False)
    method = Column(String, nullable=False)
    path = Column(Text, nullable=False)
    http_version = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_size = Column(Integer)
    referer = Column(Text)
    user_agent = Column(Text)
    raw_log = Column(Text, nullable=False)
    file_source = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Define indexes as table arguments
    __table_args__ = (
        Index('idx_nginx_timestamp', 'timestamp'),
        Index('idx_nginx_method', 'method'),
        Index('idx_nginx_path', 'path'),
        Index('idx_nginx_method_path', 'method', 'path'),
    )
```

### Database Operations

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

class DatabaseOperations:
    """AI: Database operations with proper connection management."""

    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        """AI: Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def batch_insert(self, model_class, data: List[Dict]) -> int:
        """AI: Efficient batch insert with transaction management."""
        with self.get_session() as session:
            objects = [model_class(**item) for item in data]
            session.bulk_save_objects(objects)
            return len(objects)
```

---

## Testing Implementation Guidelines

### Test Structure and Organization

```
tests/
├── unit/
│   ├── test_nginx_processor.py
│   ├── test_nexus_processor.py
│   ├── test_file_handler.py
│   └── test_database_operations.py
├── integration/
│   ├── test_end_to_end_processing.py
│   └── test_api_endpoints.py
├── playwright/
│   ├── test_web_interface.py
│   └── test_sql_execution.py
├── fixtures/
│   ├── sample_logs.py
│   └── test_data.py
└── conftest.py
```

### Unit Test Patterns

```python
import pytest
from pathlib import Path
from app.processors.nginx_processor import NginxLogProcessor

class TestNginxProcessor:
    """AI: Test nginx log processing functionality."""

    def setup_method(self):
        """AI: Setup test instance before each test."""
        self.processor = NginxLogProcessor()

    def test_parse_valid_nginx_log(self):
        """AI: Test parsing of standard nginx log entry."""
        log_line = '127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /api/test HTTP/1.1" 200 1234 "-" "test-agent"'

        result = self.processor.parse_log_line(log_line, 1, "test.log")

        assert result is not None
        assert result['ip_address'] == '127.0.0.1'
        assert result['method'] == 'GET'
        assert result['path'] == '/api/test'
        assert result['status_code'] == 200

    def test_parse_malformed_log_returns_none(self):
        """AI: Test that malformed logs return None and log error."""
        log_line = 'invalid log format'

        result = self.processor.parse_log_line(log_line, 1, "test.log")

        assert result is None

    @pytest.mark.parametrize("log_line,expected_method,expected_path", [
        ('127.0.0.1 - - [29/May/2025:00:00:09 -0400] "GET /test HTTP/1.1" 200 1234', 'GET', '/test'),
        ('127.0.0.1 - - [29/May/2025:00:00:09 -0400] "POST /api/data HTTP/1.1" 201 567', 'POST', '/api/data'),
    ])
    def test_parse_different_methods(self, log_line, expected_method, expected_path):
        """AI: Test parsing different HTTP methods."""
        result = self.processor.parse_log_line(log_line, 1, "test.log")
        assert result['method'] == expected_method
        assert result['path'] == expected_path
```

### Integration Test Patterns

```python
import pytest
import tempfile
from pathlib import Path
from app.database.operations import DatabaseOperations
from app.database.models import Base, NginxLog

class TestDatabaseIntegration:
    """AI: Test database operations with temporary database."""

    @pytest.fixture
    def temp_db(self):
        """AI: Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_ops = DatabaseOperations(db_path)
        Base.metadata.create_all(db_ops.engine)

        yield db_ops

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_batch_insert_nginx_logs(self, temp_db):
        """AI: Test batch insertion of nginx log entries."""
        test_data = [
            {
                'ip_address': '127.0.0.1',
                'method': 'GET',
                'path': '/test',
                'status_code': 200,
                'raw_log': 'test log line',
                'file_source': 'test.log'
            }
        ]

        count = temp_db.batch_insert(NginxLog, test_data)
        assert count == 1

        # Verify data inserted
        with temp_db.get_session() as session:
            logs = session.query(NginxLog).all()
            assert len(logs) == 1
            assert logs[0].ip_address == '127.0.0.1'
```

### Mock vs Real Testing (CRITICAL LESSON)

**PROBLEM:** Mock tests can pass while real implementations fail

```python
# Mock test - may not catch attribute access errors
class TestMCPServerMocked:
    def test_database_path_access_mocked(self):
        """AI: Mock test - may not catch attribute access errors."""
        mock_db_ops = Mock()
        mock_db_ops.db_path = "test.db"  # Mock allows any attribute

        server = MCPServer(mock_db_ops)
        # This test passes but real implementation fails!
        assert server.get_db_path() == "test.db"

# SOLUTION: Test with real object attribute chains
class TestMCPServerReal:
    def test_database_path_access_real(self):
        """AI: Real test - catches actual attribute access errors."""
        real_db_ops = DatabaseOperations("test.db")

        server = MCPServer(real_db_ops)
        # This would fail if attribute chain is incorrect
        # Error: AttributeError: 'DatabaseOperations' object has no attribute 'db_path'
        # Should be: real_db_ops.db_connection.db_path
        assert server.get_db_path() == "test.db"
```

**Testing Strategy:**
- **Unit Tests:** Use mocks for isolated component testing
- **Integration Tests:** Use real objects to validate actual attribute chains
- **Critical Path Testing:** Always test real implementations for production code paths
- **Attribute Validation:** Test actual object hierarchies, not just mock interfaces
- **Error Discovery:** Real tests reveal errors that mocks miss

### Playwright E2E Tests

```python
import pytest
from playwright.sync_api import Page, expect

class TestWebInterface:
    """AI: Test web interface functionality using Playwright."""

    def test_table_previews_display(self, page: Page):
        """AI: Test that both log table previews are displayed."""
        page.goto("http://localhost:8000")

        # Check nginx table preview
        nginx_table = page.locator("#nginx-table")
        expect(nginx_table).to_be_visible()

        # Check nexus table preview
        nexus_table = page.locator("#nexus-table")
        expect(nexus_table).to_be_visible()

    def test_sql_query_execution(self, page: Page):
        """AI: Test SQL query execution through web interface."""
        page.goto("http://localhost:8000")

        # Enter SQL query
        query_textarea = page.locator("#sql-query")
        query_textarea.fill("SELECT COUNT(*) as total FROM nginx_logs")

        # Execute query
        execute_button = page.locator("#execute-query")
        execute_button.click()

        # Verify results displayed
        results_div = page.locator("#query-results")
        expect(results_div).to_contain_text("total")
```

### Test Coverage Standards

**Systematic Test Coverage Assessment:**
- **MANDATORY:** Conduct systematic test coverage assessment after completing significant functionality
- **Trigger Points:** Major feature completion, release milestones, coverage below 80%, architectural changes
- **Process:** Run coverage analysis, identify gaps, create phase-based improvement plan, implement with proven patterns
- **Target Standards:**
  - Overall: 85%+
  - Critical modules: 90%+
  - Core logic: 85%+
  - Infrastructure: 80%+
- **Documentation:** Maintain `docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md` with current status, roadmap, and lessons learned
- **Mock vs Real Testing:** Ensure critical paths are tested with real implementations, not just mocked components
- **Attribute Access Validation:** Test actual object attribute chains, as mocks may not catch incorrect attribute access patterns

---

## Performance Guidelines

### Memory-Efficient Processing

```python
def process_large_file(self, file_path: Path) -> Iterator[Dict]:
    """AI: Process large files using generators to control memory usage."""
    with open(file_path, 'r') as f:
        batch = []
        for line_num, line in enumerate(f, 1):
            parsed = self.parse_log_line(line.strip(), line_num, str(file_path))
            if parsed:
                batch.append(parsed)

            if len(batch) >= self.batch_size:
                yield batch
                batch = []  # Free memory

        if batch:  # Final batch
            yield batch

def process_all_batches(self, file_path: Path):
    """AI: Process file in batches with database commits."""
    for batch in self.process_large_file(file_path):
        self.db_ops.batch_insert(self.model_class, batch)
        # Memory freed after each batch
```

### Database Optimization

```python
# Use indexes effectively
def get_logs_by_timerange(self, start_time: datetime, end_time: datetime) -> List[Dict]:
    """AI: Query logs using timestamp index for efficiency."""
    query = """
    SELECT method, path, COUNT(*) as hits
    FROM nginx_logs
    WHERE timestamp BETWEEN ? AND ?
    GROUP BY method, path
    ORDER BY hits DESC
    LIMIT 100
    """
    return self.execute_query(query, [start_time, end_time])

# Batch operations
def bulk_insert_with_transaction(self, data: List[Dict]):
    """AI: Use transactions for bulk operations."""
    with self.get_session() as session:
        session.execute(
            insert(self.model_class),
            data
        )
        # Single commit for entire batch
```

---

## Security Implementation Guidelines

### SQL Injection Prevention

```python
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword

def validate_select_only(query: str) -> bool:
    """
    AI: Validate that query contains only SELECT statements.

    Uses sqlparse to analyze SQL structure and reject any
    non-SELECT operations for security.
    """
    try:
        parsed = sqlparse.parse(query)
        for statement in parsed:
            if statement.get_type() != 'SELECT':
                return False
        return True
    except Exception:
        return False

def sanitize_query(query: str) -> str:
    """AI: Sanitize query string and add safety limits."""
    query = query.strip()

    # Add LIMIT if not present
    if 'LIMIT' not in query.upper():
        query += ' LIMIT 1000'

    return query
```

### File System Security

```python
def validate_file_path(file_path: Path, allowed_base: Path) -> bool:
    """
    AI: Validate that file path is within allowed directory.

    Prevents directory traversal attacks and ensures files
    are only accessed from configured log directories.
    """
    try:
        resolved_path = file_path.resolve()
        allowed_resolved = allowed_base.resolve()
        return resolved_path.is_relative_to(allowed_resolved)
    except Exception:
        return False

def safe_extract_archive(archive_path: Path, max_size: int = 100_000_000, max_depth: int = 3) -> bool:
    """
    AI: Safely extract archive with size, path, and depth checks.

    Prevents zip bombs, directory traversal, and infinite recursion
    during nested archive extraction.
    """
    total_size = 0

    def _extract_recursive(arch_path: Path, current_depth: int = 0):
        nonlocal total_size

        if current_depth > max_depth:
            raise SecurityError(f"Archive nesting too deep: {current_depth} levels")

        with zipfile.ZipFile(arch_path, 'r') as archive:
            for member in archive.infolist():
                # Check for directory traversal
                if os.path.isabs(member.filename) or '..' in member.filename:
                    raise SecurityError(f"Unsafe path in archive: {member.filename}")

                # Check extracted size
                total_size += member.file_size
                if total_size > max_size:
                    raise SecurityError("Archive too large - possible zip bomb")

    _extract_recursive(archive_path)
    return True
```

---

## MCP Server Implementation Guidelines

### Integrated Architecture

**CRITICAL:** Use single entry point through `app.main`:

```python
# CORRECT: Use main app entry point
uv run python -m app.main --mcp-stdio

# INCORRECT: Create separate MCP server files
# DO NOT create standalone run_mcp_*.py scripts
```

### Dual Transport Support

```python
from enum import Enum

class TransportMode(Enum):
    """AI: MCP server transport modes."""
    STDIO = "stdio"    # For VS Code Copilot
    NETWORK = "network"  # For network-based clients

class LogAnalysisMCPServer:
    """AI: Unified MCP server supporting multiple transports."""

    def __init__(
        self,
        db_ops: DatabaseOperations,
        transport_mode: TransportMode = TransportMode.NETWORK
    ):
        self.db_ops = db_ops
        self.transport_mode = transport_mode
        self.server = Server("log-analysis")
        self._register_tools()
```

### MCP Tool Implementation

```python
async def execute_sql_query(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    AI: Execute SELECT query with comprehensive security validation.

    Security measures:
    - Only SELECT statements allowed
    - Query parsing and validation
    - Result limits enforced
    - Input sanitization
    """
    # Validate SELECT only
    if not self._is_select_query(query):
        raise SecurityError("Only SELECT queries are allowed")

    # Apply result limits
    safe_query = self._apply_limit(query, min(limit, 1000))

    try:
        return self.db_ops.execute_query(safe_query)
    except Exception as e:
        # Log security events
        logger.warning(f"MCP query failed: {e}")
        raise MCPToolError(f"Query execution failed: {str(e)}")
```

### Database Connection Pattern

**CRITICAL:** Verify actual attribute access patterns:

```python
# CORRECT attribute chain
db_path = self.db_ops.db_connection.db_path

# INCORRECT - Will fail at runtime
db_path = self.db_ops.db_path  # AttributeError!
```

### Factory Function Pattern

```python
def create_stdio_server(db_ops: DatabaseOperations) -> LogAnalysisMCPServer:
    """AI: Factory for VS Code Copilot stdio integration."""
    return LogAnalysisMCPServer(db_ops, TransportMode.STDIO)

def create_network_server(db_ops: DatabaseOperations, host: str = "0.0.0.0", port: int = 8001) -> LogAnalysisMCPServer:
    """AI: Factory for network-based MCP clients."""
    return LogAnalysisMCPServer(db_ops, TransportMode.NETWORK, host, port)
```

### CLI Integration Patterns

```python
# Validate directories only when needed
if process_logs and (not nexus_dir or not nginx_dir):
    print("❌ Error: --nexus-dir and --nginx-dir are required when using --process-logs")
    sys.exit(1)

# Auto-assign dummy directories for MCP-only mode
if mcp_stdio and not nexus_dir:
    nexus_dir = "/tmp"  # Dummy directory for MCP mode
```

---

## Project Documentation Structure

### Documentation Organization

```
docs/
├── SPEC.md                 # Technical specification and architecture
├── adr/                    # Architectural Decision Records
│   ├── ADR_YYYYMMDD_NN_*.md
└── [future docs]           # API docs, user guides, etc.

README.md                   # Project overview and setup instructions
AGENTS.md                   # This file - AI assistant instructions
history.txt                 # Pure log of user requirements and changes
```

### Architectural Decision Records (ADRs)

- **Location:** All ADRs stored in `docs/adr/` following industry standards
- **Naming Convention:** `ADR_YYYYMMDD_NN_description.md` format
- **Discovery:** Use `find docs/adr/ -name "*.md" | sort` to list all current ADRs
- **Usage:** Reference ADRs by ID in code comments and documentation
- **Updates:** Create new ADR file for architectural changes, never modify existing ADRs
- **Knowledge Source:** Always check `docs/adr/` directory for current architectural decisions
- **Technical Foundation:** Review `docs/SPEC.md` for comprehensive system architecture before implementing changes

---

## Development Workflow

### Branch and PR Strategy

- **MANDATORY:** Every commit must be made on a separate feature branch
- **NEVER** commit directly to main branch
- Branch naming: `feature/description` or `fix/description`
- Each PR must include:
  - Concise summary of changes
  - Reference to user requirements that led to changes
  - Test results confirmation
  - Updated documentation if applicable

### Pre-Commit Requirements

**MANDATORY:** Run all tests before creating PR:
- Unit/Integration: `uv run pytest tests/unit tests/integration`
- E2E: `./run_playwright_e2e.sh`

**MANDATORY:** Add all new/modified files to git: `git add .`

**MANDATORY:** Clean code with zero warnings requirement:
- All pytest runs must complete without warning messages
- No deprecation warnings from dependencies
- No unused imports, variables, or unreachable code
- Proper resource cleanup to prevent ResourceWarnings
- Mock configuration validated to avoid warnings

**MANDATORY:** Configuration consistency check:
- Verify `.env.example` reflects all Settings class fields
- Update `.env.example` if new configuration options added
- Check CLI options match Settings class properties
- Ensure documentation reflects current configuration options

- Ensure no untracked files remain that should be committed
- Verify all tests pass before opening PR

### History Tracking

- **ONLY** add user prompts and instructions to `history.txt`
- **DO NOT** add implementation notes, summaries, or test results
- Keep `history.txt` as pure log of user requirements
- Format: `[Date] User Request: [actual user instruction]`

---

## Common Pitfalls to Avoid

1. **Don't hardcode configuration values** - Always use Settings instance
2. **Don't create separate MCP server files** - Use unified app entry point
3. **Don't skip integration tests** - Configuration changes need end-to-end validation
4. **Don't rely solely on mock tests** - Critical paths need real object testing
5. **Don't forget nested archive support** - File discovery must handle recursive extraction
6. **Don't modify ADRs** - Create new ones for architectural changes
7. **Don't forget "AI:" prefix** - All docstrings must include this prefix
8. **Don't use pip directly** - Always use `uv` for dependency management
9. **Don't add to history.txt** - Only user prompts go there, not implementation notes
10. **Don't ignore warnings** - All pytest runs must be warning-free

---

## Final Implementation Checklist

### Before Each Commit

- [ ] All tests pass (unit, integration, E2E, MCP)
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Security considerations addressed
- [ ] Performance optimizations applied
- [ ] All files added to git
- [ ] MCP integration follows unified architecture
- [ ] Configuration consistency verified:
  - [ ] `.env.example` matches Settings class fields
  - [ ] CLI options align with configuration properties
  - [ ] Documentation reflects current configuration options
- [ ] Clean code with zero warnings:
  - [ ] No pytest warnings in test output
  - [ ] No deprecation warnings from dependencies
  - [ ] No unused imports or variables
  - [ ] No runtime warnings from async operations
  - [ ] Proper resource cleanup to prevent ResourceWarnings
  - [ ] Mock objects properly configured to avoid warnings

### Before Each PR

- [ ] Branch created from main
- [ ] All requirements implemented
- [ ] Tests comprehensive and passing
- [ ] Documentation complete
- [ ] Security review completed
- [ ] Performance acceptable
- [ ] User requirements addressed
- [ ] No duplicate MCP server implementations

---

## AI Tool-Specific Integration

### VS Code Copilot / Claude Code MCP Integration

Configuration file: `.vscode/mcp.json`
```json
{
  "servers": {
    "log-analysis": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.main", "--db-name", "log_analysis.db", "--mcp-stdio"]
    }
  }
}
```

Ask questions like:
- "Show me the nginx log table structure"
- "What are the most common HTTP methods?"
- "Find all 404 errors"
