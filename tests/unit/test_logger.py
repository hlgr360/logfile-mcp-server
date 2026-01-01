"""
AI: Unit tests for custom Logger class.

Tests logger functionality:
- Singleton pattern
- Log level filtering
- Stderr output (not stdout)
- Test mode detection
- Message formatting
"""

import sys
import pytest
from io import StringIO

from app.utils.logger import Logger, LogLevel, logger


class TestLoggerSingleton:
    """AI: Test Logger singleton pattern."""

    def test_singleton_instance(self):
        """AI: Test that Logger returns same instance."""
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2
        assert logger1 is logger

    def test_module_level_logger(self):
        """AI: Test that module-level logger is singleton instance."""
        assert logger is Logger()


class TestLogLevelFiltering:
    """AI: Test log level filtering."""

    def setup_method(self):
        """AI: Setup test instance before each test."""
        self.logger = Logger()
        # Save original level
        self.original_level = self.logger.current_level

    def teardown_method(self):
        """AI: Restore original level after each test."""
        self.logger.current_level = self.original_level

    def test_default_level(self):
        """AI: Test default log level is INFO."""
        logger_instance = Logger()
        assert logger_instance.current_level == LogLevel.INFO

    def test_set_level(self):
        """AI: Test setting log level."""
        self.logger.set_level(LogLevel.ERROR)
        assert self.logger.current_level == LogLevel.ERROR

        self.logger.set_level(LogLevel.TRACE)
        assert self.logger.current_level == LogLevel.TRACE

    def test_level_filtering(self, capsys):
        """AI: Test that messages below current level are suppressed."""
        self.logger.set_level(LogLevel.WARN)

        # These should be suppressed
        self.logger.trace("Trace message")
        self.logger.debug("Debug message")
        self.logger.info("Info message")

        # These should be shown
        self.logger.warn("Warning message")
        self.logger.error("Error message")

        captured = capsys.readouterr()
        assert "Trace message" not in captured.err
        assert "Debug message" not in captured.err
        assert "Info message" not in captured.err
        assert "Warning message" in captured.err
        assert "Error message" in captured.err


class TestStderrOutput:
    """AI: Test that logger outputs to stderr, not stdout."""

    def test_output_to_stderr_not_stdout(self, capsys):
        """AI: Test that logger uses stderr (using WARN level for test mode)."""
        test_logger = Logger()
        test_logger.warn("Test warning message")

        captured = capsys.readouterr()

        # Should be in stderr
        assert "Test warning message" in captured.err

        # Should NOT be in stdout
        assert "Test warning message" not in captured.out

    def test_all_levels_use_stderr(self, capsys):
        """AI: Test that WARN and ERROR use stderr (test mode suppresses others)."""
        test_logger = Logger()
        test_logger.set_level(LogLevel.TRACE)

        # In test mode, only WARN and ERROR will be visible
        test_logger.warn("Warn to stderr")
        test_logger.error("Error to stderr")

        captured = capsys.readouterr()

        # These should be in stderr (test mode suppresses TRACE/DEBUG/INFO)
        assert "Warn to stderr" in captured.err
        assert "Error to stderr" in captured.err

        # None should be in stdout
        assert captured.out == ""


class TestMessageFormatting:
    """AI: Test message formatting with arguments."""

    def test_format_with_string_args(self, capsys):
        """AI: Test string formatting with % operator (using WARN for test mode)."""
        test_logger = Logger()
        test_logger.warn("Hello %s", "World")

        captured = capsys.readouterr()
        assert "Hello World" in captured.err

    def test_format_with_multiple_args(self, capsys):
        """AI: Test formatting with multiple arguments (using ERROR for test mode)."""
        test_logger = Logger()
        test_logger.error("File: %s, Line: %d, Status: %s", "test.py", 42, "OK")

        captured = capsys.readouterr()
        assert "File: test.py, Line: 42, Status: OK" in captured.err

    def test_format_with_no_args(self, capsys):
        """AI: Test message with no format arguments (using WARN for test mode)."""
        test_logger = Logger()
        test_logger.warn("Simple message")

        captured = capsys.readouterr()
        assert "Simple message" in captured.err

    def test_emoji_prefixes(self, capsys):
        """AI: Test that emoji prefixes are included (WARN/ERROR visible in test mode)."""
        test_logger = Logger()
        test_logger.set_level(LogLevel.TRACE)

        # In test mode, only WARN and ERROR will be visible
        test_logger.warn("Warn message")
        test_logger.error("Error message")

        captured = capsys.readouterr()

        # Only WARN and ERROR emojis will be visible in test mode
        assert "⚠️  WARN:" in captured.err
        assert "❌ ERROR:" in captured.err


class TestTestModeDetection:
    """AI: Test automatic test mode detection."""

    def test_pytest_detected_as_test_environment(self):
        """AI: Test that pytest is detected as test environment."""
        test_logger = Logger()
        # pytest module should be in sys.modules
        assert test_logger._is_test_environment() is True

    def test_effective_level_in_test_mode(self):
        """AI: Test that effective level is elevated in test mode."""
        test_logger = Logger()
        test_logger.set_level(LogLevel.INFO)

        # In test mode, effective level should be WARN
        effective_level = test_logger._get_effective_level()
        assert effective_level == LogLevel.WARN

    def test_trace_debug_info_suppressed_in_tests(self, capsys):
        """AI: Test that TRACE, DEBUG, INFO are suppressed in test mode."""
        test_logger = Logger()
        test_logger.set_level(LogLevel.TRACE)

        # These should be suppressed in test mode
        test_logger.trace("Trace message")
        test_logger.debug("Debug message")
        test_logger.info("Info message")

        # These should still show
        test_logger.warn("Warning message")
        test_logger.error("Error message")

        captured = capsys.readouterr()

        # TRACE, DEBUG, INFO should be suppressed
        assert "Trace message" not in captured.err
        assert "Debug message" not in captured.err
        assert "Info message" not in captured.err

        # WARN and ERROR should show
        assert "Warning message" in captured.err
        assert "Error message" in captured.err
