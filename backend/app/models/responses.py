"""
API response models for the CV Layout Cloner endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from app.models.schemas import FidelityTier


class ConversionResponse(BaseModel):
    """Response from the /api/convert endpoint."""
    success: bool
    fidelity_tier: FidelityTier
    tier_label: str = Field(
        description="Human-readable tier label: 'Exact Match', 'Near-Exact Match', or 'Best-Effort Reconstruction'"
    )
    docx_download_url: str = Field(description="URL to download the output .docx")
    pdf_download_url: str = Field(description="URL to download the output .pdf")
    preview_image_url: str = Field(description="URL to the low-res preview image")
    docx_note: Optional[str] = Field(
        default=None,
        description="Additional note about docx output quality (e.g., 'close match' for Tier 2)",
    )
    processing_time_seconds: float = Field(description="Total processing time")
    content_sections_found: list[str] = Field(
        default_factory=list,
        description="List of canonical sections that were found and mapped",
    )


class HealthResponse(BaseModel):
    """Response from the /api/health endpoint."""
    status: str = "ok"
    version: str = "1.0.0"
    libreoffice_available: bool = False
    playwright_available: bool = False
    tesseract_available: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
