import numpy as np
from sklearn.decomposition import PCA


def extract_pca(data: list, pca_n_components: int = 24, **kwargs) -> list:
    """
    Extract principal components from time series data for dimensionality reduction.

    Applies Principal Component Analysis to reduce the dimensionality of time series
    data while preserving the most important variance. Uses sklearn's PCA implementation
    on the time series data directly.

    Note: We initially coded a manual PCA implementation using numpy's eigenvalue
    decomposition, but decided to use sklearn's PCA for better numerical stability,
    automatic edge case handling, and maintainability.

    Args:
        data: Processed time series data as list of values
        pca_n_components: Number of principal components to extract (must be <= len(data))
        **kwargs: Additional parameters (ignored)

    Returns:
        list: Principal component values representing the transformed data.
              Length will be min(pca_n_components, len(data)).
    """
    # Input validation
    if not data or len(data) == 0:
        return []

    if len(data) == 1:
        return [data[0]]

    # Convert to numpy array and reshape for PCA (each point as a feature)
    data_array = np.array(data).reshape(1, -1)  # 1 sample, n features

    # Ensure pca_n_components doesn't exceed data length
    pca_n_components = min(pca_n_components, len(data))

    try:
        # Apply sklearn PCA
        pca = PCA(n_components=pca_n_components)
        pca_result = pca.fit_transform(data_array)

        # Return the transformed values
        result = pca_result[0].tolist()

        # Pad with zeros if needed
        while len(result) < pca_n_components:
            result.append(0.0)

        return result[:pca_n_components]

    except Exception as e:
        # Fallback if PCA fails
        print(
            f"Warning: PCA computation failed ({e}), returning truncated original data"
        )
        return data[:pca_n_components] + [0.0] * max(0, pca_n_components - len(data))
