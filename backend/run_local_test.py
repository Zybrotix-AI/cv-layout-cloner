import asyncio
from pathlib import Path
import os
import sys

# Add the app directory to sys.path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routes.convert import detect_file_type
from app.services.content_extractor import extract_content
from app.services.code_generator import generate_python_docx_script
from app.services.executor import execute_generated_script

async def run_test():
    base_dir = Path("/tmp/cv-layout-cloner/1783629134_bf84d18e")
    content_path = base_dir / "content_Syed_Farhan_CV.pdf"
    sample_path = base_dir / "sample_Lubna_Tahseen1.pdf"
    
    if not content_path.exists() or not sample_path.exists():
        print("Test files not found.")
        return
        
    print("--- 1. Extracting Content ---")
    content_info = detect_file_type(content_path)
    canonical_cv = await extract_content(content_info)
    print(f"Extracted CV for {canonical_cv.name}")
    
    print("\n--- 2. Generating Script ---")
    script_code = await generate_python_docx_script(sample_path, canonical_cv)
    print("Script generated successfully.")
    
    print("\n--- 3. Executing Script ---")
    output_docx = await execute_generated_script(script_code, base_dir)
    print(f"Success! DOCX generated at: {output_docx}")

if __name__ == "__main__":
    asyncio.run(run_test())
