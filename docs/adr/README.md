# Architectural Decision Records (ADRs)

This directory contains all architectural decisions made during the development of logfile-mcp-server.

---

## What are ADRs?

Architectural Decision Records document significant architectural choices made during project development. Each ADR captures:
- **Context**: The problem or situation requiring a decision
- **Decision**: The choice that was made
- **Consequences**: The positive, negative, and neutral outcomes

ADRs help future contributors understand **why** decisions were made, not just **what** was implemented.

---

## Active ADRs

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-01](./ADR_20250728_01_general.md) | General Architectural Principles | Accepted | 2025-07-28 |
| [ADR-02](./ADR_20250728_02_adopt_uv.md) | Adopt UV for Python Package Management | Accepted | 2025-07-28 |
| [ADR-03](./ADR_20250728_03_chunk_size_lines.md) | Change chunk_size from Bytes to Lines | Accepted | 2025-07-28 |
| [ADR-04](./ADR_20250728_04_architectural_pattern_consistency.md) | Architectural Pattern Consistency Prevention | Accepted | 2025-07-28 |
| [ADR-05](./ADR_20250731_05_test_database_consolidation.md) | Test Database Consolidation | Accepted | 2025-07-31 |
| [ADR-06](./ADR_20250731_06_mcp_server_integration.md) | MCP Server Integration Architecture | Accepted | 2025-07-31 |
| [ADR-08](./ADR_20250802_08_systematic_test_coverage_assessment.md) | Systematic Test Coverage Assessment | Accepted | 2025-08-02 |

---

## ADR Quick Reference

### Development & Tooling
- **[ADR-02](./ADR_20250728_02_adopt_uv.md)**: Why we use UV instead of pip for package management (10-100x faster)
- **[ADR-08](./ADR_20250802_08_systematic_test_coverage_assessment.md)**: Systematic test coverage process after major milestones

### Architecture & Patterns
- **[ADR-01](./ADR_20250728_01_general.md)**: Foundational architectural principles (separate models, single process, modular design)
- **[ADR-04](./ADR_20250728_04_architectural_pattern_consistency.md)**: Why configuration must use dependency injection (no hardcoded patterns)
- **[ADR-06](./ADR_20250731_06_mcp_server_integration.md)**: Single entry point with dual transport support (stdio + network)

### Testing & Data
- **[ADR-05](./ADR_20250731_05_test_database_consolidation.md)**: Shared test database factory pattern to eliminate duplication
- **[ADR-03](./ADR_20250728_03_chunk_size_lines.md)**: Why chunk_size represents lines, not bytes (log entry integrity)

---

## How to Use ADRs

### When Reading Code
- Wondering why a specific approach was chosen? Check relevant ADRs
- ADRs are referenced in code comments and documentation
- Use the Quick Reference above to find decisions by topic

### When Making Changes
- If you're changing architecture, **create a new ADR** (don't modify existing ones)
- ADRs document the rationale, helping future contributors understand trade-offs
- See [DEVELOPMENT.md](../best-practices/DEVELOPMENT.md) for ADR lifecycle rules

### ADR Lifecycle Rules
1. **Never modify accepted ADRs** - They're historical records
2. **Create new ADRs** when decisions change - Mark old ADRs as "Superseded by ADR-XX"
3. **Reference ADRs** in code comments and documentation
4. **Update status** only (Proposed → Accepted, Accepted → Superseded)

---

## ADR Naming Convention

**Format**: `ADR_YYYYMMDD_NN_description.md`

**Examples**:
- `ADR_20250728_01_general.md` - General principles from July 28, 2025
- `ADR_20250731_06_mcp_server_integration.md` - MCP server decision from July 31, 2025

**Benefits**:
- Chronological ordering (date-based)
- Easy to find latest decisions
- Sequential numbering prevents conflicts

---

## Creating New ADRs

See [DEVELOPMENT.md](../best-practices/DEVELOPMENT.md#architectural-decision-records) for ADR template and creation guidelines.

**Quick template**:
```markdown
# ADR_YYYYMMDD_NN: [Title]

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XX

## Date
YYYY-MM-DD

## Context
What problem are we solving? What constraints exist?

## Decision
What did we decide to do?

## Consequences

### Positive
- Benefits of this decision

### Negative
- Drawbacks or costs

### Neutral
- Neither good nor bad but worth noting

## References
- Links to docs, commits, discussions
```

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - How project implements these decisions
- [SPEC.md](../SPEC.md) - Technical specification based on these decisions
- [DEVELOPMENT.md](../best-practices/DEVELOPMENT.md) - ADR lifecycle and creation guidelines
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - How to contribute to this project

---

## See Also

- [ADR GitHub Organization](https://adr.github.io/) - ADR resources and best practices
- [Keep a Changelog](https://keepachangelog.com/) - Complementary to ADRs for version tracking
