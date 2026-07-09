"""
Preview generator — creates a low-res PNG preview from the output PDF.
Uses PyMuPDF to rasterize the first page.
"""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def generate_preview(pdf_path: Path, job_dir: Path, dpi: int = 150) -> Path:
    """
    Generate a low-res preview image from the first page of a PDF.

    Args:
        pdf_path: Path to the PDF file
        job_dir: Directory to save the preview
        dpi: Resolution for the preview (default: 150 DPI for reasonable quality + small size)

    Returns:
        Path to the preview PNG file
    """
    preview_path = job_dir / "preview.png"

    try:
        doc = fitz.open(str(pdf_path))
        page = doc[0]

        # Render at specified DPI
        zoom = dpi / 72  # 72 is the default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        pix.save(str(preview_path))
        doc.close()

        logger.info(
            f"Generated preview: {preview_path} "
            f"({pix.width}x{pix.height}px, {preview_path.stat().st_size} bytes)"
        )
        return preview_path

    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        # Create a minimal placeholder if preview generation fails
        _create_placeholder_preview(preview_path)
        return preview_path


def _create_placeholder_preview(path: Path):
    """Create a minimal placeholder image if preview generation fails."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (595, 842), color="#f0f0f0")
        draw = ImageDraw.Draw(img)
        draw.text(
            (595 // 2, 842 // 2),
            "Preview\nUnavailable",
            fill="#999999",
            anchor="mm",
        )
        img.save(str(path))
    except ImportError:
        # If Pillow isn't available, create a minimal 1x1 PNG
        import struct
        import zlib

        def create_minimal_png():
            signature = b"\x89PNG\r\n\x1a\n"
            ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
            ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
            raw_data = b"\x00\xf0\xf0\xf0"
            compressed = zlib.compress(raw_data)
            idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
            idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)
            iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
            iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
            return signature + ihdr + idat + iend

        path.write_bytes(create_minimal_png())
