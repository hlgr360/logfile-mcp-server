# Testing Best Practices

**Convention Type**: Reusable across projects
**Last Updated**: 2025-12-29

**Project Context**: Originally developed for browser automation (Playwright). Principles apply universally, but browser-specific examples (E2E with Playwright) may not apply to all projects.

## Overview

Use a multi-layered testing approach that balances coverage, speed, and value. Avoid the trap of chasing high coverage percentages on code that's inherently difficult to test meaningfully (UI automation, external integrations, etc.).

## Multi-Layered Testing Strategy

### Test Pyramid

```
        /\
       /  \     E2E Tests (Slow, High Value)
      /────\    - Critical user flows
     /──────\   - Integration with external systems
    /────────\  Integration Tests (Medium Speed, Medium Value)
   /──────────\ - Component interactions
  /────────────\ - Mocked external dependencies
 /──────────────\ Unit Tests (Fast, Broad Coverage)
```

### Layer Breakdown

| Layer | Technology | Speed | Purpose | Coverage Target |
|-------|-----------|-------|---------|----------------|
| **Unit** | Jest/Vitest | ~1s | Pure logic, validation | 80%+ |
| **Integration (Mocks)** | Jest + Mocks | ~2s | Component interactions | 60%+ |
| **Integration (Fixtures)** | Jest + Snapshots | ~0.5s | Parsing with HTML fixtures | 70%+ |
| **E2E** | Playwright/Cypress | ~5min | Full user flows | 30%+ (critical paths) |

## Unit Testing

### What to Test

✅ **DO test:**
- Pure functions and calculations
- Validation logic (cookie expiry, data parsing)
- Type guards and utility functions
- Configuration parsing
- Error message formatting

❌ **DON'T test:**
- Simple getters/setters with no logic
- Trivial delegators (methods that just call another method)
- Framework code (trust the framework)

### Example Structure

```typescript
describe('Validation Logic', () => {
  describe('validateCookieExpiry()', () => {
    it('should return true for non-expired cookies', () => {
      const futureTimestamp = Date.now() / 1000 + 3600; // 1 hour from now
      expect(validateCookieExpiry(futureTimestamp)).toBe(true);
    });

    it('should return false for expired cookies', () => {
      const pastTimestamp = Date.now() / 1000 - 3600; // 1 hour ago
      expect(validateCookieExpiry(pastTimestamp)).toBe(false);
    });

    it('should handle edge case: exactly now', () => {
      const nowTimestamp = Date.now() / 1000;
      expect(validateCookieExpiry(nowTimestamp)).toBe(false);
    });
  });
});
```

## Integration Testing (Mocks)

### When to Use Mocks

Use mocked integration tests for:
- Complex component interactions
- External API interactions (HTTP, database, file system)
- Browser automation flows (mock Playwright/Puppeteer)
- Expensive or slow operations

### Mock Factory Pattern

```typescript
// test/helpers/mock-factory.ts
export function createMockBrowser() {
  return {
    newContext: jest.fn().mockResolvedValue(createMockContext()),
    close: jest.fn().mockResolvedValue(undefined)
  };
}

export function createMockContext() {
  return {
    newPage: jest.fn().mockResolvedValue(createMockPage()),
    storageState: jest.fn().mockResolvedValue({ cookies: [], origins: [] })
  };
}

export function createMockPage() {
  return {
    goto: jest.fn().mockResolvedValue(undefined),
    waitForSelector: jest.fn().mockResolvedValue(undefined),
    evaluate: jest.fn().mockResolvedValue(null)
  };
}
```

### Usage Example

```typescript
import { createMockBrowser } from '../helpers/mock-factory';

describe('BrowserClient Integration', () => {
  let mockBrowser: ReturnType<typeof createMockBrowser>;

  beforeEach(() => {
    mockBrowser = createMockBrowser();
  });

  it('should initialize browser with correct options', async () => {
    const client = new BrowserClient();
    await client.initialize(mockBrowser);

    expect(mockBrowser.newContext).toHaveBeenCalledWith(
      expect.objectContaining({
        viewport: { width: 1280, height: 720 }
      })
    );
  });
});
```

> **Note**: The fixture-based testing approach below was designed for HTML snapshot testing in browser automation. The principles (fast, deterministic tests with saved artifacts) apply to any domain - replace HTML fixtures with JSON API responses, log file samples, etc.

## Integration Testing (Fixtures)

### When to Use Fixtures

Use HTML/data fixtures for:
- Parsing logic (DOM extraction, data transformation)
- Avoiding fragile live page dependencies
- Fast, deterministic tests
- Snapshot testing of parsers

### Fixture Structure

```
tests/
├── fixtures/
│   ├── article-list-2024-12.html      # HTML snapshot
│   ├── article-content-paywalled.html
│   └── search-results-empty.html
├── parsers/
│   ├── article-parser.ts              # Standalone parser
│   └── search-parser.ts
└── integration/
    ├── article-parser.test.ts         # Tests using fixtures
    └── search-parser.test.ts
```

### Example Test

```typescript
import { parseArticleList } from '../parsers/article-parser';
import { readFileSync } from 'fs';
import { JSDOM } from 'jsdom';

describe('Article Parser (Fixture-Based)', () => {
  it('should parse article list from December 2024 snapshot', () => {
    const html = readFileSync('./fixtures/article-list-2024-12.html', 'utf8');
    const dom = new JSDOM(html);

    const articles = parseArticleList(dom.window.document);

    expect(articles).toHaveLength(5);
    expect(articles[0]).toMatchObject({
      title: expect.any(String),
      url: expect.stringMatching(/^https:\/\/medium\.com/),
      publishDate: expect.any(String)
    });
  });
});
```

## E2E Testing

### What to Test E2E

Only test critical user-facing flows end-to-end:
- Authentication and session management
- Core feature happy paths
- Data persistence across sessions
- Critical error handling

### E2E Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should persist session across browser restarts', async ({ page }) => {
    // Login
    await page.goto('https://app.example.com/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="submit"]');

    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Save session
    const cookies = await page.context().cookies();

    // Simulate browser restart
    await page.context().close();
    const newContext = await page.context().browser()!.newContext();
    await newContext.addCookies(cookies);
    const newPage = await newContext.newPage();

    // Verify still logged in
    await newPage.goto('https://app.example.com/dashboard');
    await expect(newPage.locator('[data-testid="user-menu"]')).toBeVisible();
  });
});
```

## Coverage Philosophy

### Appropriate Coverage Targets

Different code types have different realistic coverage targets:

| Code Type | Statement | Branch | Rationale |
|-----------|-----------|--------|-----------|
| Pure logic | 90%+ | 85%+ | Easy to test, high value |
| Business logic | 80%+ | 70%+ | Core functionality |
| UI automation | 40-50% | 30-40% | Many fallback branches, low value mocking |
| External integrations | 50-60% | 40-50% | Hard to mock meaningfully |
| Configuration/glue | 60-70% | 50-60% | Mostly delegation |

### Why NOT to Chase 80%+ Coverage Everywhere

❌ **Avoid testing:**
- **Fallback selector arrays**: 100 branches for different DOM selectors
  - Testing mocked selectors provides little value
  - Actual selector validity changes when site updates
  - E2E tests validate this better

- **Complex browser automation**: Deep try-catch trees
  - Mocking browser interactions is fragile
  - Real value comes from E2E tests
  - Focus on testing the logic, not the automation

- **External API error codes**: Testing every HTTP status
  - Mock every possible API response (429, 503, 504, etc.)
  - Low ROI - external API behavior shouldn't drive internal coverage
  - Focus on error *handling* logic, not exhaustive status codes

### Coverage Quality > Quantity

✅ **Focus on:**
- Test quality: Clear, maintainable, valuable tests
- Critical paths: Test what breaks user experience
- Regression prevention: Test previous bugs
- Documentation: Tests as living documentation

❌ **Avoid:**
- Coverage theater: Tests that just exercise code without assertions
- Brittle tests: Tests that break on every refactor
- Mock-heavy tests: More mock setup than actual test logic
- Testing implementation details: Tests coupled to internal structure

## Test Organization

### Directory Structure

```
src/
├── __tests__/
│   ├── unit/              # Fast, focused unit tests
│   │   ├── validation.test.ts
│   │   └── utils.test.ts
│   ├── integration/       # Mocked integration tests
│   │   ├── client.test.ts
│   │   └── service.test.ts
│   └── helpers/           # Test utilities
│       ├── mock-factory.ts
│       ├── fixtures.ts
│       └── matchers.ts
tests/                     # E2E and fixture-based tests
├── fixtures/              # HTML snapshots, JSON data
├── integration/           # Fixture-based integration tests
└── *.spec.ts              # Playwright E2E tests
```

### Naming Conventions

- **Unit tests**: `*.test.ts` (runs with jest/vitest)
- **E2E tests**: `*.spec.ts` (runs with playwright/cypress)
- **Fixtures**: Descriptive names with dates: `article-list-2024-12.html`
- **Mocks**: `mock-*.ts` or `*.mock.ts`

## Running Tests

### Command Organization

```json
{
  "scripts": {
    "test:unit": "jest",
    "test:unit:watch": "jest --watch",
    "test:unit:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm run test:unit && npm run test:e2e"
  }
}
```

### Fast Feedback Loop

```bash
# Development: Fast unit tests in watch mode
npm run test:unit:watch

# Pre-commit: Run affected unit tests
npm run test:unit -- --changedSince=main

# CI: Full suite
npm run test:all
```

## Test-Driven Development (TDD)

### When to Use TDD

✅ **Great for TDD:**
- Pure functions and algorithms
- Validation and parsing logic
- Bug fixes (write failing test first)
- Data transformations

⚠️  **Not ideal for TDD:**
- Exploratory UI work (selectors unknown)
- External integrations (API not designed yet)
- Rapid prototyping (requirements unclear)

### TDD Cycle

```
Red → Green → Refactor
 ↓      ↓        ↓
Write  Make     Improve
failing passing design
test   test    + remove
              duplication
```

## Test Quality Standards

### Zero Warnings Requirement

**MANDATORY**: All tests must run without warnings

**What this means**:
- ✅ No deprecation warnings from dependencies
- ✅ No unused import warnings
- ✅ No unused variable warnings
- ✅ No unreachable code warnings
- ✅ No resource leak warnings (ResourceWarning, file handles, etc.)
- ✅ No async operation warnings (unhandled promises)
- ✅ Properly configured mocks (no mock-related warnings)

**Why this matters**:
- Warnings hide real issues
- Warnings accumulate into technical debt
- Warnings make it harder to spot new problems
- Clean output = professional codebase

**How to achieve**:
```bash
# Run tests with verbose output to see warnings
npm test -- --verbose

# Fix all warnings before committing
# Common fixes:
# - Remove unused imports
# - Migrate from deprecated APIs
# - Add proper await to async calls
# - Close resources (files, connections, browsers)
# - Configure mocks properly
```

**Example - Good test output**:
```bash
$ npm test
✓ 149 tests passing (6.2s)
# No warnings = clean code ✅
```

**Example - Bad test output**:
```bash
$ npm test
⚠ Warning: Deprecated function `oldMethod` used
⚠ Warning: Unused import 'FooBar'
✓ 149 tests passing (6.2s)
# Warnings present = needs fixing ❌
```

**Common warning sources**:

| Warning Type | Cause | Fix |
|--------------|-------|-----|
| Deprecated API | Using old version of library function | Migrate to new API |
| Unused imports | Import statement not used | Remove import |
| Unhandled promise | Missing await or .catch() | Add await or .catch() |
| Resource leak | File/connection not closed | Add cleanup in afterEach |
| Mock configuration | Mock not properly set up | Configure mock correctly |

### Test Isolation

**Each test should**:
- ✅ Run independently (no shared state)
- ✅ Clean up after itself (close connections, files, browsers)
- ✅ Not depend on test execution order
- ✅ Not leave side effects (database changes, file system changes)

**Use setup/teardown**:
```typescript
describe('MyComponent', () => {
  let resource: Resource;

  beforeEach(() => {
    resource = new Resource();
  });

  afterEach(() => {
    resource.cleanup(); // Prevents resource warnings
  });

  it('test 1', () => {
    // Uses fresh resource
  });

  it('test 2', () => {
    // Uses fresh resource (independent from test 1)
  });
});
```

### Test Speed

**Performance targets**:
- Unit tests: < 100ms per test
- Integration tests (mocks): < 500ms per test
- Integration tests (fixtures): < 200ms per test
- E2E tests: < 60s per test

**If tests are slow**:
1. Profile to find bottleneck
2. Use mocks for external dependencies
3. Use fixtures instead of live data
4. Parallelize test execution
5. Consider if E2E test is really needed

### Test Determinism

**Tests must be deterministic** (same result every time):

```typescript
// ❌ BAD - Random/flaky test
it('should process items', () => {
  const items = getRandomItems(); // Different each time
  expect(process(items)).toBe(expected); // Flaky!
});

// ✅ GOOD - Deterministic test
it('should process items', () => {
  const items = [item1, item2, item3]; // Fixed data
  expect(process(items)).toBe(expected); // Always same
});
```

**Avoid**:
- ❌ Random data generators
- ❌ Current timestamps (use fixed dates)
- ❌ Network calls (use mocks)
- ❌ File system dependencies (use in-memory or fixtures)
- ❌ Race conditions (properly await async operations)

## Best Practices

1. **Test behavior, not implementation**
   - Test what the code does, not how it does it
   - Avoid coupling tests to internal method names

2. **Arrange-Act-Assert pattern**
   ```typescript
   it('should calculate total price', () => {
     // Arrange
     const cart = new ShoppingCart();
     cart.addItem({ price: 10 });
     cart.addItem({ price: 20 });

     // Act
     const total = cart.getTotal();

     // Assert
     expect(total).toBe(30);
   });
   ```

3. **One logical assertion per test**
   - Tests should verify one behavior
   - Multiple technical assertions OK if testing one concept

4. **Descriptive test names**
   ```typescript
   // ❌ Bad
   it('works', () => { ... });

   // ✅ Good
   it('should return empty array when no items match filter', () => { ... });
   ```

5. **Independent tests**
   - Tests should not depend on execution order
   - Clean up after each test (beforeEach/afterEach)

6. **Avoid test logic**
   - No if statements, loops, or complex logic in tests
   - Tests should be simple and linear

## Related Conventions

- See [LOGGING.md](./LOGGING.md) for logging in tests
- See [TYPESCRIPT.md](./TYPESCRIPT.md) for type safety in test code

## Version History

- **2025-12-29**: Initial convention document
- Extracted from Medium MCP Server project
- Generalized for reuse across projects
