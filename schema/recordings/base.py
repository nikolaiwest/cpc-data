from abc import ABC, abstractmethod

import yaml

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

    @abstractmethod
    def _get_class_name(self):
        """Return the class name for config lookup (e.g., 'injection_upper')."""
        pass

    def get_data(self):
        """Extract features/data using config file or manual method."""
        # Step 1: Use serial data that child classes populated
        if self.serial_data is None:
            return None  # Handle missing data gracefully

        # Step 2: Apply processing (uses config from processing.yml)
        processed_data = self._apply_processing(self.serial_data)

        # Step 3: Apply extraction (uses config from extraction.yml)
        extracted_data = self._apply_extraction(processed_data)

        return extracted_data

    def _apply_processing(self, raw_series):
        """Apply processing settings to all time series data."""
        try:
            # Load processing settings
            processing_settings = get_processing_settings()

            # Get class-specific settings using class name path
            class_path = self._get_class_name().split(".")
            class_settings = processing_settings
            for path_part in class_path:
                class_settings = class_settings.get(path_part, {})

            processed_series = {}

            for series_name, series_data in raw_series.items():
                # Get settings for this specific series
                series_settings = class_settings.get(series_name, {})

                # Apply processing steps in order
                processed_data = series_data.copy() if series_data is not None else None

                if processed_data is not None:
                    # Apply equal lengths
                    processed_data = self._process_equal_lengths(
                        processed_data, series_settings, series_name
                    )

                processed_series[series_name] = processed_data

            return processed_series

        except Exception as e:
            print(f"Warning: Processing failed for {self._get_class_name()}: {e}")
            # Return raw data if processing fails
            return raw_series

    def _apply_extraction(self, processed_data):
        """Apply extraction using extraction.yml config."""
        try:
            # Load extraction settings
            extraction_settings = get_extraction_settings()

            class_name = self._get_class_name()
            class_config = extraction_settings.get(class_name, {})

            results = {}
            for series_name, series_config in class_config.items():
                if (
                    series_config.get("use_series", False)
                    and series_name in processed_data
                ):
                    method = series_config.get("method", "raw")
                    params = {
                        k: v
                        for k, v in series_config.items()
                        if k not in ["use_series", "method"]
                    }

                    series_data = processed_data[series_name]
                    results[series_name] = self._apply_method(
                        series_data, method, **params
                    )

            return results

        except Exception as e:
            print(f"Warning: Extraction failed for {self._get_class_name()}: {e}")
            # Return processed data if extraction fails
            return processed_data

    def _process_equal_lengths(self, series_data, series_settings, series_name):
        """Apply equal length processing to a time series."""
        equal_length_settings = series_settings.get("apply_equal_lengths", False)

        # If processing is disabled, return original data
        if not equal_length_settings:
            return series_data

        # Extract parameters
        target_length = equal_length_settings.get("target_length", 1000)
        cutoff_position = equal_length_settings.get("cutoff_position", "post")
        padding_val = equal_length_settings.get("padding_val", 0.0)
        padding_pos = equal_length_settings.get("padding_pos", "post")

        current_length = len(series_data)

        print(
            f"Processing {series_name} ({self._get_class_name()}): {current_length} -> {target_length} samples"
        )

        # If already the right length, return as-is
        if current_length == target_length:
            return series_data

        # If too long, cut to target length
        elif current_length > target_length:
            if cutoff_position == "pre":
                # Cut from beginning
                processed_data = series_data[-target_length:]
            else:  # 'post'
                # Cut from end
                processed_data = series_data[:target_length]

        # If too short, pad to target length
        else:
            padding_needed = target_length - current_length
            padding = [padding_val] * padding_needed

            if padding_pos == "pre":
                # Pad at beginning
                processed_data = padding + series_data
            else:  # 'post'
                # Pad at end
                processed_data = series_data + padding

        return processed_data

    def _load_config(self, config_path=None, config_dict=None):
        """Load configuration from file or dict."""
        if config_dict:
            return config_dict
        elif config_path:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        else:
            raise ValueError("Either config_path or config_dict must be provided")

    def _extract_from_config(self, time_series_data, config):
        """Extract features based on YAML configuration."""
        class_name = self._get_class_name()
        class_config = config.get("extraction", {}).get(class_name, {})

        results = {}
        for series_name, series_config in class_config.items():
            if (
                series_config.get("use_series", False)
                and series_name in time_series_data
            ):
                method = series_config.get("method", "raw")
                params = {
                    k: v
                    for k, v in series_config.items()
                    if k not in ["use_series", "method"]
                }

                series_data = time_series_data[series_name]
                results[series_name] = self._apply_method(series_data, method, **params)

        return results

    def _extract_manual(self, time_series_data, method, **kwargs):
        """Extract features using manual method for all time series."""
        results = {}
        for series_name, series_data in time_series_data.items():
            results[series_name] = self._apply_method(series_data, method, **kwargs)
        return results

    def _apply_method(self, series_data, method, **kwargs):
        """Apply extraction method to a single time series."""
        if method == "raw":
            return series_data
        elif method == "paa":
            return self._extract_paa(series_data, **kwargs)
        elif method == "tsfresh":
            return self._extract_tsfresh(series_data, **kwargs)
        elif method == "catch22":
            return self._extract_catch22(series_data, **kwargs)
        else:
            raise ValueError(f"Unknown extraction method: {method}")

    def _extract_paa(self, series_data, segments=10, normalize=False, **kwargs):
        """Placeholder for PAA feature extraction."""
        # TODO: Implement PAA (Piecewise Aggregate Approximation)
        return {
            "method": "paa",
            "segments": segments,
            "normalize": normalize,
            "data": "placeholder",
        }

    def _extract_tsfresh(self, series_data, normalize=False, **kwargs):
        """Placeholder for tsfresh feature extraction."""
        # TODO: Implement tsfresh feature extraction
        return {"method": "tsfresh", "normalize": normalize, "data": "placeholder"}

    def _extract_catch22(self, series_data, normalize=False, **kwargs):
        """Placeholder for catch22 feature extraction."""
        # TODO: Implement catch22 feature extraction
        return {"method": "catch22", "normalize": normalize, "data": "placeholder"}
