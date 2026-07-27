# CLAUDE.md — Multi-LLM RAG (Chat with Your Documents, Compared Across Models)

> **Working mode:** this is a learning project. See **LEARNING.md** — Claude
> mentors and reviews but writes NO code unless the user explicitly types
> `WRITE THE CODE`, `SHOW THE SOLUTION`, or `GIVE THE IMPLEMENTATION`.

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

## Visual Design Reference

UI target is a Stitch-generated mockup, exported to
`C:\Users\tkpar\Downloads\stitch_rag_hub_ai_interface\stitch_rag_hub_ai_interface\`
(4 screens as `code.html` + `screen.png` pairs, plus `rag_hub_core/DESIGN.md`
with the full token spec). Adopt the visual language; do NOT adopt every
screen 1:1 — some elements are out of scope, see below.

- **Palette/type:** warm off-white surfaces (`#fcf9f8`), primary red
  `#b7131a`/`#bb171c`, Inter for body/headings, Geist for labels/mono
  metadata. Full token list in `DESIGN.md` front matter.
- **Layout:** 3-panel — left sidebar 280px (nav + chat history + knowledge
  source uploader), fluid center (chat/compare), right config panel 320px.
  12px radius on cards/inputs/buttons, 16px on dashboard cards, pill radius
  on status badges/model tags only.
- **Screen → app mode mapping:**
  - "Main Chat" screen → Continue mode (§8)
  - "Multi-LLM Arena" screen → Compare mode (§7), MINUS the auto "WINNER"
    badge — see §10 below, that part of the mockup is not what we're building.
  - "Chat History" screen → the sidebar chat list (already required, §-none
    specifically but implied by `chat_history.list_chats`)
  - "Analytics Dashboard" screen → new, see §11 below.

## Core Requirements

1. **Ingestion (Project 2):** multi-file Streamlit uploader for PDF/TXT/DOCX.
   Use LangChain loaders: **`PyMuPDFLoader`** for PDF (with
   `extract_tables="markdown"` + `RapidOCRBlobParser` image OCR, so tabular /
   scanned documents like medical reports are captured), `TextLoader` for
   TXT/MD, `Docx2txtLoader` for DOCX. Per-file error handling — one bad file
   must not crash the batch.
2. **Chunking:** `RecursiveCharacterTextSplitter`, `chunk_size=1000`,
   `chunk_overlap=200` (constants at top of `ingestion.py`; env-overridable —
   these are the DEFAULTs). Larger chunks are deliberate — they keep
   medical-report tables intact rather than splitting a row's label from its
   value. Each chunk keeps metadata: source filename + chunk index.
   The Model Config panel (§9) additionally lets the user override chunk size
   PER CHAT at "Build Index" time — a per-chat BUILD-TIME parameter, not a
   retrieval-time or per-query setting. Changing it after a chat's index
   already exists requires "Clear Index" + rebuild, since chunks are baked
   into the stored vectors, not adjustable retroactively.
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
7. **Side-by-side UI / "Arena" (Project 1):** one column per model with the
   model's answer. Under each column: a "Continue with <model>" button. See
   §10 for the manual preference marker.
8. **Continue mode (Project 1):** after choosing a model, the app switches to
   a normal chat with ONLY that model. Each model keeps its **own** chat
   history, persisted per-chat in `chats/{chat_id}.json` via `chat_history.py`
   (`histories: {model_label: [turn, ...]}` — NOT `st.session_state`, which
   only holds the current `chat_id`; see `LEARNING.md` "Per-chat collection
   architecture"). Follow-up questions still do RAG retrieval for context. A
   "Back to compare" button returns to side-by-side mode.
9. **Generation parameters (Model Config panel):** Temperature, Top-P, and Max
   Tokens are user-adjustable via sidebar/config-panel sliders — one shared
   set of generation params applied to whichever model(s) get called, threaded
   through `models.get_models(temperature=..., top_p=..., max_tokens=...)`
   (Top-P and Max Tokens are new params `make_chat` doesn't take yet — Max
   Tokens already exists as `DEFAULT_NUM_PREDICT`/`max_tokens`, just not
   user-adjustable; Top-P needs adding). These are session-level, not
   persisted per chat (ephemeral like any other widget default). Chunk Size
   lives here too but behaves differently — see §2, it's a per-chat
   build-time value, not a live generation param.
10. **Manual preference marking (Arena):** after a compare turn, the user may
    click a "Mark as preferred" control on ONE answer column. This is a plain
    per-turn flag persisted in that turn's `chat_history` record — NOT an
    automated score, NOT LLM-as-judge, NOT a computed "winner." No ranking
    logic of any kind decides it; only a human click does. (The Stitch mockup's
    auto-assigned "WINNER" badge is explicitly NOT what we're building — see
    "Out of Scope.")
11. **Analytics dashboard (new page):** documents indexed, average latency,
    total queries, daily request volume, model-usage split, and
    top-queried-document stats — aggregated from lightweight per-turn
    instrumentation: latency measured around each `llm.invoke` call in
    `graph.py`, token counts read from each response's `usage_metadata` when
    the provider populates it (OpenAI/Anthropic/Gemini do via LangChain's
    standard usage metadata; Ollama may not — fall back to a placeholder like
    "—", never crash on a missing field). Stats live in a small local
    log/file the dashboard reads and aggregates — stays consistent with "no
    database beyond Chroma's files" (a flat JSON/JSONL stats file is fine; an
    actual DB engine is not). Exact stats-file shape and where it's written
    from is a design decision for whoever implements it — not fixed here.

## Coding Conventions

- Beginner-readable, academic submission: small functions, docstrings, type hints.
- Every module importable on its own; Streamlit imports only in `app.py`.
- All API calls wrapped in try/except; errors shown in the UI per model/file,
  never a crash. One model failing must not hide the other models' answers.
- No hardcoded keys — `.env` only; warn in the UI which models are unavailable
  (Ollama down, or a cloud key missing/unfunded).
- Constants (CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, model names) at the top of
  their modules.

## How to Run (uv)

Dependencies are managed by **uv** via `pyproject.toml` (not pip/requirements).

```bash
# 1. Ensure Ollama is running and models are pulled (see prerequisite above)
uv sync                         # create .venv and install everything
cp .env.example .env            # optional: add cloud keys / OLLAMA_BASE_URL
uv run streamlit run app.py     # launch the app
```

## Custom command: reindex

A small CLI (`reindex.py`, wired as a uv script in `pyproject.toml`) manages the
Chroma index outside the UI:

```bash
uv run reindex --clear              # delete the persisted index
uv run reindex --rebuild            # re-embed docs/ into a fresh index
uv run reindex --clear --rebuild    # wipe then rebuild
```

Why it matters: flipping `USE_OLLAMA` changes the embedding dimension
(nomic-embed-text = 768 vs text-embedding-3-small = 1536), and a Chroma
collection is tied to one dimension. After switching the flag you must
`--clear --rebuild`. (`--rebuild` is scaffolded now and becomes active once
ingestion.py + rag.py exist in Phase 2.)

## Dependencies

Full list in `pyproject.toml`. `pymupdf` powers `PyMuPDFLoader`;
`rapidocr-onnxruntime` powers `RapidOCRBlobParser` image OCR — both heavier
than plain `pypdf`, the deliberate cost of table/scan fidelity.
`requirements.txt` is kept only as a mirror for non-uv users; uv is the source
of truth.

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
- Drag the Temperature/Top-P/Max Tokens sliders → next generation call
  reflects the new values (check via `logger.debug` of the request, or by
  observing answer variability at high temperature).
- Change Chunk Size before "Build Index" on a chat with no index yet → new
  chunks reflect the override; changing it on an ALREADY-built chat should
  require "Clear Index" first (no silent partial-rebuild).
- Click "Mark as preferred" on one Arena column → persists in that turn's
  chat_history record; reloading the chat (or restarting the app) still shows
  the same preference. No other column's answer changes as a result.
- After a few turns across a couple of chats, open the Analytics Dashboard →
  document/query counts and latency reflect real activity, not mockup
  placeholders. A provider that omits `usage_metadata` (e.g. Ollama) shows a
  placeholder instead of crashing the page.

## Out of Scope (keep it simple)

- No agents, tool-calling, or MCP.
- No streaming responses, no async UI tricks beyond the LangGraph fan-out.
- No re-ranking, hybrid search, or query rewriting.
- No AUTOMATED answer-quality judging/scoring between models (no LLM-as-judge,
  no heuristic ranking, no computed "winner"). The human is the judge — the
  app only records which answer a human clicked as preferred (§10), it never
  decides that on its own.
- No authentication, no multi-user support, no database beyond Chroma's files.
