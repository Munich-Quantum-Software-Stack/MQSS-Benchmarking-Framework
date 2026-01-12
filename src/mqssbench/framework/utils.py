from .types import VALID_ORIGINS
import os
import re
import sys
import matplotlib.pyplot as plt
import matplotlib
from typing import Iterable, Callable, IO
import webbrowser
from pathlib import Path


def atomic_write(target_path: Path, write_fn: Callable[[IO], None], encoding="utf-8"):
    """
    Atomically write to a file. Writes to a temp file first then renames it.
    """
    temp_path = target_path.with_suffix(".tmp")
    os.makedirs(target_path.parent, exist_ok=True)
    with open(temp_path, "w", encoding=encoding) as f:
        write_fn(f)
    temp_path.replace(target_path)


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

def make_output_filepath(
    benchmark_key: str,
    run_dir: str,
    tag: str = "output",
    ext: str = "png"
) -> str:
    """
    Generate a safe output filename for saving artifacts (plots, diagrams, etc.)
    inside the run folder. Automatically creates an 'artifacts' subfolder.

    Args:
        benchmark_key: Full benchmark key (e.g., "origin/source/name").
        run_dir: Run folder where the artifacts subfolder will be created.
        tag: Descriptive tag for the artifact (plot, diagram, etc.).
        ext: File extension (default "png").

    Returns:
        Full path to the artifact file.
    """
    if not run_dir:
        raise ValueError("run_dir must be provided to make_output_filepath")

    # Create artifacts subfolder
    artifact_dir = os.path.join(run_dir, "artifacts")
    os.makedirs(artifact_dir, exist_ok=True)

    # Take last part of benchmark_key and sanitize
    bench_name = benchmark_key.split("/")[-1].lower()
    safe_name = re.sub(r"[^a-z0-9_]+", "_", bench_name)

    filename = f"{safe_name}_{tag}.{ext}"

    path = os.path.join(artifact_dir, filename)

    return path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".svg"}

def can_display() -> bool:
    """
    Determine if the current environment can display artifacts.

    Returns True if running interactively (e.g., VS Code, local terminal) 
    and a display is available. Returns False in headless environments 
    (CI, SSH without X11) or if display is disabled via MQSSBENCH_DISPLAY.
    """
    if os.environ.get("MQSSBENCH_DISPLAY", "1") != "1":
        plt.close()
        return False

    try:
        interactive_env = (
            matplotlib.is_interactive() or
            os.environ.get("DISPLAY") or
            os.environ.get("WAYLAND_DISPLAY") or
            sys.stdout.isatty()
        )
        return bool(interactive_env)
    except Exception:
        return False


def show_artifacts(artifact_paths: Iterable[str], max_files: int = 3):
    """
    Open artifacts in the default system viewer, respecting headless environments.
    
    Args:
        artifact_paths: Iterable of file paths to artifacts.
        max_files: Maximum number of artifacts to open (default 10).
    """
    if not can_display():
        return

    opened = 0
    for path_str in artifact_paths:
        if opened >= max_files:
            break

        path = Path(path_str).resolve()
        if not path.exists():
            continue
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            webbrowser.open(f"file://{path}")
            opened += 1

