"""
PDF converter — wraps LibreOffice headless for docx→pdf conversion.
"""

import asyncio
import logging
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


async def convert_docx_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    """
    Convert a .docx file to PDF using LibreOffice headless.

    Args:
        docx_path: Path to the input .docx file
        output_dir: Directory where the PDF will be saved

    Returns:
        Path to the output PDF file

    Raises:
        RuntimeError: If LibreOffice conversion fails
    """
    logger.info(f"Converting {docx_path.name} to PDF via LibreOffice...")

    cmd = [
        settings.libreoffice_path,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(docx_path),
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=settings.libreoffice_timeout,
        )

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"LibreOffice conversion failed (exit code {process.returncode}): {error_msg}"
            )

        # LibreOffice names the output file with the same stem
        pdf_path = output_dir / f"{docx_path.stem}.pdf"

        # Rename to standard output name if needed
        expected_path = output_dir / "output.pdf"
        if pdf_path != expected_path and pdf_path.exists():
            pdf_path.rename(expected_path)
            pdf_path = expected_path

        if not pdf_path.exists():
            # Try to find the PDF by any name
            pdfs = list(output_dir.glob("*.pdf"))
            if pdfs:
                pdf_path = pdfs[0]
                if pdf_path.name != "output.pdf":
                    target = output_dir / "output.pdf"
                    pdf_path.rename(target)
                    pdf_path = target
            else:
                raise RuntimeError("LibreOffice conversion produced no PDF output")

        logger.info(f"PDF conversion successful: {pdf_path}")
        return pdf_path

    except asyncio.TimeoutError:
        raise RuntimeError(
            f"LibreOffice conversion timed out after {settings.libreoffice_timeout}s"
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"LibreOffice not found at '{settings.libreoffice_path}'. "
            "Please install LibreOffice or set LIBREOFFICE_PATH in .env"
        )
