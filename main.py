from schema import ExperimentData, ExperimentDataset

# Basic usage example
if __name__ == "__main__":
    # Single experiment
    experiment = ExperimentData(upper_workpiece_id=17401)
    print(f"Loaded experiment: {experiment}")

    # Dataset for analysis
    dataset = ExperimentDataset.from_class_values(
        class_column="class_value_screw_driving",
        filter_type="contains",
        filter_value="switching-point",
        # sample_size=5,
    )

    # Extract tabular data
    df = dataset.get_data()
    print(f"Dataset shape: {df.shape}")
    print(f"Available features: {list(df.columns)[:10]}...")  # Show first 10
