"""
Main conversion endpoint.
Accepts two file uploads (content CV + sample CV), routes to the appropriate
tier pipeline, and returns download URLs and preview.
"""

import time
import logging
import asyncio
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
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
from app.utils.temp_files import create_job_dir, save_upload, update_job_status, get_job_status

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum file size in bytes
MAX_SIZE = settings.max_file_size_mb * 1024 * 1024


async def run_conversion_job(job_dir: Path, content_path: Path, sample_path: Path, sample_info, start_time: float):
    """
    Background worker that runs the full conversion pipeline and updates status.json.
    """
    try:
        update_job_status(job_dir, {
            "status": "processing", 
            "progress": 10, 
            "step": "Extracting content from your CV...", 
            "estimated_remaining_seconds": 60
        })
        
        # --- Detect file types ---
        content_info = detect_file_type(content_path)
        
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

        update_job_status(job_dir, {
            "progress": 25, 
            "step": "AI is mapping your content into the new layout...", 
            "estimated_remaining_seconds": 55
        })

        # --- Step 2: Generate Python Script to Recreate Layout ---
        logger.info("Step 2: Generating python-docx script from template...")
        script_code = await generate_python_docx_script(sample_path, canonical_cv)

        update_job_status(job_dir, {
            "progress": 75, 
            "step": "Rendering the final DOCX document...", 
            "estimated_remaining_seconds": 10
        })

        # --- Step 3: Execute Script to Generate DOCX ---
        logger.info("Step 3: Executing generated script...")
        output_docx = await execute_generated_script(script_code, job_dir)
        docx_note = "Generated via AI layout reconstruction"

        update_job_status(job_dir, {
            "progress": 90, 
            "step": "Converting to PDF and generating preview...", 
            "estimated_remaining_seconds": 3
        })

        # --- Step 4: Convert DOCX to PDF ---
        logger.info("Step 4: Converting generated DOCX to PDF...")
        output_pdf = await convert_docx_to_pdf(output_docx, job_dir)

        # --- Step 5: Generate preview ---
        logger.info("Step 5: Generating preview image...")
        preview_path = generate_preview(output_pdf, job_dir)

        # --- Build response ---
        processing_time = round(time.time() - start_time, 2)
        job_id = job_dir.name

        result = {
            "success": True,
            "fidelity_tier": sample_info.tier.value,
            "tier_label": get_tier_label(sample_info.tier),
            "docx_download_url": f"/api/download/{job_id}/output.docx",
            "pdf_download_url": f"/api/download/{job_id}/output.pdf",
            "preview_image_url": f"/api/download/{job_id}/preview.png",
            "docx_note": docx_note,
            "processing_time_seconds": processing_time,
            "content_sections_found": content_sections,
        }
        
        update_job_status(job_dir, {
            "status": "done",
            "progress": 100,
            "step": "Complete!",
            "estimated_remaining_seconds": 0,
            "result": result
        })

    except Exception as e:
        logger.error(f"Conversion job failed: {e}", exc_info=True)
        update_job_status(job_dir, {
            "status": "error",
            "error": f"Conversion failed: {str(e)}"
        })


@router.post("/convert")
async def start_convert_cv(
    background_tasks: BackgroundTasks,
    content_cv: UploadFile = File(..., description="User's CV with content to use"),
    sample_cv: UploadFile = File(..., description="Sample/template CV whose layout to clone"),
):
    """
    Start the conversion job in the background and return a job ID.
    """
    start_time = time.time()

    # --- Validate uploads ---
    for upload, label in [(content_cv, "Content CV"), (sample_cv, "Sample CV")]:
        if not upload.filename:
            raise HTTPException(status_code=400, detail=f"{label}: no filename provided")

    # --- Create job directory ---
    job_dir = create_job_dir()
    logger.info(f"Starting background job in {job_dir}")
    
    update_job_status(job_dir, {
        "status": "started",
        "progress": 0,
        "step": "Uploading files..."
    })

    try:
        # --- Save uploaded files ---
        content_bytes = await content_cv.read()
        sample_bytes = await sample_cv.read()

        if len(content_bytes) > MAX_SIZE:
            raise HTTPException(status_code=413, detail=f"Content CV exceeds {settings.max_file_size_mb}MB")
        if len(sample_bytes) > MAX_SIZE:
            raise HTTPException(status_code=413, detail=f"Sample CV exceeds {settings.max_file_size_mb}MB")

        content_path = save_upload(content_bytes, f"content_{content_cv.filename}", job_dir)
        sample_path = save_upload(sample_bytes, f"sample_{sample_cv.filename}", job_dir)

        # Detect file types for tier info (doing this here to validate early)
        sample_info = detect_file_type(sample_path)
        
        update_job_status(job_dir, {
            "status": "processing",
            "progress": 5,
            "step": "Files received, initializing...",
            "estimated_remaining_seconds": 65
        })

        # Start the background task
        background_tasks.add_task(run_conversion_job, job_dir, content_path, sample_path, sample_info, start_time)

        return {"job_id": job_dir.name, "status": "started"}

    except HTTPException:
        update_job_status(job_dir, {"status": "error", "error": "Validation failed"})
        raise
    except Exception as e:
        logger.error(f"Failed to start job: {e}", exc_info=True)
        update_job_status(job_dir, {"status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")


@router.get("/status/{job_id}")
async def get_conversion_status(job_id: str):
    """
    Get the status of a running or completed conversion job.
    """
    if "/" in job_id or "\\" in job_id or ".." in job_id:
        raise HTTPException(status_code=400, detail="Invalid job ID")
        
    job_dir = settings.temp_dir / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found or expired")
        
    status_data = get_job_status(job_dir)
    return status_data


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
