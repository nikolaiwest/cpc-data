from typing import Any, Dict, List, Optional

import pandas as pd

from .data import ExperimentData


class ExperimentDataset:
    """
    Collection of multiple experiments for cross-experiment analysis.
    Enables PCA, correlation analysis, classification etc. across many manufacturing runs.
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
                        - "exact": Exact match (old behavior)
                        - "contains": Values containing substring
                        - "list": Match any value in provided list
            filter_value: What to filter for:
                        - String for "exact" or "contains"
                        - List of strings for "list"
            sample_size: Optional limit on number of experiments to load

        Examples:
            # Get all glass fiber experiments
            dataset = ExperimentDataset.from_class_values(
                class_column="class_value_upper_work_piece",
                filter_type="contains",
                filter_value="glass_fiber_content"
            )

            # Get specific glass fiber percentages
            dataset = ExperimentDataset.from_class_values(
                class_column="class_value_upper_work_piece",
                filter_type="list",
                filter_value=["glass_fiber_content_22", "glass_fiber_content_24", "glass_fiber_content_26"]
            )

            # Get exact control group (old behavior)
            dataset = ExperimentDataset.from_class_values(
                class_column="class_value_upper_work_piece",
                filter_type="exact",
                filter_value="control_group_01"
            )
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

    def get_data(
        self,
        method: str = "raw",
        series_path: str = None,
        config_path: str = None,
        **kwargs,
    ):
        """
        Extract data from specified series across all experiments.

        Args:
            method: Extraction method ("raw", "pca", "correlation", "features_matrix")
            series_path: Path to series like "injection_upper.injection_pressure" (required for raw/pca)
            config_path: Optional config file path
            **kwargs: Method-specific parameters

        Returns:
            Dict or DataFrame with extracted data across experiments
        """
        if method == "raw":
            if not series_path:
                raise ValueError("series_path is required for raw method")
            return self._collect_raw_series(series_path)
        elif method == "pca":
            if not series_path:
                raise ValueError("series_path is required for pca method")
            return self._extract_pca(series_path, **kwargs)
        elif method == "correlation":
            return self._extract_correlation(**kwargs)
        elif method == "features_matrix":
            return self._extract_features_matrix(config_path, **kwargs)
        else:
            raise ValueError(f"Unknown cross-experiment method: {method}")

    def _collect_raw_series(self, series_path: str):
        """Collect raw time series data across all experiments."""
        process_name, series_name = series_path.split(".")

        all_series = []
        experiment_ids = []

        for experiment in self.experiments:
            process_obj = getattr(experiment, process_name, None)
            if process_obj and hasattr(process_obj, series_name):
                series_data = getattr(process_obj, series_name)
                if series_data is not None:
                    all_series.append(series_data)
                    experiment_ids.append(experiment.upper_workpiece_id)

        return {
            "data": all_series,
            "experiment_ids": experiment_ids,
            "series_path": series_path,
        }

    def _extract_pca(self, series_path: str, components: int = 5, **kwargs):
        """Placeholder for PCA across multiple time series."""
        raw_data = self._collect_raw_series(series_path)
        # TODO: Implement PCA feature extraction
        return {
            "method": "pca",
            "components": components,
            "series_path": series_path,
            "n_experiments": len(raw_data["data"]),
            "data": "placeholder_pca_features",
        }

    def _extract_correlation(self, series_pairs: List[List[str]] = None, **kwargs):
        """Placeholder for cross-series correlation analysis."""
        # TODO: Implement correlation analysis between different series
        return {
            "method": "correlation",
            "series_pairs": series_pairs or [],
            "data": "placeholder_correlation_matrix",
        }

    def _extract_features_matrix(self, config_path: str = None, **kwargs):
        """Extract features from all experiments and create feature matrix."""
        feature_matrix = []
        experiment_ids = []

        for experiment in self.experiments:
            # Get features from each experiment using individual methods
            features = experiment.get_data(config_path=config_path, **kwargs)
            if features:
                # Flatten features into single row
                flattened = self._flatten_features(features)
                feature_matrix.append(flattened)
                experiment_ids.append(experiment.upper_workpiece_id)

        return {
            "feature_matrix": feature_matrix,
            "experiment_ids": experiment_ids,
            "method": "features_matrix",
        }

    def _flatten_features(self, features_dict: Dict):
        """Flatten nested feature dictionary into single list."""
        # TODO: Implement proper feature flattening
        # This would concatenate all extracted features into one vector
        return [0.0] * 100  # Placeholder

    def get_class_labels(self, label_column: str = "class_value_upper_work_piece"):
        """Get class labels for all experiments in dataset."""
        if self.class_values_df is None:
            return None

        labels = []
        for experiment in self.experiments:
            row = self.class_values_df[
                self.class_values_df["upper_workpiece_id"]
                == experiment.upper_workpiece_id
            ]
            if not row.empty and label_column in row.columns:
                labels.append(row[label_column].iloc[0])
            else:
                labels.append(None)

        return labels

    def get_experiment_info(self):
        """Get summary information about the dataset."""
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
