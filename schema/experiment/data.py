import matplotlib.pyplot as plt
import numpy as np

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

    def get_data(self, processes="all"):
        """
        Extract data from all or selected processes.

        Args:
            processes: "all" or list of process names ["injection_upper", "screw_left", ...]

        Returns:
            Dict with process names as keys and extracted data as values
        """
        # Get selected processes
        selected_processes = self._get_selected_processes(processes)

        results = {}
        for process_name, process_obj in selected_processes.items():
            if process_obj is not None:  # Handle missing data gracefully
                process_data = process_obj.get_data()  # Use new simplified interface
                if process_data is not None:
                    results[process_name] = process_data

        return results

    def _get_selected_processes(self, processes):
        """Get dictionary of selected process objects."""
        available_processes = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        if processes == "all":
            return available_processes
        elif isinstance(processes, list):
            return {
                name: available_processes[name]
                for name in processes
                if name in available_processes
            }
        else:
            raise ValueError("processes must be 'all' or a list of process names")

    def get_available_processes(self):
        """Return list of processes that have data available."""
        available = []
        processes = {
            "injection_upper": self.injection_upper,
            "injection_lower": self.injection_lower,
            "screw_left": self.screw_left,
            "screw_right": self.screw_right,
        }

        for name, process_obj in processes.items():
            if (
                process_obj is not None
                and process_obj._get_time_series_data() is not None
            ):
                available.append(name)

        return available

    def plot_data(self, figsize=(15, 10), save_path=None, show_plot=True):
        """
        Create a 2x2 plot showing all time series data from all 4 processes.

        Layout:
        - Top Left: Upper Injection Molding
        - Top Right: Lower Injection Molding
        - Bottom Left: Left Screw Driving
        - Bottom Right: Right Screw Driving

        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save the plot
            show_plot: Whether to display the plot

        Returns:
            matplotlib.figure.Figure: The created figure
        """

        # Create 2x2 subplot layout
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(
            f"Experiment {self.upper_workpiece_id} - All Process Data",
            fontsize=16,
            fontweight="bold",
        )

        # Plot upper injection molding (top left)
        self._plot_injection_molding(
            axes[0, 0], self.injection_upper, "Upper Injection Molding"
        )

        # Plot lower injection molding (top right)
        self._plot_injection_molding(
            axes[0, 1], self.injection_lower, "Lower Injection Molding"
        )

        # Plot left screw driving (bottom left)
        self._plot_screw_driving(axes[1, 0], self.screw_left, "Left Screw Driving")

        # Plot right screw driving (bottom right)
        self._plot_screw_driving(axes[1, 1], self.screw_right, "Right Screw Driving")

        # Adjust layout to prevent overlap
        plt.tight_layout()

        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Plot saved to: {save_path}")

        # Show if requested
        if show_plot:
            plt.show()

        return fig

    def _plot_injection_molding(self, ax, injection_data, title):
        """Plot injection molding time series with dual y-axes for pressures vs other series"""

        if injection_data is None or injection_data.time_series is None:
            ax.text(
                0.5,
                0.5,
                "No Data Available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            return

        # Use sample count as x-axis instead of time values
        # This way padding doesn't affect the visualization

        lines_plotted = []
        labels_plotted = []

        # Plot non-pressure series on primary (left) y-axis
        primary_series = [
            ("melt_volume", "Melt Volume", "green"),
            ("injection_velocity", "Velocity", "orange"),
        ]

        for attr_name, label, color in primary_series:
            if hasattr(injection_data, attr_name):
                series_data = getattr(injection_data, attr_name)
                if series_data is not None and len(series_data) > 0:
                    # Use sample index as x-axis (0, 1, 2, 3, ...)
                    sample_axis = np.arange(len(series_data))
                    line = ax.plot(
                        sample_axis, series_data, label=label, color=color, alpha=0.7
                    )
                    lines_plotted.extend(line)
                    labels_plotted.append(label)

        # Set primary axis properties
        ax.set_xlabel("Sample Count")
        ax.set_ylabel("Volume / Velocity", color="black")
        ax.tick_params(axis="y", labelcolor="black")

        # Create secondary y-axis (right side) for both pressures
        ax2 = ax.twinx()

        # Plot both pressure series on secondary (right) y-axis
        pressure_series = [
            ("injection_pressure_target", "Pressure Target", "blue", "-"),
            ("injection_pressure_actual", "Pressure Actual", "red", "--"),
        ]

        for attr_name, label, color, linestyle in pressure_series:
            if hasattr(injection_data, attr_name):
                pressure_data = getattr(injection_data, attr_name)
                if pressure_data is not None and len(pressure_data) > 0:
                    # Use sample index as x-axis
                    sample_axis = np.arange(len(pressure_data))
                    line2 = ax2.plot(
                        sample_axis,
                        pressure_data,
                        label=label,
                        color=color,
                        alpha=0.7,
                        linestyle=linestyle,
                    )
                    lines_plotted.extend(line2)
                    labels_plotted.append(label)

        # Set secondary axis properties
        ax2.set_ylabel("Pressure", color="darkblue")
        ax2.tick_params(axis="y", labelcolor="darkblue")

        # Combined legend for both y-axes
        if lines_plotted:
            ax.legend(lines_plotted, labels_plotted, loc="upper left", fontsize=8)

        ax.set_title(title, fontweight="bold")
        ax.grid(True, alpha=0.3)

    def _plot_screw_driving(self, ax, screw_data, title):
        """Plot screw driving time series with angle on secondary y-axis"""

        if screw_data is None or screw_data.time_series is None:
            ax.text(
                0.5,
                0.5,
                "No Data Available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            return

        # Use sample count as x-axis instead of time values
        # This way padding doesn't affect the visualization

        # Plot torque and gradient on primary (left) y-axis
        primary_series = [
            ("torque", "Torque", "red"),
            ("gradient", "Gradient", "green"),
        ]

        lines_plotted = []
        labels_plotted = []

        for attr_name, label, color in primary_series:
            if hasattr(screw_data, attr_name):
                series_data = getattr(screw_data, attr_name)
                if series_data is not None and len(series_data) > 0:
                    # Use sample index as x-axis (0, 1, 2, 3, ...)
                    sample_axis = np.arange(len(series_data))
                    line = ax.plot(
                        sample_axis, series_data, label=label, color=color, alpha=0.7
                    )
                    lines_plotted.extend(line)
                    labels_plotted.append(label)

        # Set primary axis properties
        ax.set_xlabel("Sample Count")
        ax.set_ylabel("Torque / Gradient", color="black")
        ax.tick_params(axis="y", labelcolor="black")

        # Create secondary y-axis (right side) for angle
        ax2 = ax.twinx()

        # Plot angle on secondary (right) y-axis
        if hasattr(screw_data, "angle"):
            angle_data = getattr(screw_data, "angle")
            if angle_data is not None and len(angle_data) > 0:
                # Use sample index as x-axis
                sample_axis = np.arange(len(angle_data))
                line2 = ax2.plot(
                    sample_axis,
                    angle_data,
                    label="Angle",
                    color="blue",
                    alpha=0.7,
                    linestyle="--",
                )
                lines_plotted.extend(line2)
                labels_plotted.append("Angle")

        # Set secondary axis properties
        ax2.set_ylabel("Angle", color="blue")
        ax2.tick_params(axis="y", labelcolor="blue")

        # Combined legend for both y-axes
        if lines_plotted:
            ax.legend(lines_plotted, labels_plotted, loc="upper left", fontsize=8)

        ax.set_title(title, fontweight="bold")
        ax.grid(True, alpha=0.3)

    def __repr__(self):
        available = self.get_available_processes()
        return f"ExperimentData(id={self.upper_workpiece_id}, processes={available})"
