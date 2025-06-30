from ..processes import (
    LowerInjectionMoldingData,
    ScrewDrivingData,
    UpperInjectionMoldingData,
)


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
        self.screw_left = ScrewDrivingData(upper_workpiece_id, position="left")
        self.screw_right = ScrewDrivingData(upper_workpiece_id, position="right")

    def get_data(
        self,
        config_path=None,
        config_dict=None,
        processes="all",
        method="raw",
        **kwargs,
    ):
        """
        Extract data from all or selected processes using config or manual method.

        Args:
            config_path: Path to YAML config file
            config_dict: Config dictionary (alternative to file)
            processes: "all" or list of process names ["injection_upper", "screw_left", ...]
            method: Fallback method if no config provided
            **kwargs: Parameters for fallback method

        Returns:
            Dict with process names as keys and extracted data as values
        """
        # Get selected processes
        selected_processes = self._get_selected_processes(processes)

        results = {}
        for process_name, process_obj in selected_processes.items():
            if process_obj is not None:  # Handle missing data gracefully
                process_data = process_obj.get_data(
                    config_path=config_path,
                    config_dict=config_dict,
                    method=method,
                    **kwargs,
                )
                if process_data is not None:
                    results[process_name] = process_data

        return results

    def _get_selected_processes(self, processes):
        """Get dictionary of selected process objects."""
        all_processes = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        if processes == "all":
            return all_processes
        elif isinstance(processes, list):
            return {
                name: all_processes[name] for name in processes if name in all_processes
            }
        else:
            raise ValueError("processes must be 'all' or list of process names")

    def get_available_processes(self):
        """Return list of processes that have data available."""
        available = []
        processes = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        for name, process in processes.items():
            if hasattr(process, "file_name") and process.file_name is not None:
                available.append(name)

        return available

    def __repr__(self):
        available = self.get_available_processes()
        return f"ExperimentData(upper_workpiece_id={self.upper_workpiece_id}, available={available})"
