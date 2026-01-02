# Scripts

Utility scripts for logfile-mcp-server development, testing, and demonstration.

---

## Available Scripts

### create_demo_db.py

**Purpose**: Create a demo database with realistic sample data for testing and demonstration.

**Usage**:
```bash
uv run python scripts/create_demo_db.py
```

**What it does**:
- Creates `demo.db` in the project root
- Populates database with sample nginx and nexus log entries
- Uses shared test database factory (from `tests/fixtures/test_database.py`)
- Provides realistic test data matching production log formats

**Output**:
- Database file: `demo.db`
- Sample counts displayed (nginx and nexus entries)

**When to use**:
- Testing the web interface locally
- Demonstrating log analysis features
- VS Code Copilot MCP integration testing
- E2E test preparation

**Example output**:
```
🚀 Creating demo database using shared test factory...
✅ Demo database created successfully!
📊 Database populated with:
   - 15 nginx log entries
   - 10 nexus log entries
   - Realistic test data from sample logs
🌐 You can now start the web interface or connect VS Code Copilot
```

---

### start_web.py

**Purpose**: Quick-start script for launching the web interface with demo settings.

**Usage**:
```bash
# Option 1: Direct execution
uv run python scripts/start_web.py

# Option 2: With uvicorn (auto-reload for development)
uv run uvicorn scripts.start_web:app --reload
```

**What it does**:
- Creates FastAPI web app with default demo configuration
- Uses `demo.db` database (create with `create_demo_db.py` first)
- Starts web server on http://localhost:8000
- Configured for development with auto-reload

**When to use**:
- Quick local development testing
- Demonstrating web interface features
- Alternative to `uv run python -m app.main` with manual configuration

**Note**: For production use, prefer the main entry point:
```bash
uv run python -m app.main --nexus-dir /path/to/logs --nginx-dir /path/to/logs
```

---

## Adding New Scripts

When creating new utility scripts, follow these conventions:

### Naming Convention
- Use descriptive verb_noun format: `{verb}_{noun}.py`
- Examples: `migrate_database.py`, `export_logs.py`, `validate_config.py`

### Script Structure
```python
#!/usr/bin/env python3
"""
AI: Brief description of what this script does.

Detailed explanation of purpose, usage, and any important notes.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import Settings
# ... other imports

def main():
    """AI: Main entry point for the script."""
    # Implementation
    pass

if __name__ == "__main__":
    main()
```

### Documentation Requirements
1. Add docstring explaining purpose
2. Update this README.md with:
   - Script name and purpose
   - Usage examples
   - Expected output
   - When to use it
3. Use "AI:" prefix in docstrings (project convention)
4. Include error handling and user-friendly messages

---

## Common Use Cases

### Quick Demo Setup
```bash
# 1. Create demo database
uv run python scripts/create_demo_db.py

# 2. Start web interface
uv run python scripts/start_web.py

# 3. Open browser to http://localhost:8000
```

### Testing MCP Integration
```bash
# 1. Create demo database
uv run python scripts/create_demo_db.py

# 2. Start MCP server in stdio mode
uv run python -m app.main --db-name demo.db --mcp-stdio

# 3. Connect VS Code Copilot (configured in .vscode/mcp.json)
# Ask: "Show me the nginx log table structure"
```

### Full Development Workflow
```bash
# 1. Create demo database
uv run python scripts/create_demo_db.py

# 2. Run all tests
uv run pytest

# 3. Start web interface
uv run python -m app.main --db-name demo.db --web-port 8000
```

---

## Related Documentation

- [AGENTS.md](../AGENTS.md) - Developer guide with complete project patterns
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [README.md](../README.md) - User-facing documentation with usage examples

---

## Script Maintenance

**When modifying scripts**:
- [ ] Test the script works as documented
- [ ] Update this README if behavior changes
- [ ] Add to CHANGELOG.md if user-facing
- [ ] Ensure all 330 tests still pass
- [ ] Follow [Python Best Practices](../docs/best-practices/PYTHON.md)
