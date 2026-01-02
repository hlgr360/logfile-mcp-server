# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation restructuring with two-tier architecture
- Best practices documentation (PYTHON.md, SECURITY.md, DEVELOPMENT.md, TESTING.md, LOGGING.md, DOCUMENTATION.md)
- CHANGELOG.md for version tracking
- Custom Logger class with stderr-only output for MCP protocol compliance
- Mandatory PR policy and contribution guidelines (CONTRIBUTING.md)
- Universal Pull Request best practices (docs/best-practices/PULL_REQUESTS.md)
- Subdirectory README guidance in DOCUMENTATION.md
- Contributing section in AGENTS.md with Definition of Done checklist
- ADR index (docs/adr/README.md) with complete listing and quick reference
- Scripts documentation (scripts/README.md) with usage examples
- Test mode detection in Logger to suppress INFO/DEBUG/TRACE in test environments

### Changed
- **BREAKING**: Migrated all 210 print() statements to logger calls (MCP stdio compliance)
- **BREAKING**: All application output now goes to stderr instead of stdout
- Updated 330 tests to check stderr instead of stdout for log output
- AGENTS.md updated with best practices integration section
- docs/README.md enhanced with AI agent navigation
- README.md rewritten from user perspective (removed development phases/milestones)
- CHANGELOG format improved with better categorization

### Fixed
- MCP stdio protocol corruption from stdout pollution
- Test failures from logging migration (33 tests updated for stderr checking)
- Test mode suppression hiding INFO-level messages (added test mode overrides)

### Removed
- history.txt file (replaced by CHANGELOG.md)
- TYPESCRIPT.md (replaced by PYTHON.md)
- Development phase checkboxes from README.md (user-facing doc should not have dev status)

## [0.1.0] - 2025-07-28

### Added
- Initial release
- FastAPI web interface for log querying
- SQLite database with log entry storage
- MCP server with dual transport (stdio/network)
- Support for multiple log formats (Apache, Nginx, custom)
- Archive extraction (zip, tar.gz, tar.bz2)
- Comprehensive testing across unit, integration, E2E, and MCP layers

[Unreleased]: https://github.com/hlgr360/logfile-mcp-server/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hlgr360/logfile-mcp-server/releases/tag/v0.1.0
