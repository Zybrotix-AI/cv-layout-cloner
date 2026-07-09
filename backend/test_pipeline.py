import asyncio
from app.routes.convert import detect_file_type
from app.services.content_extractor import extract_content
from app.services.template_analyzer import analyze_template
from pathlib import Path

async def run_test():
    content_path = Path("/tmp/cv-layout-cloner/1783523336_6cc123ea/content_Cv_ShreyaDixit.pdf")
    sample_path = Path("/tmp/cv-layout-cloner/1783523336_6cc123ea/sample_Syed_Farhan_CV.pdf")
    
    content_info = detect_file_type(content_path)
    sample_info = detect_file_type(sample_path)
    
    print("Testing content_extractor...")
    canonical_cv = await extract_content(content_info)
    print("Canonical CV Name:", canonical_cv.name)
    
    print("Testing template_analyzer...")
    template_map = await analyze_template(sample_info)
    print("Template mapping success!")
    print(list(template_map.keys())[:5])
    
if __name__ == "__main__":
    asyncio.run(run_test())
