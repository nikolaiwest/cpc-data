from abc import ABC, abstractmethod

from extraction.apply import apply_extraction
from processing.apply import apply_processing
from settings import get_extraction_settings, get_processing_settings


class BaseRecording(ABC):

    def __init__(self, upper_workpiece_id: int) -> None:
        """
        Initialize base recording with workpiece ID and empty data attributes.
        Child classes populate static_data and serial_data during initialization.

        Args:
            upper_workpiece_id: Unique identifier for the manufacturing experiment.
        """
        self.upper_workpiece_id = int(upper_workpiece_id)

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

        Applies a two-stage pipeline with full series context:
        1. Processing: Data cleaning, normalization, and preparation across all series
        2. Extraction: Feature extraction and transformation with cross-series awareness

        Both stages receive the complete series dictionary (including time data) enabling
        time-aware operations like resampling and cross-series normalization.
        Configuration is loaded from YAML files based on the recording's class hierarchy.

        Returns:
            dict or None: Dictionary where keys are series names and values are
                        the processed/extracted features. Only includes series with
                        use_series=True in extraction config. Returns None if no serial
                        data is available for processing.

        Pipeline Interface:
            - apply_processing_pipeline(series_dict, config_dict) -> processed_series_dict
            - apply_extraction_pipeline(series_dict, config_dict) -> extracted_features_dict
        """
        # Check if serial data is available
        if self.serial_data is None:
            return None

        # Get configuration settings with class-specific settings
        recording_type, position_value = self._get_class_name().split(".")
        processing_settings = get_processing_settings()[recording_type][position_value]
        extraction_settings = get_extraction_settings()[recording_type][position_value]

        # Apply two-stage pipeline with full series context
        processed_data = apply_processing(self.serial_data, processing_settings)
        extracted_data = apply_extraction(processed_data, extraction_settings)

        return extracted_data
