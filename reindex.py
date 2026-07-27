"""Command-line tool to clear and (later) rebuild the Chroma vector index.

Run via uv:
    uv run reindex --clear            # delete the persisted index
    uv run reindex --rebuild          # re-embed docs/ into a fresh index
    uv run reindex --clear --rebuild  # wipe then rebuild (use after switching
                                      # USE_OLLAMA, since embedding dims differ)

Why this exists: switching the embedding backend (USE_OLLAMA true/false) changes
the vector dimension (nomic-embed-text = 768, text-embedding-3-small = 1536).
Chroma ties a collection to one dimension, so the index must be cleared and
rebuilt when you flip the switch. This command makes that a one-liner instead
of clicking through the Streamlit UI.

--rebuild loads every supported file sitting DIRECTLY in docs/ (not in chat
subfolders) through ingestion.load_and_split (load + normalize + chunk) and
embeds the chunks via rag.build_index into the single default collection.

Scope note: with the Streamlit app, each chat owns its own docs/<chat_id>/
folder and its own Chroma collection, and the UI manages those. This CLI is a
developer convenience for the shared default collection only -- e.g. rebuilding
after flipping USE_OLLAMA. It deliberately ignores per-chat subfolders so it
never merges different chats' documents into one collection.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Where the persisted Chroma store lives (kept in sync with rag.py later).
CHROMA_DIR = Path(__file__).parent / "chroma_db"
# Folder the rebuild step will read source documents from.
DOCS_DIR = Path(__file__).parent / "docs"


def clear_index() -> None:
    """Delete the persisted Chroma index directory, if it exists."""
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        print(f"Cleared index: removed {CHROMA_DIR}")
    else:
        print(f"Nothing to clear: {CHROMA_DIR} does not exist")


def rebuild_index() -> None:
    """Re-embed supported documents in the top level of docs/ into the default collection.

    Files inside chat subfolders (docs/<chat_id>/) are intentionally skipped --
    those belong to per-chat collections the UI manages, and merging them here
    would break chat isolation.
    """
    # Deferred import (not at module top): ingestion pulls in heavy PDF/OCR
    # libraries, so importing lazily keeps plain `--clear` fast and dependency-
    # light. These modules now exist, so a real ImportError here is a genuine
    # bug and is deliberately NOT swallowed.
    from ingestion import load_and_split
    from rag import build_index, COLLECTION_NAME

    if not DOCS_DIR.exists() or not any(DOCS_DIR.iterdir()):
        print(
            f"No documents found in {DOCS_DIR}. Add PDF/TXT/DOCX files first.")
        return

    # load_and_split works on ONE file; walk docs/ and accumulate all chunks.
    # glob (not rglob): only files directly in docs/, so per-chat subfolders
    # are ignored. Per-file try/except so one bad file cannot abort the rebuild.
    supported_exts = (".txt", ".md", ".pdf", ".docx")
    chunks = []
    for path in sorted(DOCS_DIR.glob("*")):
        if path.is_file() and path.suffix.lower() in supported_exts:
            try:
                chunks.extend(load_and_split(str(path)))
            except Exception as e:
                print(f"Skipped {path.name}: {e}")

    if not chunks:
        print(f"No supported documents (PDF/TXT/DOCX/MD) found in {DOCS_DIR}.")
        return

    print(f"Rebuilding index from {DOCS_DIR} ...")
    build_index(chunks, collection_name=COLLECTION_NAME)
    print(f"Rebuilt index with {len(chunks)} chunks.")


def main() -> None:
    """Parse arguments and run the requested index operations."""
    parser = argparse.ArgumentParser(
        prog="reindex",
        description="Clear and/or rebuild the Chroma vector index.",
    )
    parser.add_argument(
        "--clear", action="store_true", help="Delete the persisted index."
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Re-embed docs/ into a fresh index.",
    )
    args = parser.parse_args()

    if not args.clear and not args.rebuild:
        parser.print_help()
        sys.exit(1)

    # Clear before rebuild so a flipped USE_OLLAMA gets a clean, correctly-sized store.
    if args.clear:
        clear_index()
    if args.rebuild:
        rebuild_index()


if __name__ == "__main__":
    main()
