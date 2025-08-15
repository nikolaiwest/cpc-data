# Placeholder code from base
from settings import get_extraction_settings, get_processing_settings

from . import EXTRACTION_REGISTRY


def apply_extraction_pipeline(data, config):
    """
    Apply extraction method based on configuration.

    Args:
        data: Processed time series data (list of values)
        config: Dictionary containing method and parameters

    Returns:
        Extracted features (format depends on method)
    """
    if data is None:
        return None

    method = config.get("method", "raw")

    if method not in EXTRACTION_REGISTRY:
        raise ValueError(f"Unknown extraction method: {method}")

    # Extract method-specific parameters (exclude 'method' and 'use_series')
    params = {k: v for k, v in config.items() if k not in ["method", "use_series"]}

    func = EXTRACTION_REGISTRY[method]
    return func(data, **params)


def _apply_extraction(self, processed_data):
    """Apply extraction using extraction.yml config."""
    try:
        # Load extraction settings
        extraction_settings = get_extraction_settings()

        class_name = self._get_class_name()
        class_config = extraction_settings.get(class_name, {})

        results = {}
        for series_name, series_config in class_config.items():
            if series_config.get("use_series", False) and series_name in processed_data:
                method = series_config.get("method", "raw")
                params = {
                    k: v
                    for k, v in series_config.items()
                    if k not in ["use_series", "method"]
                }

                series_data = processed_data[series_name]
                results[series_name] = self._apply_method(series_data, method, **params)

        return results

    except Exception as e:
        print(f"Warning: Extraction failed for {self._get_class_name()}: {e}")
        # Return processed data if extraction fails
        return processed_data


def _extract_from_config(self, time_series_data, config):
    """Extract features based on YAML configuration."""
    class_name = self._get_class_name()
    class_config = config.get("extraction", {}).get(class_name, {})

    results = {}
    for series_name, series_config in class_config.items():
        if series_config.get("use_series", False) and series_name in time_series_data:
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
