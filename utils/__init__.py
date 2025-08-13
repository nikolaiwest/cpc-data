"""
Project-wide utilities for cross-process chain error detection.

This package provides robust utilities that work regardless of:
- Whether you're developing from source or using as an installed library
- What your current working directory is (great for notebooks!)
- Where you run your scripts from

Main modules:
- paths: Path resolution utilities for data, settings, and project files
"""

from .paths import (
    # Core path functions
    get_project_root,
    get_data_path,
    get_settings_path,
    get_notebooks_path,
    # Convenience functions for common data access
    get_injection_molding_metadata,
    get_injection_molding_raw_data,
    get_screw_driving_metadata,
    get_screw_driving_raw_data,
    get_class_values,
)

__all__ = [
    # Core path functions
    "get_project_root",
    "get_data_path",
    "get_settings_path",
    "get_notebooks_path",
    # Data access convenience functions
    "get_injection_molding_metadata",
    "get_injection_molding_raw_data",
    "get_screw_driving_metadata",
    "get_screw_driving_raw_data",
    "get_class_values",
]
