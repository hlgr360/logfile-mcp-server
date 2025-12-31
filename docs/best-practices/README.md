# Development Best Practices

This directory contains reusable development best practices designed for the logfile-mcp-server project but applicable to any Python project.

---

## Overview

These best practices were developed through building a log analysis MCP server with complex testing needs. They're designed to be:
- **Project-agnostic**: Can be copied to any Python project
- **Self-contained**: Each best practice is fully documented
- **Practical**: Based on real-world experience, not theory

---

## Best Practices

### 📘 [Logging Best Practices](./LOGGING.md)

**Purpose**: Structured logging with semantic levels that respects protocol constraints

**Key Features**:
- Custom Logger class with 5 semantic levels (TRACE, DEBUG, INFO, WARN, ERROR)
- All logs to stderr (MCP protocol safety - stdout reserved for JSON-RPC)
- Automatic test suppression (no manual `if (!testing)` checks)
- Environment-aware configuration

**When to use**:
- Any project with structured logging needs
- Projects using stdio transport (MCP servers, CLIs)
- Projects requiring different log levels in dev vs production
- Projects with automated testing that needs clean output

---

### 📘 [Testing Best Practices](./TESTING.md)

**Purpose**: Multi-layered testing strategy with appropriate coverage targets

**Key Features**:
- 3-layer testing: Unit (fast) → Integration (fixtures) → E2E (comprehensive)
- Fixture-based testing with snapshots (fast, deterministic)
- Coverage philosophy: not all code needs 80% (appropriate targets vary by code type)
- Test organization patterns

**When to use**:
- Any project with complex testing needs
- Any project with multi-layered testing needs
- Projects where mocking provides limited value

**Coverage Guidance**:
- Core logic (validation, algorithms): 80%+
- Integration code: 50-60%
- Overall: Appropriate targets depend on code complexity

---

### 📘 [Python Best Practices](./PYTHON.md)

**Purpose**: Python coding standards for type safety and code quality

**Key Features**:
- Type hints with typing module
- Runtime validation with Pydantic
- UV dependency management
- Pythonic patterns (generators, context managers, comprehensions)
- Error handling and custom exceptions

**When to use**:
- Any Python project prioritizing type safety and code quality
- Projects with external data sources (APIs, file parsing, databases)
- Projects requiring runtime configuration validation
- Teams wanting to enforce consistent Python practices

---

### 📘 [Development Best Practices](./DEVELOPMENT.md)

**Purpose**: Universal development workflow and quality standards (git, testing, documentation)

**Key Features**:
- Git workflow and branch strategy (never commit to main)
- Zero warnings requirement for all tests
- Pre-commit and PR checklists
- Architecture Decision Record (ADR) lifecycle rules
- Common development pitfalls and how to avoid them

**When to use**:
- Any software project with team collaboration
- Projects using git with PR-based workflows
- Projects requiring consistent quality standards
- Teams with both human and AI developers

**What it covers**:
- Git branching and commit message conventions
- Code quality standards (zero warnings, style consistency)
- Testing requirements (coverage, isolation, determinism)
- Documentation requirements (README, ADRs, CHANGELOG)
- Pre-commit and pull request checklists

**Quick Example**:
```bash
# ❌ Don't commit to main
git checkout main
git commit -m "fix: update selector"

# ✅ Use feature branch + PR
git checkout -b fix/update-selector
git commit -m "fix: update selector fallback array"
git push origin fix/update-selector
# Create PR on GitHub
```

---

### 📘 [Documentation Best Practices](./DOCUMENTATION.md)

**Purpose**: Guidelines for organizing and maintaining project documentation

**Key Features**:
- Two-tier architecture (universal best practices vs project-specific)
- File organization patterns
- Documentation standards and quality checks
- When to update documentation
- Decision tree for where to add new docs

**When to use**:
- Any project with multiple documentation files
- Projects with both best practices and project-specific docs
- Teams with AI contributors who need clear documentation structure
- Projects wanting reusable documentation patterns

**What it covers**:
- Two-tier documentation architecture
- Quality checks for each tier (project-agnostic vs project-specific)
- Common documentation patterns (README, CONTRIBUTING, AGENTS.md, ADRs)
- How tiers connect (Best Practice → Application → Rationale)
- Documentation maintenance and health metrics

**Quick Example**:
```markdown
# ❌ BAD - Project-specific in best practices
Use Winston logger with our CloudWatch transport.

# ✅ GOOD - Universal pattern in best practices
Use a structured logger with semantic levels.
Choose a logger that fits your infrastructure.
```

---

## Using These Best Practices in Other Projects

### Option 1: Direct Copy
```bash
# Copy entire best-practices directory
cp -r docs/best-practices/ ../my-project/docs/

# Copy individual best practice
cp docs/best-practices/LOGGING.md ../my-project/docs/
```

### Option 2: Reference as Template
- Read the best practice
- Adapt to your project's needs
- Keep the core principles

---

## Project-Specific Implementations

These best practices are **standards**. For project-specific implementations, see:

- [AGENTS.md](../../AGENTS.md) - How logfile-mcp-server applies these best practices
- [SPEC.md](../../docs/SPEC.md) - Technical specification based on best practices

**Example**:
- [TESTING.md](./TESTING.md) defines multi-layered testing strategy (standard)
- [AGENTS.md](../../AGENTS.md#testing-implementation-guidelines) shows how logfile-mcp-server implements it

---

## See Also

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - How to contribute to this project
- [AGENTS.md](../../AGENTS.md) - Complete project guide
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Technical architecture
- [DOCUMENTATION.md](./DOCUMENTATION.md) - Documentation organization best practices

---

## License

These best practices are part of the logfile-mcp-server project and are licensed under the MIT License. You are free to use, modify, and distribute them in your own projects.
