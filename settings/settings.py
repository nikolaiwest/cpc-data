import os
from typing import Dict, Optional, Union

import yaml


def get_settings(
    settings_type: Optional[str] = None, settings_dir: str = "settings"
) -> Union[Dict, Dict[str, Dict]]:
    """
    Load processing and/or extraction settings files.

    Args:
        settings_type: Which settings to load:
                      - None: Load both processing and extraction (default)
                      - "processing": Load only processing.yml
                      - "extraction": Load only extraction.yml
        settings_dir: Directory containing the YAML files

    Returns:
        Dict: If settings_type specified, returns single settings dict
              If settings_type is None, returns {'processing': {...}, 'extraction': {...}}

    Raises:
        FileNotFoundError: If specified settings file(s) don't exist
        yaml.YAMLError: If YAML files are malformed
    """

    def _load_yaml(filename: str) -> Dict:
        """Load a single YAML file."""
        filepath = os.path.join(settings_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Settings file not found: {filepath}")

        with open(filepath, "r") as file:
            return yaml.safe_load(file) or {}

    if settings_type == "processing":
        return _load_yaml("processing.yml")
    elif settings_type == "extraction":
        return _load_yaml("extraction.yml")
    elif settings_type is None:
        # Load both settings
        return {
            "processing": _load_yaml("processing.yml"),
            "extraction": _load_yaml("extraction.yml"),
        }
    else:
        raise ValueError(
            f"Unknown settings_type: {settings_type}. Use 'processing', 'extraction', or None"
        )


def get_processing_settings(settings_dir: str = "settings") -> Dict:
    """Convenience function to load only processing settings."""
    return get_settings(settings_type="processing", settings_dir=settings_dir)


def get_extraction_settings(settings_dir: str = "settings") -> Dict:
    """Convenience function to load only extraction settings."""
    return get_settings(settings_type="extraction", settings_dir=settings_dir)
