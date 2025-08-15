import json
from abc import abstractmethod
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


@dataclass
class ScrewDrivingCSVColumns:
    """
    Column names for screw driving static data CSV file.

    Provides consistent string constants for accessing CSV columns
    and building return dictionaries from static_data.csv.
    """

    file_name: str = "file_name"
    workpiece_id: str = "upper_workpiece_id"
    class_value: str = "class_value"
    date: str = "date"
    time: str = "time"
    workpiece_usage: str = "workpiece_usage"
    workpiece_result: str = "workpiece_result"
    scenario_condition: str = "scenario_condition"
    scenario_exception: str = "scenario_exception"
    workpiece_location: str = "workpiece_location"


# Alias for cleaner code and reduced verbosity
SDA = ScrewDrivingAttributes
CSV = ScrewDrivingCSVColumns


class ScrewDrivingBase(BaseRecording):
    """
    Base class for screw driving data with shared functionality.

    Handles common operations like static data loading from CSV files
    and JSON parsing. Child classes implement position-specific logic
    for left and right screw driving operations.
    """

    def __init__(self, upper_workpiece_id: int) -> None:
        """
        Initialize screw driving recording with workpiece ID.

        Loads both static measurement data and time series data from files during
        initialization. Static data comes from the shared static_data.csv file,
        while serial data is loaded from position-specific JSON files in the
        serial_data/ directory.

        Args:
            upper_workpiece_id: Unique identifier for the manufacturing experiment

        Attributes:
            static_data: Loaded static measurements (quality codes, process control)
            serial_data: Loaded time series data (torque, angle, gradient over time)

        Note:
            File loading occurs once during initialization. If files are missing
            or corrupted, the corresponding data attributes will be set to None.
        """
        super().__init__(upper_workpiece_id)
        # Populate data attributes by loading from files during initialization
        self.static_data = self._get_static_data()
        self.serial_data = self._get_serial_data()

    @abstractmethod
    def _get_position(self) -> str:
        """
        Return the position identifier for this screw driving recording.

        Each workpiece has two screw positions that are tightened during assembly.
        The position identifier corresponds to the 'workpiece_location' field in
        the static data CSV file and determines which JSON files contain the
        relevant time series data for this recording.

        The position affects the torque-angle characteristics due to physical
        differences in screw accessibility, material stress distribution, and
        assembly tooling constraints between left and right positions.

        Returns:
            str: Position identifier - either "left" or "right"
        """
        pass

    def _get_class_name(self) -> str:
        """
        Return the hierarchical class identifier for configuration lookup.

        This identifier is used to navigate the YAML configuration files
        (processing.yml and extraction.yml) to find the appropriate settings
        for this specific recording type. The path follows the structure:
        process_type.position (e.g., 'screw_driving.left', 'screw_driving.right').

        Returns:
            str: Dot-separated hierarchical path used to locate this recording's
                 settings in YAML configuration files.
        """
        return f"screw_driving.{self._get_position()}"

    def _get_static_data(self) -> dict | None:
        """
        Load and return static data for this screw driving recording.

        Reads static measurement data from the shared static_data.csv file,
        filtering by upper_workpiece_id and workpiece_location (position).
        Static data contains process metadata, quality indicators, and file
        references that remain constant throughout the screw driving cycle.

        The method performs a two-step filtering process:
        1. Filter by upper_workpiece_id to isolate the specific recording
        2. Filter by workpiece_location to get position-specific data

        Returns:
            dict or None: Dictionary containing static measurements including
                file_name, class_value, dates, usage/result codes,
                and scenario conditions. Returns None if no matching
                data is found for this workpiece and position combination.

        Raises:
            FileNotFoundError: If static_data.csv cannot be located
            pandas.errors.ParserError: If CSV file is malformed
        """
        # Load static data from csv as dataframe
        static_data_path = get_screw_driving_static_data()
        df = pd.read_csv(static_data_path, index_col=0, sep=";")

        # Filter by id ("upper_workpiece_id") first
        row = df[df[CSV.workpiece_id] == self.upper_workpiece_id]
        if row.empty:
            return None

        # Filter by position ("workpiece_location") next
        position_rows = row[row[CSV.workpiece_location] == self._get_position()]
        if position_rows.empty:
            return None

        # Get the single row for this workpiece and position
        static_data = position_rows.iloc[0]  # Should be exactly one row

        # Return as dictionary
        return {
            CSV.file_name: static_data[CSV.file_name],
            # Note: different key name for simplicity
            "workpiece_id": static_data[CSV.workpiece_id],
            CSV.class_value: static_data[CSV.class_value],
            CSV.date: static_data[CSV.date],
            CSV.time: static_data[CSV.time],
            CSV.workpiece_usage: static_data[CSV.workpiece_usage],
            CSV.workpiece_result: static_data[CSV.workpiece_result],
            CSV.scenario_condition: static_data[CSV.scenario_condition],
            CSV.scenario_exception: static_data[CSV.scenario_exception],
        }

    def _get_serial_data(self) -> dict | None:
        """
        Load and return time series data for this screw driving recording.

        Reads time series measurements from position-specific JSON files in the
        serial_data/ directory. The filename is obtained from static data and
        contains multi-step tightening sequences with torque, angle, and gradient
        measurements sampled at regular intervals during the screw driving process.

        The method combines data from all tightening steps into unified time series,
        preserving chronological order across the complete assembly sequence.

        Returns:
            dict or None: Dictionary with time series data where keys are
                parameter names (time, torque, angle, gradient, torqueRed,
                angleRed) and values are combined lists of measurements
                ordered chronologically across all tightening steps.
                Returns None if static data is unavailable or JSON file
                cannot be read.
        """
        # Need static data first to get file name
        if self.static_data is None:
            return None

        # Load time series data from JSON file
        serial_data_path = get_screw_driving_serial_data(
            self.static_data[CSV.file_name]
        )

        with open(serial_data_path, "r") as file:
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

        # A screw run consists of up to four screw steps that have to be combined
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


class ScrewDrivingLeft(ScrewDrivingBase):
    """
    Left position screw driving data from JSON files.

    Loads time series data including torque, angle, and gradient measurements
    from JSON files for left-side screw driving operations.
    """

    def _get_position(self) -> str:
        """Return position identifier for left-side screw driving."""
        return "left"


class ScrewDrivingRight(ScrewDrivingBase):
    """
    Right position screw driving data from JSON files.

    Loads time series data including torque, angle, and gradient measurements
    from JSON files for right-side screw driving operations.
    """

    def _get_position(self) -> str:
        """Return position identifier for right-side screw driving."""
        return "right"
