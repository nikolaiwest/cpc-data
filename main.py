from schema.experiment_data import ExperimentData
from schema.experiment_dataset import ExperimentDataset

# Test individual experiment
print("=== Testing Individual Experiment ===")
experiment = ExperimentData(upper_workpiece_id=17401)
print(f"Single experiment: {experiment}")
print(f"Available processes: {experiment.get_available_processes()}")

# Test manual data extraction
try:
    data = experiment.get_data(method="raw")
    print(f"Manual extraction successful: {len(data)} processes")
except Exception as e:
    print(f"Manual extraction failed: {e}")

# Test config-based extraction
try:
    data = experiment.get_data(config_path="settings.yml")
    print(f"Config extraction successful: {len(data)} processes")
except Exception as e:
    print(f"Config extraction failed: {e}")

print("\n" + "=" * 50 + "\n")

# Test dataset creation from class values
print("=== Testing ExperimentDataset with Flexible Filtering ===")

# Initialize variables for later testing
control_dataset = None
recyclate_dataset = None
glass_fiber_dataset = None

# Create control group dataset (exact match)
print("Creating control group dataset...")
try:
    control_dataset = ExperimentDataset.from_class_values(
        class_column="class_value_upper_work_piece",
        filter_type="exact",
        filter_value="control_group_01",
        sample_size=10,
    )
    print(f"Control dataset: {control_dataset}")
except Exception as e:
    print(f"Control dataset creation failed: {e}")

# Create recyclate content dataset (contains filter)
print("\nCreating recyclate content dataset (contains filter)...")
try:
    recyclate_dataset = ExperimentDataset.from_class_values(
        class_column="class_value_upper_work_piece",
        filter_type="contains",
        filter_value="recyclate_content",
        sample_size=5,
    )
    print(f"Recyclate dataset: {recyclate_dataset}")
except Exception as e:
    print(f"Recyclate dataset creation failed: {e}")

# Create glass fiber dataset (contains filter)
print("\nCreating glass fiber dataset (contains filter)...")
try:
    glass_fiber_dataset = ExperimentDataset.from_class_values(
        class_column="class_value_upper_work_piece",
        filter_type="contains",
        filter_value="glass_fiber",
        sample_size=3,
    )
    print(f"Glass fiber dataset: {glass_fiber_dataset}")
except Exception as e:
    print(f"Glass fiber dataset creation failed: {e}")

# Test specific glass fiber percentages (list filter)
print("\nTesting specific glass fiber percentages (list filter)...")
try:
    specific_glass_fiber = ExperimentDataset.from_class_values(
        class_column="class_value_upper_work_piece",
        filter_type="list",
        filter_value=[
            "glass_fiber_content_22",
            "glass_fiber_content_24",
            "glass_fiber_content_26",
        ],
        sample_size=3,
    )
    print(f"Specific glass fiber dataset: {specific_glass_fiber}")
except Exception as e:
    print(f"Specific glass fiber dataset creation failed: {e}")

# Test filtering by different class columns
print("\nTesting different class columns...")
try:
    tightening_dataset = ExperimentDataset.from_class_values(
        class_column="class_value_tightening_process",
        filter_type="contains",
        filter_value="temperature",
        sample_size=2,
    )
    print(f"Tightening process dataset: {tightening_dataset}")
except Exception as e:
    print(f"Tightening process dataset creation failed: {e}")

# Test dataset from specific IDs
print("\nCreating dataset from specific IDs...")
try:
    id_dataset = ExperimentDataset.from_ids([17401, 17402, 17403])
    print(f"ID-based dataset: {id_dataset}")
    print(f"Dataset length: {len(id_dataset)}")
except Exception as e:
    print(f"ID-based dataset creation failed: {e}")
    id_dataset = None

# Demonstration of research workflow
print("\n" + "=" * 50)
print("=== Research Workflow Demonstration ===")

# Compare different material conditions
print("Setting up comparative analysis...")
if control_dataset and (recyclate_dataset or glass_fiber_dataset):
    print("✅ Multiple material conditions available for comparison")

    # Show class distributions
    for name, dataset in [
        ("Control", control_dataset),
        ("Recyclate", recyclate_dataset),
        ("Glass Fiber", glass_fiber_dataset),
    ]:
        if dataset:
            labels = dataset.get_class_labels()
            if labels:
                unique_labels = set([l for l in labels if l is not None])
                print(f"{name}: {len(dataset)} experiments, classes: {unique_labels}")
else:
    print("⚠️ Not enough different material conditions for comparison")

print("\n" + "=" * 50)

# Test cross-experiment data extraction
print("\nTesting cross-experiment data extraction...")
try:
    # Use whichever dataset was created successfully
    test_dataset = (
        control_dataset or recyclate_dataset or glass_fiber_dataset or id_dataset
    )

    if test_dataset and len(test_dataset) > 0:
        # Find available processes for this dataset
        info = test_dataset.get_experiment_info()
        available_processes = info["available_processes"]
        print(f"Available processes: {available_processes}")

        if available_processes:
            # Use the first available process and series
            if "screw_left" in available_processes:
                series_path = "screw_left.torque"
            elif "injection_lower" in available_processes:
                series_path = "injection_lower.injection_pressure"
            else:
                series_path = list(available_processes.keys())[0] + ".time_series"

            # Test raw series collection
            pressure_data = test_dataset.get_data(series_path=series_path, method="raw")
            print(
                f"Raw {series_path} data: {len(pressure_data['data'])} series collected"
            )

            # Test PCA placeholder
            pca_data = test_dataset.get_data(
                series_path=series_path, method="pca", components=5
            )
            print(
                f"PCA analysis: {pca_data['method']} on {pca_data['n_experiments']} experiments"
            )

        # Test feature matrix (no series_path needed)
        feature_matrix = test_dataset.get_data(method="features_matrix")
        print(f"Feature matrix: {len(feature_matrix['feature_matrix'])} experiments")
    else:
        print("No datasets available for cross-experiment testing")

except Exception as e:
    print(f"Cross-experiment extraction failed: {e}")

print("\n" + "=" * 50)
print("Testing complete! Check for any errors above.")
