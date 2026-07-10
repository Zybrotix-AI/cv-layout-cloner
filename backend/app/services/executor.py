import re
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _sanitize_generated_code(code: str) -> str:
    """
    Fix common python-docx mistakes that Gemini frequently makes.
    This runs as a pre-processing step before executing the generated script.
    """
    # Fix 1: RGBColor has no .rgb attribute — it IS the color.
    # e.g. color.rgb.hex() → str(color) or f'{color}'
    code = re.sub(
        r'(\w+)\.rgb\.hex\(\)',
        r"str(\1)",
        code
    )

    # Fix 2: font.color = RGBColor(...) is WRONG. Must be font.color.rgb = RGBColor(...)
    # The Font.color property returns a ColorFormat object; you set .rgb on it.
    code = re.sub(
        r'(\w+\.color)\s*=\s*(RGBColor\([^)]+\))',
        r'\1.rgb = \2',
        code
    )

    # Fix 3: Gemini sometimes uses hex() on RGBColor which doesn't exist
    # e.g. RGBColor(0,0,0).hex() → str(RGBColor(0,0,0))
    code = re.sub(
        r'(RGBColor\([^)]+\))\.hex\(\)',
        r'str(\1)',
        code
    )

    # Fix 4: Sometimes Gemini forgets the 'w:' namespace prefix
    # This is typically fine, but let's make sure qn() is used correctly.

    # Fix 5: KeyError: '{http' when passing an already namespaced tag to qn()
    # e.g. qn(child.tag) -> child.tag
    code = re.sub(
        r'qn\((child\.tag|element\.tag)\)',
        r'\1',
        code
    )

    # Fix 5: Sometimes Gemini writes 'from docx.oxml.ns import qn' but uses nsdecls
    # without importing it. Add the import if nsdecls is used but not imported.
    if 'nsdecls' in code and 'import nsdecls' not in code and 'from docx.oxml' not in code:
        code = code.replace(
            'from docx.oxml.ns import qn',
            'from docx.oxml.ns import qn, nsdecls'
        )
    elif 'nsdecls' in code and 'nsdecls' not in code.split('import')[0] if 'import' in code else True:
        # Make sure nsdecls is imported
        if 'from docx.oxml.ns import qn' in code and 'nsdecls' not in code.split('\n')[0:20].__repr__():
            code = code.replace(
                'from docx.oxml.ns import qn',
                'from docx.oxml.ns import qn, nsdecls'
            )
            
    # Fix 6: Gemini sometimes imports qn from docx.oxml instead of docx.oxml.ns
    code = re.sub(
        r'from docx\.oxml import ([^\n]*)qn([^\n]*)',
        r'from docx.oxml import \1\2\nfrom docx.oxml.ns import qn',
        code
    )
    # clean up any trailing commas from the above regex
    code = code.replace('import ,', 'import ').replace(', \n', '\n')

    # Fix 6: Gemini sometimes uses document.add_section() incorrectly
    # (less common, but let's be safe)

    return code


async def execute_generated_script(script_code: str, job_dir: Path) -> Path:
    """
    Writes the script_code to a file in job_dir and executes it in an isolated subprocess.
    The script is expected to generate 'output.docx' inside job_dir.

    Returns the Path to output.docx if successful, raises Exception otherwise.
    """
    script_path = job_dir / "generate.py"
    output_docx_path = job_dir / "output.docx"

    # SECURITY AUDIT: Check for dangerous imports
    import ast
    try:
        tree = ast.parse(script_code)
        dangerous_modules = {'subprocess', 'shutil', 'socket', 'requests', 'urllib'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name.split('.')[0] in dangerous_modules:
                        raise ValueError(f"Security Policy Violation: AI generated dangerous import '{name.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in dangerous_modules:
                    raise ValueError(f"Security Policy Violation: AI generated dangerous import '{node.module}'")
    except SyntaxError as e:
        raise ValueError(f"AI generated invalid Python code: {e}")

    # Sanitize common Gemini code generation mistakes
    script_code = _sanitize_generated_code(script_code)

    script_path.write_text(script_code, encoding="utf-8")

    logger.info(f"Executing generated script at {script_path}...")

    try:
        result = subprocess.run(
            ["python", str(script_path.name)],
            cwd=str(job_dir),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Script execution failed:\nStdout: {result.stdout}\nStderr: {result.stderr}")
            # Try to auto-fix and retry once
            fixed_code = _attempt_auto_fix(script_code, result.stderr)
            if fixed_code and fixed_code != script_code:
                logger.info("Attempting auto-fix of generated script...")
                script_path.write_text(fixed_code, encoding="utf-8")
                result2 = subprocess.run(
                    ["python", str(script_path.name)],
                    cwd=str(job_dir),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result2.returncode == 0 and output_docx_path.exists():
                    logger.info(f"Auto-fix successful! Generated {output_docx_path}")
                    return output_docx_path
                else:
                    logger.error(f"Auto-fix also failed:\nStderr: {result2.stderr}")

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


def _attempt_auto_fix(code: str, error_msg: str) -> str:
    """
    Try to fix the generated code based on the error message.
    Returns modified code, or the original if no fix could be applied.
    """
    fixed = code

    # Fix missing commas in dictionary/json data structures (causes SyntaxError)
    if "SyntaxError" in error_msg:
        fixed = re.sub(r'(["\'\]\}])\s*\n\s*(["\']\w+["\']\s*:)', r'\1,\n\2', fixed)
        # Also catch missing commas in lists (e.g., "string" \n "string")
        # but only if preceded by a comma on some previous element, or inside brackets.
        # It's safer to just fix the dictionary keys for now since that's the most common failure.

    # Fix AttributeError on RGBColor
    if "AttributeError" in error_msg and "RGBColor" in error_msg:
        # Fix string formatting hallucination: '%02x%02x%02x' % color.rgb
        fixed = re.sub(r"'%02[xX]%02[xX]%02[xX]' % (\w+)\.rgb", r"str(\1)", fixed)
        fixed = re.sub(r'"%02[xX]%02[xX]%02[xX]" % (\w+)\.rgb', r"str(\1)", fixed)
        # Fix f-string hallucination: f'{color.rgb:06X}'
        fixed = re.sub(r"f['\"]\{([^:}]+)(?:\.rgb)?(?::06[xX]|:[xX])\}['\"]", r"str(\1)", fixed)
        # Fix f-string hallucination: f'{color.r:02x}{color.g:02x}{color.b:02x}'
        fixed = re.sub(r"f['\"]\{([^:]+)\.r:02[xX]\}\{\1\.g:02[xX]\}\{\1\.b:02[xX]\}['\"]", r"str(\1)", fixed)
        # Remove any remaining .rgb references on color objects
        fixed = re.sub(r'\.rgb(?=[\.\)\s,\]:]|$)', '', fixed)
        # Remove any .r, .g, .b references (risky, but usually safe in color contexts if not caught above)
        # It's better to just catch the f-string format above.
        # Fix hex() calls on RGBColor
        fixed = re.sub(r'\.hex\(\)', '', fixed)

    # Fix font.color has no setter
    if "has no setter" in error_msg and "color" in error_msg:
        fixed = re.sub(
            r'(\w+\.color)\s*=\s*(RGBColor\([^)]+\))',
            r'\1.rgb = \2',
            fixed
        )

    # Fix KeyError: '{http' in qn()
    if "KeyError: '{http'" in error_msg:
        fixed = re.sub(
            r'qn\((child\.tag|element\.tag)\)',
            r'\1',
            fixed
        )
        
    # Fix AttributeError: 'CT_PPr' object has no attribute 'insert_before'
    if "AttributeError" in error_msg and "insert_before" in error_msg:
        fixed = re.sub(
            r'(\w+)\.insert_before\(([^,]+),[^)]+\)',
            r'\1.append(\2)',
            fixed
        )
        
    # Fix AttributeError: 'lxml.etree._Element' object has no attribute 'first_child_found_in'
    if "AttributeError" in error_msg and "first_child_found_in" in error_msg:
        fixed = fixed.replace(".first_child_found_in(", ".find(qn(")
        # Need to close the qn() parenthesis. We'll do a basic regex.
        fixed = re.sub(
            r'\.find\(\s*qn\(\s*([^)]+)\s*\)',
            r'.find(qn(\1))',
            fixed
        )
        
    # Fix TypeError: OxmlElement() got an unexpected keyword argument 'text'
    if "unexpected keyword argument 'text'" in error_msg and "OxmlElement" in error_msg:
        fixed = re.sub(
            r'OxmlElement\(([^,]+),\s*text=([^)]+)\)',
            r'(lambda e: setattr(e, "text", \2) or e)(OxmlElement(\1))',
            fixed
        )

    # Fix ImportError: cannot import name 'qn' from 'docx.oxml'
    if "cannot import name 'qn' from 'docx.oxml'" in error_msg:
        fixed = re.sub(
            r'from docx\.oxml import ([^\n]*)qn([^\n]*)',
            r'from docx.oxml import \1\2\nfrom docx.oxml.ns import qn',
            fixed
        )
        fixed = fixed.replace('import ,', 'import ').replace(', \n', '\n')

    # Fix NameError for missing imports
    if "NameError: name" in error_msg:
        import re as re_mod
        match = re_mod.search(r"NameError: name '(\w+)' is not defined", error_msg)
        if match:
            missing_name = match.group(1)
            if missing_name == 'OxmlElement':
                if 'from docx.oxml import OxmlElement' not in fixed:
                    fixed = 'from docx.oxml import OxmlElement\n' + fixed
            elif missing_name == 'qn':
                if 'from docx.oxml.ns import qn' not in fixed:
                    fixed = 'from docx.oxml.ns import qn\n' + fixed
            elif missing_name == 'nsdecls':
                if 'nsdecls' not in fixed:
                    fixed = fixed.replace(
                        'from docx.oxml.ns import qn',
                        'from docx.oxml.ns import qn, nsdecls'
                    )

    # Fix IndexError when accessing runs[0] on empty paragraph
    if "IndexError: list index out of range" in error_msg:
        # Wrap runs[0] access in a check
        fixed = re.sub(
            r'(\w+)\.runs\[0\]',
            r'(\1.runs[0] if \1.runs else \1.add_run(""))',
            fixed
        )

    return fixed
