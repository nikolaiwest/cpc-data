from abc import abstractmethod
from dataclasses import dataclass

import pandas as pd

from schema.recordings import BaseRecording
from utils import get_injection_molding_serial_data, get_injection_molding_static_data


@dataclass
class InjectionMoldingAttributes:
    """Attribute names for injection molding time series data."""

    time_series: str = "time_series"
    injection_pressure_target: str = "injection_pressure_target"
    injection_pressure_actual: str = "injection_pressure_actual"
    injection_velocity: str = "injection_velocity"
    melt_volume: str = "melt_volume"
    state: str = "state"


class BaseInjectionMoldingCycle(BaseRecording):
    """Abstract base class for injection molding data with shared functionality"""

    def __init__(self, upper_workpiece_id: int) -> None:
        super().__init__(upper_workpiece_id)

        # Populate data attributes using new methods
        self.static_data = self._get_static_data()
        self.serial_data = self._get_serial_data()

    def _get_static_data(self) -> dict | None:
        """Load and return static data for injection molding (from static_data.csv)."""
        csv_path = self._get_static_data_path()
        df_static = pd.read_csv(csv_path, sep=";")

        # Check for the ID in the upper_workpiece_id column (handle both int and string)
        target_id = self.upper_workpiece_id
        matching_rows = df_static[
            (df_static["upper_workpiece_id"] == target_id)
            | (df_static["upper_workpiece_id"] == str(target_id))
        ]

        if matching_rows.empty:
            return None

        # Get the first matching row
        static = matching_rows.iloc[0]

        # Create static data dict
        static_data_cols = {
            "file_name",
            "lower_workpiece_id",
            "class_value",
            "date",
            "time",
            "file_name_h5",
            "upper_workpiece_id",  # Add this to excluded cols
        }

        # Basic static attributes
        result = {
            "file_name": static["file_name"],
            "lower_workpiece_id": static["lower_workpiece_id"],
            "class_value": static["class_value"],
            "date": static["date"],
            "time": static["time"],
            "file_name_h5": static["file_name_h5"],
        }

        # Add all measurements (everything else)
        measurements = {
            col: static[col] for col in static.index if col not in static_data_cols
        }
        result.update(measurements)

        return result

    def get_measurements(self):
        """Return dict of measurement values for this workpiece"""
        if self.static_data is None:
            return {}

        # Filter out the basic static attributes to get just measurements
        basic_attrs = {
            "file_name",
            "lower_workpiece_id",
            "class_value",
            "date",
            "time",
            "file_name_h5",
        }
        return {k: v for k, v in self.static_data.items() if k not in basic_attrs}

    @abstractmethod
    def _get_static_data_path(self):
        """Return path to static data CSV file"""
        pass


class UpperInjectionMoldingData(BaseInjectionMoldingCycle):

    def _get_static_data_path(self):
        return str(get_injection_molding_static_data("upper"))

    def _get_class_name(self):
        return "injection_molding.upper_workpiece"

    def _get_serial_data(self) -> dict | None:
        """Load and return serial data for upper injection molding (from CSV files)."""
        # Need static data first to get file name
        if self.static_data is None:
            return None

        csv_path = str(
            get_injection_molding_serial_data("upper", self.static_data["file_name"])
        )
        df_cycle = pd.read_csv(csv_path, index_col=0)

        # Return raw time series dict
        return {
            InjectionMoldingAttributes.time_series: df_cycle["time"].tolist(),
            InjectionMoldingAttributes.injection_pressure_target: df_cycle[
                InjectionMoldingAttributes.injection_pressure_target
            ].tolist(),
            InjectionMoldingAttributes.injection_pressure_actual: df_cycle[
                InjectionMoldingAttributes.injection_pressure_actual
            ].tolist(),
            InjectionMoldingAttributes.injection_velocity: df_cycle[
                InjectionMoldingAttributes.injection_velocity
            ].tolist(),
            InjectionMoldingAttributes.melt_volume: df_cycle[
                InjectionMoldingAttributes.melt_volume
            ].tolist(),
            InjectionMoldingAttributes.state: df_cycle[
                InjectionMoldingAttributes.state
            ].tolist(),
        }


class LowerInjectionMoldingData(BaseInjectionMoldingCycle):

    def _get_static_data_path(self):
        return str(get_injection_molding_static_data("lower"))

    def _get_class_name(self):
        return "injection_molding.lower_workpiece"

    def _get_serial_data(self) -> dict | None:
        """Load and return serial data for lower injection molding (from TXT files)."""
        # Need static data first to get file name
        if self.static_data is None:
            return None

        txt_path = str(
            get_injection_molding_serial_data("lower", self.static_data["file_name"])
        )

        # Read the file and find the data section
        with open(txt_path, "r") as file:
            lines = file.readlines()

        # Find where data starts (after "-start data-")
        data_start_idx = None
        for i, line in enumerate(lines):
            if "-start data-" in line:
                data_start_idx = i + 1
                break

        if data_start_idx is None:
            raise ValueError(f"Could not find data section in {txt_path}")

        # Parse data lines (semicolon-separated)
        data_lines = lines[data_start_idx:]
        data_rows = []
        for line in data_lines:
            if line.strip():  # Skip empty lines
                values = line.strip().split(";")
                data_rows.append([float(v) for v in values])

        # Convert to DataFrame
        df_cycle = pd.DataFrame(
            data_rows,
            columns=[
                InjectionMoldingAttributes.time_series,
                InjectionMoldingAttributes.injection_pressure_target,
                InjectionMoldingAttributes.injection_pressure_actual,
                InjectionMoldingAttributes.melt_volume,
                InjectionMoldingAttributes.injection_velocity,
            ],
        )

        # Return raw time series dict
        return {
            InjectionMoldingAttributes.time_series: df_cycle[
                InjectionMoldingAttributes.time_series
            ].tolist(),
            InjectionMoldingAttributes.injection_pressure_target: df_cycle[
                InjectionMoldingAttributes.injection_pressure_target
            ].tolist(),
            InjectionMoldingAttributes.injection_pressure_actual: df_cycle[
                InjectionMoldingAttributes.injection_pressure_actual
            ].tolist(),
            InjectionMoldingAttributes.injection_velocity: df_cycle[
                InjectionMoldingAttributes.injection_velocity
            ].tolist(),
            InjectionMoldingAttributes.melt_volume: df_cycle[
                InjectionMoldingAttributes.melt_volume
            ].tolist(),
        }
