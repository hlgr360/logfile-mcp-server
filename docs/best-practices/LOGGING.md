# Logging Best Practices

**Convention Type**: Reusable across projects
**Last Updated**: 2025-12-29

## Overview

Use a custom Logger class that provides semantic log levels while routing all output to stderr. This is especially important for projects using stdio-based protocols (like MCP, LSP, DAP) where stdout must remain clean for protocol messages.

**Language Note**: This best practice was originally written for TypeScript/Node.js but the principles apply universally. For Python projects, adapt the Logger class implementation to use Python's `logging` module with custom handlers, or create a simple wrapper class as shown in the examples below.

**Python Adaptation**: See [PYTHON.md](./PYTHON.md) for Python-specific logging patterns. The key principles remain the same: semantic levels, stderr-only output, automatic test suppression.

## Why stderr?

Many protocols use stdio transport where stdout is reserved for structured protocol messages (JSON-RPC, etc.). All logging must go to stderr (via `process.stderr.write()`) to avoid polluting the communication channel.

**Affected Protocols:**
- Model Context Protocol (MCP)
- Language Server Protocol (LSP)
- Debug Adapter Protocol (DAP)
- Any stdio-based IPC

## Logger Architecture

### Core Features

1. **Semantic Log Levels**: TRACE, DEBUG, INFO, WARN, ERROR
2. **stderr-only output**: Never pollutes stdout
3. **Test Mode Suppression**: Automatically detects test environments
4. **Singleton Pattern**: Single logger instance across modules
5. **TypeScript Support**: Fully typed methods

### Log Levels

| Level | Emoji | Use Case | Test Mode |
|-------|-------|----------|-----------|
| TRACE | 🔍 | Extremely detailed diagnostics | Suppressed |
| DEBUG | 🐛 | Detailed debugging information | Suppressed |
| INFO | ℹ️  | Normal operational messages | Suppressed |
| WARN | ⚠️  | Warning conditions | **Shown** |
| ERROR | ❌ | Error conditions | **Shown** |

### Test Mode Behavior

When running in test environments (Jest, Playwright, Mocha, etc.), the logger automatically:
- **Suppresses**: TRACE, DEBUG, INFO (keeps test output clean)
- **Shows**: WARN, ERROR (preserves important diagnostics)

**Environment Detection:**
```typescript
private isTestEnvironment(): boolean {
  return (
    process.env.NODE_ENV === 'test' ||
    process.env.JEST_WORKER_ID !== undefined ||
    process.env.PLAYWRIGHT_TEST !== undefined ||
    process.env.VITEST !== undefined ||
    process.env.MOCHA !== undefined
  );
}
```

## Implementation

### Logger Class Template

```typescript
/**
 * Custom Logger that routes all output to stderr.
 * Supports semantic log levels with automatic test suppression.
 */
export enum LogLevel {
  TRACE = 0,
  DEBUG = 1,
  INFO = 2,
  WARN = 3,
  ERROR = 4
}

export class Logger {
  private currentLevel: LogLevel = LogLevel.TRACE;

  private isTestEnvironment(): boolean {
    return (
      process.env.NODE_ENV === 'test' ||
      process.env.JEST_WORKER_ID !== undefined ||
      process.env.PLAYWRIGHT_TEST !== undefined
    );
  }

  private getEffectiveLevel(): LogLevel {
    if (this.isTestEnvironment()) {
      return LogLevel.WARN; // Suppress TRACE, DEBUG, INFO in tests
    }
    return this.currentLevel;
  }

  private write(level: LogLevel, prefix: string, message: string, ...args: any[]): void {
    const effectiveLevel = this.getEffectiveLevel();

    if (level < effectiveLevel) {
      return;
    }

    let formattedMessage = message;
    if (args.length > 0) {
      formattedMessage += ' ' + args.map(arg =>
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ');
    }

    // Write to stderr (stdout reserved for protocol messages)
    process.stderr.write(`${prefix} ${formattedMessage}\n`);
  }

  trace(message: string, ...args: any[]): void {
    this.write(LogLevel.TRACE, '🔍', message, ...args);
  }

  debug(message: string, ...args: any[]): void {
    this.write(LogLevel.DEBUG, '🐛', message, ...args);
  }

  info(message: string, ...args: any[]): void {
    this.write(LogLevel.INFO, 'ℹ️ ', message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    this.write(LogLevel.WARN, '⚠️ ', message, ...args);
  }

  error(message: string, ...args: any[]): void {
    this.write(LogLevel.ERROR, '❌', message, ...args);
  }

  setLevel(level: LogLevel): void {
    this.currentLevel = level;
  }

  getLevel(): LogLevel {
    return this.currentLevel;
  }
}

// Singleton instance
export const logger = new Logger();
```

## Usage Guidelines

### When to Use Each Level

**TRACE** - Extremely detailed diagnostic information
- DOM element selection attempts
- Cookie details and validation steps
- Navigation steps and URL changes
- Selector debugging and fallback attempts
- Individual item processing in loops

**DEBUG** - Detailed debugging information
- Diagnostic blocks with configuration details
- Operation progress within methods
- Intermediate values and state
- File paths, sizes, and metadata
- Network requests and responses

**INFO** - Normal operational messages
- User-facing status messages
- Operation start and completion
- State changes (session loaded, initialized, etc.)
- User guidance and instructions
- High-level operation summaries

**WARN** - Warning conditions
- Degraded functionality (expired session, will retry)
- Timeouts with fallback strategies
- Missing optional data
- Recoverable errors
- Configuration issues

**ERROR** - Error conditions
- Operation failures that stop execution
- Invalid state that requires intervention
- Exceptions in catch blocks
- Unrecoverable errors
- Failed validations

### Usage Examples

```typescript
import { logger } from './logger';

// TRACE: Very detailed diagnostics
logger.trace('Found login indicators: headerUserIcon, headerWriteButton');
logger.trace('Trying selector:', selector, 'found:', elements.length, 'elements');
logger.trace('Processing item 5 of 10:', itemTitle);

// DEBUG: Detailed operation progress
logger.debug('═══════════════════════════════════════');
logger.debug('🔧 INITIALIZATION DIAGNOSTICS');
logger.debug('   Working directory:', process.cwd());
logger.debug('   Config path:', configPath);
logger.debug('   Mode:', headlessMode ? 'headless' : 'visible');
logger.debug('═══════════════════════════════════════');

// INFO: User-facing operational messages
logger.info('🚀 Server initialized successfully');
logger.info('📚 Fetching user data...');
logger.info('✅ Found 42 items');
logger.info('🌐 Browser initialized for operation');

// WARN: Warning conditions
logger.warn('⚠️  Session expired, will re-authenticate');
logger.warn('🔐 Session invalid or missing, attempting login...');
logger.warn('⏱️  Timeout after 10s, continuing with fallback');
logger.warn('📝 Optional field missing:', fieldName);

// ERROR: Actual errors
logger.error('❌ Failed to save session:', error);
logger.error('❌ Browser not initialized');
logger.error('❌ Operation failed:', error.message);
```

## Migration from console.*

### Common Patterns

**Before:**
```typescript
// Old pattern with test suppression
if (!this.isTestEnvironment()) {
  console.error('📚 Fetching data...');
}
console.log('Debug info:', value);
console.warn('Warning!');
```

**After:**
```typescript
// New pattern - logger handles test suppression
logger.info('📚 Fetching data...');
logger.debug('Debug info:', value);
logger.warn('Warning!');
```

### Migration Checklist

- [ ] Replace `console.error()` with appropriate `logger.level()`
- [ ] Replace `console.log()` with `logger.debug()` or `logger.trace()`
- [ ] Replace `console.warn()` with `logger.warn()`
- [ ] Replace `console.info()` with `logger.info()`
- [ ] Remove all `if (!isTestEnvironment())` wrappers
- [ ] Remove custom `isTestEnvironment()` methods
- [ ] Review and categorize each log statement by severity
- [ ] Preserve emoji prefixes for visual scanning

### Migration Rules

1. **DO NOT** wrap logger calls in environment checks - logger handles it internally
2. **DO** categorize carefully based on message importance and context
3. **DO** preserve emoji prefixes for visual scanning (🚀 ✅ ❌ ⚠️  📚 🔍)
4. **DO NOT** use console.* methods directly - always use logger
5. **DO** use stderr for all logging - never write to stdout

## Benefits

1. **Semantic Clarity**: Log levels convey severity and purpose
2. **Clean Test Output**: Only warnings/errors shown during tests
3. **Protocol Safety**: All output to stderr, stdout reserved for structured data
4. **Future-Proof**: Foundation for structured logging, log aggregation
5. **Debugging**: Can enable trace/debug levels selectively
6. **Standards Compliance**: Follows industry best practices
7. **Consistent**: Single logging approach across entire codebase

## Advanced Features (Optional)

### Log Level Control

```typescript
// Set minimum log level at runtime
logger.setLevel(LogLevel.DEBUG); // Only show DEBUG and above

// Get current level
const level = logger.getLevel();
```

### Structured Logging (Future Enhancement)

```typescript
// Potential enhancement for structured logging
logger.info('User login', { userId: '123', ip: '1.2.3.4' });
// Could output: ℹ️  User login {"userId":"123","ip":"1.2.3.4"}
```

### Log Filtering (Future Enhancement)

```typescript
// Potential enhancement for filtering by module
logger.info('Message', { module: 'auth' });
// Could enable: LOGGER_FILTER=auth npm start
```

## Related Conventions

- See [TESTING.md](./TESTING.md) for test-specific logging practices
- See [TYPESCRIPT.md](./TYPESCRIPT.md) for type safety with logger usage

## Version History

- **2025-12-29**: Initial convention document
- Extracted from Medium MCP Server project
- Generalized for reuse across projects
