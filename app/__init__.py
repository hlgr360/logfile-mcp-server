"""
AI: Main application package initialization.

Log Analysis Application for processing Nexus and nginx access logs.
Provides both web interface and MCP server for LLM integration.
"""

import logging
import sys

__version__ = "1.0.0"
__author__ = "Holger Reinhardt"
__email__ = "holger.reinhardt@ingentis.com"


def configure_logging():
    """
    AI: Configure Python logging module to use stderr for MCP protocol safety.

    Ensures all logging.getLogger(__name__) calls also use stderr,
    maintaining backward compatibility with existing logging code.
    """
    # Remove any existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Add stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(name)s - %(message)s')
    )
    root.addHandler(stderr_handler)
    root.setLevel(logging.INFO)


# Configure on module import
configure_logging()
