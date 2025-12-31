# ADR_20250731_06: MCP Server Integration Architecture

## Status
**ACCEPTED** - July 31, 2025

## Context
The log analysis application required integration with Model Context Protocol (MCP) to enable LLM access (specifically VS Code Copilot) to the log analysis database. Initial implementation created duplicate server files leading to maintenance burden and architectural inconsistency.

## Decision
Implement a **unified MCP server architecture** with the following design principles:

### 1. Single Entry Point Architecture
- **ADOPTED**: Integrate MCP server functionality directly into `app/main.py`
- **REJECTED**: Maintain separate standalone MCP server scripts
- **RATIONALE**: Eliminates code duplication and provides single source of truth

### 2. Dual Transport Support
- **ADOPTED**: Support both stdio (VS Code Copilot) and network transports in single server
- **IMPLEMENTATION**: `TransportMode` enum with `STDIO` and `NETWORK` modes
- **BENEFIT**: Same codebase serves different client types without duplication

### 3. Conditional CLI Requirements
- **ADOPTED**: Make `--nexus-dir` and `--nginx-dir` optional, required only for `--process-logs`
- **IMPLEMENTATION**: Runtime validation based on operation mode
- **BENEFIT**: MCP-only mode doesn't require dummy directory arguments

### 4. Explicit Configuration
- **ADOPTED**: Use explicit `--db-name` in VS Code configuration rather than implicit defaults
- **RATIONALE**: Clear visibility of which database Copilot will query

## Implementation Details

### MCP Server Architecture
```python
class LogAnalysisMCPServer:
    def __init__(self, db_ops: DatabaseOperations, transport_mode: TransportMode):
        # Unified server supporting both transports
        
class TransportMode(Enum):
    STDIO = "stdio"    # VS Code Copilot
    NETWORK = "network"  # Other MCP clients
```

### Factory Functions
```python
def create_stdio_server(db_ops: DatabaseOperations) -> LogAnalysisMCPServer
def create_network_server(db_ops: DatabaseOperations) -> LogAnalysisMCPServer
```

### CLI Integration
```bash
# VS Code Copilot integration
python -m app.main --db-name log_analysis.db --mcp-stdio

# Network MCP with web interface
python -m app.main --nexus-dir /logs --nginx-dir /logs --enable-mcp-server
```

### VS Code Configuration
```json
{
  "servers": {
    "log-analysis": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.main", "--db-name", "log_analysis.db", "--mcp-stdio"]
    }
  }
}
```

## MCP Tools Provided

### 1. list_database_schema
- **Purpose**: Inspect database structure and relationships
- **Security**: Read-only schema inspection
- **Use Case**: Understanding available tables and columns

### 2. execute_sql_query  
- **Purpose**: Execute SELECT queries against log database
- **Security**: SELECT-only validation, result limits (1000 rows)
- **Use Case**: Custom data analysis and querying

### 3. get_table_sample
- **Purpose**: Preview table data with configurable limits
- **Security**: Configurable row limits (default 10, max 100)
- **Use Case**: Quick data exploration and validation

## Security Considerations

### Query Validation
- **ENFORCED**: Only SELECT statements allowed
- **IMPLEMENTATION**: SQL parsing and validation before execution
- **PROTECTION**: Prevents data modification through MCP interface

### Result Limits
- **ENFORCED**: Maximum 1000 rows per query result
- **RATIONALE**: Prevent memory exhaustion and improve performance
- **CONFIGURABLE**: Limits adjustable in tool parameters

### Input Sanitization
- **IMPLEMENTED**: Comprehensive input validation and error handling
- **LOGGING**: Security events logged for monitoring
- **GRACEFUL**: Errors return descriptive messages without exposing internals

## Consequences

### Positive
1. **Single Maintenance Point**: No duplicate server implementations
2. **Consistent Architecture**: All functionality accessed through main app
3. **Flexible Deployment**: Same code serves different transport needs
4. **Clear Configuration**: Explicit database selection in VS Code config
5. **Enhanced Security**: Comprehensive validation and limits

### Negative
1. **Slightly More Complex CLI**: Additional conditional validation logic
2. **Dependency Coupling**: MCP functionality tied to main application lifecycle

### Migration Impact
- **BREAKING CHANGE**: Removed `run_mcp_server.py` and `run_mcp_stdio.py`
- **MIGRATION PATH**: Use `python -m app.main --mcp-stdio` for VS Code integration
- **CONFIGURATION**: Update `.vscode/mcp.json` to use main app entry point

## Compliance
- **ADR_20250728_04**: Maintains architectural consistency with dependency injection
- **Security Best Practices**: Implements input validation and output sanitization
- **MCP 1.12.2 Specification**: Full compliance with protocol requirements

## Validation
- ✅ All MCP tools tested and validated
- ✅ VS Code Copilot integration functional
- ✅ Network transport maintains compatibility
- ✅ Security restrictions enforced
- ✅ No functionality lost in consolidation

## References
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [VS Code MCP Integration Guide](https://code.visualstudio.com/docs/copilot/copilot-mcp)
- ADR_20250728_04: Architectural Pattern Consistency
