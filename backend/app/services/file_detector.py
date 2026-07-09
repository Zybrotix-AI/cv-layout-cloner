"""
File type detection and tier routing.
Determines the file type (docx, PDF, image) and which fidelity tier to use.
"""

import logging
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF

from app.models.schemas import FileType, FidelityTier

logger = logging.getLogger(__name__)

# Supported file extensions
DOCX_EXTENSIONS = {".docx"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


@dataclass
class FileInfo:
    """Result of file type detection."""
    file_path: Path
    file_type: FileType
    tier: FidelityTier
    extension: str
    size_bytes: int


def detect_file_type(file_path: Path) -> FileInfo:
    """
    Detect the file type and determine the appropriate fidelity tier.

    For PDFs, we check whether they contain real text or are scanned/flattened:
    - If text extraction yields > 50 chars → text-based PDF (Tier 2)
    - Otherwise → scanned PDF, treated as image (Tier 3)

    Args:
        file_path: Path to the uploaded file

    Returns:
        FileInfo with file type, tier, and metadata
    """
    ext = file_path.suffix.lower()
    size = file_path.stat().st_size

    if ext in DOCX_EXTENSIONS:
        logger.info(f"Detected DOCX: {file_path.name}")
        return FileInfo(
            file_path=file_path,
            file_type=FileType.DOCX,
            tier=FidelityTier.TIER_1_EXACT,
            extension=ext,
            size_bytes=size,
        )

    elif ext in PDF_EXTENSIONS:
        return _classify_pdf(file_path, ext, size)

    elif ext in IMAGE_EXTENSIONS:
        logger.info(f"Detected image: {file_path.name}")
        return FileInfo(
            file_path=file_path,
            file_type=FileType.IMAGE,
            tier=FidelityTier.TIER_3_BEST_EFFORT,
            extension=ext,
            size_bytes=size,
        )

    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported: {', '.join(sorted(DOCX_EXTENSIONS | PDF_EXTENSIONS | IMAGE_EXTENSIONS))}"
        )


def _classify_pdf(file_path: Path, ext: str, size: int) -> FileInfo:
    """
    Classify a PDF as text-based (Tier 2) or scanned/image (Tier 3).
    Uses PyMuPDF to attempt text extraction.
    """
    try:
        doc = fitz.open(str(file_path))
        total_text = ""
        for page_num in range(min(doc.page_count, 3)):  # Check first 3 pages
            page = doc[page_num]
            total_text += page.get_text("text")
        doc.close()

        # If we extracted meaningful text, it's a text-based PDF
        cleaned_text = total_text.strip()
        if len(cleaned_text) > 50:
            logger.info(
                f"Detected text-based PDF: {file_path.name} "
                f"({len(cleaned_text)} chars extracted)"
            )
            return FileInfo(
                file_path=file_path,
                file_type=FileType.PDF_TEXT,
                tier=FidelityTier.TIER_2_NEAR_EXACT,
                extension=ext,
                size_bytes=size,
            )
        else:
            logger.info(
                f"Detected scanned/image PDF: {file_path.name} "
                f"(only {len(cleaned_text)} chars extracted)"
            )
            return FileInfo(
                file_path=file_path,
                file_type=FileType.PDF_SCANNED,
                tier=FidelityTier.TIER_3_BEST_EFFORT,
                extension=ext,
                size_bytes=size,
            )

    except Exception as e:
        logger.warning(f"Error analyzing PDF {file_path.name}: {e}. Treating as scanned.")
        return FileInfo(
            file_path=file_path,
            file_type=FileType.PDF_SCANNED,
            tier=FidelityTier.TIER_3_BEST_EFFORT,
            extension=ext,
            size_bytes=size,
        )


def get_tier_label(tier: FidelityTier) -> str:
    """Get human-readable label for a fidelity tier."""
    labels = {
        FidelityTier.TIER_1_EXACT: "Exact Match",
        FidelityTier.TIER_2_NEAR_EXACT: "Near-Exact Match",
        FidelityTier.TIER_3_BEST_EFFORT: "Best-Effort Reconstruction",
    }
    return labels[tier]
