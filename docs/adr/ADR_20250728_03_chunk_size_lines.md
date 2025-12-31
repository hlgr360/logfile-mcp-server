```markdown
# ADR_20250728_03: Change chunk_size from Bytes to Lines for Log Parsing

## Status
Accepted

## Context
During Phase 2 development planning, we identified an issue with the original `chunk_size` parameter design. The parameter was initially configured to represent bytes (default: 8192 bytes) for file reading operations, following traditional file I/O patterns.

However, log file processing has unique requirements:
- Log entries are line-based records that must remain complete
- Parsing log files by byte chunks can split log entries in the middle
- Incomplete log messages would result in parsing errors or data corruption
- Log analysis requires processing complete, meaningful log entries

The coding guidelines specify chunked file reading for memory efficiency, but the implementation must preserve log entry integrity.

## Decision
We will change the `chunk_size` parameter to represent **lines** instead of **bytes** for log parsing operations:

- **Old behavior**: `chunk_size = 8192` (bytes)
- **New behavior**: `chunk_size = 1000` (lines)

This change affects:
1. CLI parameter `--chunk-size` with updated help text
2. Settings class field description in `app/config.py`
3. Future processor implementations will read N lines per chunk

The `line_buffer_size` parameter remains unchanged and continues to represent the number of parsed log entries batched for database insertion.

## Consequences

### Positive
- **Data Integrity**: Log entries are never split, ensuring complete message processing
- **Parsing Reliability**: Each chunk contains complete, parseable log entries
- **Memory Predictability**: Processing N complete lines provides predictable memory usage patterns
- **Error Reduction**: Eliminates parsing errors from incomplete log entries
- **Performance Optimization**: Reduces overhead from handling partial entries

### Negative
- **Breaking Change**: Existing configurations using byte-based chunk sizes need adjustment
- **Memory Variation**: Memory usage per chunk now varies with log entry length
- **Migration Required**: Documentation and examples need updates

### Mitigation
- Updated CLI help text clearly describes line-based chunking
- Configuration validation remains intact for range checking
- All existing tests continue to pass
- Default value (1000 lines) provides reasonable memory usage for typical log entries

## Implementation Notes
- Changed default from `8192` to `1000` in both `app/main.py` and `app/config.py`
- Updated help text: "Number of lines to read per chunk during log parsing"
- Maintained backward compatibility for configuration validation
- No changes to `line_buffer_size` (remains 1000 parsed entries per database batch)

## References
- Coding Guidelines: Memory Management section (chunked file reading)
- Coding Guidelines: Performance Guidelines section (generator usage)
- Phase 1 implementation: Database batch processing patterns

```
