from .types import VALID_ORIGINS
import os
from datetime import datetime
import sys
import matplotlib.pyplot as plt
import matplotlib

def validate_benchmark_registry_key(identifier: str) -> None:
    """
    Validate that a benchmark identifier follows origin/source/name format.
    Raises ValueError if invalid.
    """
    parts = [p.strip() for p in identifier.split("/")]
    if len(parts) != 3:
        raise ValueError(
            f"Benchmark identifier '{identifier}' must have exactly three segments: origin/source/name."
        )
    origin, source, name = parts
    if origin not in VALID_ORIGINS:
        raise ValueError(f"Origin '{origin}' must be one of {sorted(VALID_ORIGINS)}.")
    if not source or not name:
        raise ValueError("Source and name segments must be non-empty.")

def make_output_path(name: str, output_dir: str, is_plot: bool) -> str:
    """Generate a unique output filename for saving figures or data."""
    if not output_dir:
        raise ValueError("output_dir must be provided to make_output_path")
    # ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    ext = "png"
    tag = "_plot" if is_plot else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{name}{tag}_{timestamp}"
    path = os.path.join(output_dir, f"{base}.{ext}")

    # increment if file exists
    counter = 1
    while os.path.exists(path):
        path = os.path.join(output_dir, f"{base}_{counter}.{ext}")
        counter += 1

    # print where file is saved
    print(f"Output {'plot' if is_plot else 'data'} saved to: {path}")

    return path

def safe_plot_show():
    """
    Show a plot when running interactively (e.g., VS Code, Jupyter, local terminal).
    Close the plot automatically in headless environments (CI, SSH without X11).
    """
    # Check the env variable
    if os.environ.get("MQSSBENCH_DISPLAY", "1") != "1":
        plt.close()
        return

    try:
        interactive_env = (
            matplotlib.is_interactive() or
            os.environ.get("DISPLAY") or
            os.environ.get("WAYLAND_DISPLAY") or
            sys.stdout.isatty()
        )

        if interactive_env:
            plt.show()
            return
    except Exception:
        pass

    # headless / no display
    plt.close()