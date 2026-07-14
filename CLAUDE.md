# CLAUDE.md — Multi-LLM RAG (Chat with Your Documents, Compared Across Models)

## Project Overview

Academic certification project (IIT Patna AI/ML). This is the **combination of
Project 1 + Project 2** from the guidelines PDF:

- **From Project 2 (RAG):** upload PDF/TXT/DOCX documents, chunk them, embed
  them, store vectors, retrieve top-k relevant chunks per question, and answer
  ONLY from those chunks with citations.
- **From Project 1 (Multi-LLM):** every question is answered by **multiple
  LLMs in parallel** (OpenAI + Anthropic + Google), shown **side-by-side**.
  The user can click **"Continue with this model"** to keep chatting with one
  chosen model only — each model keeps its own chat history.

One sentence pitch: *"Ask your documents a question, watch three LLMs answer
it from the same retrieved context side-by-side, pick the best one, and keep
talking to it."*

The from-scratch NumPy implementation of Project 2 lives on the `main`
branch. THIS branch intentionally uses **LangChain** (RAG plumbing) and
**LangGraph** (parallel fan-out to multiple LLMs) — the learning goal here is
orchestration frameworks, not re-implementing vector math.

## Tech Stack

- **Python 3.10+**
- **LangChain 1.x** (latest) — document loaders, text splitter, embeddings,
  vector store, retriever
- **LangGraph 1.x** — one graph: `retrieve` node → **3 parallel model nodes**
  → `collect` node (this is the "compare in parallel" requirement)
- **Chroma** (via `langchain-chroma`) — local persistent vector store in
  `./chroma_db/` (simple, no server)
- **Streamlit** — UI: uploader, side-by-side answer columns, continue-with-model chat
- **Models (cheap/fast tier, one per provider):**
  - OpenAI: `gpt-4o-mini` (`langchain-openai`) — also used for embeddings
    (`text-embedding-3-small`)
  - Anthropic: `claude-haiku-4-5` (`langchain-anthropic`)
  - Google: `gemini-2.5-flash` (`langchain-google-genai`)
- **python-dotenv** for API keys

Rules:
- If a provider's API key is missing, **skip that model gracefully** (show a
  note in the UI) — the app must work with 1, 2, or 3 keys.
- Keep it SIMPLE. No agents, no tools, no re-ranking, no streaming. The graph
  has exactly: retrieve → {openai, anthropic, google} in parallel → collect.

## Project Structure

```
├── app.py              # Streamlit UI (only file that imports streamlit)
├── ingestion.py        # load PDF/TXT/DOCX + split into chunks (LangChain loaders/splitter)
├── rag.py              # embeddings + Chroma vector store: build_index(), get_retriever(), clear_index()
├── models.py           # registry: {name: chat_model} for providers whose key exists
├── graph.py            # LangGraph graph: retrieve → parallel model nodes → collect
├── prompts.py          # grounded system prompt + context formatting with [1][2] citations
├── chroma_db/          # persisted Chroma store (gitignored)
├── requirements.txt
├── .env.example        # OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
├── .gitignore          # must include .env and chroma_db/
└── README.md
```

## Core Requirements

1. **Ingestion (Project 2):** multi-file Streamlit uploader for PDF/TXT/DOCX.
   Use LangChain loaders (`PyPDFLoader`, `TextLoader`, `Docx2txtLoader`).
   Per-file error handling — one bad file must not crash the batch.
2. **Chunking:** `RecursiveCharacterTextSplitter`, `chunk_size=500`,
   `chunk_overlap=100` (constants at top of `ingestion.py`). Each chunk keeps
   metadata: source filename + chunk index.
3. **Index:** `text-embedding-3-small` embeddings into Chroma, persisted to
   `./chroma_db/` so restarts don't re-embed. "Build Index" and "Clear Index"
   buttons + doc/chunk stats in the sidebar.
4. **Retrieval:** Chroma retriever, top k=4 chunks with similarity scores.
   Retrieval happens ONCE per question — all models get the SAME context
   (that's what makes the comparison fair).
5. **Parallel generation (Project 1, via LangGraph):** a LangGraph graph
   where the retrieve node fans out to one node per available model; nodes
   run in the same super-step (parallel). Collect node gathers
   `{model_name: answer}`.
6. **Grounding + citations (Project 2):** shared system prompt: answer ONLY
   from the numbered context chunks, cite inline as [1], [2]…, and if the
   answer is not in the context say exactly "I could not find this in the
   uploaded documents." Sources section under the answers shows filename,
   chunk index, and chunk text per citation number.
7. **Side-by-side UI (Project 1):** one column per model with the model's
   answer. Under each column: a "Continue with <model>" button.
8. **Continue mode (Project 1):** after choosing a model, the app switches to
   a normal chat with ONLY that model. Each model keeps its **own** chat
   history (`st.session_state`, keyed by model name). Follow-up questions
   still do RAG retrieval for context. A "Back to compare" button returns to
   side-by-side mode.

## Coding Conventions

- Beginner-readable, academic submission: small functions, docstrings, type hints.
- Every module importable on its own; Streamlit imports only in `app.py`.
- All API calls wrapped in try/except; errors shown in the UI per model/file,
  never a crash. One model failing must not hide the other models' answers.
- No hardcoded keys — `.env` only; warn in the UI which keys are missing.
- Constants (CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, model names) at the top of
  their modules.

## How to Run

```bash
python -m venv venv
venv\Scripts\activate           # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add whichever API keys you have
streamlit run app.py
```

## requirements.txt (target contents)

```
streamlit
langchain
langgraph
langchain-openai
langchain-anthropic
langchain-google-genai
langchain-chroma
langchain-community
pypdf
docx2txt
python-dotenv
```

## Testing / Verification

- Ingest one PDF, one TXT, one DOCX → chunk count > 0 for each; stats update.
- Ask a question answered in the docs → every available model answers with
  [n] citations pointing at the right file.
- Ask a question NOT in the docs → models reply "I could not find this in the
  uploaded documents."
- Verify parallelism: the three answers should arrive together (one graph
  invocation), not one-after-another sequentially.
- Click "Continue with <model>" → follow-up question goes only to that model;
  its history shows both turns. Switch models → separate history.
- Restart the app → Chroma index loads from `chroma_db/` without re-embedding.
- Remove one API key from `.env` → app still runs with the remaining models
  and shows a notice for the missing one.
- No secrets in the repo: `.env` and `chroma_db/` gitignored.

## Out of Scope (keep it simple)

- No agents, tool-calling, or MCP.
- No streaming responses, no async UI tricks beyond the LangGraph fan-out.
- No re-ranking, hybrid search, or query rewriting.
- No answer-quality judging/scoring between models — the human is the judge.
- No authentication, no multi-user support, no database beyond Chroma's files.
