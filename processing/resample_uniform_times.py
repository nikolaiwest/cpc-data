def resample_uniform_times(
    data: list,
    time_data: list,
    target_distance: float,
    **kwargs,
) -> list:
    """
    Resample time series data to consistent time intervals using linear interpolation.

    This processing step converts irregularly sampled time series data to a regular
    time grid with consistent intervals. This is essential for many signal processing
    and machine learning algorithms that assume uniform sampling. The function uses
    linear interpolation to estimate values at the new time points.

    Args:
        data: Input time series values to be resampled
        time_data: Corresponding time stamps for the data values
        target_distance: Desired time interval between samples (in same units as time_data)
        **kwargs: Ignored additional parameters from configuration

    Returns:
        list: Resampled time series data with consistent time intervals.
              The output will have uniform spacing of target_distance between samples.
              Start and end times are preserved from the original data.

    Example:
        data = [10, 15, 25, 30]
        time_data = [0.0, 0.005, 0.015, 0.02]
        target_distance = 0.01
        result = apply_equal_distance(data, time_data, 0.01)
        # Returns values interpolated at [0.0, 0.01, 0.02]
    """
    # Validate inputs
    if time_data is None or len(time_data) == 0:
        return data.copy()  # Can't resample without time context

    if len(data) != len(time_data):
        print("Warning: data and time_data have different lengths")
        return data.copy()

    if len(data) < 2:
        return data.copy()  # Need at least 2 points for interpolation

    if target_distance <= 0:
        print(f"Warning: Invalid target_distance {target_distance}, must be > 0")
        return data.copy()

    # Create new uniform time grid
    start_time = min(time_data)
    end_time = max(time_data)

    # Calculate number of points needed
    time_span = end_time - start_time
    num_points = int(time_span / target_distance) + 1

    # Generate new time points with rounding to avoid floating point precision issues
    new_time_points = [
        round(start_time + i * target_distance, 4) for i in range(num_points)
    ]

    # Ensure we don't exceed the original time range
    new_time_points = [t for t in new_time_points if t <= end_time]

    # If only one point or no resampling needed, return original
    if len(new_time_points) <= 1:
        return data.copy()

    # Perform linear interpolation
    interpolated_data = []
    for target_time in new_time_points:
        interpolated_value = _linear_interpolate(data, time_data, target_time)
        interpolated_data.append(interpolated_value)

    return interpolated_data


def _linear_interpolate(data: list, time_data: list, target_time: float) -> float:
    """
    Perform linear interpolation to find value at target_time.

    Args:
        data: Y values
        time_data: X values (time)
        target_time: Time point to interpolate at

    Returns:
        Interpolated value at target_time
    """
    # Handle edge cases
    if target_time <= time_data[0]:
        return data[0]
    if target_time >= time_data[-1]:
        return data[-1]

    # Find the two points that bracket target_time
    for i in range(len(time_data) - 1):
        if time_data[i] <= target_time <= time_data[i + 1]:
            # Linear interpolation formula
            t0, t1 = time_data[i], time_data[i + 1]
            y0, y1 = data[i], data[i + 1]

            # Handle case where time points are the same
            if t1 == t0:
                return y0

            # Linear interpolation: y = y0 + (y1 - y0) * (t - t0) / (t1 - t0)
            weight = (target_time - t0) / (t1 - t0)
            return y0 + (y1 - y0) * weight

    # Should never reach here, but return last value as fallback
    return data[-1]
