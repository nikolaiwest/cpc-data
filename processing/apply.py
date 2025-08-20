from . import PROCESSING_REGISTRY


def apply_processing(series_dict: dict, config: dict) -> dict:
    """
    Apply processing steps to all time series with full context awareness.

    This is the main orchestration function for the processing pipeline. It takes
    the complete set of time series data from a recording and applies configured
    processing steps to prepare the data for feature extraction. Processing steps
    are applied in the order specified in the configuration, with each step receiving
    both the current data and time context for time-aware operations.

    The function handles error recovery by falling back to original data if any
    processing step fails, ensuring that downstream processing can continue even
    when individual steps encounter issues.

    Args:
        series_dict: All time series data from recording including time axis.
                    Format: {"time": [...], "torque": [...], "angle": [...], ...}
                    The "time" key is required and contains timestamps corresponding
                    to all other time series measurements.
        config: Processing configuration for all series from YAML processing.yml.
                Format: {series_name: {step_name: step_params, ...}, ...}
                Each series can have different processing steps with individual
                parameters. Steps are applied in configuration order.

    Returns:
        dict: Processed series dictionary with same keys as input except "time".
              The time series is removed from output as it serves as context only.
              Only includes series that have processing configuration defined.
              Original data is preserved if processing fails for any series.

    Example:
        series_dict = {
            "time": [0.0, 0.01, 0.02, 0.03],
            "torque": [1.2, -0.5, 2.1, 1.8]
        }
        config = {
            "torque": {
                "remove_negative_values": {"replacement_value": 0.0},
                "apply_equal_lengths": {"target_length": 8}
            }
        }
        result = apply_processing(series_dict, config)
        # Returns: {"torque": [1.2, 0.0, 2.1, 1.8, 0.0, 0.0, 0.0, 0.0]}
    """
    # Handle empty inputs
    if not series_dict or not config:
        return series_dict.copy() if series_dict else {}

    # Prepare data for processing
    processed_data, time_data = _prepare_processing_data(series_dict)

    # Process each configured series
    for recording_to_process, series_config in config.items():
        if _should_skip_series(recording_to_process, series_dict):
            continue

        # Process this series through all its steps
        processed_series = _process_series_steps(
            series_dict[recording_to_process],
            time_data,
            series_config,
            recording_to_process,
        )

        processed_data[recording_to_process] = processed_series

    return processed_data


def _prepare_processing_data(series_dict: dict) -> tuple[dict, list]:
    """
    Extract time data and prepare processing dictionary.

    Separates the time series from other measurement data to provide clean context
    for processing operations. The time series is removed from the processing
    dictionary but preserved separately to enable time-aware processing steps
    like resampling and interpolation.

    Args:
        series_dict: Complete series data including time axis

    Returns:
        tuple: (processed_data_dict, time_data_list) where processed_data_dict
               is a copy of the input without the "time" key, and time_data_list
               contains the extracted time series for use as processing context.
    """
    processed_data = series_dict.copy()
    time_data = processed_data.pop("time")
    return processed_data, time_data


def _should_skip_series(recording_to_process: str, series_dict: dict) -> bool:
    """
    Check if series should be skipped due to missing or invalid data.

    Performs validation to determine whether a configured series can be processed.
    This includes checking for series existence in the data dictionary and
    validating that the series contains actual data rather than None values.
    Warning messages are logged for missing series to aid in debugging
    configuration mismatches.

    Args:
        recording_to_process: Name of the series to validate
        series_dict: Complete series data dictionary for existence checking

    Returns:
        bool: True if series should be skipped, False if processing should continue.
              Series are skipped when they don't exist in data or contain None values.
    """
    if recording_to_process not in series_dict:
        print(f"Warning: '{recording_to_process}' not found in data - skipping")
        return True

    if series_dict[recording_to_process] is None:
        return True

    return False


def _process_series_steps(
    original_data: list, time_data: list, series_config: dict, series_name: str
) -> list:
    """
    Process a single series through all its configured processing steps.

    Applies each configured processing step in sequence, maintaining data flow
    from one step to the next. Each step receives the current data state, time
    context, and its specific configuration parameters. If any step fails or
    returns None, processing stops and the function returns the original
    unprocessed data to ensure robust error recovery.

    Processing steps are applied in the order they appear in the configuration,
    allowing for controlled data transformation pipelines where order matters
    (e.g., cleaning before resampling before length normalization).

    Args:
        original_data: The raw time series data for this measurement parameter
        time_data: Time axis data for time-aware processing operations
        series_config: Configuration dictionary for this specific series containing
                      step names as keys and step parameters as values
        series_name: Name of the series being processed (for error reporting)

    Returns:
        list: Processed time series data after applying all configured steps.
              Returns original data if any processing step fails to ensure
              downstream processing can continue with unprocessed but valid data.
    """
    current_data = original_data.copy()

    for step_name, step_config in series_config.items():
        if _should_skip_step(step_name, step_config):
            continue

        current_data = _apply_single_step(
            current_data, time_data, step_name, step_config, series_name
        )

        # If step failed, return to original data
        if current_data is None:
            return original_data.copy()

    return current_data


def _should_skip_step(step_name: str, step_config: dict) -> bool:
    """
    Check if processing step should be skipped based on configuration and availability.

    Validates whether a configured processing step should be executed by checking
    for explicit skip directives and step registration. Steps can be disabled
    by setting their configuration to False, and unregistered steps are skipped
    with warning messages to aid in debugging configuration errors.

    Args:
        step_name: Name of the processing step to validate
        step_config: Configuration for this step (can be False, dict, or other)

    Returns:
        bool: True if step should be skipped, False if step should be executed.
              Steps are skipped when explicitly set to False or when not found
              in the processing registry.
    """
    if step_config is False:
        return True

    if step_name not in PROCESSING_REGISTRY:
        print(f"Warning: Unknown processing step '{step_name}' - skipping")
        return True

    return False


def _apply_single_step(
    current_data: list,
    time_data: list,
    step_name: str,
    step_config: dict,
    series_name: str,
) -> list | None:
    """
    Apply a single processing step to the data with comprehensive error handling.

    Executes one processing step from the registry, passing the current data state,
    time context, and step-specific parameters. The function handles both successful
    processing and error conditions, providing detailed logging for debugging.
    If a step returns None (indicating processing failure) or raises an exception,
    appropriate warning messages are logged.

    Processing functions are expected to follow the signature:
    func(data, time_data, **step_config) -> list

    Args:
        current_data: Current state of the time series data being processed
        time_data: Time axis data for time-aware processing operations
        step_name: Name of the processing step for registry lookup and error reporting
        step_config: Parameters to pass to the processing function via **kwargs
        series_name: Name of the series being processed (for error reporting context)

    Returns:
        list or None: Processed data if step succeeds, None if step fails.
                     Returning None signals that error recovery should be triggered
                     by the calling function to preserve data integrity.
    """
    processing_func = PROCESSING_REGISTRY[step_name]

    try:
        processed_data = processing_func(current_data, time_data, **step_config)

        if processed_data is None:
            print(
                f"Warning: Step '{step_name}' returned None for '{series_name}' - keeping original"
            )

        return processed_data

    except Exception as e:
        print(
            f"Error in step '{step_name}' for series '{series_name}': {e} - keeping original"
        )
        return None
