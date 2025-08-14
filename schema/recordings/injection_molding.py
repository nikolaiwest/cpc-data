from abc import abstractmethod
from dataclasses import dataclass

import pandas as pd

from schema.recordings import BaseRecording
from utils import get_injection_molding_static_data, get_injection_molding_serial_data


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

    def __init__(self, upper_workpiece_id):
        super().__init__(upper_workpiece_id)
        if self._load_static_data():
            self._load_cycle_data()
        else:
            self._set_none_attributes()

    def _load_static_data(self):
        """Load static data from CSV file. Returns True if found, False if not."""
        csv_path = self._get_static_data_path()
        # No index_col=0, get default numeric index
        df_static = pd.read_csv(csv_path, sep=";")

        # Check for the ID in the upper_workpiece_id column (handle both int and string)
        target_id = self.upper_workpiece_id
        matching_rows = df_static[
            (df_static["upper_workpiece_id"] == target_id)
            | (df_static["upper_workpiece_id"] == str(target_id))
        ]

        if matching_rows.empty:
            return False

        # Get the first matching row
        static = matching_rows.iloc[0]

        # True static attributes
        self.file_name = static["file_name"]
        self.lower_workpiece_id = static["lower_workpiece_id"]
        self.class_value = static["class_value"]
        self.date = static["date"]
        self.time = static["time"]
        self.file_name_h5 = static["file_name_h5"]

        # Store all measurements in dict (everything else)
        static_data_cols = {
            "file_name",
            "lower_workpiece_id",
            "class_value",
            "date",
            "time",
            "file_name_h5",
        }
        self.measurements = {
            col: static[col] for col in static.index if col not in static_data_cols
        }
        return True

    def _set_none_attributes(self):
        """Set all attributes to None when no static data found"""
        # Common static attributes
        self.file_name = None
        self.lower_workpiece_id = None
        self.class_value = None
        self.date = None
        self.time = None
        self.file_name_h5 = None
        self.measurements = {}

        # Set cycle data attributes to None (class-specific)
        for attr in self._get_cycle_attributes():
            setattr(self, attr, None)

    def get_measurements(self):
        """Return dict of all measurement values for this workpiece"""
        return self.measurements

    @abstractmethod
    def _get_static_data_path(self):
        """Return path to static data CSV file"""
        pass

    @abstractmethod
    def _load_cycle_data(self):
        """Load time series data in format-specific way"""
        pass

    @abstractmethod
    def _get_cycle_attributes(self):
        """Return list of cycle data attribute names"""
        pass


class UpperInjectionMoldingData(BaseInjectionMoldingCycle):

    def _get_static_data_path(self):
        return str(get_injection_molding_static_data("upper"))

    def _get_class_name(self):
        return "injection_molding.upper_workpiece"

    def _get_time_series_data(self):
        """Return dict of time series data for upper injection molding."""
        if self.time_series is None:
            return None
        return {
            InjectionMoldingAttributes.time_series: self.time_series,
            InjectionMoldingAttributes.injection_pressure_target: self.injection_pressure_target,
            InjectionMoldingAttributes.injection_pressure_actual: self.injection_pressure_actual,
            InjectionMoldingAttributes.injection_velocity: self.injection_velocity,
            InjectionMoldingAttributes.melt_volume: self.melt_volume,
            InjectionMoldingAttributes.state: self.state,
        }

    def _load_cycle_data(self):
        """Load time series data from CSV file and apply processing"""
        csv_path = str(get_injection_molding_serial_data("upper", self.file_name))
        df_cycle = pd.read_csv(csv_path, index_col=0)

        # Create raw time series dict
        raw_series = {
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

        # Apply processing using BaseData method
        processed_series = self._apply_processing(raw_series)

        # Set time series attributes with processed data
        self.time_series = processed_series[InjectionMoldingAttributes.time_series]
        self.injection_pressure_target = processed_series[
            InjectionMoldingAttributes.injection_pressure_target
        ]
        self.injection_pressure_actual = processed_series[
            InjectionMoldingAttributes.injection_pressure_actual
        ]
        self.melt_volume = processed_series[InjectionMoldingAttributes.melt_volume]
        self.injection_velocity = processed_series[
            InjectionMoldingAttributes.injection_velocity
        ]
        self.state = processed_series[InjectionMoldingAttributes.state]

    def _get_cycle_attributes(self):
        return [
            InjectionMoldingAttributes.time_series,
            InjectionMoldingAttributes.injection_pressure_target,
            InjectionMoldingAttributes.injection_pressure_actual,
            InjectionMoldingAttributes.injection_velocity,
            InjectionMoldingAttributes.melt_volume,
            InjectionMoldingAttributes.state,
        ]


class LowerInjectionMoldingData(BaseInjectionMoldingCycle):

    def _get_static_data_path(self):
        return str(get_injection_molding_static_data("lower"))

    def _get_class_name(self):
        return "injection_molding.lower_workpiece"

    def _get_time_series_data(self):
        """Return dict of time series data for lower injection molding."""
        if self.time_series is None:
            return None
        return {
            InjectionMoldingAttributes.time_series: self.time_series,
            InjectionMoldingAttributes.injection_pressure_target: self.injection_pressure_target,
            InjectionMoldingAttributes.injection_pressure_actual: self.injection_pressure_actual,
            InjectionMoldingAttributes.melt_volume: self.melt_volume,
            InjectionMoldingAttributes.injection_velocity: self.injection_velocity,
        }

    def _load_cycle_data(self):
        """Load time series data from TXT file, apply processing"""
        txt_path = str(get_injection_molding_serial_data("lower", self.file_name))

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

        # Create raw time series dict
        raw_series = {
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

        # Apply processing using BaseData method
        processed_series = self._apply_processing(raw_series)

        # Set time series attributes with processed data (mapping to similar names as upper)
        self.time_series = processed_series[InjectionMoldingAttributes.time_series]
        self.injection_pressure_target = processed_series[
            InjectionMoldingAttributes.injection_pressure_target
        ]
        self.injection_pressure_actual = processed_series[
            InjectionMoldingAttributes.injection_pressure_actual
        ]
        self.injection_velocity = processed_series[
            InjectionMoldingAttributes.injection_velocity
        ]
        self.melt_volume = processed_series[InjectionMoldingAttributes.melt_volume]

    def _get_cycle_attributes(self):
        return [
            InjectionMoldingAttributes.time_series,
            InjectionMoldingAttributes.injection_pressure_target,
            InjectionMoldingAttributes.injection_pressure_actual,
            InjectionMoldingAttributes.injection_velocity,
            InjectionMoldingAttributes.melt_volume,
        ]
