from schema.recordings import (
    InjectionMoldingLower,
    InjectionMoldingUpper,
    ScrewDrivingData,
)


class ExperimentData:
    """
    Represents one manufacturing experiment with up to 4 data recordings.
    Individual classes handle missing data by setting attributes to None.
    """

    def __init__(self, upper_workpiece_id):
        self.upper_workpiece_id = upper_workpiece_id

        # Load all 4 data recordings
        self.injection_upper = InjectionMoldingUpper(upper_workpiece_id)
        self.injection_lower = InjectionMoldingLower(upper_workpiece_id)
        self.screw_left = ScrewDrivingData(upper_workpiece_id, position="left")
        self.screw_right = ScrewDrivingData(upper_workpiece_id, position="right")

    def get_data(self, recordings="all"):
        """
        Extract data from all or selected recordings.

        Args:
            recordings: "all" or list of recording names ["injection_upper", "screw_left", ...]

        Returns:
            Dict with recording names as keys and extracted data as values
        """
        # Get selected recordings
        selected_recordings = self._get_selected_recordings(recordings)

        results = {}
        for recording_name, recording_obj in selected_recordings.items():
            if recording_obj is not None:  # Handle missing data gracefully
                recording_data = recording_obj.get_data()
                if recording_data is not None:
                    results[recording_name] = recording_data

        return results

    def _get_selected_recordings(self, recordings):
        """Get dictionary of selected recording objects."""
        available_recordings = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        if recordings == "all":
            return available_recordings
        elif isinstance(recordings, list):
            return {
                name: available_recordings[name]
                for name in recordings
                if name in available_recordings
            }
        else:
            raise ValueError("recordings must be 'all' or a list of recording names")

    def get_available_recordings(self):
        """Return list of recordings that have data available."""
        available = []
        recordings = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        for name, recording_obj in recordings.items():
            if (
                recording_obj is not None
                and recording_obj._get_time_series_data() is not None
            ):
                available.append(name)

        return available

    def plot_data(self, figsize=(15, 10), save_path=None, show_plot=True):
        """
        Create a 2x2 plot showing all time series data from all 4 recordings.

        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save the plot
            show_plot: Whether to display the plot

        Returns:
            matplotlib.figure.Figure: The created figure
        """
        # Import inside method to avoid circular imports
        from .plotting import plot_experiment_data

        return plot_experiment_data(
            self.injection_upper,
            self.injection_lower,
            self.screw_left,
            self.screw_right,
            self.upper_workpiece_id,
            figsize=figsize,
            save_path=save_path,
            show_plot=show_plot,
        )

    def __repr__(self):
        available = self.get_available_recordings()
        return f"ExperimentData(id={self.upper_workpiece_id}, recordings={available})"
