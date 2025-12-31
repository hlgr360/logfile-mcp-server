# Development Best Practices

**Purpose**: Universal development workflow and quality standards applicable to any software project.

**Scope**: Project-agnostic best practices for git workflow, code quality, testing, and documentation.

**Reusability**: Copy this file to any project and adapt project-specific sections as needed.

---

## Table of Contents

- [Git Workflow](#git-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Pre-Commit Checklist](#pre-commit-checklist)
- [Pull Request Checklist](#pull-request-checklist)
- [Architecture Decision Records](#architecture-decision-records)

---

## Git Workflow

### Branch Strategy

**MANDATORY**: Never commit directly to main/master branch

**Branch naming conventions**:
```bash
feature/description      # New features
fix/description          # Bug fixes
refactor/description     # Code refactoring
docs/description         # Documentation changes
test/description         # Test additions/improvements
chore/description        # Maintenance tasks
```

**Examples**:
```bash
feature/add-reading-lists
fix/session-expiry-detection
refactor/extract-parsers
docs/add-adrs
test/add-fixture-tests
chore/update-dependencies
```

### Commit Messages

**Format**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance (deps, build, etc.)

**Examples**:
```bash
feat: add reading list support
fix: handle session expiry correctly
docs: add ADR for fixture-based testing
refactor: extract parsing logic into standalone modules
test: add fixture-based tests for parsers
chore: update playwright to v1.40
```

**Subject line rules**:
- Use imperative mood ("add" not "added" or "adds")
- No period at the end
- Capitalize first letter
- Max 72 characters

### Creating Pull Requests

**MANDATORY requirements**:
1. **Branch**: PR must be from feature branch, not main
2. **Tests**: All tests must pass
3. **Description**: Must include:
   - Concise summary of changes
   - Reference to issue/requirement that led to changes (if applicable)
   - Test results confirmation
   - Breaking changes (if any)
4. **Documentation**: Update docs if behavior changes
5. **Clean history**: Squash commits if needed (no "fix typo" commits)

**PR title format**:
```
<type>: <description>

Examples:
feat: Add Medium publications support
fix: Fix selector breakage from Medium UI update
docs: Add architecture decision records
```

---

## Code Quality Standards

### Zero Warnings Requirement

**MANDATORY**: All code must run without warnings

**What this means**:
- ✅ No test warnings (pytest, jest, etc.)
- ✅ No deprecation warnings from dependencies
- ✅ No unused imports, variables, or unreachable code
- ✅ No linter warnings (ESLint, pylint, etc.)
- ✅ Proper resource cleanup (no ResourceWarnings)
- ✅ No TypeScript errors or warnings

**Why**: Warnings hide real issues and accumulate technical debt

**How to enforce**:
```bash
# Run tests in strict mode
npm test -- --verbose

# Check for TypeScript issues
npx tsc --noEmit

# Run linter
npm run lint
```

**Common warning sources**:
- Unused imports: Remove or use
- Deprecated APIs: Migrate to new APIs
- Unhandled promises: Add await or .catch()
- Resource leaks: Close files, connections, browsers
- Mock configuration: Properly configure mocks

### Code Style

**Consistency is key**:
- Follow existing code style in the project
- Use project's linter configuration (ESLint, Prettier, etc.)
- Run formatter before committing
- Respect language idioms

**Good practices**:
- ✅ Descriptive variable names (`articleTitle` not `at`)
- ✅ Short functions (< 50 lines ideal)
- ✅ Single responsibility principle
- ✅ Proper error handling (don't swallow errors)
- ✅ Comments for "why" not "what"
- ✅ Consistent naming conventions

---

## Testing Requirements

### Test Coverage

**Minimum expectations**:
- ✅ All new features have tests
- ✅ Bug fixes include regression tests
- ✅ Critical paths have integration/E2E tests
- ✅ Public APIs have comprehensive tests

**Coverage targets** (project-specific):
- Adjust based on project type
- Browser automation: 40-50% acceptable
- Libraries/APIs: 80%+ expected
- Business logic: 90%+ ideal

### Test Types

**Unit tests**:
- Test individual functions/classes in isolation
- Fast (< 1s per test)
- No external dependencies (mock everything)

**Integration tests**:
- Test multiple components together
- Moderate speed (< 10s per test)
- May use test databases, fixtures

**E2E tests**:
- Test complete user workflows
- Slow (30s-5min per test)
- Real environment, no mocks

### Test Quality

**Good tests are**:
- ✅ **Fast**: Quick feedback loop
- ✅ **Isolated**: No dependencies between tests
- ✅ **Deterministic**: Same result every time
- ✅ **Readable**: Clear what's being tested
- ✅ **Maintainable**: Easy to update when code changes

**Avoid**:
- ❌ Flaky tests (random failures)
- ❌ Slow tests without reason
- ❌ Tests that depend on external services (use mocks)
- ❌ Tests that test implementation details (test behavior)
- ❌ Tests without assertions

---

## Documentation Requirements

### What to Document

**MANDATORY documentation**:
- ✅ README with setup instructions
- ✅ API documentation for public interfaces
- ✅ Architecture overview (high-level design)
- ✅ Contributing guidelines
- ✅ CHANGELOG for versions

**Recommended documentation**:
- ✅ Architecture Decision Records (ADRs) for major decisions
- ✅ Troubleshooting guide for common issues
- ✅ Development conventions (logging, testing, etc.)
- ✅ Code examples for complex features

### Documentation Standards

**Keep documentation**:
- ✅ **Current**: Update with code changes
- ✅ **Concise**: Respect reader's time
- ✅ **Actionable**: Include examples and commands
- ✅ **Discoverable**: Clear navigation and structure
- ✅ **Version-aware**: Note which version docs apply to

**Documentation checklist**:
- [ ] README has setup instructions
- [ ] Public functions have docstrings/JSDoc
- [ ] Complex algorithms have explanatory comments
- [ ] Breaking changes documented in CHANGELOG
- [ ] ADRs created for architectural decisions

---

## Pre-Commit Checklist

**Before every commit, verify**:

### Code Quality
- [ ] All files added to git (`git add .`)
- [ ] No untracked files that should be committed
- [ ] Code follows project style guidelines
- [ ] No commented-out code (remove or explain)
- [ ] No debug statements (console.log, debugger, print)

### Testing
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass (if applicable)
- [ ] No test warnings
- [ ] New tests added for changes

### Documentation
- [ ] Code comments updated if behavior changed
- [ ] README updated if setup changed
- [ ] CHANGELOG updated with entry in [Unreleased]
- [ ] API docs updated if public interface changed

### Security & Performance
- [ ] No hardcoded secrets or credentials
- [ ] No security vulnerabilities introduced
- [ ] No obvious performance regressions
- [ ] Error handling implemented

---

## Pull Request Checklist

**Before opening PR, verify**:

### Branch & Commits
- [ ] Branch created from main (not old feature branch)
- [ ] All commits have clear, descriptive messages
- [ ] No "fix typo" or "WIP" commits (squash if needed)
- [ ] Branch name follows convention

### Requirements
- [ ] All user requirements addressed
- [ ] All acceptance criteria met (if applicable)
- [ ] Breaking changes documented

### Testing
- [ ] All tests pass locally
- [ ] CI/CD pipeline passes (if applicable)
- [ ] Manual testing completed
- [ ] No flaky tests introduced

### Documentation
- [ ] PR description complete with:
  - Summary of changes
  - Reference to issue/requirement
  - Test results confirmation
  - Breaking changes (if any)
- [ ] Documentation updated
- [ ] CHANGELOG updated

### Code Review
- [ ] Self-review completed
- [ ] No merge conflicts
- [ ] Ready for review (not draft)

---

## Architecture Decision Records

### ADR Lifecycle Rules

**Creating ADRs**:
- ✅ **DO** create ADRs for significant architectural decisions
- ✅ **DO** use the ADR template provided in project
- ✅ **DO** number sequentially (ADR-001, ADR-002, etc.)
- ✅ **DO** link to related ADRs, docs, commits

**Updating ADRs**:
- ❌ **NEVER** modify existing ADRs (they're historical records)
- ✅ **DO** create new ADR that supersedes old one
- ✅ **DO** update old ADR status to "Superseded by ADR-XXX"
- ✅ **DO** link between old and new ADRs

**ADR Status Values**:
- **Proposed**: Under consideration, not yet approved
- **Accepted**: Decision approved and implemented
- **Deprecated**: No longer recommended but not yet removed
- **Superseded**: Replaced by newer decision (link to new ADR)

**When to create ADRs**:
- Major technology choices (database, framework, architecture)
- Significant design patterns (testing strategy, logging approach)
- Trade-offs with long-term implications
- Controversial decisions requiring documentation
- Lessons learned from mistakes

**Example supersession**:
```markdown
# ADR-001: Use SQLite for Storage

**Status**: Superseded by [ADR-015](./015-use-postgresql.md)

(Original content remains unchanged...)
```

```markdown
# ADR-015: Migrate to PostgreSQL

**Status**: Accepted

**Supersedes**: [ADR-001](./001-use-sqlite.md)

## Context
SQLite (ADR-001) worked initially but doesn't scale...
```

### ADR Naming Conventions

**Two common formats**:

1. **Date-based** (RECOMMENDED - shows when decision was made):
   ```
   ADR_YYYYMMDD_NN_description.md
   ADR_20250131_01_use_fixture_tests.md
   ```
   - ✅ Shows when decided (date in filename)
   - ✅ Sortable by date
   - ✅ Self-documenting (no need to check git history)
   - ❌ More verbose

2. **Number-based** (alternative - simpler but less context):
   ```
   001-description.md
   002-description.md
   ```
   - ✅ Simple, clean
   - ✅ Easy to reference
   - ❌ Doesn't show date (need git history)

**Choose one format and stick to it**. Document your choice in `docs/adr/README.md`.

**Recommendation**: Use date-based format for better historical context and transparency.

### ADR Discovery

**Finding ADRs**:
```bash
# List all ADRs
find docs/adr/ -name "*.md" | sort

# Search ADRs by keyword
grep -r "fixture" docs/adr/

# View ADR index
cat docs/adr/README.md
```

**Using ADRs**:
- Reference ADRs in code comments: `// See ADR-001 for why we use fixtures`
- Reference ADRs in docs: `[ADR-001](./docs/adr/001-fixture-tests.md)`
- Reference ADRs in commit messages: `Implements ADR-005 selector fallback strategy`

---

## Common Development Pitfalls

### General Pitfalls

**Configuration**:
- ❌ Don't hardcode values → Use environment variables or config files
- ❌ Don't commit secrets → Use .env (gitignored) or secret management
- ❌ Don't skip validation → Validate all external input

**Dependencies**:
- ❌ Don't use deprecated APIs → Migrate to current APIs
- ❌ Don't pin to exact versions without reason → Use ranges (e.g., ^1.0.0)
- ❌ Don't install unused dependencies → Clean up package.json

**Testing**:
- ❌ Don't rely solely on mocks → Critical paths need real testing
- ❌ Don't skip E2E tests → Integration issues hide in unit tests
- ❌ Don't ignore flaky tests → Fix immediately, don't disable

**Git**:
- ❌ Don't commit directly to main → Use feature branches
- ❌ Don't force push shared branches → Coordinate with team
- ❌ Don't commit sensitive data → Add to .gitignore immediately

**Documentation**:
- ❌ Don't skip documenting "why" → Future you will thank you
- ❌ Don't let docs go stale → Update with code changes
- ❌ Don't write novels → Concise is better

---

## Tool-Specific Guidelines

### For AI Coding Assistants

**Before making changes**:
1. Read project's AGENTS.md or equivalent
2. Review relevant ADRs to understand past decisions
3. Check best-practices/ directory for standards
4. Use EnterPlanMode for non-trivial changes (if available)

**When making changes**:
1. Follow pre-commit checklist
2. Run all tests before committing
3. Update documentation
4. Create ADRs for architectural decisions
5. Reference user requirements in commits/PRs

**Quality standards**:
- Write code that matches existing style exactly
- No warnings in any output
- All tests must pass
- Documentation complete before marking done

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- [Semantic Versioning](https://semver.org/) - Version numbering
- [ADR GitHub Org](https://adr.github.io/) - ADR resources
- [Keep a Changelog](https://keepachangelog.com/) - CHANGELOG format
- [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/) - Branching model

---

**Note**: This is a universal development practices document. For project-specific rules, see your project's CONTRIBUTING.md or AGENTS.md.
