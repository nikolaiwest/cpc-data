import numpy as np
from scipy import signal, stats


def extract_statistical(
    data: list, statistical_features: list = None, **kwargs
) -> list:
    """
    Extract statistical features from time series data.

    Computes features across multiple domains based on the statistical_features list:
    - "basic": Essential statistical measures (14 features)
    - "time": Time-domain characteristics (5 features)
    - "frequency": Frequency-domain features (5 features)

    Args:
        data: Processed time series data as list of values
        statistical_features: List of feature types to compute (e.g., ["basic", "time"])
                             If None, defaults to ["basic"]
        **kwargs: Additional parameters (ignored)

    Returns:
        list: Statistical feature values in consistent order.
              Length depends on number and type of requested features.
    """
    # Input validation
    if not data or len(data) == 0:
        return _get_empty_features(statistical_features or ["basic"])

    if len(data) == 1:
        return _get_single_value_features(data[0], statistical_features or ["basic"])

    # Convert to numpy array for efficient computation
    data_array = np.array(data)

    try:
        return _compute_features(data_array, statistical_features or ["basic"])

    except Exception as e:
        # Fallback if computation fails
        print(f"Warning: Statistical computation failed ({e}), returning zeros")
        return _get_empty_features(statistical_features or ["basic"])


def _compute_features(data_array: np.ndarray, statistical_features: list) -> list:
    """Compute features based on the specified feature types."""
    features = []

    for feature_type in statistical_features:
        if feature_type == "basic":
            features.extend(_compute_basic_statistical_features(data_array))
        elif feature_type == "time":
            features.extend(_compute_time_domain_features(data_array))
        elif feature_type == "frequency":
            features.extend(_compute_frequency_domain_features(data_array))
        else:
            print(f"Warning: Unknown feature type '{feature_type}', skipping")

    # Replace NaN with 0.0 for downstream compatibility
    return [0.0 if np.isnan(f) else float(f) for f in features]


def _compute_basic_statistical_features(data_array: np.ndarray) -> list:
    """
    Compute basic statistical features (14 features).

    Features: mean, std, max, min, median, range, q25, q75, iqr,
              skewness, kurtosis, rms, energy, abs_energy
    """
    return [
        np.mean(data_array),  # mean
        np.std(data_array),  # std
        np.max(data_array),  # max
        np.min(data_array),  # min
        np.median(data_array),  # median
        np.ptp(data_array),  # range (peak-to-peak)
        np.percentile(data_array, 25),  # 25th percentile
        np.percentile(data_array, 75),  # 75th percentile
        np.percentile(data_array, 75) - np.percentile(data_array, 25),  # iqr
        stats.skew(data_array),  # skewness
        stats.kurtosis(data_array),  # kurtosis
        np.sqrt(np.mean(np.square(data_array))),  # rms
        np.sum(np.square(data_array)),  # energy
        np.sum(np.abs(data_array)),  # abs_energy
    ]


def _compute_time_domain_features(data_array: np.ndarray) -> list:
    """
    Compute time-domain features (5 features).

    Features: zero_crossing_rate, peak_to_peak, crest_factor, autocorr_lag_1, trend
    """
    rms = np.sqrt(np.mean(np.square(data_array)))

    return [
        # Zero crossing rate
        np.sum(np.diff(np.sign(data_array)) != 0) / len(data_array),
        # Peak to peak
        np.max(data_array) - np.min(data_array),
        # Crest factor
        np.max(np.abs(data_array)) / rms if rms > 0 else np.inf,
        # Autocorrelation at lag 1
        (
            np.correlate(data_array, data_array, mode="full")[len(data_array) :][0]
            / (np.var(data_array) * len(data_array))
            if np.var(data_array) > 0
            else 0
        ),
        # Linear trend slope
        np.polyfit(np.arange(len(data_array)), data_array, 1)[0],
    ]


def _compute_frequency_domain_features(data_array: np.ndarray) -> list:
    """
    Compute frequency-domain features (5 features).

    Features: dominant_freq, spectral_centroid, spectral_entropy, spectral_energy, spectral_kurtosis
    """
    # Compute power spectral density with adaptive window size
    nperseg = min(256, len(data_array))
    f, psd = signal.welch(data_array, nperseg=nperseg)

    total_power = np.sum(psd)

    return [
        # Dominant frequency
        f[np.argmax(psd)],
        # Spectral centroid
        np.sum(f * psd) / total_power if total_power > 0 else 0,
        # Spectral entropy
        stats.entropy(psd) if np.any(psd > 0) else 0,
        # Spectral energy
        total_power,
        # Spectral kurtosis
        stats.kurtosis(psd),
    ]


def _get_empty_features(statistical_features: list) -> list:
    """Return zero features for empty data."""
    feature_counts = {"basic": 14, "time": 5, "frequency": 5}
    total_features = sum(feature_counts.get(ft, 0) for ft in statistical_features)
    return [0.0] * total_features


def _get_single_value_features(value: float, statistical_features: list) -> list:
    """Return appropriate features for single-value data."""
    result = []

    for feature_type in statistical_features:
        if feature_type == "basic":
            # For single value: mean=min=max=median=value, std=range=iqr=0, etc.
            result.extend(
                [
                    value,  # mean
                    0.0,  # std
                    value,  # max
                    value,  # min
                    value,  # median
                    0.0,  # range
                    value,  # q25
                    value,  # q75
                    0.0,  # iqr
                    0.0,  # skewness
                    0.0,  # kurtosis
                    value,  # rms
                    value**2,  # energy
                    abs(value),  # abs_energy
                ]
            )
        elif feature_type == "time":
            # Time features don't make sense for single value
            result.extend([0.0] * 5)
        elif feature_type == "frequency":
            # Basic frequency response for single value
            result.extend([0.0, 0.0, 0.0, value**2, 0.0])

    return result
