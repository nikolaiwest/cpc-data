import json
from dataclasses import dataclass

import pandas as pd

from schema.recordings import BaseRecording
from utils import get_screw_driving_serial_data, get_screw_driving_static_data


@dataclass
class ScrewDrivingAttributes:
    """Attribute names for screw driving time series data."""

    time: str = "time"
    torque: str = "torque"
    angle: str = "angle"
    gradient: str = "gradient"
    torque_red: str = "torqueRed"
    angle_red: str = "angleRed"


class ScrewDrivingData(BaseRecording):
    """
    Represents screw driving data for left or right position.

    Loads static data from CSV and time series data from JSON files.
    Combines measurements from all steps in the screw run.
    """

    def __init__(self, upper_workpiece_id: int, position: str) -> None:
        super().__init__(upper_workpiece_id)
        # TODO: will be handled by separate childen in the future
        self.position = position  # "left" or "right"

        # Populate static and serial data attributes
        # TODO: will (probably) be moved to the base init
        self.static_data = self._get_static_data()
        self.serial_data = self._get_serial_data()

    def _get_static_data(self) -> dict | None:
        """Load and return static data for screw driving (from static_data.csv)."""
        csv_path = str(get_screw_driving_static_data())
        df_static = pd.read_csv(csv_path, index_col=0, sep=";")  # run_id is index

        # Filter by upper_workpiece_id first
        workpiece_rows = df_static[
            df_static["upper_workpiece_id"] == self.upper_workpiece_id
        ]
        if workpiece_rows.empty:
            return None

        # Then filter by position (workpiece_location)
        position_rows = workpiece_rows[
            workpiece_rows["workpiece_location"] == self.position
        ]
        if position_rows.empty:
            return None

        # Get the single row for this workpiece and position
        static = position_rows.iloc[0]  # Should be exactly one row

        # Return as dictionary
        return {
            "file_name": static["file_name"],
            "workpiece_id": static["upper_workpiece_id"],
            "class_value": static["class_value"],
            "date": static["date"],
            "time": static["time"],
            "workpiece_usage": static["workpiece_usage"],
            "workpiece_result": static["workpiece_result"],
            "scenario_condition": static["scenario_condition"],
            "scenario_exception": static["scenario_exception"],
        }

    def _get_serial_data(self) -> dict | None:
        """Load and return serial data for screw driving (from JSON files)."""
        # Need static data first to get file name
        if self.static_data is None:
            return None

        json_path = str(get_screw_driving_serial_data(self.static_data["file_name"]))

        with open(json_path, "r") as file:
            json_data = json.load(file)

        # Get the tightening steps list
        steps_data = json_data.get("tightening steps", [])

        # Combine all steps into single time series
        combined_time = []
        combined_torque = []
        combined_angle = []
        combined_gradient = []
        combined_torque_red = []
        combined_angle_red = []

        for step_data in steps_data:
            graph = step_data.get("graph", {})

            # Extract data from this step's graph
            combined_time.extend(graph.get("time values", []))
            combined_torque.extend(graph.get("torque values", []))
            combined_angle.extend(graph.get("angle values", []))
            combined_gradient.extend(graph.get("gradient values", []))
            combined_torque_red.extend(graph.get("torqueRed values", []))
            combined_angle_red.extend(graph.get("angleRed values", []))

        return {
            ScrewDrivingAttributes.time: combined_time,
            ScrewDrivingAttributes.torque: combined_torque,
            ScrewDrivingAttributes.angle: combined_angle,
            ScrewDrivingAttributes.gradient: combined_gradient,
            ScrewDrivingAttributes.torque_red: combined_torque_red,
            ScrewDrivingAttributes.angle_red: combined_angle_red,
        }

    def _set_none_attributes(self):
        """Set all attributes to None when no static data found"""
        # Static data attributes
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
            ScrewDrivingAttributes.time: self.time_series,
            ScrewDrivingAttributes.torque: self.torque,
            ScrewDrivingAttributes.angle: self.angle,
            ScrewDrivingAttributes.gradient: self.gradient,
            ScrewDrivingAttributes.torque_red: self.torqueRed,
            ScrewDrivingAttributes.angle_red: self.angleRed,
        }

    def get_measurements(self):
        """Return dict of all measurement values for this workpiece"""
        return self.measurements  # Empty for screw data, keeping consistent interface

    def __repr__(self):
        return f"ScrewDrivingData(upper_workpiece_id={self.upper_workpiece_id}, position='{self.position}', steps={self.steps_count})"
