
if __name__ == "__main__":
    from ingestion import load_and_split

from langchain_chroma import Chroma
from models import get_embeddings
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from logger import logger
from config import config as cfg


CHROMA_DIR = Path(__file__).parent / "chroma_db"
DOCS_DIR = Path(__file__).parent / "docs"


def build_index(chunks: list[Document], collection_name: str) -> Chroma:
    """Build and populate a Chroma vector store from document chunks."""

    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=collection_name,
        embedding_function=get_embeddings()
    )

    ids = vector_store.add_documents(documents=chunks)

    # Milestone at INFO; the per-chunk detail below is DEBUG-only noise.
    logger.info(
        "Indexed %d chunks into collection '%s'", len(chunks), collection_name
    )

    # One record per chunk (not three) so the file stays readable, and %.100s
    # truncates lazily -- nothing is formatted at all unless DEBUG is enabled.
    for doc_id, doc in zip(ids, chunks):
        logger.debug(
            "chunk id=%s meta=%s content=%.100s", doc_id, doc.metadata, doc.page_content
        )

    return vector_store


def get_retriever(collection_name: str, k: int | None = None) -> VectorStoreRetriever:
    """Return a retriever backed by the Chroma vector store."""
    if k is None:
        k = cfg.top_k  # live cfg so slider changes take effect without restart
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )

    return vector_store.as_retriever(
        search_kwargs={"k": k},
    )


def clear_index(collection_name: str) -> None:
    """Delete ONE Chroma collection by name (not the whole store).

    Scoped on purpose: with one collection per chat, wiping the entire
    persist directory (reindex --clear does that) would destroy every chat.
    """
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )

    vector_store.delete_collection()


if __name__ == "__main__":

    pdf_path = str(DOCS_DIR / "IIT Patna AIML Project Guidelines (1) (1).pdf")
    clear_index('chat_test')

    chunks = load_and_split(pdf_path)
    build_index(chunks, "chat_test")
    get_retriever("chat_test").invoke(
        "What are the tools used in the project 2?")
