"""
CV Layout Cloner — FastAPI Application Entry Point.

Configures CORS, mounts routes, and manages application lifecycle
(temp file cleanup on startup/shutdown).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, convert
from app.utils.temp_files import cleanup_old_jobs, ensure_temp_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # --- Startup ---
    logger.info("CV Layout Cloner backend starting up...")
    ensure_temp_dir()
    cleaned = cleanup_old_jobs()
    if cleaned:
        logger.info(f"Cleaned up {cleaned} expired job directories on startup")
    logger.info(f"Temp directory: {settings.temp_dir}")

    yield

    # --- Shutdown ---
    logger.info("CV Layout Cloner backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="CV Layout Cloner",
    description=(
        "Upload your CV and a sample CV — get your content rendered "
        "in the sample's exact layout. Supports docx, PDF, and image inputs "
        "with three fidelity tiers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(convert.router, prefix="/api", tags=["conversion"])


@app.get("/")
async def root():
    """Root endpoint — redirect to docs."""
    return {
        "app": "CV Layout Cloner",
        "docs": "/docs",
        "health": "/api/health",
    }
