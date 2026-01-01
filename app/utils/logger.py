"""
AI: Custom Logger for MCP-safe logging.

Implements best-practices/LOGGING.md requirements:
- Semantic log levels (TRACE, DEBUG, INFO, WARN, ERROR)
- Stderr-only output (critical for MCP stdio transport)
- Test mode auto-detection and suppression
- Singleton pattern for consistent logging
"""

import sys
import os
from enum import IntEnum
from typing import Any


class LogLevel(IntEnum):
    """AI: Semantic log levels matching best-practices/LOGGING.md."""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class Logger:
    """
    AI: Custom Logger that routes all output to stderr.

    Critical for MCP protocol compliance - stdout must remain clean
    for JSON-RPC messages in stdio transport mode.
    """

    _instance = None

    def __new__(cls):
        """AI: Singleton pattern - one logger instance across application."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """AI: Initialize logger with stderr output."""
        if self._initialized:
            return

        self.current_level = LogLevel.INFO
        self._initialized = True

    def _is_test_environment(self) -> bool:
        """
        AI: Detect test environment for automatic suppression.

        Suppresses TRACE/DEBUG/INFO in tests, shows only WARN/ERROR.
        """
        return (
            os.environ.get('NODE_ENV') == 'test' or
            os.environ.get('PYTEST_CURRENT_TEST') is not None or
            os.environ.get('PLAYWRIGHT_TEST') is not None or
            'pytest' in sys.modules
        )

    def _get_effective_level(self) -> LogLevel:
        """AI: Get effective log level (elevated in test mode)."""
        if self._is_test_environment():
            return LogLevel.WARN  # Suppress TRACE, DEBUG, INFO in tests
        return self.current_level

    def _write(self, level: LogLevel, prefix: str, message: str, *args: Any) -> None:
        """
        AI: Write log message to stderr if level is enabled.

        Uses sys.stderr.write() to ensure output never goes to stdout
        (critical for MCP stdio protocol safety).
        """
        effective_level = self._get_effective_level()

        if level < effective_level:
            return  # Suppressed by current level

        # Format message with args if provided
        if args:
            try:
                formatted_message = message % args
            except (TypeError, ValueError):
                formatted_message = f"{message} {args}"
        else:
            formatted_message = message

        # Write to stderr (never stdout - MCP protocol requirement)
        sys.stderr.write(f"{prefix} {formatted_message}\n")
        sys.stderr.flush()

    def trace(self, message: str, *args: Any) -> None:
        """AI: TRACE level - extremely detailed diagnostics."""
        self._write(LogLevel.TRACE, "🔍 TRACE:", message, *args)

    def debug(self, message: str, *args: Any) -> None:
        """AI: DEBUG level - detailed debugging information."""
        self._write(LogLevel.DEBUG, "🐛 DEBUG:", message, *args)

    def info(self, message: str, *args: Any) -> None:
        """AI: INFO level - normal operational messages."""
        self._write(LogLevel.INFO, "ℹ️  INFO:", message, *args)

    def warn(self, message: str, *args: Any) -> None:
        """AI: WARN level - warning conditions."""
        self._write(LogLevel.WARN, "⚠️  WARN:", message, *args)

    def error(self, message: str, *args: Any) -> None:
        """AI: ERROR level - error conditions."""
        self._write(LogLevel.ERROR, "❌ ERROR:", message, *args)

    def set_level(self, level: LogLevel) -> None:
        """AI: Set minimum log level."""
        self.current_level = level


# Singleton instance for import across modules
logger = Logger()
