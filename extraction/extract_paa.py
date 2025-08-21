import numpy as np


def extract_paa(data: list, paa_target_length: int = 200, **kwargs) -> list:
    """
    Extract Piecewise Aggregate Approximation (PAA) features from time series data.

    PAA reduces the dimensionality of time series by dividing the series into segments
    and computing the mean value for each segment. This provides a lower-dimensional
    representation while preserving the overall shape and trends of the time series.

    Args:
        data: Processed time series data as list of values
        paa_target_length: Number of PAA segments to create (target output length)
        **kwargs: Additional parameters (ignored)

    Returns:
        list: PAA feature values representing segment means.
              Length will be exactly paa_target_length.
    """
    # Input validation
    if not data or len(data) == 0:
        return [0.0] * paa_target_length

    if len(data) == 1:
        return [data[0]] * paa_target_length

    # Convert to numpy array for efficient computation
    data_array = np.array(data)
    data_length = len(data_array)

    # Handle case where target length >= data length
    if paa_target_length >= data_length:
        # Pad with zeros if needed
        result = data_array.tolist()
        while len(result) < paa_target_length:
            result.append(0.0)
        return result[:paa_target_length]

    try:
        # Calculate segment size (floating point for even division)
        segment_size = data_length / paa_target_length

        paa_features = []

        for i in range(paa_target_length):
            # Calculate start and end indices for this segment
            start_idx = int(i * segment_size)
            end_idx = int((i + 1) * segment_size)

            # Handle edge case for last segment to include any remaining points
            if i == paa_target_length - 1:
                end_idx = data_length

            # Extract segment and compute mean
            segment = data_array[start_idx:end_idx]
            segment_mean = np.mean(segment)
            paa_features.append(float(segment_mean))

        return paa_features

    except Exception as e:
        # Fallback if PAA computation fails
        print(f"Warning: PAA computation failed ({e}), returning zero-padded data")

        # Return truncated/padded original data as fallback
        if len(data) >= paa_target_length:
            return data[:paa_target_length]
        else:
            result = data.copy()
            while len(result) < paa_target_length:
                result.append(0.0)
            return result
