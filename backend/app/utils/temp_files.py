"""
Temporary file management utilities.
Handles creation, tracking, and cleanup of temp files used during conversion.
"""

import os
import time
import uuid
import shutil
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import json

from app.config import settings

logger = logging.getLogger(__name__)


def ensure_temp_dir() -> Path:
    """Create the temp directory if it doesn't exist."""
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return settings.temp_dir


def create_job_dir() -> Path:
    """
    Create a unique directory for a single conversion job.
    All input/output files for that job live here.
    Returns the job directory path.
    """
    job_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    job_dir = ensure_temp_dir() / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created job directory: {job_dir}")
    return job_dir


def cleanup_job_dir(job_dir: Path) -> None:
    """Remove a job directory and all its contents."""
    if job_dir.exists():
        shutil.rmtree(job_dir)
        logger.info(f"Cleaned up job directory: {job_dir}")


def cleanup_old_jobs(max_age_hours: int | None = None) -> int:
    """
    Remove job directories older than max_age_hours.
    Returns the number of directories cleaned up.
    """
    if max_age_hours is None:
        max_age_hours = settings.temp_file_ttl_hours

    temp_dir = settings.temp_dir
    if not temp_dir.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    cleaned = 0

    for entry in temp_dir.iterdir():
        if entry.is_dir():
            try:
                # Job dirs are named with a timestamp prefix
                dir_timestamp = int(entry.name.split("_")[0])
                if dir_timestamp < cutoff:
                    shutil.rmtree(entry)
                    cleaned += 1
                    logger.info(f"Cleaned up expired job: {entry.name}")
            except (ValueError, IndexError):
                # Directory doesn't follow our naming convention — skip
                pass

    return cleaned


@contextmanager
def temp_job() -> Generator[Path, None, None]:
    """
    Context manager that creates a temp job directory and optionally
    cleans it up after use. Useful for testing.

    Usage:
        with temp_job() as job_dir:
            # ... do work in job_dir ...
        # job_dir is cleaned up
    """
    job_dir = create_job_dir()
    try:
        yield job_dir
    finally:
        cleanup_job_dir(job_dir)


def save_upload(content: bytes, filename: str, job_dir: Path) -> Path:
    """
    Save uploaded file bytes to the job directory.
    Returns the path to the saved file.
    """
    # Sanitize filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = f"upload_{uuid.uuid4().hex[:6]}"

    file_path = job_dir / safe_name
    file_path.write_bytes(content)
    logger.info(f"Saved upload: {file_path} ({len(content)} bytes)")
    return file_path


def get_output_path(job_dir: Path, suffix: str) -> Path:
    """Get a path for an output file in the job directory."""
    return job_dir / f"output{suffix}"


def update_job_status(job_dir: Path, status_data: dict) -> None:
    """
    Write or update the status.json file in the job directory.
    """
    status_file = job_dir / "status.json"
    
    # Read existing if available to merge
    current_data = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass
            
    current_data.update(status_data)
    
    # Atomic-ish write by writing and renaming
    temp_file = job_dir / "status.json.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(current_data, f)
    temp_file.replace(status_file)


def get_job_status(job_dir: Path) -> dict:
    """
    Read the status.json file from the job directory.
    """
    status_file = job_dir / "status.json"
    if not status_file.exists():
        return {"status": "started", "progress": 0}
        
    try:
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"status": "started", "progress": 0}
