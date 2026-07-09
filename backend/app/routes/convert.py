"""
Main conversion endpoint.
Accepts two file uploads (content CV + sample CV), routes to the appropriate
tier pipeline, and returns download URLs and preview.
"""

import time
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import FidelityTier, FileType
from app.models.responses import ConversionResponse, ErrorResponse
from app.services.file_detector import detect_file_type, get_tier_label
from app.services.content_extractor import extract_content
from app.services.code_generator import generate_python_docx_script
from app.services.executor import execute_generated_script
from app.services.pdf_converter import convert_docx_to_pdf
from app.services.preview_generator import generate_preview
from app.utils.temp_files import create_job_dir, save_upload

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum file size in bytes
MAX_SIZE = settings.max_file_size_mb * 1024 * 1024


@router.post("/convert", response_model=ConversionResponse)
async def convert_cv(
    content_cv: UploadFile = File(..., description="User's CV with content to use"),
    sample_cv: UploadFile = File(..., description="Sample/template CV whose layout to clone"),
):
    """
    Main conversion endpoint.

    1. Saves both uploaded files
    2. Detects file types and determines fidelity tier (based on sample CV type)
    3. Extracts canonical content from user's CV
    4. Analyzes sample CV layout/structure
    5. Creates a mapping plan (content → template slots)
    6. Executes tier-specific rendering pipeline
    7. Generates preview and returns download URLs
    """
    start_time = time.time()

    # --- Validate uploads ---
    for upload, label in [(content_cv, "Content CV"), (sample_cv, "Sample CV")]:
        if not upload.filename:
            raise HTTPException(status_code=400, detail=f"{label}: no filename provided")

    # --- Create job directory ---
    job_dir = create_job_dir()
    logger.info(f"Starting conversion job in {job_dir}")

    try:
        # --- Save uploaded files ---
        content_bytes = await content_cv.read()
        sample_bytes = await sample_cv.read()

        if len(content_bytes) > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Content CV exceeds max size of {settings.max_file_size_mb}MB",
            )
        if len(sample_bytes) > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Sample CV exceeds max size of {settings.max_file_size_mb}MB",
            )

        content_path = save_upload(content_bytes, f"content_{content_cv.filename}", job_dir)
        sample_path = save_upload(sample_bytes, f"sample_{sample_cv.filename}", job_dir)

        # --- Detect file types ---
        content_info = detect_file_type(content_path)
        sample_info = detect_file_type(sample_path)

        logger.info(
            f"Content CV: {content_info.file_type.value}, "
            f"Sample CV: {sample_info.file_type.value} → Tier {sample_info.tier.value}"
        )

        # --- Step 1: Extract canonical content from user's CV ---
        logger.info("Step 1: Extracting content from user's CV...")
        canonical_cv = await extract_content(content_info)

        content_sections = []
        if canonical_cv.name:
            content_sections.append("name")
        if canonical_cv.summary:
            content_sections.append("summary")
        if canonical_cv.experience:
            content_sections.append(f"experience ({len(canonical_cv.experience)} entries)")
        if canonical_cv.education:
            content_sections.append(f"education ({len(canonical_cv.education)} entries)")
        if canonical_cv.skills:
            content_sections.append(f"skills ({len(canonical_cv.skills)} items)")
        if canonical_cv.projects:
            content_sections.append(f"projects ({len(canonical_cv.projects)} entries)")
        if canonical_cv.certifications:
            content_sections.append(f"certifications ({len(canonical_cv.certifications)} items)")

        logger.info(f"Extracted sections: {content_sections}")

        # --- Step 2: Generate Python Script to Recreate Layout ---
        logger.info("Step 2: Generating python-docx script from template...")
        script_code = await generate_python_docx_script(sample_path, canonical_cv)

        # --- Step 3: Execute Script to Generate DOCX ---
        logger.info("Step 3: Executing generated script...")
        output_docx = await execute_generated_script(script_code, job_dir)
        docx_note = "Generated via AI layout reconstruction"

        # --- Step 4: Convert DOCX to PDF ---
        logger.info("Step 4: Converting generated DOCX to PDF...")
        output_pdf = await convert_docx_to_pdf(output_docx, job_dir)

        # --- Step 5: Generate preview ---
        logger.info("Step 5: Generating preview image...")
        preview_path = generate_preview(output_pdf, job_dir)

        # --- Build response ---
        processing_time = round(time.time() - start_time, 2)
        job_id = job_dir.name

        return ConversionResponse(
            success=True,
            fidelity_tier=sample_info.tier,
            tier_label=get_tier_label(sample_info.tier),
            docx_download_url=f"/api/download/{job_id}/output.docx",
            pdf_download_url=f"/api/download/{job_id}/output.pdf",
            preview_image_url=f"/api/download/{job_id}/preview.png",
            docx_note=docx_note,
            processing_time_seconds=processing_time,
            content_sections_found=content_sections,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """
    Download an output file from a conversion job.
    Files are served directly from the job directory.
    """
    # Validate filename to prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = settings.temp_dir / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")

    # Determine media type
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pdf": "application/pdf",
        ".png": "image/png",
    }
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )
