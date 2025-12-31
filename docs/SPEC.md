# Log Analysis Application - Technical Specification

## 1. Project Overview

### 1.1 Objective
Develop a Python FastAPI application for loading, parsing, correlating, and analyzing access logs from Nexus Repository and nginx reverse proxy. The application provides both a web interface and MCP (Model Context Protocol) server for LLM integration.

### 1.2 Core Functionality
- Parse nginx and Nexus access logs from various archive formats
- Store parsed data in SQLite database with optimized indexing
- Provide web interface for data viewing and SQL querying
- Expose MCP server endpoints for LLM integration
- Support configurable file patterns for log rotation scenarios

### 1.3 Key Requirements
- Fresh database creation on each application start
- Memory-efficient processing of large log files
- Comprehensive error handling with detailed logging
- Modular architecture for easy format extension
- Full test coverage (unit, integration, E2E)

## 2. Architecture Design

### 2.1 System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Loader   │────│   Log Parser    │────│   SQLite DB     │
│  (zip/tar.gz)   │    │   (nginx/nexus) │    │  (2 tables)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐            │
│   Web Frontend  │────│  FastAPI Backend│────────────┤
│   (HTML/CSS/JS) │    │   (SQL Query)   │            │
└─────────────────┘    └─────────────────┘            │
                                                       │
┌─────────────────┐    ┌─────────────────┐            │
│   LLM Client    │────│   MCP Server    │────────────┘
│   (External)    │    │   (Tools API)   │
└─────────────────┘    └─────────────────┘
```

### 2.2 Directory Structure

```
app/
├── __init__.py
├── main.py                    # FastAPI app + CLI entry point
├── config.py                  # Configuration management (.env support)
├── database/
│   ├── __init__.py
│   ├── connection.py          # SQLite connection management
│   ├── models.py              # SQLAlchemy models and schemas
│   ├── operations.py          # Database CRUD operations
│   └── schema_inspector.py    # Schema introspection for MCP
├── processors/
│   ├── __init__.py
│   ├── base.py                # Abstract base processor
│   ├── file_handler.py        # Archive extraction and file discovery
│   ├── nginx_processor.py     # nginx log parsing implementation
│   └── nexus_processor.py     # Nexus log parsing implementation
├── web/
│   ├── __init__.py
│   ├── routes.py              # FastAPI web routes
│   └── templates/
│       └── index.html         # Web interface template
├── mcp/
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   ├── tools.py               # MCP tool definitions
│   └── schemas.py             # MCP request/response schemas
└── static/
    ├── style.css              # Web interface styling
    └── script.js              # Frontend JavaScript
```

## 3. Database Design

### 3.1 Schema Definition

#### nginx_logs Table
```sql
CREATE TABLE nginx_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    remote_user TEXT,              -- authenticated user (typically "-")
    timestamp DATETIME NOT NULL,
    method TEXT NOT NULL,          -- HTTP verb (GET, POST, PUT, DELETE, etc.)
    path TEXT NOT NULL,            -- URL path
    http_version TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_size INTEGER,
    referer TEXT,
    user_agent TEXT,
    raw_log TEXT NOT NULL,         -- original log line for debugging
    file_source TEXT NOT NULL,     -- source file path
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### nexus_logs Table
```sql
CREATE TABLE nexus_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    remote_user TEXT,              -- authenticated user (typically "-")
    timestamp DATETIME NOT NULL,
    method TEXT NOT NULL,          -- HTTP verb
    path TEXT NOT NULL,            -- URL path
    http_version TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_size_1 INTEGER,       -- first response size field
    response_size_2 INTEGER,       -- second response size field
    user_agent TEXT,
    thread_info TEXT,              -- thread pool information [qtp...]
    raw_log TEXT NOT NULL,
    file_source TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Performance Indexes

**Essential indexes for query optimization:**
```sql
-- nginx_logs indexes
CREATE INDEX idx_nginx_timestamp ON nginx_logs(timestamp);
CREATE INDEX idx_nginx_ip ON nginx_logs(ip_address);
CREATE INDEX idx_nginx_method ON nginx_logs(method);
CREATE INDEX idx_nginx_path ON nginx_logs(path);
CREATE INDEX idx_nginx_status ON nginx_logs(status_code);
CREATE INDEX idx_nginx_method_path ON nginx_logs(method, path);

-- nexus_logs indexes
CREATE INDEX idx_nexus_timestamp ON nexus_logs(timestamp);
CREATE INDEX idx_nexus_ip ON nexus_logs(ip_address);
CREATE INDEX idx_nexus_method ON nexus_logs(method);
CREATE INDEX idx_nexus_path ON nexus_logs(path);
CREATE INDEX idx_nexus_status ON nexus_logs(status_code);
CREATE INDEX idx_nexus_method_path ON nexus_logs(method, path);
```

### 3.3 Database Operations

- **Fresh Creation**: Drop and recreate database on each application start
- **Batch Inserts**: Process logs in batches of 1000 entries for performance
- **Transaction Management**: Use database transactions for batch operations
- **Connection Pooling**: Implement proper SQLite connection management

## 4. Configuration Management

### 4.1 Command Line Interface

```bash
python -m app \
  --nexus-dir /path/to/nexus/logs \
  --nginx-dir /path/to/nginx/logs \
  --db-name analysis.db \
  --nexus-pattern "request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz" \
  --nginx-pattern "access.log*" \
  --enable-mcp-server \
  --mcp-port 8001 \
  --web-port 8000
```

### 4.2 Environment Configuration (.env)

```env
# Directory paths
NEXUS_DIR=/path/to/nexus/logs
NGINX_DIR=/path/to/nginx/logs

# Database
DB_NAME=log_analysis.db

# File patterns (comma-separated)
NEXUS_PATTERN=request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz
NGINX_PATTERN=access.log*

# Server configuration
ENABLE_MCP_SERVER=true
MCP_PORT=8001
WEB_PORT=8000

# Processing configuration
CHUNK_SIZE=8192
LINE_BUFFER_SIZE=1000
```

### 4.3 Configuration Validation

- Validate directory paths exist and are readable
- Ensure database directory is writable
- Validate port availability for web and MCP servers
- Provide meaningful error messages for configuration issues

## 5. File Processing Requirements

### 5.1 Supported Archive Formats

1. **Single compressed file**: `access.log.gz`, `request.log.gz`
2. **Tar.gz archive**: `logs-2025-01-01.tar.gz` containing target files
3. **Tar archive**: `logs-2025-01-01.tar` containing target files
4. **Zip archive**: `logs-2025-01-01.zip` containing target files
5. **Nested archives**: Archives containing other archives (e.g., `backup.zip` containing `daily.tar.gz` containing `access.log`)

### 5.2 File Pattern Matching

**nginx Log Patterns:**
- `access.log` (current log)
- `access.log.1`, `access.log.2`, etc. (rotated logs)
- `access.log.1.gz`, `access.log.10.gz` (compressed rotated logs)

**Nexus Log Patterns:**
- `request.log` (current log)
- `request.log.1.gz` (rotated logs)
- `nexus_logs_20250612_112311.tar` (timestamped archives)
- `nexus_logs_20250613_083245.tar.gz` (compressed timestamped archives)

### 5.3 Archive Processing Logic

```python
# Pseudo-code for nested archive processing
def process_directory(directory_path, target_patterns):
    for file_path in discover_files(directory_path):
        if matches_archive_format(file_path):
            for extracted_item in extract_archive_recursive(file_path):
                if matches_target_pattern(extracted_item.name, target_patterns):
                    yield process_log_file(extracted_item)
        elif matches_target_pattern(file_path.name, target_patterns):
            yield process_log_file(file_path)

def extract_archive_recursive(archive_path, max_depth=3):
    """
    Recursively extract archives with depth protection.
    Handles nested scenarios like backup.zip -> daily.tar.gz -> access.log
    """
    for item in extract_archive(archive_path):
        if matches_archive_format(item.name) and max_depth > 0:
            # Recursively process nested archive
            yield from extract_archive_recursive(item, max_depth - 1)
        else:
            yield item
```

### 5.4 Nested Archive Processing

**Recursive Extraction Requirements:**
- Support archives within archives (e.g., `backup.zip` containing `daily.tar.gz` containing `access.log`)
- Maximum nesting depth of 3 levels to prevent infinite recursion
- Maintain file source tracking through nested extractions
- Proper resource cleanup for temporary extracted files

**Safety Considerations:**
- **Depth Limiting**: Prevent infinite recursion with configurable max depth
- **Size Limits**: Track cumulative extracted size across all nesting levels
- **Path Validation**: Validate paths at each extraction level
- **Resource Management**: Clean up temporary files from nested extractions

**Implementation Notes:**
- Use temporary directories for nested extractions
- Track extraction chain for error reporting: `backup.zip -> daily.tar.gz -> access.log:line_123`
- Support mixed archive types in nesting (zip containing tar.gz, etc.)
- Fail gracefully on corrupted nested archives while continuing with other files

### 5.5 Memory-Efficient Processing

- **Chunked Reading**: Read files in 8KB chunks
- **Line Buffering**: Process logs in batches of 1000 lines
- **Stream Processing**: Use generators to avoid loading entire files into memory
- **Resource Cleanup**: Properly close file handles and database connections

## 6. Log Parsing Specifications

### 6.1 nginx Log Format

**Format Pattern:**
```
IP - user - [timestamp] "method path HTTP/version" status size "referer" "user-agent"
```

**Example:**
```
116.202.29.193 - - [29/May/2025:00:00:09 -0400] "POST /api/v4/jobs/request HTTP/1.1" 204 0 "-" "gitlab-runner 17.10.1..."
```

**Parsing Requirements:**
- Extract IP address, timestamp, HTTP method, path, status code
- Handle quoted fields that may contain spaces
- Parse timestamp into ISO format for database storage
- Preserve original log line for debugging

### 6.2 Nexus Log Format

**Format Pattern:**
```
IP - user - [timestamp] "method path HTTP/version" status - size1 size2 "user-agent" [thread-info]
```

**Example:**
```
10.1.6.4 - - [12/Jun/2025:06:06:02 +0000] "GET / HTTP/1.0" 200 - 7927 93 "Mozilla/5.0..." [qtp1399093517-103]
```

**Parsing Requirements:**
- Extract all nginx fields plus additional response size and thread info
- Handle two response size fields (some may be empty "-")
- Parse thread pool information from brackets

### 6.3 Error Handling

**Malformed Log Processing:**
- Log errors to stdout with format: `PARSE_ERROR: {file_path}:{line_number} - {error_message}`
- Continue processing remaining lines
- Track error counts for summary reporting
- Store raw log lines even if parsing fails partially

## 7. Web Interface Requirements

### 7.1 Frontend Components

**Main Page Layout:**
- Header with application title and navigation
- Two preview sections showing first 10 rows from each table
- SQL query interface with textarea and execute button
- Results display area with formatted output
- Error message display area

**HTML Element IDs (for testing):**
```html
<!-- Table previews -->
<div id="nginx-preview-section">
  <table id="nginx-table">...</table>
</div>
<div id="nexus-preview-section">
  <table id="nexus-table">...</table>
</div>

<!-- SQL query interface -->
<div id="query-section">
  <textarea id="sql-query" placeholder="Enter SELECT query..."></textarea>
  <button id="execute-query">Execute Query</button>
</div>

<!-- Results and errors -->
<div id="query-results"></div>
<div id="error-messages"></div>
```

### 7.2 API Endpoints

```python
# FastAPI route specifications
GET  /                          # Serve main HTML page
GET  /api/nginx-preview         # First 10 nginx log entries
GET  /api/nexus-preview         # First 10 nexus log entries
POST /api/execute-query         # Execute SQL query
GET  /api/table-info           # Database schema information
```

### 7.3 SQL Query Security

- **Whitelist**: Only allow SELECT statements
- **Query Validation**: Parse and validate SQL before execution
- **Result Limits**: Enforce maximum result set size (1000 rows)
- **Timeout Protection**: Set query execution timeouts
- **Error Sanitization**: Clean error messages before displaying

## 8. MCP Server Specifications

### 8.1 MCP Tools

**Tool 1: list_database_schema**
```json
{
  "name": "list_database_schema",
  "description": "List all database tables and their complete schemas including column types and indexes",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Tool 2: execute_sql_query**
```json
{
  "name": "execute_sql_query",
  "description": "Execute a SELECT SQL query against the log analysis database",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "SQL SELECT query"},
      "limit": {"type": "integer", "description": "Max rows (default: 100)"}
    },
    "required": ["query"]
  }
}
```

**Tool 3: get_table_sample**
```json
{
  "name": "get_table_sample",
  "description": "Get sample rows from a specific table",
  "inputSchema": {
    "type": "object",
    "properties": {
      "table_name": {"type": "string", "enum": ["nginx_logs", "nexus_logs"]},
      "limit": {"type": "integer", "default": 10}
    },
    "required": ["table_name"]
  }
}
```

### 8.2 MCP Server Features

- **Concurrent Operation**: Run alongside web server
- **Security**: Same query restrictions as web interface
- **Error Handling**: Proper error responses to LLM clients
- **JSON Formatting**: Structure responses for LLM consumption
- **Schema Introspection**: Dynamic database schema discovery

## 9. Testing Requirements

### 9.1 Test Data Setup

**Sample Data Structure:**
```
tests/sample_data/
├── nginx/
│   ├── access.log                    # Current log file
│   ├── access.log.1.gz              # Rotated compressed log
│   ├── access.log.10.gz             # Older rotated log
│   ├── monthly_backup.tar.gz        # Archive containing access logs
│   ├── daily_logs.zip               # Zip archive with access logs
│   └── nested_backup.zip            # Zip containing tar.gz with access logs
├── nexus/
│   ├── request.log                   # Current log file
│   ├── request.log.1.gz             # Rotated compressed log
│   ├── nexus_logs_20250612_112311.tar       # Timestamped archive
│   ├── nexus_logs_20250613_083245.tar.gz    # Compressed timestamped
│   ├── backup_20250614.zip          # Archive containing request logs
│   └── weekly_archive.tar           # Tar containing multiple .gz files
└── malformed/
    ├── bad_nginx_access.log.gz       # Invalid log entries
    ├── bad_nexus_logs.tar            # Malformed nexus logs
    └── deeply_nested.zip             # Test depth limit protection
```

### 9.2 Unit Tests

**File: `tests/unit/test_nginx_processor.py`**
- Test regex parsing of various nginx log formats
- Test timestamp parsing and conversion
- Test handling of quoted fields with spaces
- Test malformed log entry handling

**File: `tests/unit/test_nexus_processor.py`**
- Test nexus-specific log format parsing
- Test thread info extraction
- Test dual response size field handling

**File: `tests/unit/test_file_handler.py`**
- Test archive extraction for all supported formats
- Test file pattern matching with wildcards
- Test nested directory traversal
- Test nested archive processing with depth limits
- Test error handling for corrupt archives
- Test resource cleanup for temporary files

**File: `tests/unit/test_database_operations.py`**
- Test database schema creation
- Test batch insert operations
- Test query execution with limits
- Test index creation and performance

### 9.3 Integration Tests

**File: `tests/integration/test_end_to_end.py`**
- Test complete pipeline from files to database
- Test processing of sample data archives
- Test error reporting and logging
- Test configuration management

**File: `tests/integration/test_api_endpoints.py`**
- Test all FastAPI endpoints
- Test SQL query execution via API
- Test error handling and response formats

### 9.4 Playwright E2E Tests

**File: `tests/playwright/test_web_interface.py`**
- Test table preview display
- Test SQL query execution through UI
- Test error message display
- Test results pagination

**File: `run_playwright_e2e.sh`**
- Setup test database with known data
- Start application in test mode
- Run Playwright tests
- Cleanup and shutdown

### 9.5 MCP Server Tests

**File: `tests/unit/test_mcp_server.py`**
- Test MCP tool registration
- Test schema inspection functionality
- Test query execution through MCP
- Test security restrictions

## 10. Performance Requirements

### 10.1 Processing Performance

- **File Processing**: Handle log files up to 1GB efficiently
- **Memory Usage**: Maximum 512MB RAM during processing
- **Database Inserts**: Minimum 10,000 entries per second
- **Query Response**: Web queries under 5 seconds

### 10.2 Scalability Considerations

- **Batch Size Tuning**: Configurable batch sizes for different environments
- **Index Strategy**: Optimize indexes for common query patterns
- **Connection Management**: Efficient SQLite connection pooling
- **Resource Cleanup**: Proper cleanup to prevent memory leaks

## 11. Security Considerations

### 11.1 SQL Injection Prevention

- **Query Validation**: Parse and validate all SQL queries
- **Parameterized Queries**: Use parameterized queries for dynamic content
- **Whitelist Approach**: Only allow SELECT statements
- **Error Sanitization**: Clean database errors before displaying

### 11.2 File System Security

- **Path Validation**: Validate and sanitize file paths
- **Archive Bomb Protection**: Limit extraction size and depth
- **Permission Checks**: Verify file permissions before processing
- **Temporary File Handling**: Secure cleanup of temporary files

## 12. Deployment and Operations

### 12.1 Application Startup

1. **Validation Phase**: Validate configuration and file paths
2. **Database Setup**: Create fresh database with schema and indexes
3. **Processing Phase**: Process all log files from configured directories
4. **Server Startup**: Start web server and optionally MCP server
5. **Ready State**: Application ready for queries

### 12.2 Monitoring and Logging

- **Processing Stats**: Log file counts, entry counts, error counts
- **Performance Metrics**: Processing time, memory usage, database size
- **Error Tracking**: Detailed error logs with context
- **Health Checks**: Endpoint for service health monitoring

### 12.3 Configuration Management

- **Environment Variables**: Support for containerized deployments
- **Configuration Validation**: Startup validation of all settings
- **Default Values**: Sensible defaults for all optional parameters
- **Documentation**: Clear documentation of all configuration options

## 13. Extension Points

### 13.1 Adding New Log Formats

1. **Create Processor Class**: Inherit from `BaseLogProcessor`
2. **Implement Parsing Logic**: Define regex patterns and field extraction
3. **Add Database Schema**: Create table schema for new format
4. **Register Processor**: Add to processor factory
5. **Add Tests**: Unit and integration tests for new format

### 13.2 Adding New Archive Formats

1. **Extend File Handler**: Add extraction logic for new format
2. **Update Discovery Logic**: Recognize new file extensions
3. **Add Tests**: Test extraction and error handling
4. **Update Documentation**: Document new supported formats

This specification provides comprehensive guidance for implementing a production-ready log analysis application with all required features and proper architecture for maintainability and extensibility.

