"""
Resume PDF -> raw text extraction.

We use pdfplumber because it preserves layout reasonably well for
resumes (columns, bullet points), which helps the LLM parser agent
downstream make sense of section boundaries.
"""
import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file, page by page.
    Raises ValueError if no extractable text is found (e.g. a scanned/image-only resume).
    """
    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned image without OCR — please upload a text-based PDF."
        )

    return full_text
