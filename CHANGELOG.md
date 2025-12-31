# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation restructuring with two-tier architecture
- Best practices documentation (PYTHON.md, SECURITY.md, DEVELOPMENT.md, TESTING.md, LOGGING.md, DOCUMENTATION.md)
- CHANGELOG.md for version tracking

### Changed
- AGENTS.md updated with best practices integration section
- docs/README.md enhanced with AI agent navigation
- Removed history.txt in favor of structured changelog

### Removed
- history.txt file (replaced by CHANGELOG.md)
- TYPESCRIPT.md (replaced by PYTHON.md)

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
