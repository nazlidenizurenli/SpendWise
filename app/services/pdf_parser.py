import fitz
from fastapi import UploadFile

def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extract raw text from PDF with minimal preprocessing.
    Let the LLM handle all the cleaning and parsing.
    """
    file.file.seek(0)
    pdf_bytes = file.file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    all_text = ""
    for page_num, page in enumerate(doc, 1):
        page_text = page.get_text()
        all_text += f"\n--- PAGE {page_num} ---\n"
        all_text += page_text + "\n"
    
    doc.close()
    
    return all_text.strip()
