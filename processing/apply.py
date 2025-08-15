# Placeholder code from base
from settings import get_extraction_settings, get_processing_settings

from . import PROCESSING_REGISTRY


def apply_processing_pipeline(data, config):
    """
    Apply processing steps in sequence based on configuration.

    Args:
        data: Time series data (list of values)
        config: Dictionary of processing step configurations

    Returns:
        Processed time series data
    """
    processed_data = data.copy() if data else None

    if processed_data is None:
        return None

    for step_name, step_config in config.items():
        if step_name in PROCESSING_REGISTRY:
            func = PROCESSING_REGISTRY[step_name]
            processed_data = func(processed_data, **step_config)
        else:
            print(f"Warning: Unknown processing step '{step_name}' - skipping")

    return processed_data


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
