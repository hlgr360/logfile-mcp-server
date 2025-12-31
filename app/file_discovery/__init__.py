"""
AI: File discovery module for log analysis application.

Provides file discovery functionality with archive support.
"""

from .discovery import LogFileDiscovery, create_file_iterator_from_path

__all__ = ['LogFileDiscovery', 'create_file_iterator_from_path']
