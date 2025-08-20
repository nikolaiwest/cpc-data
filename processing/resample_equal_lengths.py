def resample_equal_lengths(
    data: list,
    time_data: list,
    target_length: int,
    cutoff_position: str = "post",
    padding_val: float = 0.0,
    padding_pos: str = "post",
    **kwargs,
) -> list:
    """
    Standardize time series to exact length through truncation or padding.

    This processing step ensures all time series have identical length for consistent
    downstream processing and feature extraction. Series that are too long are truncated
    at the specified position, while series that are too short are padded with a
    specified value. The time_data parameter is ignored as this operation works
    purely on data length regardless of temporal context.

    Reminder: This function should NOT be applied to time series data itself (the "time"
    attribute), as padding time values with arbitrary values or truncating time sequences
    will result in nonsensical temporal relationships. Time series require special
    handling to maintain temporal consistency and should be processed separately if
    length standardization is needed.

    Args:
        data: Input time series data to be length-standardized
        time_data: Time axis data (ignored by this function but required for signature)
        target_length: Desired final length for the time series
        cutoff_position: Where to truncate if series too long:
            - "post": Keep first target_length values (cut from end)
            - "pre": Keep last target_length values (cut from beginning)
        padding_val: Value to use for padding if series too short
        padding_pos: Where to add padding if series too short:
            - "post": Add padding at end [1,2,3] → [1,2,3,0,0]
            - "pre": Add padding at start [1,2,3] → [0,0,1,2,3]
        **kwargs: Ignored additional parameters from configuration

    Returns:
        list: Time series data with exactly target_length elements.
              Original data is preserved through copying before modification.

    Examples:
        # Truncation (series too long)
        resample_equal_lengths([1,2,3,4,5], None, 3, "post") → [1,2,3]
        resample_equal_lengths([1,2,3,4,5], None, 3, "pre") → [3,4,5]

        # Padding (series too short)
        resample_equal_lengths([1,2], None, 4, padding_pos="post") → [1,2,0.0,0.0]
        resample_equal_lengths([1,2], None, 4, padding_pos="pre") → [0.0,0.0,1,2]
    """
    # Input validation
    if not data or target_length <= 0:
        return data.copy() if data else []

    current_length = len(data)

    # No processing needed if already correct length
    if current_length == target_length:
        return data.copy()

    # Series too long - truncate
    if current_length > target_length:
        return _truncate_series(data, target_length, cutoff_position)

    # Series too short - pad
    else:
        return _pad_series(data, target_length, padding_val, padding_pos)


def _truncate_series(data: list, target_length: int, cutoff_position: str) -> list:
    """
    Truncate series that is longer than target length.

    Args:
        data: Input series data
        target_length: Desired final length
        cutoff_position: "post" (keep beginning) or "pre" (keep end)

    Returns:
        Truncated series with target_length elements
    """
    if cutoff_position == "pre":
        # Keep last target_length values (cut from beginning)
        return data[-target_length:].copy()
    else:  # "post" or any other value defaults to post
        # Keep first target_length values (cut from end)
        return data[:target_length].copy()


def _pad_series(
    data: list, target_length: int, padding_val: float, padding_pos: str
) -> list:
    """
    Pad series that is shorter than target length.

    Args:
        data: Input series data
        target_length: Desired final length
        padding_val: Value to use for padding
        padding_pos: "post" (pad at end) or "pre" (pad at beginning)

    Returns:
        Padded series with target_length elements
    """
    current_length = len(data)
    padding_needed = target_length - current_length
    padding = [padding_val] * padding_needed

    if padding_pos == "pre":
        # Add padding at beginning
        return padding + data.copy()
    else:  # "post" or any other value defaults to post
        # Add padding at end
        return data.copy() + padding
