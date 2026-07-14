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
- **The three providers (what the brief requires, and what the UI always shows):**
  - **OpenAI** — `gpt-4o-mini` (`langchain-openai`)
  - **Anthropic** — `claude-haiku-4-5` (`langchain-anthropic`)
  - **Gemini** — `gemini-2.5-flash` (`langchain-google-genai`)
- **python-dotenv** — API keys + the dev-mode flag

### Local development bypass (KEY DESIGN POINT)

Real cloud API calls cost money and the user's OpenAI/Anthropic accounts are
unfunded. So the app has ONE switch, `USE_OLLAMA` in `.env`, that redirects
each provider slot to a local Ollama model for free offline development. The
UI still shows three columns labelled OpenAI / Anthropic / Gemini — only the
backend changes.

| UI column (fixed) | `USE_OLLAMA=false` (production) | `USE_OLLAMA=true` (local dev) |
|---|---|---|
| OpenAI · gpt-4o-mini | `ChatOpenAI` | Ollama `OLLAMA_OPENAI_MODEL` (default `llama3.2:3b`) |
| Anthropic · claude-haiku-4-5 | `ChatAnthropic` | Ollama `OLLAMA_ANTHROPIC_MODEL` (default `qwen2.5:3b`) |
| Gemini · gemini-2.5-flash | `ChatGoogleGenerativeAI` | Ollama `OLLAMA_GEMINI_MODEL` (default `gemma3:4b`) |
| Embeddings | OpenAI `text-embedding-3-small` | Ollama `nomic-embed-text` |

Rules for this switch:
- `USE_OLLAMA` is read once in `models.py`. In dev mode, each slot is a
  `ChatOllama(model=...)`; the three local model names are env-overridable so
  the user can map any locally-pulled model to a slot (must fit an 8 GB GPU).
- Distinct local models per slot keep the side-by-side comparison genuinely
  different while developing offline. All three are also used for embeddings
  choice as shown above.
- The provider labels shown to the user NEVER change with the switch — the
  academic deliverable is always "OpenAI + Anthropic + Gemini".

Rules (general):
- **Model registry is dynamic:** in production, include a provider only if its
  API key is set; in dev, include a local model only if the Ollama server is
  reachable. The app must work with any non-empty subset (1, 2, or 3 models).
- If a model fails at call time (Ollama down, billing 400/429, rate limit,
  timeout), the model node must catch it and return an error string for that
  column — the other models' answers must still show.
- Keep it SIMPLE. No agents, no tools, no re-ranking, no streaming. The graph
  has exactly: retrieve → {openai, anthropic, gemini} in parallel → collect.

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
├── .env.example        # optional cloud keys + optional OLLAMA_BASE_URL
├── .gitignore          # must include .env and chroma_db/
└── README.md
```

## Prerequisite for local dev (USE_OLLAMA=true): Ollama with models pulled

```bash
# Ollama must be installed and running (http://localhost:11434)
ollama pull nomic-embed-text    # embeddings
ollama pull llama3.2:3b         # OpenAI slot stand-in
ollama pull qwen2.5:3b          # Anthropic slot stand-in
ollama pull gemma3:4b           # Gemini slot stand-in
```

For production (`USE_OLLAMA=false`) Ollama is not needed — set the three cloud
API keys in `.env` instead.

## Core Requirements

1. **Ingestion (Project 2):** multi-file Streamlit uploader for PDF/TXT/DOCX.
   Use LangChain loaders (`PyPDFLoader`, `TextLoader`, `Docx2txtLoader`).
   Per-file error handling — one bad file must not crash the batch.
2. **Chunking:** `RecursiveCharacterTextSplitter`, `chunk_size=500`,
   `chunk_overlap=100` (constants at top of `ingestion.py`). Each chunk keeps
   metadata: source filename + chunk index.
3. **Index:** embeddings into Chroma (OpenAI `text-embedding-3-small` in prod,
   Ollama `nomic-embed-text` in dev — same `USE_OLLAMA` switch), persisted to
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
- No hardcoded keys — `.env` only; warn in the UI which models are unavailable
  (Ollama down, or a cloud key missing/unfunded).
- Constants (CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, model names) at the top of
  their modules.

## How to Run

```bash
# 1. Ensure Ollama is running and models are pulled (see prerequisite above)
python -m venv venv
venv\Scripts\activate           # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional: add cloud keys / OLLAMA_BASE_URL
streamlit run app.py
```

## requirements.txt (target contents)

```
streamlit
langchain
langgraph
langchain-ollama
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
