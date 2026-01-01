# Contributing to Logfile MCP Server

Thank you for your interest in contributing to Logfile MCP Server! This project provides log analysis capabilities for Nexus Repository and nginx access logs through both a web interface and MCP (Model Context Protocol) integration.

**For AI Agents**: This guide is designed for both human and AI contributors (like Claude Code). Follow the conventions strictly and reference the detailed documentation in `docs/best-practices/`.

---

## 📚 Universal Best Practices

**Before contributing, read these universal guidelines:**

- 📘 **[Pull Request Best Practices](./docs/best-practices/PULL_REQUESTS.md)** - PR workflow, Definition of Done, review checklist
- 📘 **[Testing Best Practices](./docs/best-practices/TESTING.md)** - Testing strategy and coverage
- 📘 **[Python Best Practices](./docs/best-practices/PYTHON.md)** - Type hints, Pydantic, UV, generators
- 📘 **[Logging Best Practices](./docs/best-practices/LOGGING.md)** - Semantic logging with Logger class
- 📘 **[Security Best Practices](./docs/best-practices/SECURITY.md)** - SQL injection, path validation, archive safety
- 📘 **[Documentation Best Practices](./docs/best-practices/DOCUMENTATION.md)** - Where and how to document

**This CONTRIBUTING.md focuses on Logfile MCP Server specifics.**

---

## 🚨 Mandatory PR Policy

**ALL code changes MUST go through pull requests. No direct commits to `main`.**

See [Pull Request Best Practices](./docs/best-practices/PULL_REQUESTS.md) for complete workflow.

---

## 🤝 How to Contribute

### Reporting Issues

- **Bug Reports**: Use GitHub Issues with detailed reproduction steps, error logs, and environment details
- **Feature Requests**: Describe the use case and expected behavior
- **Questions**: Check existing issues and AGENTS.md first, then open a discussion

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/logfile-mcp-server.git
   cd logfile-mcp-server
   ```

2. **Install Dependencies**
   ```bash
   # Install uv (Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync

   # Install development dependencies
   uv sync --dev
   ```

3. **Build and Test**
   ```bash
   # Run all tests (330 tests: 281 unit, 28 integration, 8 E2E, 13 Playwright)
   uv run pytest

   # Run with coverage
   uv run pytest --cov=app --cov-report=html

   # Run specific test types
   uv run pytest tests/unit/          # Unit tests only
   uv run pytest tests/integration/   # Integration tests only
   uv run pytest tests/e2e/            # E2E tests only
   uv run pytest tests/playwright/    # Playwright tests only
   ```

4. **Setup Test Data** (optional, for E2E tests)
   ```bash
   # Create demo database with sample logs
   uv run python scripts/create_demo_db.py
   ```

---

## 🎯 Logfile MCP Server Specifics

### Before You Start

- Check existing issues and PRs to avoid duplication
- For major changes, open an issue first to discuss the approach
- **Read AGENTS.md thoroughly** - contains essential project context and patterns
- Review relevant best practices in `docs/best-practices/`
- **AI Agents**: Always use EnterPlanMode for non-trivial changes before implementing

### Development Conventions

This project follows standardized best practices documented in `docs/best-practices/`:

- **Logging**: Use Logger class (TRACE, DEBUG, INFO, WARN, ERROR), never `print()` (critical for MCP stdio protocol)
- **Python**: Type hints everywhere, Pydantic for validation, UV for dependency management
- **Testing**: Multi-layered (unit → integration → E2E), 88% overall coverage target
- **Security**: SQL injection prevention, path traversal protection, archive safety

### Log Analysis Guidelines

**Processor Pattern** (Critical for Adding New Log Types):

```python
# ✅ GOOD - Inherit from BaseLogProcessor
from app.processors.base import BaseLogProcessor

class MyLogProcessor(BaseLogProcessor):
    def __init__(self, settings: Settings, chunk_size: int = 10000, batch_size: int = 1000):
        super().__init__(settings, chunk_size, batch_size)
        self.regex_patterns = [...]  # Multiple patterns for fallback

    def parse_log_line(self, line: str, line_number: int, source_file: str) -> Optional[Dict]:
        # Parse with comprehensive error handling
        pass

# ❌ BAD - Custom implementation without BaseLogProcessor
class MyLogProcessor:
    def parse(self, line):  # No type hints, missing base features
        return line.split()
```

**When Adding New Log Types**:

1. Create processor in `app/processors/` inheriting from `BaseLogProcessor`
2. Add database model in `app/database/models.py` with SQLAlchemy
3. Add database operations in `app/database/` for type-specific queries
4. Update orchestrator in `app/processing/orchestrator.py` to include new type
5. Add configuration in `app/config.py` for patterns and directories
6. Add MCP tools in `app/mcp/tools.py` for LLM access

### Testing This Project

**Test Organization**:
- `tests/unit/` - Pure logic, mocked dependencies (281 tests)
- `tests/integration/` - Component integration tests (28 tests)
- `tests/e2e/` - Full workflow tests with real database (8 tests)
- `tests/playwright/` - Browser-based E2E tests (13 tests)
- `tests/fixtures/` - Sample log files for testing

**Project-Specific Requirements**:
- All tests use pytest
- Database tests use temporary SQLite databases
- Archive tests use tempfile for extraction
- Logger tests verify stderr output (never stdout)

**Coverage Expectations**:
- Core logic (processors, database): >90%
- Utilities (logger, config): >85%
- MCP server (stdio integration): >70%
- Overall: ~88% (current target)

See [Testing Best Practices](./docs/best-practices/TESTING.md) for universal testing guidelines.

### MCP Protocol Compliance

**Critical Requirements** (Non-Negotiable):

| Requirement | Why Critical | How to Verify |
|------------|--------------|---------------|
| 🔴 Stderr-only logging | stdout corrupts JSON-RPC protocol | All logger output uses `logger.*()`, never `print()` |
| 🔴 JSON-RPC format | Protocol standard | Run with `--mcp-stdio` and verify valid JSON output |
| 🔴 Tool descriptions | LLM needs clear instructions | Test with VS Code Copilot integration |

**Testing MCP Integration**:
```bash
# Test stdio mode (should output only JSON to stdout)
uv run python -m app.main --mcp-stdio

# Test with VS Code Copilot (add to .vscode/mcp.json)
# Ask: "Show me the nginx log table structure"
```

### Log Analysis Domain Considerations

**Parser Robustness**:
- Handle multiple log formats (Apache, custom timestamps, etc.)
- Use regex patterns with fallbacks
- Gracefully handle malformed lines (log error, continue parsing)
- Support compressed archives (tar, tar.gz, zip, gzip)

**Security Concerns**:
- Path traversal in archive extraction (use `_is_safe_path()`)
- SQL injection in query tools (use parameterized queries)
- Archive bomb attacks (limit extraction depth)
- Resource exhaustion (chunk processing, batch inserts)

**Performance Patterns**:
- Stream processing for large files (generators, not loading entire file)
- Batch database inserts (1000 records at a time)
- Chunked file reading (10,000 lines per chunk)
- Archive extraction to tempfile (cleanup after processing)

---

## ✅ Definition of Done

See [Pull Request Best Practices - Definition of Done](./docs/best-practices/PULL_REQUESTS.md#-definition-of-done) for complete checklist.

**Logfile MCP Server additions**:

### Documentation (Project-Specific)
- [ ] **AGENTS.md** updated if processors, tools, or workflows changed
- [ ] **README.md** updated if user-facing behavior changed
- [ ] **docs/SPEC.md** updated if technical implementation changed
- [ ] **CHANGELOG.md** entry added in `[Unreleased]` section
- [ ] **ADR** created if architectural decision made (in `docs/adr/`)
- [ ] **Type hints** added for all new functions and methods

### Testing (Project-Specific)
- [ ] All 330 tests pass (281 unit, 28 integration, 8 E2E, 13 Playwright)
- [ ] New tests follow project organization (unit/integration/e2e/playwright)
- [ ] Coverage meets target (>85% for new code)
- [ ] Tests verify stderr output for logger calls
- [ ] Archive tests use tempfile and cleanup properly
- [ ] Database tests use temporary databases

### Logging Compliance
- [ ] No `print()` statements in production code (use `logger.*()`)
- [ ] Logger output verified to go to stderr only
- [ ] Test mode suppression working (INFO/DEBUG hidden in tests)
- [ ] Log levels appropriate (TRACE/DEBUG/INFO/WARN/ERROR)

---

## 🔍 PR Review Process

See [Pull Request Best Practices - PR Review Checklist](./docs/best-practices/PULL_REQUESTS.md#-pr-review-checklist) for complete checklist.

### Project-Specific Review Items

**For Processor Changes**:
- [ ] Inherits from `BaseLogProcessor`
- [ ] Multiple regex patterns for fallback
- [ ] Comprehensive error handling (invalid timestamps, malformed lines)
- [ ] Type hints on all methods
- [ ] Database model updated if new fields added
- [ ] MCP tools updated if query capabilities changed

**For Database Changes**:
- [ ] SQLAlchemy models follow project patterns
- [ ] Database migrations tested (if applicable)
- [ ] Parameterized queries (no SQL injection risk)
- [ ] Indexes added for common query patterns
- [ ] Connection pooling respected

**For MCP Protocol Changes**:
- [ ] Stderr-only logging maintained
- [ ] JSON-RPC format valid
- [ ] Tool descriptions clear for LLMs
- [ ] Tested with VS Code Copilot integration
- [ ] No stdout pollution

**For Archive Processing**:
- [ ] Path traversal protection using `_is_safe_path()`
- [ ] Archive depth limits enforced
- [ ] Temporary directories cleaned up
- [ ] Supported formats: tar, tar.gz, zip, gzip
- [ ] Error handling for corrupt archives

---

## 🎯 Common Contribution Areas

**High Impact** (Prioritize These):
- **Log Parser Improvements**: Better handling of malformed lines, new timestamp formats
- **Performance Optimization**: Faster chunking, better batch sizes, streaming improvements
- **Error Handling**: Better error messages with actionable context
- **Test Coverage**: Add missing edge case tests
- **Documentation**: Update AGENTS.md with new patterns/processors

**Medium Impact**:
- **New Log Types**: Support additional log formats (Apache common, combined, etc.)
- **Database Queries**: More sophisticated correlation queries
- **MCP Tools**: Additional tool capabilities for LLM integration
- **Archive Support**: Better compression format handling

**Feature Ideas** (Assess Impact First):
- ✅ Additional log processors (e.g., Apache, HAProxy)
- ✅ Advanced correlation queries (cross-log analysis)
- ✅ Export capabilities (CSV, JSON)
- ⚠️ Real-time log streaming (requires architectural changes)
- ⚠️ Distributed processing (significant complexity)

---

## 💬 Getting Help

**Stuck on Something?**
- **Read AGENTS.md first** - contains debugging workflows and patterns
- Check `docs/best-practices/` for logging, testing, Python, PR workflow
- Look at existing code for patterns (e.g., similar processor implementations)
- Run tests with `-v` for verbose output: `uv run pytest -v`
- Open a draft PR with questions and context
- Ask in GitHub Discussions with error logs and reproduction steps

**Communication**:
- Be respectful and constructive
- Provide full context (what you tried, error messages, environment)
- Share error logs and reproduction steps
- Include test output showing failures
- Be patient with review feedback
- **AI Agents**: Include planning context and impact assessments

---

## 📋 Quick Reference

### Essential Commands

```bash
# Development
uv sync                          # Install/update dependencies
uv run python -m app.main        # Run web server
uv run python -m app.main --mcp-stdio  # Run MCP stdio server

# Testing
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/e2e/         # E2E tests only
uv run pytest -v --tb=short      # Verbose with short tracebacks
uv run pytest --cov=app          # With coverage report

# Database
uv run python scripts/create_demo_db.py  # Create demo database
rm log_analysis.db               # Delete database to start fresh

# Debugging
uv run pytest -v -s tests/unit/test_logger.py  # Run specific test with output
uv run python -c "from app.utils.logger import logger; logger.info('test')"  # Test logger
uv run python scripts/test_processors.py  # Test processor manually
```

### File Locations

- **Database**: `log_analysis.db` (created on first run)
- **Sample logs**: `sample_logs/` (nexus and nginx examples)
- **Fixtures**: `tests/fixtures/` (test data)
- **Best practices**: `docs/best-practices/`
- **ADRs**: `docs/adr/`
- **Spec**: `docs/SPEC.md`

### Key Documentation

- **[AGENTS.md](./AGENTS.md)** - Developer guide, patterns, workflows
- **[README.md](./README.md)** - User-facing features and setup
- **[docs/SPEC.md](./docs/SPEC.md)** - Technical specification and architecture
- **[docs/best-practices/](./docs/best-practices/)** - Universal guidelines

---

## 🙏 Thank You

**Thank you for contributing to Logfile MCP Server!**

Your contributions help make log analysis more accessible through AI-powered tools while maintaining robust parsing and security standards.

**For AI Agents**:
- Follow this guide strictly
- Reference AGENTS.md for project context
- Read [Pull Request Best Practices](./docs/best-practices/PULL_REQUESTS.md) for workflow
- Read [docs/best-practices/DOCUMENTATION.md](./docs/best-practices/DOCUMENTATION.md) for documentation structure
- Use EnterPlanMode for planning non-trivial changes
- Generate comprehensive tests
- **ALWAYS use feature branches and PRs** (never commit directly to main)
- **ALWAYS review documentation** during PR creation and review
- **NEVER use print()** - always use logger for output

**Maintainers**: This project welcomes contributions from both human developers and AI agents. Please review AI-generated PRs with the same rigor, checking for test coverage, convention adherence, logging compliance, and **complete documentation updates**.
