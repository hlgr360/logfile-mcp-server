# ADR_20250731_05: Test Database Consolidation

## Status
**ACCEPTED** - Implemented July 31, 2025

## Context
During Phase 4 MCP integration testing, we identified significant duplication in test database setup across different test types:

1. **Playwright E2E tests** created temporary databases with hardcoded test data
2. **MCP E2E tests** created separate temporary databases with different hardcoded data  
3. **Legacy demo script** (`populate_demo_data.py`) duplicated functionality and was removed
4. **Integration tests** had their own database setup patterns

This duplication led to:
- Inconsistent test data across test types
- Maintenance overhead when updating test scenarios
- Potential for test data drift and inconsistent behavior
- Repeated database setup code in multiple locations

## Decision
We will consolidate all test database creation through a shared `TestDatabaseFactory` that provides:

### Unified Test Database Factory
- **Location**: `tests/fixtures/test_database.py`
- **Purpose**: Single source of truth for all test database creation
- **Capabilities**:
  - Sample log processing mode (`use_sample_logs=True`) for realistic data
  - Predefined test data mode (`use_sample_logs=False`) for controlled scenarios
  - Comprehensive edge case coverage (malformed logs, various HTTP methods, error conditions)
  - Consistent schema and data structure across all test types

### Shared Fixtures
- **Location**: `tests/fixtures/__init__.py`
- **Purpose**: Pytest fixtures for session-scoped databases and web servers
- **Features**:
  - Session-scoped shared database to improve test performance
  - Backward compatibility with existing test names
  - Automatic cleanup and resource management

### Updated Test Files
1. **MCP E2E tests** (`tests/e2e/test_mcp_e2e.py`): Updated to use shared factory
2. **Playwright conftest** (`tests/playwright/conftest.py`): Updated web server fixture 
3. **Playwright E2E script** (`run_playwright_e2e.sh`): Updated demo database creation
4. **Future integration tests**: Will use shared fixtures by default

## Implementation Details

### TestDatabaseFactory API
```python
# For realistic sample log processing
db_ops = TestDatabaseFactory.create_test_database('demo.db', use_sample_logs=True)

# For controlled test scenarios  
db_ops = TestDatabaseFactory.create_test_database('test.db', use_sample_logs=False)

# Temporary database with automatic cleanup
db_ops, db_path = TestDatabaseFactory.create_temporary_database()
```

### Test Data Consistency
- **Nginx logs**: 5 entries with various HTTP methods, status codes, and edge cases
- **Nexus logs**: 3 entries covering repository operations and artifact management
- **Edge cases**: Malformed requests, missing HTTP versions, various error conditions
- **Realistic data**: When using sample logs, processes actual log files from `sample_logs/`

### Performance Benefits
- Session-scoped databases reduce setup/teardown overhead
- Shared fixtures improve test suite execution time
- Consistent data reduces test flakiness

## Consequences

### Positive
- **Consistency**: All tests use identical data structures and content
- **Maintainability**: Single location for test data updates
- **Performance**: Reduced database creation overhead through shared fixtures
- **Reliability**: Standardized edge case coverage across all test types
- **Documentation**: Clear separation between sample log processing and controlled test data

### Negative
- **Migration effort**: Required updating multiple test files and configurations
- **Dependency**: All tests now depend on shared factory (acceptable trade-off)
- **Complexity**: Test setup slightly more complex but with better abstraction

### Mitigation
- Maintained backward compatibility with existing test fixture names
- Comprehensive documentation of factory API and usage patterns
- Gradual migration approach with existing tests continuing to work

## Verification
- [x] All 40 existing tests continue to pass
- [x] MCP E2E tests use shared database successfully  
- [x] Playwright conftest imports and runs correctly
- [x] Demo database creation works with shared factory
- [x] Test data consistency verified across all test types

## References
- Phase 4 MCP Integration implementation
- Test architecture review and consolidation analysis
- Pytest fixture best practices for shared resources
