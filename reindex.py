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

NOTE: --rebuild is scaffolded but not yet functional. It becomes active once
ingestion.py and rag.py exist (Phase 2). Until then it prints a clear notice.
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
    """Re-embed every document in docs/ into a fresh Chroma index.

    Scaffold only: the real implementation will call ingestion + rag once those
    modules exist. For now it explains what it will do and exits cleanly.
    """
    try:
        # Deferred import: these modules do not exist yet (Phase 2). Importing
        # here (not at top) keeps `--clear` working before the pipeline lands.
        from ingestion import load_and_chunk  # noqa: F401
        from rag import build_index  # noqa: F401
    except ImportError:
        print(
            "Rebuild is not available yet.\n"
            "It will re-embed documents from the docs/ folder once the "
            "ingestion.py + rag.py pipeline is built (Phase 2).\n"
            "For now, use the Streamlit app to build the index, or run "
            "`uv run reindex --clear` to wipe it."
        )
        return

    # --- Active once the pipeline exists (Phase 2 will finish this) ---
    if not DOCS_DIR.exists() or not any(DOCS_DIR.iterdir()):
        print(f"No documents found in {DOCS_DIR}. Add PDF/TXT/DOCX files first.")
        return
    print(f"Rebuilding index from {DOCS_DIR} ...")
    chunks = load_and_chunk(DOCS_DIR)
    build_index(chunks)
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
        help="Re-embed docs/ into a fresh index (Phase 2 - not yet active).",
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
