import pandas as pd
from tsfresh import extract_features
from tsfresh.feature_extraction import (
    ComprehensiveFCParameters,
    EfficientFCParameters,
    MinimalFCParameters,
)


def extract_tsfresh(
    data: list, tsfresh_feature_set: str = "efficient", **kwargs
) -> list:
    """
    Extract tsfresh statistical features from time series data.

    Uses the tsfresh library to compute comprehensive time series features.
    Supports three feature sets with different complexity and computation time:
    - "minimal": ~20 fast, basic features
    - "efficient": ~100 balanced features (good performance/speed trade-off)
    - "comprehensive": ~800 complete features (slow but thorough)

    Args:
        data: Processed time series data as list of values
        tsfresh_feature_set: Feature set complexity ('minimal', 'efficient', 'comprehensive')
        **kwargs: Additional parameters (ignored)

    Returns:
        list: Extracted tsfresh features in consistent order.
              Length depends on selected feature set.
    """
    # Input validation
    if not data or len(data) == 0:
        return _get_empty_tsfresh_features(tsfresh_feature_set)

    if len(data) == 1:
        return _get_single_value_tsfresh_features(data[0], tsfresh_feature_set)

    try:
        # Prepare data in tsfresh format (DataFrame with id and time columns)
        df = pd.DataFrame(
            {
                "id": [1] * len(data),  # Single time series ID
                "time": range(len(data)),  # Time index
                "value": data,  # Time series values
            }
        )

        # Select feature extraction settings based on feature set
        if tsfresh_feature_set == "minimal":
            fc_parameters = MinimalFCParameters()
        elif tsfresh_feature_set == "comprehensive":
            fc_parameters = ComprehensiveFCParameters()
        else:  # "efficient" or any other value
            fc_parameters = EfficientFCParameters()

        # Extract features using tsfresh
        features_df = extract_features(
            df,
            column_id="id",
            column_sort="time",
            column_value="value",
            default_fc_parameters=fc_parameters,
            disable_progressbar=True,  # Suppress progress bar for cleaner output
            n_jobs=1,  # Single process to avoid multiprocessing issues
        )

        # Convert to list and handle NaN values
        features_list = features_df.iloc[0].tolist()  # Get first (and only) row

        # Replace NaN and inf values with 0.0 for downstream compatibility
        features_list = [
            0.0 if (pd.isna(f) or f == float("inf") or f == float("-inf")) else float(f)
            for f in features_list
        ]

        return features_list

    except Exception as e:
        # Fallback if tsfresh computation fails
        print(f"Warning: TSFresh computation failed ({e}), returning zeros")
        return _get_empty_tsfresh_features(tsfresh_feature_set)


def _get_empty_tsfresh_features(tsfresh_feature_set: str) -> list:
    """Return zero features for empty data based on feature set."""
    # Approximate feature counts for each tsfresh feature set
    feature_counts = {"minimal": 20, "efficient": 100, "comprehensive": 800}

    count = feature_counts.get(tsfresh_feature_set, 100)  # Default to efficient
    return [0.0] * count


def _get_single_value_tsfresh_features(value: float, tsfresh_feature_set: str) -> list:
    """Return appropriate features for single-value data."""
    # For single values, most tsfresh features would be undefined or constant
    # Return the value for some features and 0 for others
    feature_counts = {"minimal": 20, "efficient": 100, "comprehensive": 800}

    count = feature_counts.get(tsfresh_feature_set, 100)

    # Create a mix of the actual value and zeros
    # First few features get the value, rest are zeros
    features = [value] * min(5, count) + [0.0] * max(0, count - 5)
    return features[:count]
