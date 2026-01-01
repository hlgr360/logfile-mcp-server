# Pull Request Best Practices

**Universal guidelines for creating, reviewing, and merging pull requests.**

This document provides project-agnostic best practices for pull request workflows. Individual projects should reference this document and add project-specific requirements in their CONTRIBUTING.md.

---

## Table of Contents

- [Mandatory PR Policy](#mandatory-pr-policy)
- [Definition of Done](#definition-of-done)
- [Git Workflow](#git-workflow)
- [When to Create a PR](#when-to-create-a-pr)
- [Creating Pull Requests](#creating-pull-requests)
- [PR Review Checklist](#pr-review-checklist)
- [Code Review Etiquette](#code-review-etiquette)
- [Review Efficiency](#review-efficiency)
- [When to Approve](#when-to-approve)
- [Documentation Review Process](#documentation-review-process)
- [Merging Pull Requests](#merging-pull-requests)
- [Common Mistakes](#common-mistakes)

---

## 🚨 Mandatory PR Policy

**ALL code changes MUST go through pull requests.**

### Why Pull Requests Are Required

- ✅ **Code Review**: Catches bugs, security issues, and design problems before merge
- ✅ **Knowledge Sharing**: Team learns about changes, spreads domain knowledge
- ✅ **Documentation**: PR description becomes historical record of why changes were made
- ✅ **Quality Gate**: Ensures tests pass, documentation is updated, standards are met
- ✅ **Reversibility**: Easy to revert if issues are discovered post-merge

### What Requires a PR

- ✅ **Features** - All new functionality
- ✅ **Bug Fixes** - All bug fixes, even one-liners
- ✅ **Refactoring** - Code restructuring or cleanup
- ✅ **Documentation** - Changes to docs, READMEs, comments
- ✅ **Configuration** - Changes to build configs, CI/CD, dependencies
- ✅ **Tests** - New tests or test improvements

### What Does NOT Require a PR

- ❌ **Nothing** - Even trivial changes benefit from review

**Exception**: Some projects allow direct commits to `main` for:
- Emergency hotfixes (with post-merge review)
- Automated bot commits (version bumps, dependency updates)
- These should be explicitly documented in project CONTRIBUTING.md

---

## ✅ Definition of Done

A pull request is **ready to merge** when ALL criteria are met:

### 1. Code Quality

- [ ] Code builds/compiles without errors
- [ ] No linting errors or warnings
- [ ] Follows project coding conventions and style guide
- [ ] No debug code left in (console.log, debugger statements, commented code)
- [ ] No hardcoded values that should be configurable
- [ ] Meaningful variable/function names (no `temp`, `data`, `thing`)
- [ ] Code is self-documenting or has appropriate comments

### 2. Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Edge cases covered by tests
- [ ] Test coverage meets project requirements
- [ ] No flaky tests introduced
- [ ] Tests follow project testing conventions

**Test Types by Change**:
- New feature → Unit tests + integration tests + E2E tests
- Bug fix → Regression test that would have caught the bug
- Refactoring → Existing tests still pass (no new tests needed unless coverage was poor)

### 3. Documentation ⚠️ CRITICAL

This is where the session persistence PR failed initially.

- [ ] **User-facing docs** updated if behavior changed (README, API docs, user guides)
- [ ] **Developer docs** updated if implementation changed (ARCHITECTURE, technical guides)
- [ ] **Code comments** updated if logic changed
- [ ] **CHANGELOG** entry added describing the change
- [ ] **ADRs** created if architectural decisions were made
- [ ] **Inline comments** added for complex/non-obvious code

**Documentation Review Questions**:
1. Would a user need to know about this change?
2. Would a developer working on this code need to know about this change?
3. Does any existing documentation contradict the new behavior?
4. Are there examples that need updating?

### 4. Security & Performance

- [ ] No security vulnerabilities introduced (injection, XSS, auth bypass, etc.)
- [ ] No secrets/credentials/API keys in code
- [ ] Input validation added for external data
- [ ] Error handling doesn't leak sensitive information
- [ ] No obvious performance regressions
- [ ] Database queries optimized (if applicable)

### 5. Code Review

- [ ] Self-reviewed (read your own diff carefully)
- [ ] PR description explains **what** and **why** (not just what)
- [ ] Test results included in PR description
- [ ] Breaking changes documented with migration guide
- [ ] Related issues referenced (`Fixes #123`, `Relates to #456`)
- [ ] No merge conflicts with target branch
- [ ] Commits are clean (no "fix typo" or "WIP" commits)

---

## 🌳 Git Workflow

### Branch Strategy

**Never commit directly to `main` or `master`.**

#### Branch Naming Conventions

```
feature/description      # New features
fix/description          # Bug fixes
refactor/description     # Code refactoring
docs/description         # Documentation changes
test/description         # Test additions
chore/description        # Maintenance (deps, build config)
```

**Examples**:
```bash
feature/add-user-authentication
fix/session-timeout-handling
refactor/extract-parser-module
docs/update-api-examples
test/add-integration-tests
chore/upgrade-dependencies
```

#### Branch Lifecycle

```bash
# 1. Create branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature

# 2. Make changes, commit regularly
git add .
git commit -m "feat: add user authentication"

# 3. Keep branch updated with main
git fetch origin main
git rebase origin/main  # or merge, depending on project policy

# 4. Push to remote
git push origin feature/your-feature

# 5. Create PR (via GitHub UI or gh CLI)
gh pr create --title "feat: Add user authentication" --body "..."

# 6. After merge, delete branch
git checkout main
git pull
git branch -d feature/your-feature
git push origin --delete feature/your-feature
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `type(scope): description`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code restructuring (no behavior change)
- `perf`: Performance improvements
- `chore`: Maintenance (deps, build, CI)
- `style`: Code style changes (formatting, no logic change)

**Examples**:
```bash
feat: add user authentication with JWT
feat(api): add pagination to list endpoint
fix: handle timeout in session validation
fix(auth): prevent race condition in token refresh
docs: update API examples for v2.0
test: add integration tests for payment flow
refactor: extract parser logic to separate module
chore: upgrade TypeScript to 5.0
```

**Good commit message**:
```
feat: add automatic session persistence after operations

- Save session after all browser operations
- Prevents session staleness in long-running processes
- Added 10 unit tests and 1 E2E test

Fixes #123
```

**Bad commit messages**:
```
fix stuff
WIP
asdf
fix
update code
changes
```

---

## 🎯 When to Create a PR

**TL;DR**: Create a draft PR early for visibility, convert to ready when Definition of Done is met.

### Early vs. Late PR Creation

| Timing | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **Early** (Draft PR) | • Early feedback<br>• Visibility<br>• Collaboration<br>• CI/CD runs early | • Reviewer fatigue<br>• Incomplete context<br>• May need multiple reviews | • Complex features<br>• Need design feedback<br>• Working across teams |
| **Late** (Complete) | • Ready for thorough review<br>• Complete context<br>• One review cycle | • No early feedback<br>• Late design issues<br>• Surprises at review | • Small changes<br>• Well-understood tasks<br>• Solo work |

### Recommended Workflow

```bash
# 1. Start work on feature branch
git checkout -b feature/user-auth

# 2. Make initial commits (basic structure)
git commit -m "feat: add user model"
git commit -m "feat: add authentication middleware"

# 3. Create DRAFT PR early (optional but recommended)
gh pr create --draft --title "WIP: Add user authentication" \
  --body "Early draft for visibility. Still TODO: tests, docs"

# 4. Continue development
git commit -m "feat: add password hashing"
git commit -m "test: add auth tests"

# 5. Meet Definition of Done
git commit -m "docs: update README with auth usage"

# 6. Mark as "Ready for Review"
gh pr ready  # Converts draft to ready

# 7. Respond to review feedback
git commit -m "fix: address review comments"

# 8. Request re-review if needed
gh pr review --request @reviewer
```

### Draft PRs (Recommended)

**Use draft PRs when:**
- ✅ Starting complex features (get early design feedback)
- ✅ Working across teams (visibility and coordination)
- ✅ Exploring approaches (validate direction before investing time)
- ✅ Need CI/CD feedback early (catch build issues)

**Create draft PR when:**
- Basic structure is in place (not first commit)
- Direction is clear enough to explain
- You want feedback on approach (not implementation details)

**Mark as "Ready for Review" when:**
- All items in Definition of Done are complete
- Self-review completed
- CI/CD passing
- Ready for thorough review

### What NOT to Do

❌ **Don't create PR on first commit** - Wait until there's meaningful progress
❌ **Don't leave PRs in draft forever** - Convert to ready within 1-2 weeks
❌ **Don't create PR after everything is done** - No early feedback opportunity
❌ **Don't mark as ready if Definition of Done not met** - Wastes reviewer time

### Governance: When MUST You Create a PR?

**Always required:**
- ✅ Before merging any code to `main`
- ✅ After Definition of Done is complete
- ✅ Before requesting review

**Optional but recommended:**
- 💡 Early in development (as draft)
- 💡 When stuck or need design feedback
- 💡 When working on high-risk changes

---

## 📝 Creating Pull Requests

### PR Title

Use the same format as commit messages:

```
feat: Add user authentication
fix: Handle session timeout gracefully
docs: Update installation instructions
```

### PR Description Template

```markdown
## Summary

[One paragraph: What does this PR do and why?]

## Changes

- [Bullet list of specific changes]
- [Be concrete: file names, functions, features]

## Problem Statement

[What problem does this solve? What was broken or missing?]

## Solution

[How does this PR solve the problem? What approach was taken?]

## Test Results

[Paste test output showing all tests pass]

## Documentation

- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Code comments added
- [ ] ADR created (if applicable)

## Breaking Changes

[List any breaking changes and migration guide, or write "None"]

## Related Issues

Fixes #123
Relates to #456

---

🤖 Generated with [Tool Name] (if applicable)
Co-Authored-By: [Name] <email> (if applicable)
```

### PR Size Guidelines

**Ideal PR size**: 200-400 lines changed

- ✅ **Small PRs** (< 200 lines): Easy to review, quick to merge
- ⚠️ **Medium PRs** (200-400 lines): Acceptable, need focused review time
- 🔴 **Large PRs** (> 400 lines): Hard to review, high chance of missing issues

**When you have a large change**:
1. Break into smaller PRs (preferred)
2. If must stay together, explain why in PR description
3. Provide clear navigation guide for reviewers
4. Consider using GitHub review tools (request review on specific files)

---

## 🔍 PR Review Checklist

### For Human Reviewers

Use this checklist when reviewing any PR:

#### 1. Code Quality Review

- [ ] Code follows project conventions and style guide
- [ ] No obvious bugs or logic errors
- [ ] Error handling is appropriate
- [ ] No security vulnerabilities (see Security section below)
- [ ] Code is readable and maintainable
- [ ] No over-engineering or premature optimization
- [ ] DRY principle followed (but not over-abstracted)

#### 2. Testing Review

- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Tests cover edge cases and error conditions
- [ ] Tests are clear and maintainable
- [ ] No tests skipped or commented out without explanation
- [ ] Test coverage is appropriate for change type

#### 3. Documentation Review ⚠️ MANDATORY

**This is where the session persistence PR failed.**

- [ ] **Scan all documentation** mentioned in the change
- [ ] **User-facing docs**: Does behavior match documentation?
- [ ] **Developer docs**: Does implementation match documentation?
- [ ] **Code comments**: Do they reflect current behavior?
- [ ] **CHANGELOG**: Is change documented?
- [ ] **Examples**: Are they still accurate?

**Documentation Review Process**:
1. Identify behavior changes in the code
2. Search project docs for mentions of that behavior
3. For each mention, verify it's still accurate
4. Flag outdated sections or request updates

**Common Documentation Locations**:
- README.md - User-facing features, setup, usage
- ARCHITECTURE.md - Technical implementation details
- CONTRIBUTING.md - Developer workflow
- API docs - Endpoint/function behavior
- Code comments - Logic explanation
- CHANGELOG.md - Version history

#### 4. Security Review

- [ ] No hardcoded secrets, API keys, passwords
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities (if web app)
- [ ] No command injection vulnerabilities
- [ ] Input validation present for external data
- [ ] Authentication/authorization checks in place
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies don't have known vulnerabilities

#### 5. Performance Review

- [ ] No obvious performance regressions
- [ ] Database queries are efficient (if applicable)
- [ ] No N+1 query problems
- [ ] Caching used appropriately
- [ ] Large files/data handled efficiently
- [ ] No memory leaks

### For AI Agent Reviewers

**When reviewing PRs as an AI agent, follow this systematic process:**

#### Step 1: Code Review

```bash
# Read all changed files
git diff main...feature-branch

# Check for:
- TypeScript/compiler errors
- Security vulnerabilities
- Logic errors
- Convention violations
```

#### Step 2: Test Review

```bash
# Verify tests pass
npm test  # or appropriate test command

# Check for:
- New functionality has tests
- Edge cases covered
- No skipped tests without reason
```

#### Step 3: Documentation Review 🔴 CRITICAL

**Systematic Process**:

1. **Extract behavior changes** from code diff
   ```bash
   # Example: If code changes session management behavior
   git diff main src/session-manager.ts
   ```

2. **Search documentation** for related content
   ```bash
   grep -r "session" README.md ARCHITECTURE.md docs/
   ```

3. **For each documentation file**, verify:
   - Does it mention the changed behavior?
   - Is the description still accurate?
   - Are examples still correct?

4. **Create checklist** of documentation to update:
   - [ ] README.md line 123: Update session persistence description
   - [ ] ARCHITECTURE.md line 456: Add new session lifecycle step
   - [ ] docs/api.md: Update session API behavior

5. **Flag in review** if documentation is outdated

#### Step 4: Safety Review

- [ ] No credentials in code
- [ ] No debug code left in
- [ ] No TODO comments without issues
- [ ] No performance regressions

#### Step 5: Provide Feedback

**Good review comment**:
```markdown
## Documentation Update Required

The code now saves sessions after every operation (browser-client.ts:600),
but README.md line 270 still says sessions are only saved during login.

Suggested update for README.md:
- Old: "Session saved during login"
- New: "Session automatically saved after every operation to keep cookies fresh"

Also check:
- ARCHITECTURE.md session lifecycle section
- AGENTS.md session management section
```

**Bad review comment**:
```markdown
LGTM 👍
```

---

## 💬 Code Review Etiquette

**TL;DR**: Be constructive, kind, and focused on improving code quality, not ego.

### For Reviewers

**Do:**
- ✅ **Be constructive**: Suggest improvements with examples
  ```markdown
  // Good
  Consider using a Map instead of an object for O(1) lookups:
  const cache = new Map();

  // Bad
  This is slow.
  ```

- ✅ **Explain "why"**: Help the author learn
  ```markdown
  // Good
  Let's extract this into a helper function to improve testability
  and reduce duplication in lines 45 and 78.

  // Bad
  Extract this.
  ```

- ✅ **Praise good code**: Positive reinforcement matters
  ```markdown
  Nice use of early returns here! Much more readable than nested if statements.
  ```

- ✅ **Assume good intent**: Authors are doing their best
  ```markdown
  // Good
  I'm curious about the approach here - could we use X instead?

  // Bad
  Why didn't you use X? This is obviously wrong.
  ```

- ✅ **Ask questions**: Collaborate, don't command
  ```markdown
  // Good
  Could we simplify this by...?
  Have you considered...?
  What do you think about...?

  // Bad
  Change this to...
  You must...
  ```

- ✅ **Distinguish nitpicks from blockers**: Use labels
  ```markdown
  nit: Consider adding a comment explaining the regex

  blocking: This breaks backward compatibility
  ```

**Don't:**
- ❌ **Be dismissive**: "This is terrible", "Obviously wrong"
- ❌ **Attack the author**: "You don't understand...", "You always..."
- ❌ **Nitpick excessively**: Don't block PRs over minor style preferences
- ❌ **Rewrite everything**: Suggest targeted improvements, not complete rewrites
- ❌ **Review when frustrated**: Take a break, review with fresh eyes

### For PR Authors

**Do:**
- ✅ **Don't take it personally**: Feedback is about code, not you
- ✅ **Respond to all comments**: Even if it's just "Done ✅" or "Good catch!"
- ✅ **Ask for clarification**: "Could you elaborate on...?"
- ✅ **Explain trade-offs**: If you disagree, explain your reasoning respectfully
- ✅ **Thank reviewers**: They're volunteering their time
- ✅ **Mark conversations resolved**: After addressing feedback

**Don't:**
- ❌ **Get defensive**: "You don't understand my code"
- ❌ **Ignore feedback**: Address every comment
- ❌ **Argue without reason**: Explain trade-offs, don't just disagree
- ❌ **Ghost the PR**: Respond within 1-2 days

### Handling Disagreements

1. **Assume good faith** - Both sides want good code
2. **Discuss trade-offs** - Explain pros/cons of each approach
3. **Consult documentation** - Style guides, project conventions
4. **Ask a third party** - Get another opinion if stuck
5. **Accept the decision** - Reviewer has final say (or escalate to maintainer)

---

## ⏱️ Review Efficiency

**TL;DR**: Review in focused 60-90 minute sessions, <400 lines at a time.

### Time Limits (Prevent Review Fatigue)

Based on [industry research](https://www.codereviewchecklist.com/), review effectiveness drops significantly after:
- **60-90 minutes**: Attention span declines, errors get missed
- **400 lines of code**: Accuracy drops, critical issues overlooked

**Best practices:**
```markdown
Large PR (1000 lines):
❌ Don't: Review all 1000 lines in one 3-hour session
✅ Do: Break into three 60-minute sessions over 1-2 days

OR

✅ Do: Ask author to split into smaller PRs (300-400 lines each)
```

### Response Time Expectations

| PR Type | Expected Response Time | Example |
|---------|----------------------|---------|
| **Critical fix** | Within hours | Production bug, security fix |
| **Normal PR** | Within 1 business day | Features, refactoring |
| **Large PR** | Within 2 business days | May need scheduled time |
| **Draft PR** | No expectation | Author still working |

### Review Session Structure

**Effective review workflow:**
1. **Skim first** (5 min) - Get overview of changes
2. **Deep review** (40-60 min) - Detailed code review
3. **Document feedback** (10-15 min) - Write clear comments
4. **Take break** (15 min) - If continuing to another PR

**If interrupted mid-review:**
- Mark your place with a comment (even if private note to self)
- Resume where you left off, don't start over

### Managing Large PRs

**If you receive a PR >400 lines:**

1. **Request split** (preferred)
   ```markdown
   This PR is quite large (850 lines). Could we split it into:
   1. Core functionality (Part 1/2)
   2. Additional features + tests (Part 2/2)

   This will make review more thorough and faster.
   ```

2. **Review in chunks** (if split not possible)
   ```markdown
   I'll review this in three sessions:
   - Session 1: Core logic (files A, B, C)
   - Session 2: Tests (file D)
   - Session 3: Documentation and integration

   Expect feedback over 2 days.
   ```

3. **Focus on high-risk areas** (if urgent)
   ```markdown
   Given urgency, I focused on:
   - Security-critical authentication logic ✅
   - Database migration scripts ✅
   - Light review of tests and docs

   Suggest follow-up PR for comprehensive test review.
   ```

---

## ✅ When to Approve

**TL;DR**: Approve if the PR improves overall code health, even if not perfect. *(Google's principle)*

### The "Good Enough" Standard

From [Google's Engineering Practices](https://google.github.io/eng-practices/review/reviewer/standard.html):

> **Reviewers should favor approving a CL once it is in a state where it definitely improves the overall code health of the system, even if the CL isn't perfect.**

**Ask yourself**: "Is this code better than what's there now?"

| Scenario | Should You Approve? | Reasoning |
|----------|-------------------|-----------|
| PR fixes bug, has minor style inconsistencies | ✅ Yes | Functionality improvement matters more |
| PR adds feature with perfect code, no tests | ❌ No | Tests are non-negotiable |
| PR refactors code, makes it slightly slower but much more readable | ✅ Yes (usually) | Readability often wins unless perf is critical |
| PR has everything but variable naming could be better | ✅ Yes | Nitpicks shouldn't block merge |
| PR works but duplicates existing utility function | ⚠️ Maybe | Request using existing function, but not blocking |

### Nitpicks vs. Blockers

**Nitpicks** (approve with comments):
- Variable naming preferences
- Comment formatting
- Minor style inconsistencies (if not covered by style guide)
- "Could also do it this way..." suggestions
- Non-critical performance micro-optimizations

**Blockers** (request changes):
- Tests missing or failing
- Security vulnerabilities
- Breaking changes without migration guide
- Doesn't solve stated problem
- Violates project conventions
- Documentation not updated
- Introduces bugs

### Approval Workflow

```markdown
1. Review completed

2. Choose response:

   Option A: Approve ✅
   - All blockers addressed
   - Nitpicks noted as comments
   - Message: "LGTM! Nice work on X. Minor suggestions in comments."

   Option B: Approve with suggestions ✅
   - Core is good, minor improvements possible
   - Message: "Approving! Consider addressing comments before merge."

   Option C: Request changes 🔴
   - Blockers present
   - Message: "Great start! Please address the blocking items:
     1. Add tests for happy path and error cases
     2. Update ARCHITECTURE.md session lifecycle section
     After these are addressed, I'll re-review."

   Option D: Comment (no approval/rejection)
   - Questions or clarifications needed
   - Early feedback on draft PR
```

### The Incremental Improvement Philosophy

**Perfect is the enemy of good:**
- ✅ Small improvements add up over time
- ✅ Incremental refactoring is safer than big rewrites
- ✅ Shipping working code > perfect code delayed

**However:**
- ❌ Don't compromise on security
- ❌ Don't skip tests "for now"
- ❌ Don't accept documentation debt repeatedly

### When to Escalate

If author and reviewer disagree:
1. **Discuss trade-offs** in PR comments
2. **Consult style guide** or project conventions
3. **Ask maintainer** or tech lead
4. **Schedule meeting** if complex architectural decision

---

## 📚 Documentation Review Process

**This is the critical process that was missed in the session persistence PR.**

### When to Update Documentation

| Change Type | Documentation Required |
|-------------|------------------------|
| New feature | README (usage), ARCHITECTURE (implementation), CHANGELOG |
| Behavior change | All docs mentioning that behavior |
| Bug fix | CHANGELOG (unless doc was wrong, then fix doc too) |
| Refactoring | ARCHITECTURE if structure changed significantly |
| API change | API docs, README, CHANGELOG, migration guide |
| Performance improvement | CHANGELOG, ARCHITECTURE if implementation changed |

### Documentation Review Steps

#### 1. Identify Behavior Changes

Read the PR and list what behaviors changed:
- ✅ "Sessions now saved after every operation" (not just login)
- ✅ "API now requires authentication header"
- ✅ "Search now supports wildcards"

#### 2. Search Documentation

For each behavior change, search all documentation:

```bash
# Example: Session behavior changed
grep -r "session" README.md ARCHITECTURE.md AGENTS.md docs/
```

#### 3. Verify Each Mention

For each search result:
- Read the context
- Does it describe the OLD behavior?
- Does it need updating to reflect NEW behavior?

#### 4. Create Update List

Make a checklist:
- [ ] README.md line 270: "session saved during login" → "session saved after every operation"
- [ ] ARCHITECTURE.md line 205: Add step "Auto-save after operation"
- [ ] AGENTS.md line 110: Add "Auto-Update" step

#### 5. Request Updates or Make Updates

If you're reviewing: Request changes with specific line numbers and suggestions

If you're creating the PR: Update all affected documentation before submitting

### Documentation That Must Always Be Updated

1. **CHANGELOG.md** - ALWAYS document user-visible changes
2. **README.md** - If users need to know about it
3. **ARCHITECTURE.md** - If implementation details changed
4. **API docs** - If API behavior changed
5. **Migration guides** - If breaking changes introduced

---

## 🔀 Merging Pull Requests

### Merge Strategies

**Create a merge commit** (recommended):
- Preserves full history with all commits
- Easy to revert entire PR
- Shows clear boundary between features

**Squash and merge**:
- Combines all commits into one
- Cleaner history for small PRs
- Loses granular commit history

**Rebase and merge**:
- Linear history
- Requires clean, well-organized commits
- More complex to revert

**Project should choose ONE strategy and document it in CONTRIBUTING.md.**

### Pre-Merge Checklist

- [ ] All review comments addressed
- [ ] All CI/CD checks passing
- [ ] Required approvals received
- [ ] No merge conflicts
- [ ] Branch is up to date with target branch
- [ ] Definition of Done met

### Post-Merge Cleanup

```bash
# Delete remote branch
git push origin --delete feature/branch-name

# Delete local branch
git checkout main
git pull
git branch -d feature/branch-name
```

---

## ❌ Common Mistakes

### Mistake 1: Documentation Not Updated

**What happened**: Code behavior changed but docs still describe old behavior

**Example**: Session persistence PR - code saved sessions after operations, but docs said only during login

**Prevention**:
- Add documentation review to PR checklist
- Search docs for mentions of changed behavior
- Require documentation updates before approval

### Mistake 2: PRs Too Large

**What happened**: 2000+ line PR submitted, impossible to review thoroughly

**Prevention**:
- Break features into smaller PRs
- Submit incrementally (Part 1/3, Part 2/3, etc.)
- Each PR should be independently reviewable

### Mistake 3: Unclear PR Description

**What happened**: PR says "fix bug" with no context

**Prevention**:
- Use PR description template
- Explain WHAT and WHY, not just WHAT
- Include test results and examples

### Mistake 4: Tests Added But Don't Test The Change

**What happened**: Tests added but they don't actually verify the new behavior

**Prevention**:
- Review tests as carefully as code
- Verify tests fail without the code changes
- Check tests cover edge cases

### Mistake 5: Breaking Changes Without Migration Guide

**What happened**: API changed, existing users' code breaks with no guidance

**Prevention**:
- Document all breaking changes in PR
- Provide migration guide
- Consider deprecation period

---

## 🎯 Summary

### Minimum Requirements for Every PR

1. ✅ **All tests pass**
2. ✅ **Code reviewed** (by human or AI)
3. ✅ **Documentation updated** (user-facing and developer-facing)
4. ✅ **CHANGELOG updated**
5. ✅ **No security vulnerabilities**
6. ✅ **Follows project conventions**

### The Critical Lesson from Session Persistence PR

**Code changes were perfect. Tests were excellent. But documentation was not updated.**

The failure was not technical - it was process:
1. PR creation didn't include documentation review
2. PR review didn't catch missing documentation updates
3. Only after merge was the gap noticed

**Solution**: Make documentation review **mandatory and systematic** in both PR creation and PR review.

---

## 📖 Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [Code Review Best Practices](https://google.github.io/eng-practices/review/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Version**: 1.0
**Last Updated**: 2026-01-01
**Maintained By**: Project maintainers and AI agent contributors
