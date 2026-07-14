# RAG From Scratch — Chat with Your Documents (with Citations)

An academic project (IIT Patna AI/ML Project 2) implementing the **full
Retrieval-Augmented Generation (RAG) pipeline from scratch** — no LangChain,
no LlamaIndex, no FAISS or any vector database. Every step is explicit and
readable:

1. **Ingest** — extract plain text from PDF / TXT / DOCX ([ingest.py](ingest.py))
2. **Chunk** — split text into ~500-character chunks with ~100-character overlap ([chunker.py](chunker.py))
3. **Embed** — batched calls to OpenAI `text-embedding-3-small` ([embedder.py](embedder.py))
4. **Store** — a hand-rolled vector store: NumPy matrix + JSON metadata ([vector_store.py](vector_store.py))
5. **Retrieve** — hand-written NumPy cosine similarity, top-k results ([retriever.py](retriever.py))
6. **Generate** — answer from ONLY the retrieved chunks, via `gpt-4o-mini` ([generator.py](generator.py))
7. **Cite** — the UI shows exactly which document and chunk each answer used ([app.py](app.py))

## Setup & Run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then add your OPENAI_API_KEY
streamlit run app.py
```

## How to Use

1. In the **sidebar**, upload one or more PDF / TXT / DOCX files.
2. Click **Build Index** — files are extracted, chunked, embedded, and saved
   to the `store/` folder (`embeddings.npy` + `metadata.json`).
3. In the **main area**, type a question. The app retrieves the top-4 most
   similar chunks (cosine similarity), sends only those to the model, and
   shows the answer with inline `[1]`, `[2]` citations.
4. Expand each entry under **Sources** to see the exact chunk text, its
   source file, chunk id, and similarity score.
5. The index persists on disk — restart the app and it loads without
   re-embedding. **Clear Index** deletes it.

## How Retrieval Works (the graded part)

Cosine similarity is written directly in NumPy in
[retriever.py](retriever.py):

```python
sim = (A @ q) / (norm(A, axis=1) * norm(q))
```

where `A` is the `(n_chunks, dim)` embedding matrix and `q` is the question
embedding. The top-k rows by score are the retrieved chunks.

## Grounding Guarantee

The system prompt forbids outside knowledge. If the answer is not in the
retrieved chunks, the model replies:

> I could not find this in the uploaded documents.

## Project Structure

```
├── app.py                 # Streamlit UI (main entry point)
├── ingest.py              # extract_text_from_pdf/txt/docx()
├── chunker.py             # chunk_text() — size + overlap based
├── embedder.py            # embed_texts() — batched embedding API calls
├── vector_store.py        # VectorStore (NumPy matrix + metadata list)
├── retriever.py           # cosine_similarity() + retrieve_top_k()
├── generator.py           # build_prompt() + generate_answer()
├── store/                 # persisted index (gitignored)
├── requirements.txt
├── .env.example           # OPENAI_API_KEY=
└── .gitignore
```

## Configuration

All knobs are constants at the top of their modules:

| Constant | Module | Default |
|---|---|---|
| `CHUNK_SIZE` | chunker.py | 500 characters |
| `CHUNK_OVERLAP` | chunker.py | 100 characters |
| `EMBED_MODEL` | embedder.py | `text-embedding-3-small` |
| `EMBED_BATCH_SIZE` | embedder.py | 100 texts per call |
| `TOP_K` | retriever.py | 4 chunks |
| `CHAT_MODEL` | generator.py | `gpt-4o-mini` |
