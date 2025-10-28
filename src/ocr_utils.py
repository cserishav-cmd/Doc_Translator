from PyPDF2 import PdfReader
from docx import Document

# -------- PDF Extraction (No OCR) -------- #
def extract_pdf_without_ocr(pdf_path):
    """
    Extracts text from PDF without OCR.
    Returns a list of elements similar to OCR output.
    """
    reader = PdfReader(pdf_path)
    elements = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            for para in text.split("\n"):
                if para.strip():
                    elements.append({
                        "type": "paragraph",
                        "text": para.strip()
                    })

    return elements


# -------- DOCX Extraction (Preserve Formatting) -------- #
def extract_docx_with_format(docx_path):
    """
    Extracts paragraphs from DOCX.
    Returns a list of elements similar to OCR format.
    """
    doc = Document(docx_path)
    elements = []

    for para in doc.paragraphs:
        if para.text.strip():
            elements.append({
                "type": "paragraph",
                "text": para.text.strip()
            })

    return elements
