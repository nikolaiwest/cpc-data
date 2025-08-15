from abc import abstractmethod
from dataclasses import dataclass

import pandas as pd

from schema.recordings import BaseRecording
from utils import get_injection_molding_serial_data, get_injection_molding_static_data


@dataclass
class InjectionMoldingAttributes:
    """
    Attribute names for injection molding time series data.

    Provides consistent string constants for accessing time series data
    across upper and lower workpiece injection molding processes.
    """

    time: str = "time"
    pressure_target: str = "injection_pressure_target"
    pressure_actual: str = "injection_pressure_actual"
    velocity: str = "injection_velocity"
    volume: str = "melt_volume"
    state: str = "state"


@dataclass
class InjectionMoldingCSVColumns:
    """
    Column names for injection molding static data CSV files.

    Provides consistent string constants for accessing CSV columns
    and building return dictionaries from static_data.csv files.
    """

    file_name: str = "file_name"
    lower_workpiece_id: str = "lower_workpiece_id"
    class_value: str = "class_value"
    date: str = "date"
    time: str = "time"
    file_name_h5: str = "file_name_h5"
    upper_workpiece_id: str = "upper_workpiece_id"


# Aliases for cleaner code and reduced verbosity
IMA = InjectionMoldingAttributes
CSV = InjectionMoldingCSVColumns


class InjectionMoldingBase(BaseRecording):
    """
    Base class for injection molding data with shared functionality.

    Handles common operations like static data loading from CSV files
    and measurement extraction. Child classes implement workpiece-specific
    serial data loading for upper and lower workpieces with different
    file formats (CSV vs TXT) and parsing requirements.
    """

    def __init__(self, upper_workpiece_id: int) -> None:
        """
        Initialize injection molding recording with workpiece ID.

        Loads both static measurement data and time series data from files during
        initialization. Static data comes from workpiece-specific static_data.csv files,
        while serial data is loaded from either CSV files (upper) or custom TXT files
        (lower) in the corresponding serial_data/ directories.

        Args:
            upper_workpiece_id: Unique identifier for the manufacturing experiment

        Attributes:
            static_data: Loaded static measurements (process parameters, quality data)
            serial_data: Loaded time series data (pressure, velocity, volume over time)

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
        Return the position identifier for this injection molding recording.

        Each manufacturing experiment produces two workpieces - upper and lower -
        that are injection molded separately. The position identifier determines
        which workpiece's data files are accessed and corresponds to the directory
        structure in the data filesystem.

        The position affects the data format and available measurements due to
        different molding processes and tooling configurations between upper
        and lower workpiece production.

        Returns:
            str: Position identifier - either "upper" or "lower"
        """
        pass

    def _get_class_name(self) -> str:
        """
        Return the hierarchical class identifier for configuration lookup.

        This identifier is used to navigate the YAML configuration files
        (processing.yml and extraction.yml) to find the appropriate settings
        for this specific recording type. The path follows the structure:
        process_type.position (e.g., 'injection_molding.upper_workpiece',
        'injection_molding.lower_workpiece').

        Returns:
            str: Dot-separated hierarchical path used to locate this recording's
                 settings in YAML configuration files.
        """
        return f"injection_molding.{self._get_position()}_workpiece"

    def _get_static_data(self) -> dict | None:
        """
        Load and return static data for this injection molding recording.

        Reads static measurement data from workpiece-specific static_data.csv files,
        filtering by upper_workpiece_id. Static data contains process parameters,
        quality measurements, and file references that remain constant throughout
        the injection molding cycle.

        The method handles both integer and string ID matching to ensure
        robust data retrieval across different CSV formatting approaches.

        Returns:
            dict or None: Dictionary containing static measurements including
                         file_name, class_value, dates, and all process parameters.
                         Returns None if no matching data is found for this workpiece.

        Raises:
            FileNotFoundError: If static_data.csv cannot be located
            pandas.errors.ParserError: If CSV file is malformed
        """
        # Load static data from workpiece-specific CSV file
        static_data_path = get_injection_molding_static_data(self._get_position())
        df = pd.read_csv(static_data_path, sep=";")

        # Filter by upper_workpiece_id (handle both int and string types)
        target_id = self.upper_workpiece_id
        matching_rows = df[
            (df[CSV.upper_workpiece_id] == target_id)
            | (df[CSV.upper_workpiece_id] == str(target_id))
        ]

        if matching_rows.empty:
            return None

        # Get the first matching row
        static_data = matching_rows.iloc[0]

        # Define basic static attributes to exclude from measurements
        basic_static_cols = {
            CSV.file_name,
            CSV.lower_workpiece_id,
            CSV.class_value,
            CSV.date,
            CSV.time,
            CSV.file_name_h5,
            CSV.upper_workpiece_id,
        }

        # Build result dictionary with basic static attributes
        result = {
            CSV.file_name: static_data[CSV.file_name],
            CSV.lower_workpiece_id: static_data[CSV.lower_workpiece_id],
            CSV.class_value: static_data[CSV.class_value],
            CSV.date: static_data[CSV.date],
            CSV.time: static_data[CSV.time],
            CSV.file_name_h5: static_data[CSV.file_name_h5],
        }

        # Add all measurement columns (everything not in basic static attributes)
        measurements = {
            col: static_data[col]
            for col in static_data.index
            if col not in basic_static_cols
        }
        result.update(measurements)

        return result


class InjectionMoldingUpper(InjectionMoldingBase):
    """
    Upper workpiece injection molding data from CSV files.

    Loads time series data including pressure, velocity, volume, and state
    measurements from CSV files in the upper_workpiece serial_data directory.

    Note: Upper workpiece data may include state information that is not
    available in the lower workpiece data. Hence, it is not loaded by default
    to maintain consistency with the lower recording data.
    """

    def _get_position(self) -> str:
        """Return position identifier for upper workpiece injection molding."""
        return "upper"

    def _get_serial_data(self) -> dict | None:
        """
        Load and return time series data for upper workpiece injection molding.

        Reads time series measurements from CSV files in the upper_workpiece
        serial_data/ directory. The filename is obtained from static data and
        contains pressure, velocity, volume, and state measurements sampled
        at regular intervals during the injection molding cycle.

        Upper workpiece data includes state information that tracks the
        injection molding machine's operational mode throughout the cycle.

        Returns:
            dict or None: Dictionary with time series data where keys are parameter
                         names (time, injection_pressure_target, injection_pressure_actual,
                         injection_velocity, melt_volume, state) and values are lists
                         of measurements ordered chronologically. Returns None if static
                         data is unavailable or CSV file cannot be read.

        Raises:
            FileNotFoundError: If the CSV file specified in static data is missing
            pandas.errors.ParserError: If CSV file is malformed
        """
        # Need static data first to get file name
        if self.static_data is None:
            return None

        # Load time series data from CSV file
        serial_data_path = get_injection_molding_serial_data(
            self._get_position(), self.static_data[CSV.file_name]
        )
        df = pd.read_csv(serial_data_path, index_col=0)

        # Return time series data using consistent attribute names
        return {
            IMA.time: df[IMA.time].tolist(),
            IMA.pressure_target: df[IMA.pressure_target].tolist(),
            IMA.pressure_actual: df[IMA.pressure_actual].tolist(),
            IMA.velocity: df[IMA.velocity].tolist(),
            IMA.volume: df[IMA.volume].tolist(),
            IMA.state: df[IMA.state].tolist(),
        }


class InjectionMoldingLower(InjectionMoldingBase):
    """
    Lower workpiece injection molding data from TXT files.

    Loads time series data from semicolon-delimited TXT files with custom
    parsing logic. Contains similar measurements to upper workpiece but
    excludes state information and uses different file format.
    """

    def _get_position(self) -> str:
        """Return position identifier for lower workpiece injection molding."""
        return "lower"

    def _get_serial_data(self) -> dict | None:
        """
        Load and return time series data for lower workpiece injection molding.

        Reads time series measurements from custom TXT files in the lower_workpiece
        serial_data/ directory. The filename is obtained from static data and
        contains semicolon-delimited data with a special "-start data-" marker
        indicating where the actual measurement data begins.

        Lower workpiece data excludes state information but includes the same
        pressure, velocity, and volume measurements as upper workpiece data.

        Returns:
            dict or None: Dictionary with time series data where keys are parameter
                         names (time, injection_pressure_target, injection_pressure_actual,
                         injection_velocity, melt_volume) and values are lists of
                         measurements ordered chronologically. Returns None if static
                         data is unavailable or TXT file cannot be read.

        Raises:
            FileNotFoundError: If the TXT file specified in static data is missing
            ValueError: If "-start data-" marker is not found in the file
        """
        # Need static data first to get file name
        if self.static_data is None:
            return None

        # Load time series data from custom TXT file
        serial_data_path = get_injection_molding_serial_data(
            self._get_position(), self.static_data[CSV.file_name]
        )

        # Read file and locate data section
        with open(serial_data_path, "r") as file:
            lines = file.readlines()

        # Find where actual data starts (after "-start data-" marker)
        data_start_idx = None
        for i, line in enumerate(lines):
            if "-start data-" in line:
                data_start_idx = i + 1
                break

        if data_start_idx is None:
            raise ValueError(f"Could not find data section in {serial_data_path}")

        # Parse semicolon-separated data lines
        data_lines = lines[data_start_idx:]
        data_rows = []
        for line in data_lines:
            if line.strip():  # Skip empty lines
                values = line.strip().split(";")
                data_rows.append([float(v) for v in values])

        # Convert to DataFrame with proper column names
        df = pd.DataFrame(
            data_rows,
            columns=[
                IMA.time,
                IMA.pressure_target,
                IMA.pressure_actual,
                IMA.volume,
                IMA.velocity,
            ],
        )

        # Return time series data (note: no state data for lower workpiece)
        return {
            IMA.time: df[IMA.time].tolist(),
            IMA.pressure_target: df[IMA.pressure_target].tolist(),
            IMA.pressure_actual: df[IMA.pressure_actual].tolist(),
            IMA.velocity: df[IMA.velocity].tolist(),
            IMA.volume: df[IMA.volume].tolist(),
        }
