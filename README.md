# Log Analysis Application

A Python FastAPI application for loading, parsing, correlating, and analyzing access logs from Nexus Repository and nginx reverse proxy.

## Phase 1: Foundation Complete ✅

This implementation provides the foundation for the log analysis application:

- ✅ Complete project structure per specification
- ✅ Configuration management with CLI and environment support
- ✅ Database models and connection management
- ✅ Basic unit tests for configuration validation
- ✅ Fresh database creation on each startup

## Phase 2: Core Processing Complete ✅

The log processing engine is now fully implemented:

- ✅ Memory-efficient log processing with chunked reading
- ✅ Abstract BaseLogProcessor with concrete nginx/Nexus implementations
- ✅ File discovery system with archive support (.tar, .zip, nested)
- ✅ Processing orchestration with statistics and error handling
- ✅ Comprehensive test coverage (54/54 tests passing)
- ✅ End-to-end workflow validation with demo script

## Phase 3: Web Interface Complete ✅

Full-featured web interface with comprehensive testing:

- ✅ FastAPI web application with responsive HTML/CSS interface
- ✅ Table previews for nginx and nexus logs with sample data display
- ✅ SQL query interface with custom query execution and pre-built examples
- ✅ Error handling with user-friendly error messages and security validation
- ✅ Health check endpoints for system monitoring
- ✅ Comprehensive Playwright E2E testing (13/13 tests passing)
- ✅ Real nginx log format support (GitLab runner logs)
- ✅ Apache-style log format standardization

## Features

- Parse nginx and Nexus access logs from various archive formats
- Store parsed data in SQLite database with optimized indexing
- **Web interface for data viewing and SQL querying** ✅ **Complete**
- **MCP server for LLM integration (VS Code Copilot)** ✅ **Complete**
- Interactive table previews with sample data
- Custom SQL query execution with result display
- Pre-built example queries for common analysis tasks
- VS Code Copilot integration with database querying capabilities
- Support for configurable file patterns and nested archive processing

## Documentation

- **[Technical Specification](docs/SPEC.md)** - Comprehensive architecture and implementation details
- **[Architectural Decision Records](docs/adr/)** - Design decisions and rationale

## Installation

### Prerequisites
Install [uv](https://docs.astral.sh/uv/) for fast Python package management:

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with homebrew (macOS)
brew install uv
```

### Setup

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"

# Or install everything at once
uv pip install -e ".[dev]"
```

## Usage

### Quick Start with VS Code Copilot Integration

```bash
# 1. Create demo database using shared test factory
uv run python scripts/create_demo_db.py

# 2. VS Code Copilot will automatically connect using .vscode/mcp.json
# 3. Ask Copilot questions about your log data:
#    - "Show me the nginx log table structure"
#    - "What are the most common HTTP methods?"
#    - "Find all 404 errors"
```

### Quick Start with Sample Data

```bash
# Create demo database with sample data and start web interface
uv run python scripts/create_demo_db.py

# Start the web application with demo data
uv run python -m app.main --nexus-dir ./sample_logs/nexus --nginx-dir ./sample_logs/nginx --db-name demo.db

# Access the web interface at http://localhost:8000
```

### Basic Usage

```bash
# Process logs from directories and start web interface
uv run python -m app.main --nexus-dir /path/to/nexus/logs --nginx-dir /path/to/nginx/logs --process-logs

# Or activate environment first
source .venv/bin/activate  # Linux/macOS
python -m app.main --nexus-dir /path/to/nexus/logs --nginx-dir /path/to/nginx/logs --process-logs
```

### Full Configuration

```bash
uv run python -m app.main \\
  --nexus-dir /path/to/nexus/logs \\
  --nginx-dir /path/to/nginx/logs \\
  --process-logs \\
  --db-name analysis.db \\
  --nexus-pattern "request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz" \\
  --nginx-pattern "access.log*" \\
  --enable-mcp-server \\
  --mcp-port 8001 \\
  --web-port 8000 \\
  --max-archive-depth 3
```

### MCP Server Integration

The application includes a comprehensive **Model Context Protocol (MCP)** server for LLM integration:

#### VS Code Copilot Integration

Connect VS Code Copilot to your log analysis database:

```bash
# Start MCP server for VS Code Copilot (stdio mode)
uv run python -m app.main --db-name log_analysis.db --mcp-stdio
```

VS Code configuration is automatically set up in `.vscode/mcp.json`. Once connected, you can ask Copilot:

- *"Show me the nginx log table structure"*
- *"What are the most common HTTP methods in the logs?"* 
- *"Find all 404 errors from the last day"*
- *"Show me sample nexus log entries"*

#### Network MCP Server

For other MCP clients, use network mode:

```bash
# Start with web interface AND MCP server
uv run python -m app.main --nexus-dir /logs/nexus --nginx-dir /logs/nginx --enable-mcp-server --mcp-port 8001
```

#### Available MCP Tools

1. **`list_database_schema`** - Inspect database structure and relationships
2. **`execute_sql_query`** - Run secure SELECT queries with result limits
3. **`get_table_sample`** - Preview table data with configurable row limits

#### MCP Security Features

- Only SELECT statements allowed (no data modification)
- Query result limits to prevent memory issues
- Input validation and sanitization
- Comprehensive error handling and logging

### Environment Configuration

Create a `.env` file:

```env
NEXUS_DIR=/path/to/nexus/logs
NGINX_DIR=/path/to/nginx/logs
DB_NAME=log_analysis.db
NEXUS_PATTERN=request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz
NGINX_PATTERN=access.log*
ENABLE_MCP_SERVER=true
MCP_PORT=8001
WEB_PORT=8000
MAX_ARCHIVE_DEPTH=3
```

## Testing

### Comprehensive Test Suite

The application includes multiple layers of testing:

#### Unit Tests
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific processor tests
uv run pytest tests/unit/test_nginx_processor.py -v
uv run pytest tests/unit/test_nexus_processor.py -v
uv run pytest tests/unit/test_database_operations.py -v
```

#### Integration Tests
```bash
# Run integration tests
uv run pytest tests/integration/ -v

# Run web interface integration tests
uv run pytest tests/integration/test_web_interface_integration.py -v

# Run MCP server integration tests
uv run pytest tests/integration/test_mcp_integration.py -v
```

#### End-to-End (E2E) Tests with Playwright
```bash
# Run comprehensive E2E tests (recommended)
./run_playwright_e2e.sh

# Or run Playwright tests directly
uv run pytest tests/playwright/test_web_interface.py -v

# Run E2E tests with browser visible (for debugging)
uv run pytest tests/playwright/test_web_interface.py -v --headed
```

#### Complete Test Suite
```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term

# Run all tests in parallel (faster)
uv run pytest -n auto

# Run tests by category
uv run pytest -m "not e2e"        # Skip E2E tests for faster runs
uv run pytest -m "unit"           # Unit tests only  
uv run pytest -m "integration"    # Integration tests only
uv run pytest -m "e2e"            # E2E tests only

# Alternative: activate environment first
source .venv/bin/activate  # Linux/macOS
pytest --cov=app --cov-report=html
```

#### Test Coverage Reporting
```bash
# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
# View report: open htmlcov/index.html

# Generate terminal coverage report
uv run pytest --cov=app --cov-report=term-missing
```

### Test Categories Explained

- **Unit Tests**: Test individual components in isolation (processors, database operations)
- **Integration Tests**: Test component interactions and workflows
- **E2E Tests**: Test complete user workflows through the web interface using real browsers
- **Playwright Tests**: Comprehensive browser automation testing (13 test scenarios)

## Development Phases

### ✅ Phase 1: Foundation (`feature/project-setup`)
- Project structure and dependencies
- Configuration management with validation
- Database models and connection setup
- Basic unit tests

### ✅ Phase 2: Core Processing (`feature/phase2-log-processing`)
- Memory-efficient log processing architecture
- File discovery and pattern matching with archive support
- nginx and Nexus log format parsing with regex patterns
- Processing orchestration with statistics tracking
- Comprehensive unit and integration tests (54/54 passing)

### ✅ Phase 3: Web Interface (`feature/web-interface`)
- FastAPI application with HTML templates
- Table preview endpoints
- SQL query interface with security
- Results display and error handling

### ✅ Phase 4: MCP Integration (`feature/mcp-server`)
- Integrated MCP server with dual transport support (stdio + network)
- VS Code Copilot integration via stdio transport
- Database schema inspection tools
- LLM integration with secure query endpoints
- Comprehensive MCP tool testing and validation

### ⏳ Phase 5: Testing & Polish (`feature/comprehensive-tests`)
- Full test coverage
- Playwright E2E tests
- Performance optimizations
- Documentation completion

## Architecture

**For complete architecture details, see [Technical Specification](docs/SPEC.md)**

```
app/
├── __init__.py
├── main.py                    # CLI entry point and application startup
├── config.py                  # Configuration management (.env support)
├── database/
│   ├── __init__.py
│   ├── connection.py          # SQLite connection management
│   ├── models.py              # SQLAlchemy models (NginxLog, NexusLog)
│   └── operations.py          # Database CRUD operations
├── processors/               # Log parsing (Phase 2)
├── web/                     # FastAPI web interface (Phase 3)
├── mcp/                     # MCP server for LLM integration (Phase 4) ✅
│   ├── __init__.py
│   ├── server.py            # Integrated MCP server with dual transport
│   └── tools.py             # MCP tool implementations
├── static/                  # Web assets (Phase 3)
└── scripts/                 # Utility scripts for setup and development
    └── create_demo_db.py    # Demo database creation using shared factory
```

## Configuration Options

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| `--nexus-dir` | `NEXUS_DIR` | Optional* | Path to Nexus logs directory |
| `--nginx-dir` | `NGINX_DIR` | Optional* | Path to nginx logs directory |
| `--db-name` | `DB_NAME` | `log_analysis.db` | SQLite database filename |
| `--nexus-pattern` | `NEXUS_PATTERN` | `request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz` | Nexus file patterns |
| `--nginx-pattern` | `NGINX_PATTERN` | `access.log*` | nginx file patterns |
| `--process-logs` | - | `false` | Process log files and populate database |
| `--enable-mcp-server` | `ENABLE_MCP_SERVER` | `false` | Enable MCP server (network mode) |
| `--mcp-stdio` | - | `false` | Run MCP server in stdio mode for VS Code Copilot |
| `--mcp-port` | `MCP_PORT` | `8001` | MCP server port (network mode) |
| `--web-port` | `WEB_PORT` | `8000` | Web server port |
| `--max-archive-depth` | `MAX_ARCHIVE_DEPTH` | `3` | Maximum nested archive depth |

*Required only when using `--process-logs`

## Troubleshooting

### Common Issues

1. **No data displayed in web interface**: Run data processing first with `--process-logs`
2. **VS Code Copilot not connecting**: Ensure database exists and check `.vscode/mcp.json` configuration
3. **MCP tool errors**: Verify database path and ensure SELECT-only queries are being used
4. **Test failures**: Ensure web server is not running during tests
5. **Port conflicts**: Change ports in configuration if 8000/8001 are in use
6. **Missing dependencies**: Reinstall with `uv sync --dev`
7. **Database issues**: Delete `log_analysis.db` to reset and reprocess logs
8. **Archive processing**: Ensure tar/gzip files are properly formatted and readable

### Development Notes

- Web interface uses FastAPI with automatic OpenAPI documentation
- Database uses SQLite with SQLAlchemy ORM
- MCP server supports both stdio (VS Code) and network transports
- MCP tools provide secure database access with SELECT-only queries
- E2E testing requires Playwright browser automation
- Log processing supports nested archives with depth limits
- Comprehensive error handling and logging throughout application
- Single entry point eliminates duplicate server implementations

## Log Formats Supported

### nginx Access Logs
```
IP - user - [timestamp] "method path HTTP/version" status size "referer" "user-agent"
```

### Nexus Access Logs  
```
IP - user - [timestamp] "method path HTTP/version" status - size1 size2 "user-agent" [thread-info]
```

## Archive Formats Supported

- Single compressed files: `*.gz`
- Tar archives: `*.tar`, `*.tar.gz`  
- Zip archives: `*.zip`
- Nested archives up to configurable depth

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following coding guidelines
3. Add comprehensive tests
4. Submit pull request for review

## License

MIT License - see LICENSE file for details.
