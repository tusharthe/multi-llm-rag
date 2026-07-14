"""Streamlit UI for the RAG From Scratch project.

Flow: upload documents in the sidebar -> Build Index (extract, chunk, embed,
store) -> ask a question in the main area -> see a grounded answer with
inline [n] citations and an expandable Sources section.

Run with: streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

from chunker import chunk_text
from embedder import EmbeddingError, embed_texts
from generator import GenerationError, generate_answer
from ingest import ExtractionError, extract_text
from retriever import TOP_K, retrieve_top_k
from vector_store import VectorStore

load_dotenv()

st.set_page_config(page_title="RAG From Scratch", page_icon="📄", layout="wide")


def get_store() -> VectorStore:
    """Return the VectorStore from session state, loading from disk once.

    On the first run of a session, try to load a previously built index from
    the store/ folder so the app survives restarts without re-embedding.
    """
    if "store" not in st.session_state:
        st.session_state.store = VectorStore.load() or VectorStore()
    return st.session_state.store


def build_index(uploaded_files: list) -> None:
    """Extract, chunk, embed, and store every uploaded file.

    Each file is processed independently: if one fails (e.g. a scanned PDF
    with no text), the error is shown and the remaining files still go in.
    """
    store = get_store()
    already_indexed = {meta["filename"] for meta in store.metadata}
    total_new_chunks = 0

    for uploaded in uploaded_files:
        if uploaded.name in already_indexed:
            st.sidebar.info(f"{uploaded.name}: already in the index, skipped.")
            continue
        try:
            text = extract_text(uploaded, uploaded.name)
        except ExtractionError as exc:
            st.sidebar.error(f"{uploaded.name}: {exc}")
            continue

        chunks = chunk_text(text, uploaded.name)
        if not chunks:
            st.sidebar.warning(f"{uploaded.name}: no chunks produced, skipped.")
            continue

        try:
            with st.spinner(f"Embedding {len(chunks)} chunks from {uploaded.name}..."):
                embeddings = embed_texts([chunk["text"] for chunk in chunks])
        except EmbeddingError as exc:
            st.sidebar.error(f"{uploaded.name}: {exc}")
            continue

        store.add(embeddings, chunks)
        total_new_chunks += len(chunks)
        st.sidebar.success(f"{uploaded.name}: {len(chunks)} chunks indexed.")

    if total_new_chunks > 0:
        store.save()


def render_sidebar() -> None:
    """Sidebar: file uploader, Build Index, Clear Index, and index stats."""
    st.sidebar.header("📚 Documents")

    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF, TXT, or DOCX files",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
    )

    if st.sidebar.button("Build Index", type="primary", use_container_width=True):
        if uploaded_files:
            build_index(uploaded_files)
        else:
            st.sidebar.warning("Upload at least one file first.")

    if st.sidebar.button("Clear Index", use_container_width=True):
        VectorStore.clear()
        st.session_state.store = VectorStore()
        st.sidebar.info("Index cleared.")

    store = get_store()
    st.sidebar.divider()
    st.sidebar.subheader("Index stats")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Documents", store.num_documents)
    col2.metric("Chunks", len(store))


def render_main() -> None:
    """Main area: question input, answer with citations, sources section."""
    st.title("📄 Chat with Your Documents")
    st.caption(
        "A RAG pipeline built from scratch: chunking, embeddings, NumPy cosine "
        "similarity, and citation-grounded answers."
    )

    if not os.getenv("OPENAI_API_KEY"):
        st.warning(
            "OPENAI_API_KEY is not set. Copy `.env.example` to `.env` and add "
            "your key, then restart the app."
        )

    store = get_store()
    question = st.text_input("Ask a question about your documents:")

    if not question:
        return
    if len(store) == 0:
        st.info("The index is empty. Upload documents and click Build Index first.")
        return

    try:
        with st.spinner("Retrieving relevant chunks..."):
            chunks = retrieve_top_k(question, store, k=TOP_K)
        with st.spinner("Generating answer..."):
            answer = generate_answer(question, chunks)
    except (EmbeddingError, GenerationError) as exc:
        st.error(str(exc))
        return

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Sources")
    for i, chunk in enumerate(chunks, start=1):
        label = (
            f"[{i}] {chunk['filename']} — chunk {chunk['chunk_id']} "
            f"(similarity: {chunk['score']:.3f})"
        )
        with st.expander(label):
            st.write(chunk["text"])


def main() -> None:
    """Entry point: render sidebar and main area."""
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
