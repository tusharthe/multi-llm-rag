# CLAUDE.md — RAG From Scratch (Chat with Your Documents + Citations)

## Project Overview

This is an academic project (IIT Patna AI/ML Project 2). We are building a
document-based AI assistant implementing the **full RAG pipeline from scratch**
— no LangChain, no LlamaIndex, no FAISS/Chroma. The point of the project is to
show every step explicitly:

1. **Ingest** documents (PDF / TXT / DOCX)
2. **Chunk** text into small overlapping parts
3. **Create embeddings** for each chunk
4. **Store** vectors + metadata in a simple vector store (our own, NumPy + JSON)
5. **Retrieve** top-k relevant chunks for a question using **cosine similarity**
6. **Generate** an answer using ONLY the retrieved chunks
7. **Show citations** — which document and chunk each answer came from

## Tech Stack

- **Python 3.10+**
- **Streamlit** for the UI (upload docs, ask questions, see answer + citations)
- **pypdf** for PDF text extraction (per project brief; pymupdf is the allowed alternative)
- **python-docx** for DOCX extraction
- **NumPy** for all vector math (cosine similarity written by hand — this is graded)
- **OpenAI** API for embeddings (`text-embedding-3-small`) and answer generation (`gpt-4o-mini`)
- **python-dotenv** for the API key

Explicitly FORBIDDEN (defeats the purpose of "from scratch"):
- LangChain, LlamaIndex, Haystack
- FAISS, ChromaDB, Pinecone, Weaviate, or any vector database
- `sklearn.metrics.pairwise.cosine_similarity` — write it with NumPy directly

## Project Structure

```
rag-from-scratch/
├── app.py                 # Streamlit UI (main entry point)
├── ingest.py              # extract_text_from_pdf/txt/docx()
├── chunker.py             # chunk_text() — size + overlap based
├── embedder.py            # embed_texts() — batched calls to embedding API
├── vector_store.py        # VectorStore class (NumPy matrix + metadata list, saved to disk)
├── retriever.py           # cosine_similarity() + retrieve_top_k()
├── generator.py           # build_prompt() + generate_answer() with citation instructions
├── store/                 # persisted vector store (embeddings.npy + metadata.json)
├── requirements.txt
├── .env.example           # OPENAI_API_KEY=
├── .gitignore             # MUST include .env and store/
└── README.md
```

## Core Requirements (from the project brief)

1. **Ingestion:** user uploads one or more PDF/TXT/DOCX files via Streamlit
   file uploader. Extract plain text per file. Handle extraction errors per
   file without crashing.
2. **Chunking:** split text into chunks of ~500 characters with ~100 character
   overlap (make both constants configurable at the top of `chunker.py`).
   Each chunk gets metadata: `{"filename": str, "chunk_id": int, "text": str}`.
3. **Embeddings:** batch chunks (e.g., 100 per API call) into
   `text-embedding-3-small`. Store as a single NumPy array of shape
   `(n_chunks, dim)`.
4. **Vector store:** a small `VectorStore` class with `add()`, `save()`,
   `load()`, and `search()`. Persistence = `embeddings.npy` + `metadata.json`
   in the `store/` folder. Nothing fancier.
5. **Retrieval:** hand-written cosine similarity in NumPy:
   `sim = (A @ q) / (norm(A, axis=1) * norm(q))`. Return top-k (default k=4)
   chunks with their scores and metadata.
6. **Generation:** build a prompt that includes ONLY the retrieved chunks,
   numbered [1], [2], [3]... The system prompt must instruct the model:
   - Answer ONLY from the provided context
   - If the answer is not in the context, say "I could not find this in the
     uploaded documents" — do not use outside knowledge
   - Cite sources inline as [1], [2] etc.
7. **Citations UI:** below the answer, show an expandable section per cited
   chunk: filename, chunk_id, similarity score, and the chunk text itself.

## Coding Conventions

- Beginner-readable, academic submission: clear functions, docstrings, type hints.
- Every module must be importable and testable on its own (no Streamlit
  imports outside `app.py`).
- Wrap all API calls in try/except; surface errors in the UI, never crash.
- No hardcoded API keys — load from `.env`. If missing, show a clear warning.
- Constants (CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, EMBED_MODEL, CHAT_MODEL,
  EMBED_BATCH_SIZE) live at the top of their respective modules.

## How to Run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then add OPENAI_API_KEY
streamlit run app.py
```

## requirements.txt (target contents)

```
streamlit
openai
pypdf
python-docx
numpy
python-dotenv
```

## App Flow (Streamlit)

- **Sidebar:** file uploader (multiple files) + "Build Index" button +
  index stats (number of docs, number of chunks). Also a "Clear Index" button.
- **Main area:** question input → on submit: retrieve top-k → generate answer
  → display answer with inline [n] citations → expandable "Sources" section
  showing each cited chunk with filename, chunk_id, and similarity score.
- Keep the loaded VectorStore in `st.session_state` so it survives reruns;
  load from `store/` on startup if it exists.

## Testing / Verification

- Ingest at least: one PDF, one TXT, one DOCX. Chunk counts must be > 0 for each.
- Ask a question whose answer IS in the docs → answer must cite the correct file.
- Ask a question whose answer is NOT in the docs → app must say it could not
  find it (no hallucinated answer).
- `retriever.cosine_similarity` must return 1.0 (±1e-6) for a vector with itself.
- Restart the app → index loads from `store/` without re-embedding.
- No secrets in the repo: `.env` and `store/` are gitignored.

## Out of Scope

- No re-ranking, no hybrid search, no query rewriting (stretch goals only).
- No database beyond the npy/json files.
- No authentication, no multi-user support.
- No streaming responses.
