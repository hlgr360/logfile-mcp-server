# Documentation

Comprehensive documentation for logfile-mcp-server.

---

## For Users

**Getting Started**:
- [README.md](../README.md) - Installation, configuration, usage guide
- [SPEC.md](./SPEC.md) - Technical specification

**Understanding the Project**:
- [CHANGELOG.md](../CHANGELOG.md) - Version history and release notes
- [LICENSE](../LICENSE) - MIT License
- [ADDING_NEW_LOG_FORMATS.md](./ADDING_NEW_LOG_FORMATS.md) - How to add custom log formats

---

## For Contributors

**Essential Reading**:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines, PR process (if exists)
- [AGENTS.md](../AGENTS.md) - Complete project guide (for AI agents and developers)
- [Best Practices](./best-practices/README.md) - Universal development standards

**Before Contributing**:
1. Review [Development Best Practices](./best-practices/DEVELOPMENT.md) for git workflow
2. Check [Testing Best Practices](./best-practices/TESTING.md) for testing standards
3. Read [Python Best Practices](./best-practices/PYTHON.md) for coding standards

**Architecture Decision Records** (Why Decisions Were Made):
- [ADR Index](./adr/README.md) - All ADRs with quick navigation and rationale

**Development Best Practices** (Reusable Standards):
- [Python Standards](./best-practices/PYTHON.md) - Type hints, Pydantic, UV, error handling
- [Security Practices](./best-practices/SECURITY.md) - SQL injection, path validation, archive safety
- [Testing Best Practices](./best-practices/TESTING.md) - Multi-layered testing strategy
- [Logging Best Practices](./best-practices/LOGGING.md) - Semantic levels, stderr routing
- [Development Workflow](./best-practices/DEVELOPMENT.md) - Git workflow, zero warnings, ADR lifecycle
- [Documentation](./best-practices/DOCUMENTATION.md) - Two-tier documentation architecture

See [best-practices/README.md](./best-practices/README.md) for overview.

---

## Quick Links by Topic

### Configuration
- [README.md](../README.md) - MCP server setup and usage
- [SPEC.md](./SPEC.md) - Database schemas and API design

### Testing
- [Testing Best Practices](./best-practices/TESTING.md) - Multi-layered testing strategy
- [AGENTS.md](../AGENTS.md#testing-implementation-guidelines) - Project-specific test organization
- [Python Best Practices](./best-practices/PYTHON.md) - Testing patterns

### Development
- [Python Standards](./best-practices/PYTHON.md) - Type hints, Pydantic, UV
- [Security Practices](./best-practices/SECURITY.md) - SQL injection, path validation
- [Development Workflow](./best-practices/DEVELOPMENT.md) - Git workflow, zero warnings

### Architecture
- [SPEC.md](./SPEC.md) - System architecture and database design
- [AGENTS.md](../AGENTS.md#architecture-overview) - Architecture patterns
- [ADRs](./adr/README.md) - Why architectural decisions were made

### Best Practices
- [best-practices/README.md](./best-practices/README.md) - Overview of all best practices
- [DOCUMENTATION.md](./best-practices/DOCUMENTATION.md) - Two-tier documentation architecture

---

## For AI Agents

**Primary documentation**: [AGENTS.md](../AGENTS.md)

**Documentation Architecture**: This project uses a two-tier documentation system:
- **Tier 1 (Universal)**: Reusable best practices in `best-practices/` - can be copied to other projects
- **Tier 2 (Project-Specific)**: Implementation details in AGENTS.md, SPEC.md, ADRs

**Reading Order for AI Coding Assistants**:
1. **Start here**: [AGENTS.md](../AGENTS.md) - Complete project guide with architecture, patterns, workflow
2. **Best Practices**: Review applicable best practices before coding:
   - [Python Standards](./best-practices/PYTHON.md) - Type hints, Pydantic, UV, error handling
   - [Development Workflow](./best-practices/DEVELOPMENT.md) - Git workflow, zero warnings, PR process
   - [Testing Strategies](./best-practices/TESTING.md) - Multi-layered testing, coverage philosophy
   - [Security Practices](./best-practices/SECURITY.md) - SQL injection, path validation, archive safety
   - [Logging](./best-practices/LOGGING.md) - Semantic levels, stderr routing, test suppression
   - [Documentation](./best-practices/DOCUMENTATION.md) - Two-tier architecture guide
3. **Architecture**: [SPEC.md](./SPEC.md) - Database schemas, API design
4. **Decisions**: [ADRs](./adr/README.md) - Why architectural choices were made
5. **Feature Guide**: [ADDING_NEW_LOG_FORMATS.md](./ADDING_NEW_LOG_FORMATS.md) - Extending log formats

**Before making changes**:
- Read AGENTS.md thoroughly
- Review relevant best practices
- Check ADRs for decision context
- Use EnterPlanMode for non-trivial changes

---

## Keeping Documentation Updated

**When making changes**:

| Change Type | Update These Docs |
|-------------|-------------------|
| New MCP tool | README.md, AGENTS.md, CHANGELOG.md |
| Selector update | AGENTS.md (Current Selectors section) |
| Architecture change | ARCHITECTURE.md, AGENTS.md |
| New best practice | docs/best-practices/, CONTRIBUTING.md |
| Breaking change | CHANGELOG.md (with migration guide) |
| Bug fix | CHANGELOG.md |
| Debug script added | scripts/README.md, AGENTS.md |

See [CONTRIBUTING.md](../CONTRIBUTING.md#changelog-maintenance) for CHANGELOG update guidelines.
