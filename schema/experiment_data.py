from .screw_tightening import BaseScrewTighteningRun
from .injection_molding import BaseInjectionMoldingCycle


class ExperimentData:

    def __init__(self, upper_workpiece_id):

        self.injection_mold_upper = upper_workpiece_id

        self.screw_run_left: BaseScrewTighteningRun = None
        self.screw_run_right: BaseScrewTighteningRun = None

        self.get_injection_mold_upper()

        self.injection_mold_lower: BaseInjectionMoldingCycle = None

    def get_injection_mold_upper(self):
        self.injection_mold_upper = BaseInjectionMoldingCycle(
            self.injection_mold_upper, "upper"
        )
