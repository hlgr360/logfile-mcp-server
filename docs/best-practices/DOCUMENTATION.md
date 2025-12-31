# Documentation Best Practices

**Purpose**: Guidelines for organizing and maintaining project documentation

**Scope**: Project-agnostic documentation structure and organization principles

**Reusability**: Copy this file to any project and adapt examples as needed

---

## Table of Contents

- [Documentation Philosophy](#documentation-philosophy)
- [Two-Tier Architecture](#two-tier-architecture)
- [File Organization Patterns](#file-organization-patterns)
- [When to Update Documentation](#when-to-update-documentation)
- [Documentation Standards](#documentation-standards)
- [For AI Agents](#for-ai-agents)

---

## Documentation Philosophy

Effective project documentation maintains a **two-tier architecture** that separates:

1. **Universal Best Practices** - Project-independent standards (reusable across projects)
2. **Project-Specific Guidance** - Implementation details and decisions

**Why this separation?**
- ✅ **Reusability**: Best practices can be copied to other projects
- ✅ **Clarity**: Clear distinction between principles and implementations
- ✅ **Maintainability**: Project-specific docs stay focused, best practices stay portable
- ✅ **Discoverability**: Helps users find what they need quickly

---

## Two-Tier Architecture

### Tier 1: Universal Best Practices

**Characteristics**:
- ✅ **Project-agnostic**: No references to your specific project, product names, or tech stack details
- ✅ **Portable**: Can be copied to any project with minimal changes
- ✅ **Self-contained**: Each file is fully documented
- ✅ **Universal principles**: Describe patterns, not implementations

**Typical files**:
- `DEVELOPMENT.md` - Git workflow, quality standards, ADRs, checklists
- `LOGGING.md` - Logging patterns and semantic levels
- `TESTING.md` - Testing strategy and coverage philosophy
- `TYPESCRIPT.md` - Type safety guidelines
- `DOCUMENTATION.md` - This file
- `README.md` - Overview of all best practices

**Example** (Good - project-agnostic):
```markdown
## Semantic Log Levels

**TRACE**: Extremely detailed diagnostics (DOM selectors, API calls)
**DEBUG**: Development diagnostics (operation progress)
**INFO**: User-facing messages (operation start/complete)

Use these levels consistently across your project.
```
→ No specific project references, applicable to any project

**Example** (Bad - project-specific):
```markdown
## Logging in MyApp

Use `MyAppLogger.info()` for all user actions.
The logger outputs to CloudWatch in production.
```
→ Tied to specific project, not reusable

---

### Tier 2: Project-Specific Guidance

**Characteristics**:
- 🎯 **Context-specific**: References your specific tools, APIs, architecture
- 🎯 **Implementation details**: Exact commands, file paths, configuration
- 🎯 **Tool choices**: Why you chose framework X over Y
- 🎯 **Project conventions**: Your team's specific workflows

**Typical files**:
- `AGENTS.md` or `CLAUDE.md` - Project guide for AI assistants
- `CONTRIBUTING.md` - Contribution guidelines
- `ARCHITECTURE.md` - Technical architecture
- `README.md` - User-facing documentation
- `docs/adr/*.md` - Architecture Decision Records
- `docs/README.md` - Documentation navigation hub

**Example** (Good - project-specific):
```markdown
## Current API Endpoints

**Authentication** (v2.0+):
```typescript
POST /api/v2/auth/login
GET /api/v2/auth/session
```

→ Specific to your project's API structure

---

## File Organization Patterns

### Recommended Structure

```
your-project/
├── AGENTS.md                        # 📋 Tier 2: AI assistant guide
├── CONTRIBUTING.md                  # 📋 Tier 2: Contribution process
├── ARCHITECTURE.md                  # 📋 Tier 2: Technical architecture
├── README.md                        # 📋 Tier 2: User documentation
├── CHANGELOG.md                     # 📋 Tier 2: Version history
│
├── docs/
│   ├── README.md                    # 📋 Tier 2: Documentation navigation
│   │
│   ├── adr/                         # 📋 Tier 2: Architecture decisions
│   │   ├── README.md                # ADR index and guidance
│   │   ├── ADR_YYYYMMDD_NN_*.md     # Individual ADRs (date-based naming)
│   │   └── ...
│   │
│   └── best-practices/              # 📘 Tier 1: Universal standards
│       ├── README.md                # Best practices overview
│       ├── DEVELOPMENT.md           # Git, quality, ADRs
│       ├── DOCUMENTATION.md         # This file
│       ├── LOGGING.md               # Logging patterns
│       ├── TESTING.md               # Testing strategy
│       └── TYPESCRIPT.md            # Type safety (or language-specific)
│
└── ... (source code, tests, etc.)
```

**Legend**:
- 📘 **Tier 1** (Universal Best Practices) - Reusable across projects
- 📋 **Tier 2** (Project-Specific) - Your project's implementations

---

## When to Update Documentation

### Changes Requiring Documentation Updates

| Change Type | Update These Docs | Tier |
|-------------|-------------------|------|
| **New feature** | README.md, CHANGELOG.md, project guide | Tier 2 |
| **API change** | Project guide, API docs | Tier 2 |
| **Architecture change** | ARCHITECTURE.md, create ADR | Tier 2 |
| **New best practice** | docs/best-practices/, CONTRIBUTING.md | Tier 1 |
| **Breaking change** | CHANGELOG.md (with migration guide) | Tier 2 |
| **Bug fix** | CHANGELOG.md | Tier 2 |

**Golden Rule**: If a change affects user behavior or developer workflow, document it.

---

## Documentation Standards

### For Tier 1 (Universal Best Practices)

**DO**:
- ✅ Write for any project in your language/ecosystem
- ✅ Use hypothetical examples (not your project's specifics)
- ✅ Focus on principles and patterns
- ✅ Keep language tool-agnostic where possible
- ✅ Document the "why" behind practices

**DON'T**:
- ❌ Reference your project name or product
- ❌ Include project-specific implementation details
- ❌ Use project-specific examples (use generic ones)
- ❌ Assume specific libraries beyond common standards

**Quality Check**:
> "Can I copy this file to a new project and have it still be useful?"
>
> If yes → Good Tier 1 documentation ✅
>
> If no → Move content to Tier 2 or make it more generic

**Example refinement**:
```markdown
# ❌ BAD (too specific)
Use Winston logger with our custom transport to CloudWatch.

# ✅ GOOD (universal)
Use a structured logger with semantic levels (DEBUG, INFO, WARN, ERROR).
Choose a logger that fits your infrastructure (Winston, Bunyan, custom).
```

---

### For Tier 2 (Project-Specific Guidance)

**DO**:
- ✅ Reference best practices: "See `docs/best-practices/TESTING.md`"
- ✅ Provide exact implementation: "Run `npm test` (149 tests)"
- ✅ Link to ADRs: "See ADR-004 for why we chose X"
- ✅ Include project context: "Our API rate limit is 100 req/min"
- ✅ Document current state: "As of v2.0, we use React 18"

**DON'T**:
- ❌ Duplicate content from Tier 1 (link to it instead)
- ❌ Document principles without application (too abstract)
- ❌ Omit rationale (use ADRs to document "why")

**Quality Check**:
> "Does this help someone contribute to my specific project?"
>
> If yes → Good Tier 2 documentation ✅
>
> If no → Move to Tier 1 or delete if not valuable

**Example structure**:
```markdown
## Testing Strategy

See [Testing Best Practices](./docs/best-practices/TESTING.md) for our multi-layer approach.

**Our implementation**:
- Unit tests: Jest (127 tests, ~2s)
- Integration tests: Supertest (43 tests, ~10s)
- E2E tests: Playwright (56 tests, ~3min)
- Total: 226 tests, ~4min CI time

**Run tests**: `npm test`
```

---

## How Tiers Connect

**Pattern**: Best Practice → Application → Rationale

### Example: Logging

1. **Best Practice** (`docs/best-practices/LOGGING.md`):
   - "Use semantic log levels: TRACE, DEBUG, INFO, WARN, ERROR"

2. **Application** (project-specific docs):
   - "Use `logger.info()` for user-facing operations"
   - "Use `logger.trace()` for detailed diagnostics"

3. **Rationale** (ADR):
   - "Why custom Logger class instead of Winston" (ADR-004)
   - "Rationale: Protocol constraints required stderr-only logging"

---

### Example: Testing

1. **Best Practice** (`docs/best-practices/TESTING.md`):
   - "Use fixture-based testing for parsers"
   - "3-layer strategy: Unit → Integration → E2E"

2. **Application** (project-specific docs):
   - "Run `npm run fixtures:update` to refresh HTML snapshots"
   - "226 tests: 127 unit + 43 integration + 56 E2E"

3. **Rationale** (ADR):
   - "Why fixtures instead of mocks" (ADR-001)
   - "Benefits: 300x faster, deterministic, no auth required"

---

## For AI Agents

### Reading Order (New to Project)

1. **Start**: Project guide (AGENTS.md, CLAUDE.md, or CONTRIBUTING.md)
2. **Best Practices**: Review `docs/best-practices/` for standards
3. **Rationale**: Read relevant ADRs to understand decisions
4. **Navigation**: Use documentation index (docs/README.md)

---

### Before Making Changes

**Checklist**:
- [ ] Read project guide thoroughly
- [ ] Review relevant best practices
- [ ] Read ADRs to understand why decisions were made
- [ ] Use EnterPlanMode for non-trivial changes (if available)
- [ ] Follow contribution guidelines
- [ ] Create new ADRs for significant architectural decisions

---

### Adding New Documentation

**Decision Tree**:

```
Is this documentation specific to this project?
│
├── YES → Tier 2 (Project-Specific)
│   │
│   ├── Is it an architectural decision?
│   │   └── YES → Create ADR in docs/adr/
│   │
│   ├── Is it for AI assistants specifically?
│   │   └── YES → Add to AGENTS.md
│   │
│   ├── Is it for contributors?
│   │   └── YES → Add to CONTRIBUTING.md
│   │
│   └── Is it for users?
│       └── YES → Add to README.md
│
└── NO → Tier 1 (Universal Best Practice)
    │
    ├── Is it about git/quality/ADRs?
    │   └── YES → Add to best-practices/DEVELOPMENT.md
    │
    ├── Is it about logging?
    │   └── YES → Add to best-practices/LOGGING.md
    │
    ├── Is it about testing?
    │   └── YES → Add to best-practices/TESTING.md
    │
    ├── Is it about documentation?
    │   └── YES → Add to best-practices/DOCUMENTATION.md
    │
    └── Is it language-specific (TypeScript, Python, etc.)?
        └── YES → Add to best-practices/[LANGUAGE].md
```

---

## Documentation Maintenance

### Periodic Reviews (Quarterly)

**Best Practices** (`docs/best-practices/`):
- [ ] Still project-agnostic? (no project-specific references)
- [ ] Examples still relevant to similar projects?
- [ ] New patterns discovered that should be documented?
- [ ] Outdated tool recommendations? (update if needed)

**Project Docs** (README, CONTRIBUTING, etc.):
- [ ] Commands still accurate? (verify examples work)
- [ ] Links still valid? (files moved/renamed?)
- [ ] Metrics current? (test counts, performance numbers)
- [ ] ADRs reflect current architecture? (create new ADRs if superseded)

---

### Documentation Health Metrics

**Good documentation has**:
- ✅ Clear navigation (README → specific docs in < 2 clicks)
- ✅ Up-to-date examples (all commands work as written)
- ✅ No broken links (run link checker quarterly)
- ✅ Consistent formatting (use linter/formatter)
- ✅ Recent updates (no docs > 1 year old without review)

**Warning signs**:
- ⚠️ "See code for details" (document it instead)
- ⚠️ Outdated screenshots (remove or update)
- ⚠️ Broken examples (test commands as part of CI)
- ⚠️ Duplicate content (consolidate or link)
- ⚠️ No CHANGELOG entries (enforce in PR process)

---

## Common Documentation Patterns

### README.md (Project Root)

**Purpose**: First impression for users and contributors

**Essential sections**:
1. **One-line description** - What does this project do?
2. **Quick start** - Install and run in < 5 min
3. **Features** - What can users do?
4. **Documentation links** - Point to detailed docs
5. **Contributing** - Link to CONTRIBUTING.md
6. **License** - Legal terms

**Keep it short**: 200-400 lines max, deep-dive content goes elsewhere

---

### CONTRIBUTING.md

**Purpose**: Onboarding guide for contributors

**Essential sections**:
1. **How to contribute** - Bug reports, features, PRs
2. **Development setup** - Environment requirements
3. **Code style** - Link to best practices
4. **Testing requirements** - What tests are required
5. **PR process** - Review expectations
6. **Code of conduct** - Community standards (or link)

---

### AGENTS.md / CLAUDE.md

**Purpose**: Comprehensive guide for AI coding assistants

**Essential sections**:
1. **Project overview** - What is this project?
2. **Architecture** - How is it structured?
3. **Development conventions** - Link to best practices
4. **Testing strategy** - How to run tests, coverage expectations
5. **Common pitfalls** - Known issues and gotchas
6. **Debugging workflow** - How to debug when things break

**Length**: 500-1000 lines typical (comprehensive but scannable)

---

### Architecture Decision Records (ADRs)

**Purpose**: Document why architectural decisions were made

**Format**:
```markdown
# ADR-NNN: [Title]

**Status**: Accepted | Proposed | Deprecated | Superseded by ADR-XXX

**Date**: YYYY-MM-DD

## Context

What problem are we solving? What constraints exist?

## Decision

What did we decide to do?

## Consequences

### Positive
- What benefits does this provide?

### Negative
- What drawbacks or costs?

### Neutral
- What's neither good nor bad but worth noting?

## References

- Links to docs, commits, discussions
```

**Naming**: `ADR_YYYYMMDD_NN_description.md` (date-based, recommended)

**Lifecycle**: Never modify accepted ADRs; create new ADRs that supersede them

---

## Quick Reference Card

### Where to Document What

| Content Type | Tier | Location |
|-------------|------|----------|
| **Git workflow standards** | Tier 1 | best-practices/DEVELOPMENT.md |
| **Your team's git branch names** | Tier 2 | CONTRIBUTING.md |
| **Logging principles** | Tier 1 | best-practices/LOGGING.md |
| **Your logger configuration** | Tier 2 | ARCHITECTURE.md or ADR |
| **Testing strategy patterns** | Tier 1 | best-practices/TESTING.md |
| **Your test commands & counts** | Tier 2 | AGENTS.md, CONTRIBUTING.md |
| **Documentation organization** | Tier 1 | best-practices/DOCUMENTATION.md |
| **Your documentation index** | Tier 2 | docs/README.md |
| **Why you chose framework X** | Tier 2 | docs/adr/ADR-NNN-*.md |

---

## Common Mistakes to Avoid

### ❌ Mistake 1: No Documentation Structure

**Problem**: All docs in flat directory, hard to find anything

**Solution**: Use two-tier architecture with clear navigation

---

### ❌ Mistake 2: Duplicated Content

**Problem**: Same information in multiple files, gets out of sync

**Solution**: Write once, link many times. Use Tier 1 for principles, Tier 2 references it.

---

### ❌ Mistake 3: Outdated Examples

**Problem**: Code examples don't work, commands fail

**Solution**: Test examples as part of CI, review docs quarterly

---

### ❌ Mistake 4: No "Why" Documentation

**Problem**: Code shows "what", but not "why"

**Solution**: Use ADRs to document architectural decisions and rationale

---

### ❌ Mistake 5: Project-Specific Best Practices

**Problem**: Best practices tied to your project, can't be reused

**Solution**: Write generic patterns in Tier 1, specific applications in Tier 2

---

## Adapting to Your Project

**When copying this best practice**:

1. **Review sections**: Keep what's relevant, remove what's not
2. **Adjust examples**: Use examples from your language/ecosystem
3. **Add sections**: If you have domain-specific needs (e.g., security docs)
4. **Update links**: Point to your project structure
5. **Customize tiers**: Two-tier is recommended, but adapt if needed

**This is a template, not a prescription**. Adapt to your team's needs.

---

## See Also

- [DEVELOPMENT.md](./DEVELOPMENT.md) - Git workflow, quality standards
- [TESTING.md](./TESTING.md) - Testing strategy and patterns
- [LOGGING.md](./LOGGING.md) - Logging best practices
- [Keep a Changelog](https://keepachangelog.com/) - CHANGELOG format
- [ADR GitHub Org](https://adr.github.io/) - ADR resources

---

## License

This documentation best practice is designed to be reusable. You are free to copy, modify, and distribute it in your own projects.

---

**Version**: 1.0.0

**Last Updated**: 2025-12-31
