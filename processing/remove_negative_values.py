from typing import Union


def remove_negative_values(
    data: list,
    time_data: list,
    replacement_value: Union[float, None, str] = 0.0,
    **kwargs
) -> list:
    """
    Handle negative values in time series data based on replacement strategy.

    This processing step cleans time series data by applying different strategies
    for handling negative values. The time_data parameter is ignored as this
    operation doesn't require temporal context, but is included for consistent
    function signature across all processing steps.

    Args:
        data: Input time series as list of numbers to be processed
        time_data: Time axis data (ignored by this function but required for signature)
        replacement_value: Strategy for handling negatives:
            - float: Replace negatives with this value (e.g., 0.0)
            - None: Replace negatives with None/null values
            - "keep": Keep negatives unchanged (no-op)
        **kwargs: Ignored additional parameters from configuration

    Returns:
        list: Processed time series with negatives handled according to strategy.
              Length and order preserved, only negative values are modified.

    Examples:
        remove_negative_values([1, -2, 3], None, 0.0)     -> [1, 0.0, 3]
        remove_negative_values([1, -2, 3], None, None)    -> [1, None, 3]
        remove_negative_values([1, -2, 3], None, "keep")  -> [1, -2, 3]
    """
    # Handle "keep" strategy - return data unchanged
    if replacement_value == "keep":
        return data.copy()

    # Process each value based on replacement strategy
    processed_data = []
    for value in data:
        if value < 0:
            # Replace negative with specified replacement_value
            processed_data.append(replacement_value)
        else:
            # Keep positive values unchanged
            processed_data.append(value)

    return processed_data
