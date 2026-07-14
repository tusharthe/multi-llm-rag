"""Document ingestion: extract plain text from PDF, TXT, and DOCX files.

Each extractor takes a file-like object (as returned by Streamlit's file
uploader) and returns the extracted text as a single string. Errors are
raised as ExtractionError so the caller can handle them per file without
crashing the app.
"""

from io import BytesIO
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader


class ExtractionError(Exception):
    """Raised when text extraction from a document fails."""


def extract_text_from_pdf(file: BinaryIO) -> str:
    """Extract text from a PDF file using pypdf.

    Args:
        file: A binary file-like object containing the PDF.

    Returns:
        The concatenated text of all pages.

    Raises:
        ExtractionError: If the PDF cannot be read or contains no text.
    """
    try:
        reader = PdfReader(file)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
    except Exception as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc

    if not text:
        raise ExtractionError("PDF contains no extractable text (it may be scanned images).")
    return text


def extract_text_from_txt(file: BinaryIO) -> str:
    """Extract text from a plain-text file.

    Args:
        file: A binary file-like object containing the text file.

    Returns:
        The decoded text (UTF-8, falling back to Latin-1).

    Raises:
        ExtractionError: If the file cannot be decoded or is empty.
    """
    try:
        raw = file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        text = text.strip()
    except Exception as exc:
        raise ExtractionError(f"Could not read TXT: {exc}") from exc

    if not text:
        raise ExtractionError("TXT file is empty.")
    return text


def extract_text_from_docx(file: BinaryIO) -> str:
    """Extract text from a DOCX file using python-docx.

    Args:
        file: A binary file-like object containing the DOCX.

    Returns:
        The concatenated text of all paragraphs.

    Raises:
        ExtractionError: If the DOCX cannot be read or contains no text.
    """
    try:
        # python-docx needs a seekable stream; wrap the bytes to be safe.
        document = Document(BytesIO(file.read()))
        paragraphs = [para.text for para in document.paragraphs]
        text = "\n".join(paragraphs).strip()
    except Exception as exc:
        raise ExtractionError(f"Could not read DOCX: {exc}") from exc

    if not text:
        raise ExtractionError("DOCX contains no extractable text.")
    return text


def extract_text(file: BinaryIO, filename: str) -> str:
    """Dispatch to the right extractor based on the file extension.

    Args:
        file: A binary file-like object.
        filename: The original file name (used to pick the extractor).

    Returns:
        The extracted plain text.

    Raises:
        ExtractionError: If the extension is unsupported or extraction fails.
    """
    # Streamlit keeps uploaded files in memory across reruns; rewind so a
    # second "Build Index" click does not read from the end of the file.
    if hasattr(file, "seek"):
        file.seek(0)

    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return extract_text_from_pdf(file)
    if lowered.endswith(".txt"):
        return extract_text_from_txt(file)
    if lowered.endswith(".docx"):
        return extract_text_from_docx(file)
    raise ExtractionError(f"Unsupported file type: {filename} (use PDF, TXT, or DOCX).")
