from abc import ABC, abstractmethod

import yaml


class BaseData(ABC):

    def __init__(self, upper_workpiece_id):
        self.upper_workpiece_id = upper_workpiece_id

    @abstractmethod
    def _get_time_series_data(self):
        """Return dict of time series data for this data stream."""
        pass

    @abstractmethod
    def _get_class_name(self):
        """Return the class name for config lookup (e.g., 'injection_upper')."""
        pass

    def get_data(self, config_path=None, config_dict=None, method="raw", **kwargs):
        """Extract features/data using config file or manual method."""
        time_series_data = self._get_time_series_data()

        if time_series_data is None:
            return None  # Handle missing data gracefully

        # Use config-based extraction if config provided
        if config_path or config_dict:
            config = self._load_config(config_path, config_dict)
            return self._extract_from_config(time_series_data, config)
        else:
            # Fallback to manual method for all time series
            return self._extract_manual(time_series_data, method, **kwargs)

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
