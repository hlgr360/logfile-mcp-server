# Logfile MCP Server

A powerful Python application for analyzing access logs from Nexus Repository and nginx reverse proxy. Provides both a web interface for interactive querying and an MCP (Model Context Protocol) server for AI-powered log analysis via VS Code Copilot and other LLM tools.

---

## Features

- ✅ **Parse Multiple Log Formats**: nginx and Nexus Repository access logs with flexible pattern matching
- ✅ **Archive Support**: Automatically extract and process logs from tar, tar.gz, zip, and nested archives
- ✅ **SQLite Database**: Fast, indexed storage for efficient querying of millions of log entries
- ✅ **Web Interface**: Interactive table previews and custom SQL query execution
- ✅ **AI Integration**: MCP server for VS Code Copilot - ask questions about your logs in natural language
- ✅ **Memory Efficient**: Stream-based processing handles multi-GB log files without loading into memory
- ✅ **Comprehensive Testing**: 330 tests (88% coverage) ensure reliability

---

## Quick Start

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) for fast Python package management:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with homebrew (macOS)
brew install uv
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/logfile-mcp-server.git
cd logfile-mcp-server

# Create virtual environment and install dependencies
uv sync
```

### Demo Setup

```bash
# 1. Create demo database with sample data
uv run python scripts/create_demo_db.py

# 2. Start web interface
uv run python -m app.main --db-name demo.db

# 3. Open browser to http://localhost:8000
```

---

## Usage

### Basic Log Processing

Process logs from directories and start the web interface:

```bash
uv run python -m app.main \
  --nexus-dir /path/to/nexus/logs \
  --nginx-dir /path/to/nginx/logs \
  --process-logs
```

The application will:
1. Discover all log files (including archives)
2. Parse log entries
3. Store in SQLite database (`log_analysis.db`)
4. Start web server on http://localhost:8000

### Web Interface

Access the web interface at `http://localhost:8000` to:
- View table previews (latest 10 entries from each log type)
- Execute custom SQL queries
- Explore sample queries for common analysis tasks
- View query results in formatted tables

**Example queries**:
```sql
-- Most common HTTP methods
SELECT method, COUNT(*) as count
FROM nginx_logs
GROUP BY method
ORDER BY count DESC;

-- Error responses in last day
SELECT * FROM nginx_logs
WHERE status_code >= 400
  AND timestamp >= datetime('now', '-1 day');

-- Top 10 most accessed paths
SELECT path, COUNT(*) as hits
FROM nginx_logs
GROUP BY path
ORDER BY hits DESC
LIMIT 10;
```

### AI-Powered Analysis with VS Code Copilot

The MCP server lets you analyze logs using natural language through VS Code Copilot:

**Setup**:
```bash
# Start MCP server in stdio mode
uv run python -m app.main --db-name log_analysis.db --mcp-stdio
```

VS Code Copilot is automatically configured via `.vscode/mcp.json`.

**Example questions** you can ask Copilot:
- *"Show me the nginx log table structure"*
- *"What are the most common HTTP methods in my logs?"*
- *"Find all 404 errors from the last day"*
- *"Show me sample nexus log entries"*
- *"Which paths have the most traffic?"*

### Advanced Configuration

```bash
uv run python -m app.main \
  --nexus-dir /path/to/nexus/logs \
  --nginx-dir /path/to/nginx/logs \
  --process-logs \
  --db-name analysis.db \
  --nexus-pattern "request.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz" \
  --nginx-pattern "access.log*" \
  --enable-mcp-server \
  --mcp-port 8001 \
  --web-port 8000 \
  --max-archive-depth 3
```

### Environment Configuration

Create a `.env` file for persistent configuration:

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

See [.env.example](./.env.example) for all available options.

---

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

---

## Supported Log Formats

### nginx Access Logs
```
IP - user - [timestamp] "method path HTTP/version" status size "referer" "user-agent"
```

**Example**:
```
116.202.29.193 - - [29/May/2025:00:00:09 -0400] "POST /api/v4/jobs/request HTTP/1.1" 204 0 "-" "gitlab-runner 17.10.1"
```

### Nexus Repository Logs
```
IP - user - [timestamp] "method path HTTP/version" status - size1 size2 time "user-agent" [thread-info]
```

**Example**:
```
10.1.6.4 - - [12/Jun/2025:06:06:02 +0000] "GET / HTTP/1.0" 200 - 7927 93 "Mozilla/5.0" [qtp1399093517-103]
```

---

## Archive Support

Automatically extracts and processes logs from:
- **Compressed files**: `*.gz`
- **Tar archives**: `*.tar`, `*.tar.gz`, `*.tar.bz2`
- **Zip archives**: `*.zip`
- **Nested archives**: Up to 3 levels deep (e.g., `backup.zip` → `daily.tar.gz` → `access.log`)

---

## MCP Server Integration

### Available MCP Tools

The MCP server provides three tools for AI-powered log analysis:

1. **`list_database_schema`** - Inspect database structure and relationships
2. **`execute_sql_query`** - Run secure SELECT queries with result limits
3. **`get_table_sample`** - Preview table data with configurable row limits

### Security Features

- ✅ Only SELECT statements allowed (no data modification)
- ✅ Query result limits to prevent memory issues
- ✅ Input validation and sanitization
- ✅ Comprehensive error handling and logging

### Network MCP Server

For other MCP clients (not VS Code Copilot), use network mode:

```bash
uv run python -m app.main \
  --nexus-dir /logs/nexus \
  --nginx-dir /logs/nginx \
  --enable-mcp-server \
  --mcp-port 8001
```

---

## Testing

### Run All Tests

```bash
# All 330 tests (281 unit, 28 integration, 8 E2E, 13 Playwright)
uv run pytest

# With coverage report
uv run pytest --cov=app --cov-report=html --cov-report=term

# Run in parallel (faster)
uv run pytest -n auto
```

### Run Specific Test Types

```bash
# Unit tests only (fast)
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# E2E tests with Playwright
./run_playwright_e2e.sh

# Or run Playwright tests directly
uv run pytest tests/playwright/test_web_interface.py -v

# With browser visible (debugging)
uv run pytest tests/playwright/test_web_interface.py -v --headed
```

### Test Coverage

View HTML coverage report:
```bash
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Troubleshooting

### Common Issues

**No data displayed in web interface**
- Run data processing first with `--process-logs`
- Verify database file exists: `ls -lh log_analysis.db`

**VS Code Copilot not connecting**
- Ensure database exists: `uv run python scripts/create_demo_db.py`
- Check `.vscode/mcp.json` configuration
- Verify MCP server starts without errors

**MCP tool errors**
- Verify database path is correct
- Ensure only SELECT queries are being used
- Check MCP server logs for specific errors

**Test failures**
- Ensure web server is not running during tests
- Delete `log_analysis.db` and rerun tests
- Check for port conflicts (8000/8001 in use)

**Port conflicts**
- Change ports in configuration: `--web-port 8080 --mcp-port 8002`
- Check which process is using the port: `lsof -i :8000`

**Missing dependencies**
- Reinstall with `uv sync --dev`
- Verify uv is up to date: `uv --version`

**Database issues**
- Delete database to start fresh: `rm log_analysis.db`
- Reprocess logs with `--process-logs`

**Archive processing errors**
- Ensure tar/gzip files are properly formatted
- Check file permissions are readable
- Reduce `--max-archive-depth` if extraction is too slow

---

## Documentation

- **[Technical Specification](docs/SPEC.md)** - Complete architecture and implementation details
- **[Developer Guide](AGENTS.md)** - For contributors and AI coding assistants
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to this project
- **[Architectural Decisions](docs/adr/)** - Design decisions and rationale
- **[Best Practices](docs/best-practices/)** - Universal development standards

---

## Contributing

We welcome contributions from both human developers and AI coding assistants!

See [CONTRIBUTING.md](./CONTRIBUTING.md) for complete guidelines.

**Quick summary**:
- ✅ **All changes MUST go through pull requests** (no direct commits to main)
- ✅ Follow [Python Best Practices](docs/best-practices/PYTHON.md)
- ✅ Ensure all 330 tests pass before creating PR
- ✅ Use `logger.*()` for all output (never `print()` - corrupts MCP stdio protocol)
- ✅ Add type hints to all functions
- ✅ Write comprehensive tests (>85% coverage for new code)
- ✅ Update documentation (AGENTS.md, SPEC.md, CHANGELOG.md)

**For AI Agents**:
- Read [AGENTS.md](./AGENTS.md) thoroughly before contributing
- Use EnterPlanMode for non-trivial changes
- Always create feature branch
- Never commit directly to main

---

## License

MIT License - see [LICENSE](./LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/logfile-mcp-server/issues)
- **Documentation**: [docs/](./docs/)
- **Developer Guide**: [AGENTS.md](./AGENTS.md)
