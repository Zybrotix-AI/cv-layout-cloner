"""
Configuration settings for CV Layout Cloner backend.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    gemini_api_key: str = Field(..., description="Google Gemini API key")

    # Gemini model configuration
    gemini_model: str = Field(
        default="gemini-2.5-pro",
        description="Gemini model for text extraction and vision/code generation",
    )



    # File handling
    max_file_size_mb: int = Field(default=20, description="Maximum upload file size in MB")
    temp_dir: Path = Field(
        default=Path("/tmp/cv-layout-cloner"),
        description="Directory for temporary files",
    )
    temp_file_ttl_hours: int = Field(
        default=24,
        description="Hours before temp files are auto-deleted",
    )

    # Server
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # LibreOffice
    libreoffice_path: str = Field(
        default="soffice",
        description="Path to LibreOffice soffice binary",
    )
    libreoffice_timeout: int = Field(
        default=30,
        description="Timeout in seconds for LibreOffice conversions",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance — import this throughout the app
settings = Settings()
