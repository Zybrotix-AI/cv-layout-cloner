"""
Gemini API client wrapper.
Handles all interactions with the Google Gemini API for:
- Canonical CV content extraction/normalization
"""

import logging
import base64
from pathlib import Path
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models.schemas import CanonicalCV

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a structured data extraction assistant. "
    "If you cannot extract a field, use an empty string or empty array. "
    "Extract ALL information present. Do not omit anything. "
    "If a field is not present in the text, use empty strings for strings and empty arrays for arrays. "
    "For experience entries, keep the chronological order from the CV. "
    "For bullets, capture each bullet point as a separate string. "
    "For skills, split comma-separated or listed skills into individual strings.\n"
    "You MUST return valid JSON matching the following schema structure exactly:\n"
    "{\n"
    "  'name': 'str',\n"
    "  'title': 'str',\n"
    "  'contact': {'email': 'str', 'phone': 'str', 'location': 'str', 'linkedin': 'str', 'website': 'str'},\n"
    "  'summary': 'str',\n"
    "  'experience': [{'company': 'str', 'role': 'str', 'dates': 'str', 'bullets': ['str']}],\n"
    "  'education': [{'institution': 'str', 'degree': 'str', 'dates': 'str'}],\n"
    "  'skills': ['str'],\n"
    "  'projects': [{'name': 'str', 'description': 'str'}],\n"
    "  'certifications': ['str']\n"
    "}"
)


import itertools

# Global iterator for API keys
_api_key_cycle = None

def _get_client() -> genai.Client:
    """Create a Google GenAI client instance using round-robin API keys."""
    global _api_key_cycle
    if _api_key_cycle is None:
        # Split by comma and strip whitespace
        keys = [k.strip() for k in settings.gemini_api_key.split(",") if k.strip()]
        if not keys:
            raise ValueError("No Gemini API keys found in configuration.")
        _api_key_cycle = itertools.cycle(keys)
    
    current_key = next(_api_key_cycle)
    return genai.Client(api_key=current_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def extract_canonical_cv(raw_text: str) -> CanonicalCV:
    """
    Send raw extracted text to Gemini to normalize into the canonical CV JSON schema.

    Args:
        raw_text: Raw text extracted from the user's CV (any format)

    Returns:
        CanonicalCV: Validated canonical CV data
    """
    client = _get_client()

    prompt = f"Extract the following CV/resume text into structured data.\n\nCV TEXT:\n{raw_text}"

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
            ),
        )
        # Parse the JSON response directly into the Pydantic model
        if response.text:
            return CanonicalCV.model_validate_json(response.text)
        else:
            raise ValueError("Empty response text from Gemini.")
    except Exception as e:
        logger.error(f"Failed to parse Gemini response as CanonicalCV: {e}")
        raise ValueError(f"Failed to parse CV content: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def extract_canonical_cv_from_image(image_bytes: bytes, media_type: str = "image/png") -> CanonicalCV:
    """
    Send a CV image directly to Gemini for content extraction.

    Args:
        image_bytes: Raw image bytes
        media_type: MIME type of the image

    Returns:
        CanonicalCV: Validated canonical CV data
    """
    client = _get_client()

    prompt = "Extract ALL text content from this CV/resume image and structure it. Extract EVERYTHING visible."

    part = types.Part.from_bytes(data=image_bytes, mime_type=media_type)

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[part, prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
            ),
        )
        if response.text:
            return CanonicalCV.model_validate_json(response.text)
        else:
            raise ValueError("Empty response text from Gemini.")
    except Exception as e:
        logger.error(f"Failed to parse vision CV extraction: {e}")
        raise ValueError(f"Failed to extract CV content from image: {e}")
