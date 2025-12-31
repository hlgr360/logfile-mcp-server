# Python Best Practices

**Convention Type**: Reusable across projects
**Last Updated**: 2025-12-31

## Overview

Use Python's type system and best practices to catch bugs early, improve code quality, and maintain consistency. This guide covers type safety, dependency management, error handling, and Pythonic patterns applicable to any Python 3.10+ project.

## Type Safety with typing Module

### Goals

1. **Type hints for IDE support**: Enable autocomplete, refactoring, and navigation
2. **Self-documenting code**: Types serve as inline documentation
3. **Runtime validation with Pydantic**: Catch configuration errors before execution
4. **Reduced runtime errors**: Many bugs caught during development

### Common Patterns

#### 1. Type Hints with typing Module

```python
from typing import List, Dict, Optional, Iterator, Tuple, Any
from pathlib import Path

def parse_log_line(line: str, line_number: int, source_file: str) -> Optional[Dict[str, Any]]:
    """Parse individual log line with detailed error reporting."""
    try:
        return apply_regex_parsing(line)
    except ParsingError as e:
        logger.error(f"PARSE_ERROR: {source_file}:{line_number} - {e}")
        return None  # Continue processing other lines

def process_large_file(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Process large file using generators for memory efficiency."""
    with open(file_path) as f:
        for line_number, line in enumerate(f, start=1):
            parsed = parse_log_line(line, line_number, file_path.name)
            if parsed:
                yield parsed
```

**Benefits:**
- ✅ IDE autocomplete knows `line` is a string
- ✅ Type checker catches `parse_log_line(123, ...)` as error
- ✅ `Optional[Dict]` documents that function may return None
- ✅ `Iterator[Dict]` indicates generator function

#### 2. Pydantic for Runtime Validation

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path

class Settings(BaseModel):
    """Application configuration with runtime validation."""

    db_name: str = Field(default="logs.db", description="SQLite database filename")
    chunk_size: int = Field(default=1000, gt=0, description="Processing batch size")
    log_patterns: List[str] = Field(default_factory=lambda: ["*.log"])
    max_archive_depth: int = Field(default=3, ge=0, le=10)

    @validator('db_name')
    def validate_db_name(cls, v: str) -> str:
        """Ensure database name has .db extension."""
        if not v.endswith('.db'):
            raise ValueError('Database name must end with .db')
        return v

    @validator('log_patterns')
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """Ensure patterns list is not empty."""
        if not v:
            raise ValueError('log_patterns cannot be empty')
        return v

# Usage
try:
    settings = Settings(db_name="data.sqlite")  # ❌ Raises ValidationError
except ValidationError as e:
    print(f"Configuration error: {e}")

settings = Settings(db_name="data.db")  # ✅ Valid
```

**Benefits:**
- ✅ Configuration errors caught at startup, not during processing
- ✅ Clear error messages for invalid values
- ✅ Type coercion (strings to ints, etc.) handled automatically
- ✅ Environment variable loading with `pydantic-settings`

#### 3. Context Managers for Resources

```python
from contextlib import contextmanager
from typing import Iterator
import sqlite3

@contextmanager
def database_session(db_path: str) -> Iterator[sqlite3.Connection]:
    """Provide database connection with automatic commit/rollback."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage
with database_session("logs.db") as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs VALUES (?, ?)", (timestamp, message))
    # Automatically committed on success, rolled back on exception
```

**Benefits:**
- ✅ Resources always cleaned up (even on exceptions)
- ✅ Prevents resource leaks (file handles, database connections)
- ✅ Clearer intent than try/finally blocks
- ✅ Composable with nested context managers

## Dependency Management with UV

### UV Commands

```bash
# Project setup
uv sync                    # Install all dependencies from lock file
uv add package_name       # Add new dependency to pyproject.toml
uv add --dev pytest       # Add development dependency
uv remove package_name    # Remove dependency

# Running commands in UV environment
uv run python -m app.main  # Run application
uv run pytest              # Run tests
uv run python script.py    # Run script

# Environment management
uv venv                    # Create virtual environment (if needed)
uv pip list                # List installed packages
```

### Why UV over pip

| Feature | UV | pip |
|---------|-----|-----|
| Dependency resolution | ✅ Fast (Rust-based) | ❌ Slow (Python) |
| Lock file management | ✅ Automatic `uv.lock` | ❌ Manual `requirements.txt` |
| Virtual environment | ✅ Integrated | ⚠️  Separate tool (venv) |
| Deterministic builds | ✅ Yes (lock file) | ❌ No (unless frozen) |
| Cross-platform | ✅ Consistent | ⚠️  Platform differences |

### Dependency Guidelines

**DO:**
- ✅ Use `uv add` for all new dependencies
- ✅ Prefix commands with `uv run` to ensure correct environment
- ✅ Commit both `pyproject.toml` and `uv.lock` to git
- ✅ Use `--dev` flag for development-only tools (pytest, black, ruff)
- ✅ Run `uv sync` after pulling changes

**DON'T:**
- ❌ Use `pip install` directly
- ❌ Manually edit `uv.lock` file
- ❌ Add production dependencies with `--dev` flag
- ❌ Forget to run `uv sync` in CI/CD pipelines

## Error Handling Patterns

### Custom Exceptions

Define specific exception types for different error categories:

```python
class ApplicationError(Exception):
    """Base exception for application-specific errors."""
    pass

class LogParsingError(ApplicationError):
    """Raised when log entry cannot be parsed."""
    pass

class ArchiveExtractionError(ApplicationError):
    """Raised when archive extraction fails."""
    pass

class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid."""
    pass

class DatabaseError(ApplicationError):
    """Raised when database operations fail."""
    pass
```

**Benefits:**
- ✅ Specific exception types for different failures
- ✅ Can catch category of errors: `except ApplicationError`
- ✅ Clear intent in exception hierarchy
- ✅ Easy to add context-specific data to exceptions

### Exception Handling with Context

```python
def parse_log_line(line: str, line_number: int, source_file: str) -> Optional[Dict]:
    """Parse individual log line with detailed error reporting."""
    try:
        return _parse_regex(line)
    except LogParsingError as e:
        logger.error(f"PARSE_ERROR: {source_file}:{line_number} - {e}")
        return None  # Continue processing other lines
    except Exception as e:
        logger.error(f"UNEXPECTED_ERROR: {source_file}:{line_number} - {e}")
        return None

def process_file(file_path: Path) -> int:
    """Process log file and return count of successful entries."""
    count = 0
    try:
        with open(file_path) as f:
            for line_number, line in enumerate(f, start=1):
                parsed = parse_log_line(line, line_number, file_path.name)
                if parsed:
                    count += 1
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise  # Re-raise to caller
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        raise

    return count
```

**Patterns:**
- ✅ Specific exceptions for specific errors
- ✅ Log error context (filename, line number) before continuing
- ✅ Return None for recoverable errors, raise for fatal errors
- ✅ Re-raise system exceptions (FileNotFoundError, PermissionError)

## Pythonic Patterns

### Generators for Memory Efficiency

```python
def process_large_file(file_path: Path, chunk_size: int = 1000) -> Iterator[List[Dict]]:
    """
    Process large file in chunks using generators.

    Memory usage: O(chunk_size) instead of O(file_size)
    """
    with open(file_path) as f:
        batch = []
        for line in f:
            parsed = parse_line(line)
            if parsed:
                batch.append(parsed)

            if len(batch) >= chunk_size:
                yield batch  # Yield chunk
                batch = []  # Reset for next chunk

        if batch:  # Yield final partial chunk
            yield batch

# Usage - processes file in constant memory
for batch in process_large_file(Path("huge.log")):
    database.insert_batch(batch)  # Process one chunk at a time
```

**Benefits:**
- ✅ Constant memory usage regardless of file size
- ✅ Start processing before entire file is loaded
- ✅ Can chain generators: `filtered = (x for x in data if condition)`
- ✅ Lazy evaluation - only compute when needed

### List/Dict Comprehensions

```python
# ✅ Good: Concise and readable
patterns = [p.strip() for p in pattern_string.split(',') if p.strip()]

# ✅ Good: Dictionary comprehension
status_counts = {status: len(entries) for status, entries in grouped_by_status.items()}

# ✅ Better with generator for large datasets
pattern_gen = (p.strip() for p in pattern_string.split(',') if p.strip())

# ❌ Bad: Traditional loop for simple transformation
patterns = []
for p in pattern_string.split(','):
    if p.strip():
        patterns.append(p.strip())
```

### Pathlib for File Operations

```python
from pathlib import Path

# ✅ Good: Modern pathlib
log_dir = Path("logs")
for log_file in log_dir.glob("*.log"):
    if log_file.stat().st_size > 0:
        process_file(log_file)

# ❌ Bad: Old os.path approach
import os
log_dir = "logs"
for filename in os.listdir(log_dir):
    if filename.endswith(".log"):
        full_path = os.path.join(log_dir, filename)
        if os.path.getsize(full_path) > 0:
            process_file(full_path)
```

**Benefits:**
- ✅ Object-oriented interface (`path.parent`, `path.stem`, `path.suffix`)
- ✅ Cross-platform path handling
- ✅ Built-in glob support: `Path("dir").glob("*.log")`
- ✅ Chainable operations: `path.resolve().parent / "other_file.txt"`

## Code Quality Standards

### Docstring Requirements

```python
def process_log(file_path: Path, settings: Settings) -> int:
    """
    AI: Process log file and insert entries into database.

    The "AI:" prefix indicates this code is AI-generated or AI-maintained.
    Use this prefix consistently for all AI-written docstrings.

    Args:
        file_path: Path to log file (must exist and be readable)
        settings: Application settings with database config

    Returns:
        Number of entries successfully processed

    Raises:
        FileNotFoundError: If log file doesn't exist
        PermissionError: If log file cannot be read
        ProcessingError: If processing fails for other reasons

    Example:
        >>> settings = Settings(db_name="test.db")
        >>> count = process_log(Path("app.log"), settings)
        >>> print(f"Processed {count} entries")
    """
    pass
```

**Docstring Standards:**
- ✅ Use "AI:" prefix for AI-generated/maintained code
- ✅ Include Args, Returns, Raises sections
- ✅ Document exceptions that can be raised
- ✅ Provide usage examples for complex functions
- ✅ Describe validation performed on arguments

### Zero Warnings Requirement

**MANDATORY:** All code must execute without warnings:

```bash
# ✅ Good: Clean test output
$ uv run pytest
===== 42 tests passed in 2.1s =====

# ❌ Bad: Warnings present
$ uv run pytest
DeprecationWarning: function 'old_api' is deprecated
ResourceWarning: unclosed file <_io.TextIOWrapper>
===== 42 tests passed in 2.1s =====
```

**Common Warning Sources:**

| Warning Type | Cause | Fix |
|--------------|-------|-----|
| DeprecationWarning | Using deprecated API | Migrate to new API |
| ResourceWarning | File/connection not closed | Use context managers |
| UnusedImportWarning | Import not used | Remove import |
| UnreachableCodeWarning | Code after return/raise | Remove dead code |

**How to Achieve Zero Warnings:**
- ✅ Use context managers for all resources
- ✅ Remove unused imports (use `ruff check --select F401`)
- ✅ Migrate from deprecated APIs immediately
- ✅ Properly await async operations
- ✅ Close database connections explicitly

### Type Checking

```bash
# Optional but recommended: mypy for static type checking
uv add --dev mypy
uv run mypy app/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Benefits:**
- ✅ Catch type errors before runtime
- ✅ Enforce type hints across codebase
- ✅ Gradual adoption (can enable per-file)

## Testing Best Practices

### Test Structure

```python
import pytest
from pathlib import Path

def test_parse_valid_log_line():
    """AI: Test parsing of valid Apache log line."""
    # Arrange
    line = '127.0.0.1 - - [01/Jan/2025:12:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234'

    # Act
    result = parse_log_line(line, line_number=1, source_file="test.log")

    # Assert
    assert result is not None
    assert result["ip"] == "127.0.0.1"
    assert result["status"] == 200
    assert result["size"] == 1234

def test_parse_invalid_log_line():
    """AI: Test that invalid lines return None and don't raise exceptions."""
    # Arrange
    line = "invalid log format"

    # Act
    result = parse_log_line(line, line_number=1, source_file="test.log")

    # Assert
    assert result is None  # Graceful degradation
```

**Test Principles:**
- ✅ Arrange-Act-Assert pattern
- ✅ One logical assertion per test
- ✅ Descriptive test names: `test_<what>_<condition>_<expected>`
- ✅ Test both happy path and error cases

See [TESTING.md](./TESTING.md) for comprehensive testing strategies.

## Performance Patterns

### Use Generators for Large Data

```python
# ❌ Bad: Loads entire file into memory
def get_all_entries(file_path: Path) -> List[Dict]:
    entries = []
    with open(file_path) as f:
        for line in f:
            entries.append(parse_line(line))
    return entries  # Memory usage: O(file_size)

# ✅ Good: Process one entry at a time
def get_entries(file_path: Path) -> Iterator[Dict]:
    with open(file_path) as f:
        for line in f:
            yield parse_line(line)  # Memory usage: O(1)
```

### Batch Database Operations

```python
# ❌ Bad: Individual inserts
for entry in entries:
    cursor.execute("INSERT INTO logs VALUES (?)", (entry,))

# ✅ Good: Batch insert
cursor.executemany("INSERT INTO logs VALUES (?)", entries)
```

## Related Conventions

- See [DEVELOPMENT.md](./DEVELOPMENT.md) for git workflow and code quality standards
- See [TESTING.md](./TESTING.md) for comprehensive testing patterns
- See [SECURITY.md](./SECURITY.md) for security best practices
- See [LOGGING.md](./LOGGING.md) for logging patterns (adapt TypeScript examples to Python)

## Version History

- **2025-12-31**: Initial Python best practices document
- Adapted from TypeScript best practices
- Focused on Python 3.10+ features
- Added UV dependency management patterns
- Added Pydantic validation patterns
- Added generator and context manager patterns
