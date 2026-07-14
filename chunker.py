"""Text chunking: split a document's text into small overlapping chunks.

Each chunk carries metadata (filename, chunk_id, text) so that answers can
later be traced back to the exact place they came from (citations).
"""

from typing import Dict, List, Union

# Configurable chunking constants (characters, not tokens).
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 100

# A chunk is a plain dict: {"filename": str, "chunk_id": int, "text": str}
Chunk = Dict[str, Union[str, int]]


def chunk_text(
    text: str,
    filename: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Chunk]:
    """Split text into overlapping chunks with metadata.

    The text is cut into windows of `chunk_size` characters; each new window
    starts `chunk_size - overlap` characters after the previous one, so
    consecutive chunks share `overlap` characters. Overlap prevents an idea
    from being split exactly at a chunk boundary and lost.

    Args:
        text: The full plain text of one document.
        filename: The source file name, stored in each chunk's metadata.
        chunk_size: Maximum characters per chunk.
        overlap: Characters shared between consecutive chunks.

    Returns:
        A list of chunk dicts: {"filename", "chunk_id", "text"}.

    Raises:
        ValueError: If overlap >= chunk_size (the window would never advance).
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    step = chunk_size - overlap
    chunks: List[Chunk] = []
    chunk_id = 0

    for start in range(0, len(text), step):
        piece = text[start : start + chunk_size].strip()
        if piece:  # skip pieces that are pure whitespace
            chunks.append({"filename": filename, "chunk_id": chunk_id, "text": piece})
            chunk_id += 1
        if start + chunk_size >= len(text):
            break  # this window already reached the end of the text

    return chunks
