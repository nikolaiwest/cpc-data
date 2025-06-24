import os

import pandas as pd

from .base_data import BaseData


class BaseInjectionMoldingCycle(BaseData):

    def __init__(self, position, kwargs):
        super().__init__(kwargs)
        self.position = position  # either "upper" or "lower"

        self.get_meta_data()

    def get_meta_data(self):
        # Open the csv file from path
        csv_path = f"data/injection_molding/{self.position}_workpiece/meta_data.csv"
        df_meta_data = pd.read(csv_path, index_col=0)

        # Get the matching row via upper workpiece id
        meta_data = df_meta_data.loc[self.upper_workpiece_id]

        # Create attributes from df
        self.file_name = meta_data["file_name"]

        # Optional attributes:
        self.lower_workpiece_id = meta_data["lower_workpiece_id"]
        self.date = meta_data["date"]
        self.time = meta_data["time"]

    def get_cycle_data(self):

        if self.position == "upper":
            self.get_cycle_data_from_csv()
        elif self.position == "lower":
            self.get_cycle_data_from_txt()
        else:
            raise ValueError(f"Unknown position {self.position}")

    def get_cycle_data_from_csv(self):
        # Load file from path
        csv_path = f"{os.getcwd()}/data/injection_molding/upper_workpiece/raw_data/upper_workpiece_{self.upper_workpiece_id:05d}.csv"
        csv_file = pd.read_csv(csv_path)

        # Set time series data as attributes
        self.process_time = csv_file["time"]
        self.injection_pressure = csv_file["injection_pressure"]
        self.resulting_injection_pressure = csv_file["resulting_injection_pressure"]
        self.melt_volume = csv_file["melt_volume"]
        self.injection_velocity = csv_file["injection_velocity"]
        # Optional:
        self.process_state = csv_file["state"]

    def get_cycle_data_from_txt(self):
        return 0
