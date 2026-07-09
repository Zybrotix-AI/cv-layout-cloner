import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def execute_generated_script(script_code: str, job_dir: Path) -> Path:
    """
    Writes the script_code to a file in job_dir and executes it in an isolated subprocess.
    The script is expected to generate 'output.docx' inside job_dir.
    
    Returns the Path to output.docx if successful, raises Exception otherwise.
    """
    script_path = job_dir / "generate.py"
    output_docx_path = job_dir / "output.docx"
    
    script_path.write_text(script_code, encoding="utf-8")
    
    logger.info(f"Executing generated script at {script_path}...")
    
    try:
        # Run the script with python, setting the cwd to the job_dir
        # so output.docx is written there.
        result = subprocess.run(
            ["python", str(script_path.name)],
            cwd=str(job_dir),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Script execution failed:\nStdout: {result.stdout}\nStderr: {result.stderr}")
            raise RuntimeError(f"Script execution failed with return code {result.returncode}.\nStderr: {result.stderr}")
            
        if not output_docx_path.exists():
            raise FileNotFoundError("Script executed successfully but output.docx was not created.")
            
        logger.info(f"Successfully generated {output_docx_path}")
        return output_docx_path
        
    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out.")
        raise RuntimeError("Script execution timed out.")
    except Exception as e:
        logger.error(f"Error during script execution: {e}")
        raise
