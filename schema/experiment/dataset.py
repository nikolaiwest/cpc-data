"""
ExperimentDataset class for cross-experiment analysis.

This module provides the ExperimentDataset class which handles collections
of manufacturing experiments for comparative analysis across different
material conditions, process parameters, and quality outcomes.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from utils import get_class_values

from .data import ExperimentData


class ExperimentDataset:
    """
    Collection of multiple experiments for cross-experiment analysis.

    This class enables researchers to:
    - Load groups of experiments based on material conditions
    - Compare different recyclate contents, glass fiber percentages, etc.
    - Extract and analyze data across multiple manufacturing runs
    - Generate training/test datasets for machine learning

    Example:
        # Create dataset for recyclate content studies
        recyclate_dataset = ExperimentDataset.from_class_values(
            class_column="class_value_upper_work_piece",
            filter_type="contains",
            filter_value="recyclate_content",
            sample_size=50
        )

        # Extract features for analysis
        features_df = recyclate_dataset.get_data()
    """

    def __init__(self, experiments: Optional[List[ExperimentData]] = None):
        """
        Initialize ExperimentDataset.

        Args:
            experiments: List of ExperimentData objects. If None, starts empty.
        """
        self.experiments = experiments or []
        self.class_values_df = None

    @classmethod
    def from_ids(cls, upper_workpiece_ids: List[int]) -> "ExperimentDataset":
        """
        Create dataset from a list of upper workpiece IDs.

        This is useful when you have specific experiment IDs you want to analyze,
        rather than filtering by material conditions.

        Args:
            upper_workpiece_ids: List of integer IDs for experiments to load

        Returns:
            ExperimentDataset: Dataset containing the requested experiments

        Example:
            >>> dataset = ExperimentDataset.from_ids([17401, 17402, 17403])
            >>> print(f"Loaded {len(dataset)} experiments")
        """
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
        filter_value: Optional[Any] = None,
        sample_size: Optional[int] = None,
    ) -> "ExperimentDataset":
        """
        Create dataset by filtering the class_values.csv file with flexible criteria.

        This is the main way to create datasets for research. You can filter
        experiments by material conditions, process parameters, or any other
        classification criteria stored in the class values file.

        Args:
            class_column: Which class column to filter on. Options:
                        - "class_value_upper_work_piece" (material conditions)
                        - "class_value_lower_work_piece" (material conditions)
                        - "class_value_screw_driving" (assembly conditions)
            filter_type: How to apply the filter:
                        - "exact": Exact string match
                        - "contains": Values containing the substring
                        - "list": Match any value in the provided list
            filter_value: What to filter for:
                        - String for "exact" or "contains" filters
                        - List of strings for "list" filter
                        - None to include all experiments
            sample_size: Optional limit on number of experiments to load.
                        Useful for development/testing with large datasets.

        Returns:
            ExperimentDataset: Filtered dataset ready for analysis

        Raises:
            ValueError: If filter_type is invalid or filter_value doesn't match filter_type

        Examples:
            >>> # Control group experiments
            >>> control = ExperimentDataset.from_class_values(
            ...     filter_type="exact",
            ...     filter_value="control_group_01"
            ... )

            >>> # All recyclate content variations
            >>> recyclate = ExperimentDataset.from_class_values(
            ...     filter_type="contains",
            ...     filter_value="recyclate_content"
            ... )

            >>> # Specific glass fiber percentages
            >>> glass_fiber = ExperimentDataset.from_class_values(
            ...     filter_type="list",
            ...     filter_value=["glass_fiber_content_22", "glass_fiber_content_24"]
            ... )
        """
        # Load class values from csv file
        df = pd.read_csv(get_class_values(), index_col=0)

        # Apply filtering based on type
        if filter_value is not None:
            # Validate filter_type and filter_value compatibility
            if isinstance(filter_value, list) and filter_type != "list":
                raise ValueError(
                    f"filter_value is a list but filter_type='{filter_type}'. "
                    f"Use filter_type='list' when passing a list of values. "
                    f"Got: {filter_value}"
                )

            if class_column not in df.columns:
                print(f"Warning: Column '{class_column}' not found in class_values.csv")
                available_cols = list(df.columns)
                print(f"Available columns: {available_cols}")
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
                        f"Unknown filter_type: {filter_type}. "
                        "Use 'exact', 'contains', or 'list'"
                    )

        # Sample if requested (useful for development with large datasets)
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)

        # Filter out unused workpiece IDs
        used_df = df[df["upper_workpiece_id"] != "workpiece_not_used"]
        ids = used_df["upper_workpiece_id"].tolist()

        unused_count = len(df["upper_workpiece_id"].tolist()) - len(ids)
        if unused_count > 0:
            print(
                f"Excluded {unused_count} unused workpiece entries ('workpiece_not_used')"
            )

        dataset = cls.from_ids(ids)
        dataset.class_values_df = used_df

        # Provide feedback about what was created
        print(
            f"Created dataset with {len(dataset)} experiments from {len(df)} matching records"
        )
        if len(df) > 0:
            class_distribution = df[class_column].value_counts().to_dict()
            print(f"Class distribution: {class_distribution}")

        return dataset

    def get_data(self) -> pd.DataFrame:
        """
        Extract data from complete experiments into a DataFrame.

        Combines class values and flattened time series features, automatically
        excluding experiments with missing serial data. Generates data quality
        report accessible via self.data_quality_report.

        Returns:
            pandas.DataFrame: Each row is a complete experiment with:
                            - First 5 columns: Class values (upper_workpiece_id,
                            lower_workpiece_id, class_value_upper_work_piece,
                            class_value_lower_work_piece, class_value_screw_driving)
                            - Remaining columns: Flattened features from time series data
                            - Default integer index (0, 1, 2, ...)
                            - Empty DataFrame if no complete experiments found

        Example:
            >>> dataset = ExperimentDataset.from_class_values(
            ...     filter_type="contains", filter_value="control"
            ... )
            >>> features_df = dataset.get_data()
            >>> print(f"Complete experiments: {len(features_df)}")
            >>> print(f"Data quality: {dataset.data_quality_report}")
        """
        # Initialize data quality tracking
        self.data_quality_report = self._init_data_quality_report()

        # Aggregate experiment-level results
        all_data = []

        for experiment in self.experiments:
            # Evaluate data quality for this experiment
            missing_processes = self._evaluate_experiment_data_quality(experiment)

            # Only include experiments with complete data (all 4 processes)
            if len(missing_processes) == 0:
                self.data_quality_report["complete_experiments"] += 1

                exp_data = experiment.get_data()
                if exp_data:  # Additional check for successful data extraction
                    # Start with class values for this experiment
                    row_data = {}

                    # Add class values as first columns if available
                    if self.class_values_df is not None:
                        try:
                            class_row = self.class_values_df.loc[
                                int(experiment.upper_workpiece_id)
                            ]
                            row_data.update(class_row.to_dict())
                        except KeyError:
                            print(
                                f"Warning: No class values found for experiment {experiment.upper_workpiece_id}"
                            )

                    # Flatten and add the experiment feature data
                    flattened = self._flatten_experiment_data(exp_data)
                    row_data.update(flattened)

                    all_data.append(row_data)

        # Calculate percentages and print summary
        self._finalize_data_quality_report()

        if not all_data:
            return pd.DataFrame()

        return pd.DataFrame(all_data)

    def _finalize_data_quality_report(self):
        """Calculate percentages and print data quality summary."""
        total_experiments = self.data_quality_report["total_experiments"]

        # Calculate percentages
        if total_experiments > 0:
            for process in self.data_quality_report["missing_data_counts"]:
                missing_count = self.data_quality_report["missing_data_counts"][process]
                percentage = (missing_count / total_experiments) * 100
                self.data_quality_report["missing_data_percentages"][process] = round(
                    percentage, 1
                )

        # Print summary
        excluded = total_experiments - self.data_quality_report["complete_experiments"]
        if excluded > 0:
            print(f"Excluded {excluded} experiments due to missing serial data")
            print(
                f"Using {self.data_quality_report['complete_experiments']} complete experiments"
            )

    def _init_data_quality_report(self) -> dict:
        """Initialize empty data quality report structure."""
        return {
            "total_experiments": len(self.experiments),
            "missing_data_counts": {
                "injection_upper": 0,
                "injection_lower": 0,
                "screw_left": 0,
                "screw_right": 0,
            },
            "missing_data_percentages": {},
            "missing_experiment_ids": {
                "injection_upper": [],
                "injection_lower": [],
                "screw_left": [],
                "screw_right": [],
            },
            "complete_experiments": 0,
        }

    def _evaluate_experiment_data_quality(self, experiment) -> list:
        """
        Evaluate data quality for a single experiment and update report.

        Args:
            experiment: ExperimentData instance to evaluate

        Returns:
            list: Names of processes with missing data (empty if complete)
        """
        missing_processes = []

        # Check each process and update report if missing
        processes_to_check = [
            ("injection_upper", experiment.injection_upper),
            ("injection_lower", experiment.injection_lower),
            ("screw_left", experiment.screw_left),
            ("screw_right", experiment.screw_right),
        ]

        for process_name, process_obj in processes_to_check:
            if process_obj.serial_data is None:
                self.data_quality_report["missing_data_counts"][process_name] += 1
                self.data_quality_report["missing_experiment_ids"][process_name].append(
                    experiment.upper_workpiece_id
                )
                missing_processes.append(process_name)

        return missing_processes

    def _flatten_experiment_data(self, exp_data: Dict) -> Dict:
        """
        Flatten experiment data into a single dictionary for DataFrame row.

        This converts the nested structure from individual experiments into
        a flat structure suitable for machine learning and statistical analysis.

        Takes nested structure like:
        {
            'injection_upper': {
                'injection_pressure_target': [series_data],
                'melt_volume': [series_data]
            },
            'screw_left': {
                'torque': [series_data],
                'angle': [series_data]
            }
        }

        And flattens to:
        {
            'injection_upper.injection_pressure_target': [series_data],
            'injection_upper.melt_volume': [series_data],
            'screw_left.torque': [series_data],
            'screw_left.angle': [series_data]
        }

        Args:
            exp_data: Nested dictionary from ExperimentData.get_data()

        Returns:
            Dict: Flattened dictionary with dot-notation keys
        """
        flattened = {}

        for process_name, process_data in exp_data.items():
            if isinstance(process_data, dict):
                # Flatten nested process data
                for series_name, series_data in process_data.items():
                    key = f"{process_name}.{series_name}"
                    flattened[key] = series_data
            else:
                # If process_data is not nested, store it directly
                flattened[process_name] = process_data

        return flattened

    def get_class_labels(self) -> List[Optional[str]]:
        """
        Return class labels for all experiments in the dataset.

        This extracts the class/condition labels for each experiment,
        which is useful for supervised learning and analysis.

        Returns:
            List[Optional[str]]: List of class labels, one per experiment.
                               None for experiments without class information.

        Example:
            >>> dataset = ExperimentDataset.from_class_values(
            ...     filter_type="contains", filter_value="recyclate"
            ... )
            >>> labels = dataset.get_class_labels()
            >>> print(f"Unique conditions: {set(labels)}")
        """
        labels = []

        for experiment in self.experiments:
            # Try to get class label from different recording sources
            # Priority: injection_upper -> injection_lower -> screw_left -> screw_right
            label = None

            if (
                hasattr(experiment.injection_upper, "class_value")
                and experiment.injection_upper.class_value
            ):
                label = experiment.injection_upper.class_value
            elif (
                hasattr(experiment.injection_lower, "class_value")
                and experiment.injection_lower.class_value
            ):
                label = experiment.injection_lower.class_value
            elif (
                hasattr(experiment.screw_left, "class_value")
                and experiment.screw_left.class_value
            ):
                label = experiment.screw_left.class_value
            elif (
                hasattr(experiment.screw_right, "class_value")
                and experiment.screw_right.class_value
            ):
                label = experiment.screw_right.class_value

            labels.append(label)

        return labels

    def get_experiment_info(self) -> Dict[str, Any]:
        """
        Return summary information about the experiments in this dataset.

        This provides an overview of what data is available in the dataset,
        which processes have data, and the distribution of conditions.

        Returns:
            Dict[str, Any]: Summary information including:
                - total_experiments: Number of experiments in dataset
                - available_processes: Count of experiments with each process type
                - class_distribution: Distribution of class values

        Example:
            >>> dataset = ExperimentDataset.from_class_values(
            ...     filter_type="contains", filter_value="glass_fiber"
            ... )
            >>> info = dataset.get_experiment_info()
            >>> print(f"Total experiments: {info['total_experiments']}")
            >>> print(f"Processes available: {info['available_processes']}")
        """
        available_processes = {}

        # Count how many experiments have each process type
        for experiment in self.experiments:
            for process in experiment.get_available_recordings():
                available_processes[process] = available_processes.get(process, 0) + 1

        return {
            "total_experiments": len(self.experiments),
            "available_processes": available_processes,
            "class_distribution": self._get_class_distribution(),
        }

    def _get_class_distribution(self) -> Dict[str, int]:
        """
        Get distribution of class values in the dataset.

        Returns:
            Dict[str, int]: Mapping of class values to their counts
        """
        if self.class_values_df is None:
            return {}

        # Count experiments by upper workpiece class (most common use case)
        class_col = "class_value_upper_work_piece"
        if class_col in self.class_values_df.columns:
            return self.class_values_df[class_col].value_counts().to_dict()

        return {}

    def __len__(self) -> int:
        """Return number of experiments in the dataset."""
        return len(self.experiments)

    def __repr__(self) -> str:
        """Return human-readable representation of the dataset."""
        info = self.get_experiment_info()
        processes = list(info["available_processes"].keys())
        return f"ExperimentDataset(experiments={len(self)}, processes={processes})"
