import os
from docx import Document
from .ocr_utils import extract_pdf_without_ocr  # Use non-OCR function

# -------- DOCX Extraction -------- #
def extract_docx(file_path):
    doc = Document(file_path)
    elements = []
    for para in doc.paragraphs:
        if para.text.strip():
            elements.append({"type": "paragraph", "text": para.text.strip()})
    return elements

# -------- General File Extraction -------- #
def extract_elements(file_path):
    if file_path.endswith(".pdf"):
        return extract_pdf_without_ocr(file_path)
    elif file_path.endswith(".docx"):
        return extract_docx(file_path)
    else:
        raise ValueError("Unsupported file format")

# -------- Ensure Directories Exist -------- #
def ensure_dirs():
    os.makedirs("storage/uploads", exist_ok=True)
    os.makedirs("storage/translated", exist_ok=True)
