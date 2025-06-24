import os
from abc import abstractmethod

import pandas as pd

from .base_data import BaseData


class BaseInjectionMoldingCycle(BaseData):
    """Abstract base class for injection molding data with shared functionality"""

    def __init__(self, upper_workpiece_id):
        super().__init__(upper_workpiece_id)
        if self._load_metadata():
            self._load_cycle_data()
        else:
            self._set_none_attributes()

    def _load_metadata(self):
        """Load metadata from CSV file. Returns True if found, False if not."""
        csv_path = self._get_metadata_path()
        df_meta = pd.read_csv(csv_path, index_col=0, sep=";")

        # Check if ID exists
        if self.upper_workpiece_id not in df_meta.index:
            return False

        # Get row for this workpiece
        meta = df_meta.loc[self.upper_workpiece_id]

        # True metadata attributes
        self.file_name = meta["file_name"]
        self.lower_workpiece_id = meta["lower_workpiece_id"]
        self.class_value = meta["class_value"]
        self.date = meta["date"]
        self.time = meta["time"]
        self.file_name_h5 = meta["file_name_h5"]

        # Store all measurements in dict (everything else)
        metadata_cols = {
            "file_name",
            "lower_workpiece_id",
            "class_value",
            "date",
            "time",
            "file_name_h5",
        }
        self.measurements = {
            col: meta[col] for col in meta.index if col not in metadata_cols
        }
        return True

    def _set_none_attributes(self):
        """Set all attributes to None when no metadata found"""
        # Common metadata attributes
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
    def _get_metadata_path(self):
        """Return path to metadata CSV file"""
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

    def _get_metadata_path(self):
        return "data/injection_molding/upper_workpiece/meta_data.csv"

    def _load_cycle_data(self):
        """Load time series data from CSV file"""
        csv_path = f"data/injection_molding/upper_workpiece/raw_data/{self.file_name}"
        df_cycle = pd.read_csv(csv_path, index_col=0)

        # Set time series attributes
        self.time_series = df_cycle["time"]
        self.injection_pressure = df_cycle["injection_pressure"]
        self.resulting_injection_pressure = df_cycle["resulting_injection_pressure"]
        self.melt_volume = df_cycle["melt_volume"]
        self.injection_velocity = df_cycle["injection_velocity"]
        self.state = df_cycle["state"]

    def _get_cycle_attributes(self):
        return [
            "time_series",
            "injection_pressure",
            "resulting_injection_pressure",
            "melt_volume",
            "injection_velocity",
            "state",
        ]


class LowerInjectionMoldingData(BaseInjectionMoldingCycle):

    def _get_metadata_path(self):
        return "data/injection_molding/lower_workpiece/meta_data.csv"

    def _load_cycle_data(self):
        """Load time series data from TXT file with special format"""
        txt_path = f"data/injection_molding/lower_workpiece/raw_data/{self.file_name}"

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
                "time",
                "injection_pressure_target",
                "injection_pressure_actual",
                "screw_volume",
                "injection_flow",
            ],
        )

        # Set time series attributes (mapping to similar names as upper)
        self.time_series = df_cycle["time"]
        self.injection_pressure = df_cycle["injection_pressure_actual"]
        self.injection_pressure_target = df_cycle["injection_pressure_target"]
        self.melt_volume = df_cycle["screw_volume"]  # Similar concept
        self.injection_velocity = df_cycle["injection_flow"]  # Similar concept

    def _get_cycle_attributes(self):
        return [
            "time_series",
            "injection_pressure",
            "injection_pressure_target",
            "melt_volume",
            "injection_velocity",
        ]
