import os
import base64
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.schemas import CanonicalCV

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Python developer specializing in the `python-docx` library.
Your task is to write a complete, executable Python script that generates a `.docx` file perfectly replicating the visual layout, styling, typography, and structure of the provided sample CV image/PDF, but populated with the user's data provided in JSON format.

REQUIREMENTS:
1. Use the `python-docx` library (`import docx`, `from docx.shared import ...`, etc.).
2. Do NOT use any other external layout libraries or attempt to parse existing files in the script.
3. The script MUST write the final document to a file named `output.docx` in the current working directory.
4. Hardcode the JSON data directly into the Python script as a dictionary, and iterate/access it to populate the document.
5. Replicate the visual design as accurately as possible: margins, fonts, font sizes, colors (using RGBColor), bold/italic weights, tables for alignment, horizontal lines, etc.
6. If the layout uses a multi-column structure or sidebar, use `python-docx` tables with invisible borders to achieve the grid layout.
7. Return ONLY valid Python code. Do not include markdown fences (like ```python) or any preamble. The output must be directly executable.

CRITICAL PYTHON-DOCX API RULES (DO NOT VIOLATE):
- RGBColor(r, g, b) IS the color value. It has NO `.rgb` attribute. Use str(color_var) to get the hex, NOT color_var.rgb.hex().
- To set font color: use `run.font.color.rgb = RGBColor(r, g, b)`. NEVER use `font.color = RGBColor(...)` — the color property has NO setter. You must access `.color.rgb`.
- `OxmlElement` (like `tblBorders`) DOES NOT have a `.first_child_found_in` method. Use `.find(qn(tag))` instead.
- `OxmlElement` DOES NOT accept a `text` keyword argument (e.g. `OxmlElement('w:t', text=...)` is INVALID). You must set it after creation: `wt = OxmlElement('w:t'); wt.text = '...'`
- When generating the hardcoded JSON data dictionary, DOUBLE CHECK your commas! A missing comma will cause a SyntaxError.
- CRITICAL: When calling helper functions or creating lists/dictionaries across multiple lines, YOU MUST INCLUDE COMMAS between arguments! (e.g., `func(arg1, \n arg2)` NOT `func(arg1 \n arg2)`). A missing comma will cause a SyntaxError and fail the build!
- When setting border colors in OxmlElement, use a literal hex string like '000000', NOT a method call.
- Always import OxmlElement: `from docx.oxml import OxmlElement`
- Always import qn exactly like this: `from docx.oxml.ns import qn`
- When accessing paragraph.runs[0], first check that runs is not empty.
- Use `paragraph.add_run("")` if you need to ensure a run exists.
- For horizontal lines, create a paragraph border using OxmlElement with proper namespace.
- NEVER wrap `child.tag` in `qn()` when checking element tags (e.g. `if child.tag == qn('w:tblBorders')`). `child.tag` is already namespaced. Calling `qn(child.tag)` will cause `KeyError: '{http'`.
- NEVER pass fully-qualified namespace URIs like `'{http://...}tag'` to `OxmlElement()`. ALWAYS use the prefix form, e.g. `'w:tag'`.
- `OxmlElement` (like `CT_PPr`) does NOT have an `insert_before` method. Use `.append(element)` instead.
"""

from app.services.gemini_client import _get_client

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def generate_python_docx_script(
    sample_file_path: Path,
    canonical_cv: CanonicalCV
) -> str:
    """
    Calls Gemini to generate a python-docx script recreating the layout.
    """
    client = _get_client()
    
    # Read the sample file
    file_bytes = sample_file_path.read_bytes()
    suffix = sample_file_path.suffix.lower()
    
    # Determine the media type and content block for Gemini
    contents = []
    
    if suffix == ".pdf":
        media_type = "application/pdf"
    elif suffix in [".png", ".jpg", ".jpeg"]:
        media_type = "image/png" if suffix == ".png" else "image/jpeg"
    elif suffix == ".docx":
        # If it's docx, just extract text for now, or ideally it should be converted to PDF first.
        # Assuming convert.py will pass a PDF/Image for best results.
        raise ValueError("Sample CV must be PDF or Image for code generation vision analysis.")
    else:
        raise ValueError(f"Unsupported sample file type for code generation: {suffix}")

    part = types.Part.from_bytes(data=file_bytes, mime_type=media_type)
    contents.append(part)

    # Add the JSON data instructions
    json_data = canonical_cv.model_dump_json(indent=2)
    prompt = f"""
Here is the user's content in JSON format:
{json_data}

Analyze the provided CV layout and write a Python script using `python-docx` that generates a visually identical layout populated with this JSON data. Save it as `output.docx`.
Return ONLY the raw Python code.
"""
    contents.append(prompt)

    logger.info("Sending layout and data to Gemini for code generation...")
    
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        
        code = response.text
        if not code:
            raise ValueError("Empty response text from Gemini.")
            
        # Clean up markdown fences if Gemini ignored the system prompt
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
            
        return code.strip()
    except Exception as e:
        logger.error(f"Failed to generate code via Gemini: {e}")
        raise ValueError(f"Failed to generate code via Gemini: {e}")
