"""
OCR helper shared by app.py (live uploads) and train_model.py (training data).

Every PDF page is rasterized and run through Tesseract OCR, rather than
relying on a PDF's embedded text layer. This is slower than pypdf's
text-layer extraction but works uniformly for both scanned/image-only
PDFs and normal text PDFs, and keeps extraction behavior identical
between training and inference.

Requires system binaries that pip cannot install:
  - tesseract-ocr   (the OCR engine)
  - poppler-utils   (so pdf2image can rasterize PDF pages)
See README / setup instructions for install commands per OS.
"""

from pdf2image import convert_from_bytes, convert_from_path
import pytesseract

# Bump if you need higher-fidelity OCR on small/blurry text; higher DPI
# = better accuracy but slower and more memory per page.
OCR_DPI = 300


def ocr_pdf_bytes(file_bytes: bytes) -> str:
    """OCR every page of an in-memory PDF (e.g. a Streamlit upload) and
    return the concatenated text."""
    pages = convert_from_bytes(file_bytes, dpi=OCR_DPI)
    return _ocr_pages(pages)


def ocr_pdf_path(filepath: str) -> str:
    """OCR every page of a PDF on disk (used for training data)."""
    pages = convert_from_path(filepath, dpi=OCR_DPI)
    return _ocr_pages(pages)


def _ocr_pages(pages) -> str:
    texts = []
    for i, page_image in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page_image)
        texts.append(text)
    return "\n".join(texts)
