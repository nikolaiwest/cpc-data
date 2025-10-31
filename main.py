"""
Quick examples of common usage patterns.

You can run this file to verify your installation and see basic functionality.
"""

from schema import ExperimentData, ExperimentDataset


def example_single_experiment():
    """Load and inspect a single experiment."""
    print("\n=== Single Experiment Example ===")
    experiment = ExperimentData(upper_workpiece_id=9765)
    print(f"Loaded: {experiment}")
    print(f"Available processes: {experiment.get_available_recordings()}")


def example_dataset_creation():
    """Create a dataset from class values."""
    print("\n=== Dataset Creation Example ===")
    dataset = ExperimentDataset.from_class_values(
        class_column="class_value_screw_driving",
        filter_type="contains",
        filter_value="switching-point",
        sample_size=10,  # Small sample for quicker testing
    )
    print(f"Dataset: {dataset}")


def example_data_extraction():
    """Extract features from a dataset."""
    print("\n=== Data Extraction Example ===")
    dataset = ExperimentDataset.from_class_values(
        class_column="class_value_screw_driving",
        filter_type="list",
        filter_value=["301_glass-fiber-content-30", "305_glass-fiber-content-10"],
        sample_size=10,
    )

    # Get data as lists (compact)
    df = dataset.get_data()
    print(f"Compact format shape: {df.shape}")
    print(f"Columns (first 10): {list(df.columns)[:10]}")

    # Get exploded data (wide format)
    df_exploded = dataset.get_data(explode=True)
    print(f"Exploded format shape: {df_exploded.shape}")


if __name__ == "__main__":
    print("Running Cross-Process Chain Error Detection Examples")
    print("=" * 60)

    # Run examples
    example_single_experiment()
    example_dataset_creation()
    example_data_extraction()

    print("\n" + "=" * 60)
    print("Examples completed successfully!")
