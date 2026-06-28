"""
RecruitAI - PDF Parser
Extracts clean text from PDF resumes using PyMuPDF (fitz).
"""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFParser:
    """Extracts text content from PDF files using PyMuPDF.

    PyMuPDF provides fast, accurate text extraction and handles
    a wide variety of PDF layouts and encodings.
    """

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract and return clean text from a PDF file.

        Args:
            file_path: Absolute or relative path to the PDF file.

        Returns:
            Extracted text content as a single string.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            RuntimeError: If text extraction fails due to corruption or other errors.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(str(path))
            text_parts: list[str] = []

            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text)
                    logger.debug(
                        f"Extracted {len(page_text)} chars from page {page_num}"
                    )

            doc.close()

            full_text = "\n".join(text_parts).strip()

            if not full_text:
                logger.warning(f"No text could be extracted from PDF: {file_path}")
                return ""

            logger.info(
                f"Successfully extracted {len(full_text)} characters "
                f"from '{path.name}' ({len(text_parts)} pages)"
            )
            return full_text

        except fitz.FileDataError as e:
            logger.error(f"Invalid or corrupted PDF file: {file_path} — {e}")
            raise RuntimeError(f"Cannot read PDF file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse PDF '{file_path}': {e}")
            raise RuntimeError(f"PDF extraction failed: {e}") from e

    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str = "upload.pdf") -> str:
        """Extract text from raw PDF bytes (useful for in-memory files).

        Args:
            file_bytes: Raw bytes of the PDF file.
            filename: Display name for logging purposes.

        Returns:
            Extracted text content as a string.

        Raises:
            RuntimeError: If extraction fails.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_parts: list[str] = []

            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text)

            doc.close()

            full_text = "\n".join(text_parts).strip()
            logger.info(
                f"Extracted {len(full_text)} chars from in-memory PDF '{filename}'"
            )
            return full_text

        except Exception as e:
            logger.error(f"Failed to parse in-memory PDF '{filename}': {e}")
            raise RuntimeError(f"PDF extraction failed: {e}") from e
