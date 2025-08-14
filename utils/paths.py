"""
Project-wide path utilities for cross-process chain error detection.

This module provides robust path resolution for data files, settings, and other resources.
It ensures the project works correctly whether you're:
- Developing from source
- Running notebooks from subdirectories
- Using the package as an installed library
- Working from any arbitrary working directory

The key principle: all paths are resolved relative to the project root,
not relative to the current working directory.
"""

from pathlib import Path
from typing import Union


def get_project_root() -> Path:
    """
    Get the root directory of the project.

    This is the single source of truth for locating the project root.
    It works by finding this file's location and navigating up to the project root.
    """
    # Get the directory containing this file (utils/paths.py)
    current_file = Path(__file__).resolve()

    # Navigate up one level: utils -> project_root
    project_root = current_file.parent.parent

    return project_root


def get_data_path(*path_parts: Union[str, Path]) -> Path:
    """
    Get path to data files relative to project root.

    This is the main function for accessing any file in the data/ directory.
    """
    return get_project_root() / "data" / Path(*path_parts)


def get_settings_path(*path_parts: Union[str, Path]) -> Path:
    """
    Get path to settings files relative to project root.

    Use this to access YAML configuration files and other settings.
    """
    return get_project_root() / "settings" / Path(*path_parts)


def get_notebooks_path(*path_parts: Union[str, Path]) -> Path:
    """
    Get path to notebooks directory relative to project root.

    Useful for accessing notebooks from other parts of the project.
    """
    return get_project_root() / "notebooks" / Path(*path_parts)


# A few more convenience functions for common data access patterns


def get_injection_molding_static_data(workpiece_type: str) -> Path:
    """Get static data CSV path for injection molding data."""
    if workpiece_type not in ("upper", "lower"):
        raise ValueError(
            f"workpiece_type must be 'upper' or 'lower', got: {workpiece_type}"
        )

    return get_data_path(
        "injection_molding", f"{workpiece_type}_workpiece", "static_data.csv"
    )


def get_injection_molding_serial_data(workpiece_type: str, filename: str) -> Path:
    """Get serial data file path for injection molding time series."""
    if workpiece_type not in ("upper", "lower"):
        raise ValueError(
            f"workpiece_type must be 'upper' or 'lower', got: {workpiece_type}"
        )

    return get_data_path(
        "injection_molding", f"{workpiece_type}_workpiece", "serial_data", filename
    )


def get_screw_driving_static_data() -> Path:
    """Get static data CSV path for screw driving data."""
    return get_data_path("screw_driving", "static_data.csv")


def get_screw_driving_serial_data(filename: str) -> Path:
    """Get serial data file path for screw driving time series."""
    return get_data_path("screw_driving", "serial_data", filename)


def get_class_values() -> Path:
    """Get path to the main class values CSV file."""
    return get_data_path("class_values.csv")
