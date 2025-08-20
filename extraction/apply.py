from . import EXTRACTION_REGISTRY


def apply_extraction(processed_series_dict: dict, config: dict) -> dict:
    """
    Extract features from processed time series based on configuration.

    This function takes processed time series data and applies feature extraction
    methods to convert time series into feature vectors suitable for machine learning
    or analysis. Any series listed in the extraction configuration will have features
    extracted using the specified method and parameters.

    Args:
        processed_series_dict: Output from apply_processing containing cleaned,
                              resampled, and length-standardized time series data.
                              Format: {series_name: [processed_values], ...}
        config: Extraction configuration from YAML extraction.yml.
                Format: {series_name: {method: str, param1: val1, ...}, ...}
                Each series specifies extraction method and parameters.

    Returns:
        dict: Extracted features dictionary where keys are series names and
              values are extracted feature representations. Only includes
              series that are configured for extraction.

    Example:
        processed_series_dict = {
            "torque": [1.2, 0.0, 2.1, 1.8, 0.0, 0.0, 0.0, 0.0],
            "angle": [0.0, 1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4]
        }
        config = {
            "torque": {"method": "raw"},
            "angle": {"method": "paa", "segments": 4}
        }
        result = apply_extraction(processed_series_dict, config)
    """
    # Handle empty inputs
    if not processed_series_dict or not config:
        return {}

    extracted_features = {}

    # Extract features from each configured series
    for series_name, series_config in config.items():
        if _should_skip_extraction(series_name, processed_series_dict):
            continue

        # Extract features from this series
        series_data = processed_series_dict[series_name]
        extracted_features[series_name] = _extract_series_features(
            series_data, series_config, series_name
        )

        # Handle extraction failure
        if extracted_features[series_name] is None:
            print(f"Warning: Feature extraction failed for '{series_name}' - skipping")
            del extracted_features[series_name]

    return extracted_features


def _should_skip_extraction(series_name: str, processed_series_dict: dict) -> bool:
    """
    Check if series should be skipped for feature extraction.

    Validates data availability and validity. Series are skipped only if
    data is missing or invalid, not based on configuration flags.

    Args:
        series_name: Name of the series to validate
        processed_series_dict: Available processed series data

    Returns:
        bool: True if series should be skipped, False if extraction should proceed.
    """
    # Skip if series not in processed data
    if series_name not in processed_series_dict:
        print(
            f"Warning: '{series_name}' not found in processed data - skipping extraction"
        )
        return True

    # Skip if series data is None or empty
    series_data = processed_series_dict[series_name]
    if series_data is None or len(series_data) == 0:
        return True

    return False


def _extract_series_features(series_data: list, series_config: dict, series_name: str):
    """
    Extract features from a single time series using configured method.

    Applies the specified extraction method to convert time series data into
    feature representation. Handles method validation, parameter extraction,
    and error recovery for robust feature extraction.

    Args:
        series_data: Processed time series data as list of values
        series_config: Configuration including method and parameters
        series_name: Name of series being processed (for error reporting)

    Returns:
        Extracted features in format determined by extraction method,
        or None if extraction fails.
    """
    method = series_config.get("method", "raw")

    # Check if extraction method is registered
    if method not in EXTRACTION_REGISTRY:
        print(
            f"Warning: Unknown extraction method '{method}' for '{series_name}' - skipping"
        )
        return None

    # Get extraction function
    extraction_func = EXTRACTION_REGISTRY[method]

    # Extract method-specific parameters (exclude 'method')
    extraction_params = {k: v for k, v in series_config.items() if k != "method"}

    try:
        # Apply extraction method
        extracted_features = extraction_func(series_data, **extraction_params)

        if extracted_features is None:
            print(
                f"Warning: Extraction method '{method}' returned None for '{series_name}'"
            )

        return extracted_features

    except Exception as e:
        print(f"Error in extraction method '{method}' for series '{series_name}': {e}")
        return None
