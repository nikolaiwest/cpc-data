"""
Settings module for cross-process chain error detection.

Provides unified access to processing and extraction configuration files.
"""

from .settings import get_settings, get_processing_settings, get_extraction_settings

__all__ = ["get_settings", "get_processing_settings", "get_extraction_settings"]
