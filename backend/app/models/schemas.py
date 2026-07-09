"""
Pydantic models for CV data schemas, template maps, and API responses.
These schemas are shared across all tiers and input formats.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Semantic Role Enum — used to classify template blocks
# ==============================================================================


class SemanticRole(str, Enum):
    """Semantic roles for text blocks in a CV template."""
    NAME = "name"
    TITLE = "title"
    CONTACT_EMAIL = "contact_email"
    CONTACT_PHONE = "contact_phone"
    CONTACT_LOCATION = "contact_location"
    CONTACT_LINKEDIN = "contact_linkedin"
    CONTACT_WEBSITE = "contact_website"
    CONTACT_BLOCK = "contact_block"  # combined contact info
    SUMMARY = "summary"
    SECTION_HEADER = "section_header"
    JOB_COMPANY = "job_company"
    JOB_ROLE = "job_role"
    JOB_DATES = "job_dates"
    JOB_BULLET = "job_bullet"
    JOB_ENTRY = "job_entry"  # combined job entry
    EDUCATION_INSTITUTION = "education_institution"
    EDUCATION_DEGREE = "education_degree"
    EDUCATION_DATES = "education_dates"
    EDUCATION_ENTRY = "education_entry"  # combined education entry
    SKILL_ITEM = "skill_item"
    SKILL_LIST = "skill_list"
    PROJECT_NAME = "project_name"
    PROJECT_DESCRIPTION = "project_description"
    PROJECT_ENTRY = "project_entry"
    CERTIFICATION = "certification"
    OTHER = "other"
    DECORATIVE = "decorative"  # non-content elements (lines, shapes, etc.)


class FidelityTier(int, Enum):
    """Fidelity tier for the conversion output."""
    TIER_1_EXACT = 1
    TIER_2_NEAR_EXACT = 2
    TIER_3_BEST_EFFORT = 3


class FileType(str, Enum):
    """Supported input file types."""
    DOCX = "docx"
    PDF_TEXT = "pdf_text"
    PDF_SCANNED = "pdf_scanned"
    IMAGE = "image"


# ==============================================================================
# Canonical CV Schema — normalized content extracted from user's CV
# ==============================================================================


class ContactInfo(BaseModel):
    """Contact information extracted from a CV."""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""


class ExperienceEntry(BaseModel):
    """A single job/work experience entry."""
    company: str = ""
    role: str = ""
    dates: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """A single education entry."""
    institution: str = ""
    degree: str = ""
    dates: str = ""


class ProjectEntry(BaseModel):
    """A single project entry."""
    name: str = ""
    description: str = ""


class CanonicalCV(BaseModel):
    """
    Canonical CV data schema. All content CVs (docx, pdf, image) are
    normalized into this exact structure before mapping to template.
    """
    name: str = ""
    title: str = ""
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


# ==============================================================================
# Template Map — describes the layout structure of the sample CV
# ==============================================================================


class TemplateBlock(BaseModel):
    """
    A classified block within the template document.
    Contains its semantic role, location reference, original text,
    and whether it repeats (e.g., one per job entry).
    """
    role: SemanticRole
    location: str = Field(
        description="Document tree reference — xpath index for docx, bbox string for PDF, css selector for HTML"
    )
    text: str = Field(description="Original text content of this block")
    is_repeating: bool = Field(
        default=False,
        description="True if this block repeats (one per job, education entry, etc.)",
    )
    group_id: Optional[str] = Field(
        default=None,
        description="Groups related repeating blocks (e.g., all parts of job entry #1)",
    )
    formatting: dict = Field(
        default_factory=dict,
        description="Read-only formatting metadata (font, size, color, etc.)",
    )
    paragraph_index: Optional[int] = Field(
        default=None,
        description="Index of the paragraph in the docx document body (Tier 1)",
    )
    run_indices: Optional[list[int]] = Field(
        default=None,
        description="Indices of runs within the paragraph (Tier 1)",
    )
    table_ref: Optional[str] = Field(
        default=None,
        description="Table/row/cell reference if block is inside a table (Tier 1)",
    )
    bbox: Optional[dict] = Field(
        default=None,
        description="Bounding box {x0, y0, x1, y1} for PDF/image blocks (Tier 2/3)",
    )
    page_num: Optional[int] = Field(
        default=None,
        description="Page number for multi-page documents (Tier 2/3)",
    )
    font_info: Optional[dict] = Field(
        default=None,
        description="Font metadata: {name, size, color, bold, italic} (Tier 2/3)",
    )


class TemplateMap(BaseModel):
    """
    Complete template map describing the sample CV's structure.
    Built by the template_analyzer service, consumed by the mapper.
    """
    tier: FidelityTier
    blocks: list[TemplateBlock] = Field(default_factory=list)
    metadata: dict = Field(
        default_factory=dict,
        description="Page dimensions, margins, column layout info, etc.",
    )
    section_order: list[str] = Field(
        default_factory=list,
        description="Ordered list of section names as they appear in the template",
    )
    repeating_groups: dict = Field(
        default_factory=dict,
        description="Map of group_id → list of TemplateBlock indices for repeating sections",
    )


# ==============================================================================
# Mapping Plan — the bridge between content and template
# ==============================================================================


class MappingSlot(BaseModel):
    """A single mapping assignment: which content goes into which template block."""
    template_block_index: int
    content_field: str  # dot-notation path into CanonicalCV, e.g., "experience.0.company"
    content_value: str
    action: str = Field(
        description="'fill', 'clone_and_fill', 'delete'",
        default="fill",
    )


class MappingPlan(BaseModel):
    """
    Complete plan for filling template blocks with content.
    Produced by the mapper, consumed by tier-specific renderers.
    """
    slots: list[MappingSlot] = Field(default_factory=list)
    blocks_to_clone: list[dict] = Field(
        default_factory=list,
        description="List of {group_id, clone_count} for blocks that need duplication",
    )
    blocks_to_delete: list[int] = Field(
        default_factory=list,
        description="Indices of template blocks to remove (user has fewer entries)",
    )
    font_size_adjustments: dict = Field(
        default_factory=dict,
        description="Block index → font size delta (max -1pt) for overflow handling",
    )
