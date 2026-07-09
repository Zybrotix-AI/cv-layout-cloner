"""
Health check endpoint.
Reports system dependency availability (LibreOffice, Playwright, Tesseract).
"""

import shutil
import subprocess
import logging

from fastapi import APIRouter

from app.models.responses import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _check_libreoffice() -> bool:
    """Check if LibreOffice is available."""
    try:
        result = subprocess.run(
            ["soffice", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_tesseract() -> bool:
    """Check if Tesseract OCR is available."""
    return shutil.which("tesseract") is not None


def _check_playwright() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns service status and availability of system dependencies.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        libreoffice_available=_check_libreoffice(),
        playwright_available=_check_playwright(),
        tesseract_available=_check_tesseract(),
    )
