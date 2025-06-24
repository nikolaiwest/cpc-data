import json

import pandas as pd

from .base_data import BaseData


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
        csv_path = "data/tightening_process/meta_data.csv"
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
        self.upper_workpiece_id = meta["upper_workpiece_id"]
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
        """Load time series data from JSON file and combine all steps"""
        json_path = f"data/tightening_process/raw_data/{self.file_name}"

        with open(json_path, "r") as file:
            json_data = json.load(file)

        # Extract tightening steps
        steps_data = json_data.get("tightening steps", [])

        # Combine measurements from all steps
        all_time = []
        all_torque = []
        all_angle = []
        all_gradient = []

        for step_data in steps_data:
            graph = step_data.get("graph", {})

            # Extend lists with data from this step
            all_time.extend(graph.get("time values", []))
            all_torque.extend(graph.get("torque values", []))
            all_angle.extend(graph.get("angle values", []))
            all_gradient.extend(graph.get("gradient values", []))

        # Set time series attributes
        self.time_series = all_time
        self.torque = all_torque
        self.angle = all_angle
        self.gradient = all_gradient

        # Store individual steps for potential detailed analysis
        self.steps_count = len(steps_data)
        self.steps_names = [step.get("name", "") for step in steps_data]

    def _set_none_attributes(self):
        """Set all attributes to None when no metadata found"""
        # Metadata attributes
        self.file_name = None
        self.workpiece_id = None
        self.class_value = None
        self.workpiece_date = None
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
        self.steps_count = None
        self.steps_names = None

    def get_measurements(self):
        """Return dict of all measurement values for this workpiece"""
        return self.measurements  # Empty for screw data, keeping consistent interface

    def __repr__(self):
        return f"ScrewDrivingData(upper_workpiece_id={self.upper_workpiece_id}, position='{self.position}', steps={self.steps_count})"
