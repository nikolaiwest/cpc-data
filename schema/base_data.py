from abc import ABC


class BaseData(ABC):

    def __init__(self, upper_workpiece_id):
        self.upper_workpiece_id = upper_workpiece_id
