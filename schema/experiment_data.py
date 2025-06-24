from .injection_molding import UpperInjectionMoldingData, LowerInjectionMoldingData
from .screw_tightening import ScrewDrivingData


class ExperimentData:
    """
    Represents one manufacturing experiment with up to 4 process data streams.
    Individual classes handle missing data by setting attributes to None.
    """

    def __init__(self, upper_workpiece_id):
        self.upper_workpiece_id = upper_workpiece_id

        # Load all 4 process data streams
        self.injection_upper = UpperInjectionMoldingData(upper_workpiece_id)
        self.injection_lower = LowerInjectionMoldingData(upper_workpiece_id)
        self.screw_left = ScrewDrivingData(upper_workpiece_id)  # , position="left")
        self.screw_right = ScrewDrivingData(upper_workpiece_id)  # , position="right")

    def __repr__(self):
        return f"ExperimentData(upper_workpiece_id={self.upper_workpiece_id})"
