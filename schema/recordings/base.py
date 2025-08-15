from abc import ABC, abstractmethod

import yaml

from extraction.apply import apply_extraction_pipeline
from processing.apply import apply_processing_pipeline
from settings import get_extraction_settings, get_processing_settings


class BaseRecording(ABC):

    def __init__(self, upper_workpiece_id: int) -> None:
        """
        Initialize base recording with workpiece ID and empty data attributes.
        Child classes populate static_data and serial_data during initialization.

        Args:
            upper_workpiece_id: Unique identifier for the manufacturing experiment.
        """
        self.upper_workpiece_id = upper_workpiece_id

        # Initialize empty data attributes, child classes will populate these
        self.static_data: dict | None = None
        self.serial_data: dict | None = None

    @abstractmethod
    def _get_class_name(self) -> str:
        """
        Return the hierarchical class identifier for configuration lookup.

        This identifier is used to navigate the YAML configuration files
        (processing.yml and extraction.yml) to find the appropriate settings
        for this specific recording type. The path follows the structure:
        process_type.workpiece_or_position (e.g., 'injection_molding.upper_workpiece',
        'screw_driving.left').

        Returns:
            str: Dot-separated hierarchical path used to locate this recording's
                settings in YAML configuration files.
        """
        pass

    @abstractmethod
    def _get_static_data(self) -> dict | None:
        """
        Load and return static data for this recording (from static_data.csv).

        Static data contains process parameters, quality measurements, and metadata
        that remain constant throughout the manufacturing cycle, either from screw
        driving or injection molding. This may include target values, actual
        measured values, quality indicators, and timestamps.

        Returns:
            dict or None: Dictionary containing static, univariate measurements where
                        keys are measurement names and values are the recorded values.
                        Returns None if no static data is available for this recording.
        """
        pass

    @abstractmethod
    def _get_serial_data(self) -> dict | None:
        """
        Load and return serial data for this recording (from files in serial_data/).

        Serial data contains time series measurements that vary over time during the
        manufacturing process cycle, either from screw driving or injection molding.
        Each series represents a different measured parameter (pressure, velocity,
        temperature, torque, angle, etc.) sampled at regular intervals.

        Returns:
            dict or None: Dictionary where keys are series names (parameter names)
                        and values are lists of measurements ordered chronologically.
                        Returns None if no serial data is available for this recording.
        """
        pass

    def get_data(self) -> dict | None:
        """
        Extract processed and transformed features from this recording's time series data.

        Applies a two-stage pipeline:
        1. Processing: Data cleaning, normalization, and preparation
        2. Extraction: Feature extraction and transformation

        Both stages are configured via YAML files and applied per time series parameter.

        Returns:
            dict or None: Dictionary where keys are parameter names and values are
                         the processed/extracted features. Returns None if no serial
                         data is available for processing.
        """
        # Check if serial data is available
        if self.serial_data is None:
            return None

        # Get configuration settings
        processing_settings = get_processing_settings()
        extraction_settings = get_extraction_settings()

        # Navigate to class-specific settings
        class_path = self._get_class_name().split(".")
        class_processing_config = processing_settings
        class_extraction_config = extraction_settings

        for path_part in class_path:
            class_processing_config = class_processing_config.get(path_part, {})
            class_extraction_config = class_extraction_config.get(path_part, {})

        # Apply processing and extraction to each time series
        results = {}
        for series_name, series_data in self.serial_data.items():
            if series_data is None:
                continue

            # Get series-specific configurations
            processing_config = class_processing_config.get(series_name, {})
            extraction_config = class_extraction_config.get(series_name, {})

            # Skip series if not configured for extraction
            if not extraction_config.get("use_series", False):
                continue

            # Step 1: Apply processing pipeline
            processed_data = apply_processing_pipeline(
                series_data,
                processing_config,
            )

            # Step 2: Apply extraction pipeline
            extracted_data = apply_extraction_pipeline(
                processed_data,
                extraction_config,
            )

            results[series_name] = extracted_data

        return results if results else None
