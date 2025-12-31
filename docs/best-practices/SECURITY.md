# Security Best Practices

**Convention Type**: Reusable across projects
**Last Updated**: 2025-12-31

## Overview

Security best practices for web applications and file processing systems. This guide covers SQL injection prevention, file system security, archive handling, and input validation patterns applicable to any Python application.

## SQL Injection Prevention

### Always Use Parameterized Queries

**The Golden Rule:** Never concatenate user input into SQL queries.

```python
import sqlite3

# ❌ DANGEROUS: SQL injection vulnerability
def get_logs_by_status(status_code: int):
    cursor.execute(f"SELECT * FROM logs WHERE status = {status_code}")
    # Attacker input: "200 OR 1=1" returns all rows
    # Attacker input: "200; DROP TABLE logs--" drops table

# ✅ SAFE: Parameterized query
def get_logs_by_status(status_code: int):
    cursor.execute("SELECT * FROM logs WHERE status = ?", (status_code,))
    # Parameters are automatically escaped, preventing injection
```

**SQLAlchemy Example:**

```python
from sqlalchemy import text

# ❌ DANGEROUS: String formatting
query = f"SELECT * FROM users WHERE username = '{username}'"
session.execute(text(query))

# ✅ SAFE: Parameterized query
query = text("SELECT * FROM users WHERE username = :username")
session.execute(query, {"username": username})
```

**Benefits:**
- ✅ Parameters are automatically escaped
- ✅ Type checking enforced by database
- ✅ Query plan caching improves performance
- ✅ Works with all data types (strings, numbers, dates)

### Query Validation with sqlparse

For applications that accept user-provided SQL queries (dashboards, analytics tools), validate query structure:

```python
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML

def validate_select_only(query: str) -> bool:
    """
    Validate that query contains only SELECT statements.

    Prevents destructive operations (INSERT, UPDATE, DELETE, DROP, etc.)
    in user-provided queries.

    Args:
        query: SQL query string to validate

    Returns:
        True if query contains only SELECT statements, False otherwise

    Example:
        >>> validate_select_only("SELECT * FROM users")
        True
        >>> validate_select_only("DROP TABLE users")
        False
    """
    try:
        parsed = sqlparse.parse(query)

        for statement in parsed:
            # Reject non-SELECT operations
            if statement.get_type() != 'SELECT':
                return False

            # Additional check: look for forbidden keywords
            forbidden_keywords = {'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE'}
            tokens = [token.value.upper() for token in statement.tokens if token.ttype is Keyword or token.ttype is DML]

            if any(keyword in tokens for keyword in forbidden_keywords):
                return False

        return True

    except Exception:
        # Reject unparseable queries
        return False

def sanitize_query(query: str, max_results: int = 1000) -> str:
    """
    Add safety limits to user queries.

    Args:
        query: SQL query to sanitize
        max_results: Maximum number of results to return

    Returns:
        Query with LIMIT clause added
    """
    query = query.strip()

    # Remove trailing semicolon if present
    if query.endswith(';'):
        query = query[:-1]

    # Add LIMIT if not already present
    if 'LIMIT' not in query.upper():
        query += f' LIMIT {max_results}'

    return query

# Usage
user_query = request.get("query")

if not validate_select_only(user_query):
    raise SecurityError("Query must contain only SELECT statements")

safe_query = sanitize_query(user_query)
results = database.execute(safe_query)
```

**Additional SQL Security Measures:**

1. **Use Read-Only Database Connections** for user queries:
```python
# SQLite
conn = sqlite3.connect('file:path/to/db.db?mode=ro', uri=True)

# PostgreSQL
conn = psycopg2.connect(database="mydb", user="readonly_user", ...)
```

2. **Implement Query Timeouts:**
```python
cursor.execute("PRAGMA query_timeout = 30000")  # 30 second timeout
```

3. **Log All User Queries for Auditing:**
```python
logger.info(f"User query executed: {query}", extra={"user_id": user.id})
```

## File System Security

### Path Traversal Prevention

**The Threat:** Users might provide paths like `../../etc/passwd` to access files outside allowed directories.

```python
from pathlib import Path

def validate_file_path(file_path: Path, allowed_base: Path) -> bool:
    """
    Validate that file path is within allowed directory.

    Prevents directory traversal attacks (../, ../../, symlinks).

    Args:
        file_path: Path to validate
        allowed_base: Base directory that file must be within

    Returns:
        True if path is safe, False otherwise

    Example:
        >>> validate_file_path(Path("logs/app.log"), Path("/var/logs"))
        True
        >>> validate_file_path(Path("../../etc/passwd"), Path("/var/logs"))
        False
    """
    try:
        # Resolve to absolute paths (resolves symlinks and ..)
        resolved_path = file_path.resolve()
        allowed_resolved = allowed_base.resolve()

        # Check if resolved path starts with allowed base
        return resolved_path.is_relative_to(allowed_resolved)

    except Exception:
        # Reject paths that can't be resolved
        return False

# Usage in web endpoint
@app.get("/download/{filename}")
def download_log(filename: str):
    """Download log file with path validation."""

    log_dir = Path("/var/logs/application")
    file_path = log_dir / filename

    if not validate_file_path(file_path, log_dir):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
```

**Additional File Security Measures:**

1. **Whitelist Allowed Extensions:**
```python
ALLOWED_EXTENSIONS = {'.log', '.txt', '.csv'}

def validate_extension(file_path: Path) -> bool:
    """Only allow specific file types."""
    return file_path.suffix.lower() in ALLOWED_EXTENSIONS
```

2. **Check File Size Before Processing:**
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

def validate_file_size(file_path: Path) -> bool:
    """Prevent processing of excessively large files."""
    return file_path.stat().st_size <= MAX_FILE_SIZE
```

3. **Set Proper File Permissions:**
```python
import os

# Create file with restricted permissions (owner read/write only)
fd = os.open(file_path, os.O_CREAT | os.O_WRONLY, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(sensitive_data)
```

### Archive Security

**The Threats:**
- **Zip Bombs**: Small compressed file that expands to gigabytes
- **Directory Traversal**: Archive contains paths like `../../etc/passwd`
- **Symlink Attacks**: Archive contains symbolic links to sensitive files
- **Infinite Nesting**: Archive contains archive contains archive...

```python
import zipfile
import tarfile
from pathlib import Path

class SecurityError(Exception):
    """Raised when security validation fails."""
    pass

def safe_extract_archive(
    archive_path: Path,
    extract_to: Path,
    max_size: int = 100_000_000,  # 100 MB
    max_depth: int = 3
) -> None:
    """
    Safely extract archive with security checks.

    Prevents:
    - Zip bombs (size limit)
    - Directory traversal (path validation)
    - Infinite nesting (depth limit)

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to
        max_size: Maximum total extracted size in bytes
        max_depth: Maximum nesting level for recursive archives

    Raises:
        SecurityError: If archive fails security checks
    """
    total_size = 0

    # Ensure extract directory exists and is empty
    extract_to.mkdir(parents=True, exist_ok=True)

    if archive_path.suffix == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as archive:
            for member in archive.infolist():
                # Check 1: Prevent directory traversal
                if os.path.isabs(member.filename):
                    raise SecurityError(f"Absolute path in archive: {member.filename}")

                if '..' in member.filename:
                    raise SecurityError(f"Path traversal in archive: {member.filename}")

                # Check 2: Prevent zip bombs
                total_size += member.file_size
                if total_size > max_size:
                    raise SecurityError(
                        f"Archive too large (>{max_size} bytes) - possible zip bomb"
                    )

                # Check 3: Validate extraction path
                extract_path = extract_to / member.filename
                if not validate_file_path(extract_path, extract_to):
                    raise SecurityError(f"Unsafe extraction path: {member.filename}")

            # All checks passed - extract
            archive.extractall(extract_to)

    elif archive_path.suffix in {'.tar', '.gz', '.tgz', '.bz2'}:
        with tarfile.open(archive_path, 'r:*') as archive:
            for member in archive.getmembers():
                # Check 1: Prevent directory traversal
                if os.path.isabs(member.name):
                    raise SecurityError(f"Absolute path in archive: {member.name}")

                if '..' in member.name:
                    raise SecurityError(f"Path traversal in archive: {member.name}")

                # Check 2: Prevent symlink attacks
                if member.issym() or member.islnk():
                    raise SecurityError(f"Symbolic link in archive: {member.name}")

                # Check 3: Prevent zip bombs
                total_size += member.size
                if total_size > max_size:
                    raise SecurityError(
                        f"Archive too large (>{max_size} bytes) - possible zip bomb"
                    )

                # Check 4: Validate extraction path
                extract_path = extract_to / member.name
                if not validate_file_path(extract_path, extract_to):
                    raise SecurityError(f"Unsafe extraction path: {member.name}")

            # All checks passed - extract
            archive.extractall(extract_to)

    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

# Usage
try:
    safe_extract_archive(
        archive_path=Path("/uploads/user_data.zip"),
        extract_to=Path("/tmp/extracted"),
        max_size=50_000_000  # 50 MB limit
    )
except SecurityError as e:
    logger.error(f"Archive security check failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

**Recursive Archive Handling:**

```python
def process_archive_recursive(
    archive_path: Path,
    max_depth: int = 3,
    current_depth: int = 0
) -> None:
    """
    Process archives with nested archive support.

    Args:
        archive_path: Path to archive
        max_depth: Maximum recursion depth
        current_depth: Current recursion level (internal)

    Raises:
        SecurityError: If max depth exceeded
    """
    if current_depth > max_depth:
        raise SecurityError(
            f"Archive nesting too deep: {current_depth} levels (max: {max_depth})"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        extract_to = Path(temp_dir)
        safe_extract_archive(archive_path, extract_to)

        # Process extracted files
        for file_path in extract_to.rglob('*'):
            if file_path.is_file():
                # If it's another archive, recurse
                if file_path.suffix in {'.zip', '.tar', '.gz', '.tgz', '.bz2'}:
                    process_archive_recursive(file_path, max_depth, current_depth + 1)
                else:
                    process_file(file_path)
```

## Input Validation

### General Principles

1. **Validate Length:**
```python
def validate_username(username: str) -> bool:
    """Username must be 3-32 characters."""
    return 3 <= len(username) <= 32
```

2. **Validate Format with Regex:**
```python
import re

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_PATTERN.match(email))
```

3. **Use Pydantic for Complex Validation:**
```python
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r'^[a-zA-Z0-9_]+$')
    email: str = Field(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    age: int = Field(ge=0, le=150)

    @validator('username')
    def validate_username_not_reserved(cls, v):
        reserved_names = {'admin', 'root', 'system'}
        if v.lower() in reserved_names:
            raise ValueError('Username is reserved')
        return v
```

## Security Checklist

**Before Deployment:**

- [ ] All SQL queries use parameterized statements (no string concatenation)
- [ ] File paths validated against directory traversal
- [ ] Archive extraction includes size and depth limits
- [ ] User input validated for length, format, and allowed values
- [ ] Sensitive data (passwords, tokens) never logged
- [ ] Error messages don't expose system details
- [ ] Authentication required for sensitive endpoints
- [ ] Rate limiting implemented on public endpoints
- [ ] HTTPS enabled in production
- [ ] Security headers configured (CORS, CSP, etc.)

## Related Conventions

- See [PYTHON.md](./PYTHON.md) for Python coding standards
- See [DEVELOPMENT.md](./DEVELOPMENT.md) for security in development workflow
- See [TESTING.md](./TESTING.md) for security testing strategies

## Version History

- **2025-12-31**: Initial security best practices document
- Patterns extracted from logfile-mcp-server project
- Generalized for reuse across projects
