import matplotlib.pyplot as plt
import numpy as np


def plot_injection_molding(injection_data, title, ax=None):
    """
    Plot injection molding time series with dual y-axes for pressures vs other series.

    Args:
        injection_data: Injection molding data object (upper or lower)
        title: Title for the plot
        ax: Matplotlib axes to plot on. If None, creates new figure.

    Returns:
        matplotlib.axes.Axes: The axes object used for plotting
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    if injection_data is None or injection_data.serial_data is None:
        ax.text(
            0.5,
            0.5,
            "No Data Available",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_title(title)
        return ax

    # Get serial data dictionary
    serial_data = injection_data.serial_data

    # Use sample count as x-axis instead of time values
    lines_plotted = []
    labels_plotted = []

    # Plot non-pressure series on primary (left) y-axis
    primary_series = [
        ("melt_volume", "Melt Volume", "green"),
        ("injection_velocity", "Velocity", "orange"),
    ]

    for series_name, label, color in primary_series:
        series_data = serial_data.get(series_name)
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

    for series_name, label, color, linestyle in pressure_series:
        pressure_data = serial_data.get(series_name)
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

    return ax


def plot_screw_driving(screw_data, title, ax=None):
    """
    Plot screw driving time series with angle on secondary y-axis.

    Args:
        screw_data: Screw driving data object
        title: Title for the plot
        ax: Matplotlib axes to plot on. If None, creates new figure.

    Returns:
        matplotlib.axes.Axes: The axes object used for plotting
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    if screw_data is None or screw_data.serial_data is None:
        ax.text(
            0.5,
            0.5,
            "No Data Available",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_title(title)
        return ax

    # Get serial data dictionary
    serial_data = screw_data.serial_data
    print(serial_data)

    # Plot torque and gradient on primary (left) y-axis
    primary_series = [
        ("torque", "Torque", "red"),
        ("gradient", "Gradient", "green"),
    ]

    lines_plotted = []
    labels_plotted = []

    for series_name, label, color in primary_series:
        series_data = serial_data.get(series_name)
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
    angle_data = serial_data.get("angle")
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

    return ax


def plot_experiment_data(
    injection_upper,
    injection_lower,
    screw_left,
    screw_right,
    experiment_id,
    figsize=(15, 10),
    save_path=None,
    show_plot=True,
):
    """
    Create a 2x2 plot showing all time series data from all 4 recordings.

    Layout:
    - Top Left: Upper Injection Molding
    - Top Right: Lower Injection Molding
    - Bottom Left: Left Screw Driving
    - Bottom Right: Right Screw Driving

    Args:
        injection_upper: Upper injection molding data object
        injection_lower: Lower injection molding data object
        screw_left: Left screw driving data object
        screw_right: Right screw driving data object
        experiment_id: ID for the experiment (used in title)
        figsize: Figure size (width, height)
        save_path: Optional path to save the plot
        show_plot: Whether to display the plot

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Create 2x2 subplot layout
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(
        f"Experiment {experiment_id} - All Recording Data",
        fontsize=16,
        fontweight="bold",
    )

    # Plot upper injection molding (top left)
    plot_injection_molding(injection_upper, "Upper Injection Molding", axes[0, 0])

    # Plot lower injection molding (top right)
    plot_injection_molding(injection_lower, "Lower Injection Molding", axes[0, 1])

    # Plot left screw driving (bottom left)
    plot_screw_driving(screw_left, "Left Screw Driving", axes[1, 0])

    # Plot right screw driving (bottom right)
    plot_screw_driving(screw_right, "Right Screw Driving", axes[1, 1])

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
