from typing import Any, Dict, List, Optional

import pandas as pd

from .data import ExperimentData


class ExperimentDataset:
    """
    Collection of multiple experiments for cross-experiment analysis.
    """

    def __init__(self, experiments: List[ExperimentData] = None):
        self.experiments = experiments or []
        self.class_values_df = None

    @classmethod
    def from_ids(cls, upper_workpiece_ids: List[int]):
        """Create dataset from list of upper workpiece IDs."""
        experiments = []
        for workpiece_id in upper_workpiece_ids:
            try:
                experiment = ExperimentData(workpiece_id)
                experiments.append(experiment)
            except Exception as e:
                print(f"Warning: Could not load experiment {workpiece_id}: {e}")

        return cls(experiments)

    @classmethod
    def from_class_values(
        cls,
        class_column: str = "class_value_upper_work_piece",
        filter_type: str = "exact",
        filter_value=None,
        sample_size: Optional[int] = None,
    ):
        """
        Create dataset by filtering the class_values.csv file with flexible criteria.

        Args:
            class_column: Which class column to filter on:
                        - "class_value_upper_work_piece"
                        - "class_value_lower_work_piece"
                        - "class_value_screw_driving"
            filter_type: How to filter:
                        - "exact": Exact match
                        - "contains": Values containing substring
                        - "list": Match any value in provided list
            filter_value: What to filter for:
                        - String for "exact" or "contains"
                        - List of strings for "list"
            sample_size: Optional limit on number of experiments to load
        """
        df = pd.read_csv("data/class_values.csv", index_col=0)

        # Apply filtering based on type
        if filter_value is not None:
            if class_column not in df.columns:
                print(f"Warning: Column '{class_column}' not found in class_values.csv")
                df = df.iloc[0:0]  # Empty dataframe
            else:
                if filter_type == "exact":
                    df = df[df[class_column] == filter_value]
                elif filter_type == "contains":
                    df = df[df[class_column].str.contains(str(filter_value), na=False)]
                elif filter_type == "list":
                    if isinstance(filter_value, list):
                        df = df[df[class_column].isin(filter_value)]
                    else:
                        raise ValueError(
                            "filter_value must be a list when using filter_type='list'"
                        )
                else:
                    raise ValueError(
                        f"Unknown filter_type: {filter_type}. Use 'exact', 'contains', or 'list'"
                    )

        # Sample if requested
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)

        # Create dataset
        ids = df["upper_workpiece_id"].tolist()
        dataset = cls.from_ids(ids)
        dataset.class_values_df = df

        print(
            f"Created dataset with {len(dataset)} experiments from {len(df)} matching records"
        )
        if len(df) > 0:
            print(f"Class distribution: {df[class_column].value_counts().to_dict()}")

        return dataset

    def get_data(self):
        """
        Extract data from all experiments and combine into DataFrame.

        Returns:
            pandas.DataFrame: Each row is an experiment, columns are features
        """
        # Aggregate experiment-level results
        all_data = []
        experiment_ids = []

        for experiment in self.experiments:
            exp_data = experiment.get_data()  # Use new simplified interface
            if exp_data:  # Only include experiments with data
                # Flatten the nested dict into a single row
                flattened = self._flatten_experiment_data(exp_data)
                all_data.append(flattened)
                experiment_ids.append(experiment.upper_workpiece_id)

        if not all_data:
            return pd.DataFrame()  # Empty DataFrame if no data

        return pd.DataFrame(all_data, index=experiment_ids)

    def _flatten_experiment_data(self, exp_data: Dict) -> Dict:
        """
        Flatten experiment data into a single dictionary for DataFrame row.

        Takes nested structure like:
        {
            'injection_upper': {'injection_pressure_target': [...], 'melt_volume': [...]},
            'screw_left': {'torque': [...], 'angle': [...]}
        }

        And flattens to:
        {
            'injection_upper.injection_pressure_target': [...],
            'injection_upper.melt_volume': [...],
            'screw_left.torque': [...],
            'screw_left.angle': [...]
        }
        """
        flattened = {}

        for process_name, process_data in exp_data.items():
            if isinstance(process_data, dict):
                for series_name, series_data in process_data.items():
                    key = f"{process_name}.{series_name}"
                    flattened[key] = series_data
            else:
                # If process_data is not a dict, store it directly
                flattened[process_name] = process_data

        return flattened

    def get_class_labels(self):
        """Return class labels for all experiments in the dataset."""
        labels = []
        for experiment in self.experiments:
            # Try to get class label from injection_upper first
            if hasattr(experiment.injection_upper, "class_value"):
                labels.append(experiment.injection_upper.class_value)
            elif hasattr(experiment.injection_lower, "class_value"):
                labels.append(experiment.injection_lower.class_value)
            elif hasattr(experiment.screw_left, "class_value"):
                labels.append(experiment.screw_left.class_value)
            elif hasattr(experiment.screw_right, "class_value"):
                labels.append(experiment.screw_right.class_value)
            else:
                labels.append(None)
        return labels

    def get_experiment_info(self):
        """Return summary information about the experiments in this dataset."""
        available_processes = {}
        for experiment in self.experiments:
            for process in experiment.get_available_processes():
                available_processes[process] = available_processes.get(process, 0) + 1

        return {
            "total_experiments": len(self.experiments),
            "available_processes": available_processes,
            "class_distribution": self._get_class_distribution(),
        }

    def _get_class_distribution(self):
        """Get distribution of class values in the dataset."""
        if self.class_values_df is None:
            return {}

        # Count experiments by upper workpiece class
        class_col = "class_value_upper_work_piece"
        if class_col in self.class_values_df.columns:
            return self.class_values_df[class_col].value_counts().to_dict()

        return {}

    def __len__(self):
        return len(self.experiments)

    def __repr__(self):
        info = self.get_experiment_info()
        return f"ExperimentDataset(experiments={len(self)}, processes={list(info['available_processes'].keys())})"
