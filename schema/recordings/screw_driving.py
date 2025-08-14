import json
from dataclasses import dataclass

import pandas as pd

from schema.recordings import BaseRecording
from utils import get_screw_driving_serial_data, get_screw_driving_static_data


@dataclass
class ScrewDrivingAttributes:
    """
    Attribute names for screw driving time series data.

    Provides consistent string constants for accessing time series data
    across left and right position screw driving processes.
    """

    time: str = "time"
    torque: str = "torque"
    angle: str = "angle"
    gradient: str = "gradient"
    torque_red: str = "torqueRed"
    angle_red: str = "angleRed"


# Alias for cleaner code and reduced verbosity
SDA = ScrewDrivingAttributes


class ScrewDrivingBase(BaseRecording):
    """
    Base class for screw driving data with shared functionality.

    Handles common operations like static data loading from CSV files
    and JSON parsing. Child classes implement position-specific logic
    for left and right screw driving operations.
    """

    def __init__(self, upper_workpiece_id: int, position: str) -> None:
        self.position = position  # "left" or "right"
        super().__init__(upper_workpiece_id)

        # Populate data attributes using new methods
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
            SDA.time: combined_time,
            SDA.torque: combined_torque,
            SDA.angle: combined_angle,
            SDA.gradient: combined_gradient,
            SDA.torque_red: combined_torque_red,
            SDA.angle_red: combined_angle_red,
        }

    def get_measurements(self):
        """Return dict of measurement values for this workpiece."""
        # No additional measurements for screw driving data
        return {}

    def _get_class_name(self):
        """Return class name path for YAML config lookup."""
        return f"screw_driving.{self.position}"


class ScrewDrivingLeft(ScrewDrivingBase):
    """
    Left position screw driving data from JSON files.

    Loads time series data including torque, angle, and gradient measurements
    from JSON files for left-side screw driving operations.
    """

    def __init__(self, upper_workpiece_id: int) -> None:
        super().__init__(upper_workpiece_id, position="left")


class ScrewDrivingRight(ScrewDrivingBase):
    """
    Right position screw driving data from JSON files.

    Loads time series data including torque, angle, and gradient measurements
    from JSON files for right-side screw driving operations.
    """

    def __init__(self, upper_workpiece_id: int) -> None:
        super().__init__(upper_workpiece_id, position="right")
