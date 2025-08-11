import json

import pandas as pd

from schema.experiment.base import BaseData


class ScrewDrivingData(BaseData):
    """
    Represents screw driving data for left or right position.

    Loads metadata from CSV and time series data from JSON files.
    Combines measurements from all steps in the screw run.
    """

    def __init__(self, upper_workpiece_id, position):
        super().__init__(upper_workpiece_id)
        self.position = position  # "left" or "right"

        if self._load_metadata():
            self._load_cycle_data()
        else:
            self._set_none_attributes()

    def _load_metadata(self):
        """Load metadata from screw driving meta_data.csv. Returns True if found, False if not."""
        csv_path = "data/screw_driving/meta_data.csv"
        df_meta = pd.read_csv(csv_path, index_col=0, sep=";")  # run_id is index

        # Filter by upper_workpiece_id first
        workpiece_rows = df_meta[
            df_meta["upper_workpiece_id"] == self.upper_workpiece_id
        ]
        if workpiece_rows.empty:
            return False

        # Then filter by position (workpiece_location)
        position_rows = workpiece_rows[
            workpiece_rows["workpiece_location"] == self.position
        ]
        if position_rows.empty:
            return False

        # Get the single row for this workpiece and position
        meta = position_rows.iloc[0]  # Should be exactly one row

        # Store metadata attributes
        self.file_name = meta["file_name"]
        self.workpiece_id = meta["upper_workpiece_id"]
        self.class_value = meta["class_value"]
        self.date = meta["date"]
        self.time = meta["time"]
        self.workpiece_usage = meta["workpiece_usage"]
        self.workpiece_result = meta["workpiece_result"]
        self.scenario_condition = meta["scenario_condition"]
        self.scenario_exception = meta["scenario_exception"]

        # No additional measurements dict needed for screw data
        self.measurements = {}
        return True

    def _load_cycle_data(self):
        """Load time series data from JSON file, combine all steps, and apply processing"""
        json_path = f"data/screw_driving/raw_data/{self.file_name}"

        with open(json_path, "r") as file:
            json_data = json.load(file)

        # Extract tightening steps
        steps_data = json_data.get("tightening steps", [])

        # Combine measurements from all steps
        raw_time = []
        raw_torque = []
        raw_angle = []
        raw_gradient = []

        for step_data in steps_data:
            graph = step_data.get("graph", {})

            # Extend lists with data from this step
            raw_time.extend(graph.get("time values", []))
            raw_torque.extend(graph.get("torque values", []))
            raw_angle.extend(graph.get("angle values", []))
            raw_gradient.extend(graph.get("gradient values", []))

        # Create raw time series dict
        raw_series = {
            "time": raw_time,
            "torque": raw_torque,
            "angle": raw_angle,
            "gradient": raw_gradient,
            # Add the reduced signals (if they exist in the data)
            "torqueRed": [],  # Would be populated from JSON if available
            "angleRed": [],  # Would be populated from JSON if available
        }

        # Apply processing using BaseData method
        processed_series = self._apply_processing(raw_series)

        # Set time series attributes with processed data
        self.time_series = processed_series["time"]
        self.torque = processed_series["torque"]
        self.angle = processed_series["angle"]
        self.gradient = processed_series["gradient"]
        self.torqueRed = processed_series["torqueRed"]
        self.angleRed = processed_series["angleRed"]

        # Store individual steps for potential detailed analysis
        self.steps_count = len(steps_data)
        self.steps_names = [step.get("name", "") for step in steps_data]

    def _set_none_attributes(self):
        """Set all attributes to None when no metadata found"""
        # Metadata attributes
        self.file_name = None
        self.workpiece_id = None
        self.class_value = None
        self.date = None
        self.workpiece_usage = None
        self.workpiece_result = None
        self.scenario_condition = None
        self.scenario_exception = None
        self.measurements = {}

        # Time series attributes
        self.time_series = None
        self.torque = None
        self.angle = None
        self.gradient = None
        self.torqueRed = None
        self.angleRed = None
        self.steps_count = None
        self.steps_names = None

    def _get_class_name(self):
        """Return class name path for YAML config lookup."""
        return f"screw_driving.{self.position}"

    def _get_time_series_data(self):
        """Return dict of time series data for screw driving."""
        if self.time_series is None:
            return None
        return {
            "time": self.time_series,
            "torque": self.torque,
            "angle": self.angle,
            "gradient": self.gradient,
            "torqueRed": self.torqueRed,
            "angleRed": self.angleRed,
        }

    def get_measurements(self):
        """Return dict of all measurement values for this workpiece"""
        return self.measurements  # Empty for screw data, keeping consistent interface

    def __repr__(self):
        return f"ScrewDrivingData(upper_workpiece_id={self.upper_workpiece_id}, position='{self.position}', steps={self.steps_count})"
