"""Source validation helpers shared by API and ingestion adapters."""
from pathlib import Path
import subprocess


def media_duration_seconds(path: str | Path) -> float:
    """Read media duration with ffprobe, returning zero when unavailable."""
    completed = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, check=False)
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return 0.0


def validate_media_duration(path: str | Path, maximum: int) -> None:
    """Raise a clear validation error when a local media file exceeds a limit."""
    duration = media_duration_seconds(path)
    if duration and duration > maximum:
        raise ValueError(f"Media duration exceeds configured limit of {maximum} seconds")
