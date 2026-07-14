"""Ingestion: load PDF/TXT/DOCX files and split them into overlapping chunks.

Uses LangChain document loaders (one per file type) plus a single
RecursiveCharacterTextSplitter, so every source ends up as a list of
`Document` objects: small pieces of text carrying {"filename", "chunk_id"}
metadata. That metadata is what later lets the app cite "which document and
chunk" an answer came from.
"""

import tempfile
from pathlib import Path
from typing import BinaryIO, List

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configurable chunking constants (characters, not tokens).
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 100

_SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


class IngestionError(Exception):
    """Raised when a document cannot be loaded or produces no usable text."""


def _load_raw_documents(path: Path, extension: str) -> List[Document]:
    """Pick the right LangChain loader for `extension` and load `path`.

    Args:
        path: Path to the file on disk.
        extension: Lowercase file extension, e.g. ".pdf".

    Returns:
        The loader's raw Documents (one per page for PDF, one per file for
        TXT/DOCX) before chunking.

    Raises:
        IngestionError: If the extension is unsupported or loading fails.
    """
    try:
        if extension == ".pdf":
            return PyPDFLoader(str(path)).load()
        if extension == ".txt":
            try:
                return TextLoader(str(path), encoding="utf-8").load()
            except UnicodeDecodeError:
                return TextLoader(str(path), encoding="latin-1").load()
        if extension == ".docx":
            return Docx2txtLoader(str(path)).load()
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(f"Could not read {extension} file: {exc}") from exc

    raise IngestionError(f"Unsupported file type: {extension} (use PDF, TXT, or DOCX).")


def load_and_chunk_file(path: Path, display_name: str) -> List[Document]:
    """Load one document from disk and split it into chunks with metadata.

    Args:
        path: Path to the file on disk (may be a temp file).
        display_name: The name to store in each chunk's metadata (the
            original filename, which may differ from `path` for uploads).

    Returns:
        A list of Documents, each with metadata {"filename", "chunk_id"}.

    Raises:
        IngestionError: If loading fails or the file contains no usable text.
    """
    extension = Path(display_name).suffix.lower()
    raw_docs = _load_raw_documents(path, extension)

    full_text = "\n".join(doc.page_content for doc in raw_docs).strip()
    if not full_text:
        raise IngestionError(f"{display_name} contains no extractable text.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    pieces = splitter.split_text(full_text)

    return [
        Document(page_content=piece, metadata={"filename": display_name, "chunk_id": i})
        for i, piece in enumerate(pieces)
    ]


def load_and_chunk_upload(uploaded_file: BinaryIO, filename: str) -> List[Document]:
    """Load and chunk a Streamlit-uploaded file.

    LangChain's loaders read from a file path, so the in-memory upload is
    written to a temporary file first, then cleaned up afterward.

    Args:
        uploaded_file: A binary file-like object (e.g. a Streamlit UploadedFile).
        filename: The original file name, used to pick the loader and stored
            in chunk metadata.

    Returns:
        A list of Documents, each with metadata {"filename", "chunk_id"}.

    Raises:
        IngestionError: If loading fails or the file contains no usable text.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise IngestionError(f"Unsupported file type: {filename} (use PDF, TXT, or DOCX).")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = Path(tmp.name)

    try:
        return load_and_chunk_file(tmp_path, display_name=filename)
    finally:
        tmp_path.unlink(missing_ok=True)


def load_and_chunk_folder(folder: Path) -> List[Document]:
    """Load and chunk every supported file directly under `folder`.

    Used by the `reindex --rebuild` CLI command. Each file is handled
    independently: one bad file is skipped (with a printed warning) rather
    than aborting the whole rebuild.

    Args:
        folder: Directory containing PDF/TXT/DOCX files.

    Returns:
        The combined list of Documents from every file that loaded successfully.
    """
    all_chunks: List[Document] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            continue
        try:
            chunks = load_and_chunk_file(path, display_name=path.name)
        except IngestionError as exc:
            print(f"Skipped {path.name}: {exc}")
            continue
        all_chunks.extend(chunks)
        print(f"{path.name}: {len(chunks)} chunks")

    return all_chunks
