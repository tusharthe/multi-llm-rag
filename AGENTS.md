# AGENTS.md — High-Signal Agent Instructions

## Development Workflow
- **Dependency Management:** Use `uv`. Run `uv sync` to install.
- **App Execution:** `uv run streamlit run app.py`.
- **Index Management:** Use `uv run reindex --clear --rebuild` to wipe and rebuild the Chroma index (essential when switching `USE_OLLAMA` mode).

## Core Architecture & Constraints
- **RAG Engine:** LangChain + Chroma. Per-chat isolation is achieved via unique Chroma **collections** (`collection_name="chat_<id>"`), NOT metadata filtering.
- **Orchestration:** LangGraph handles parallel model execution (Retrieve $\rightarrow$ Parallel LLMs $\rightarrow$ Collect).
- **Local Dev Mode:** Controlled by `USE_OLLAMA` in `.env`. Redirects cloud providers to local Ollama models.
- **Data Persistence:** Chat histories are stored as JSON in `chats/{chat_id}.json`. 
- **UI Framework:** Streamlit. 

## Critical Implementation Rules
- **Error Isolation:** LLM calls must be wrapped in `try/except`. A single model failing (e.g., API error or Ollama down) must **never** prevent other models from showing answers.
- **Grounding:** Models must answer **ONLY** using the provided context. Use specific fallback: *"I could not find this in the uploaded documents."*
- **Citation Format:** Use simple inline numbered citations like `[1]` or `[1][2]`.
- **No Code Policy:** This is a learning project. Do **NOT** write code unless the user explicitly triggers: `WRITE THE CODE`, `SHOW THE SOLUTION`, or `GIVE THE IMPLEMENTATION`.

## Environment & Setup
- **Required Env Vars:** `.env` must contain `USE_OLLAMA` and API keys (or Ollama model names).
- **Ollama Requirement:** If `USE_OLLAMA=true`, ensure Ollama is running and models (`nomic-embed-text`, `llama3.2:3b`, `qwen2.5:3b`, `gemma3:4b`) are pulled.
- **GPU OOM:** `cudaMalloc failed: out of memory` from `llama-server` means Ollama can't fit the model in VRAM — free GPU memory, use a smaller model, or accept CPU fallback. Not a code bug.

## Graph Routing Pattern (`graph.py`)
- **Router returns a list of node names directly**, e.g. `["gemini_node"]` or all three — NOT a dict-keyed branch map. `add_conditional_edges("retrieve", model_router)` is called with **no mapping dict** (2-arg form). This is intentional and correct for LangGraph when the router already returns valid node names.
- **Do NOT** try to route via a dict like `{"All": [...], "Gemini": "gemini_node"}` — a list value under a string key is fine, but returning a *list* as the router's own dict key crashes with `TypeError: unhashable type: 'list'`. Keep the router returning a plain list of target node names; skip the mapping dict entirely.
- **Single-model "Continue" calls MUST go through `graph.py`**, not `models.py`/`rag.py` directly from `app_pages/*.py`. Pass `active_model` in the state dict passed to `graph.invoke(...)`; the router fans out to 1 node instead of 3. Keeps orchestration centralized — UI/page code should never call `models.get_models()` or `rag.get_retriever()` on its own.

## Known Open Bugs (as of last session)
- `current_chat.py` Continue-mode edge case: if `active_model` names a model absent from `models.keys()` at runtime, the router returns `[END]`, `answers` is empty, the `ans is None` guard fires and `None` is saved to history. Consider skipping `record_continue_turn` entirely when `ans is None`.
- DONE (2026-08-16) — `record_compare_turn` now stamps ONE `turn_id` (uuid4, generated before the loop) into both the user and assistant dicts of every model; `preferences` dict initialized. Same pattern as `record_continue_turn`.

## Agreed UX Redesign (in progress — see LEARNING.md item 12)
- **Merged transcript:** current_chat renders ALL models' turns grouped by `turn_id` (user question ONCE per group), sorted by `created_at`, each answer tagged with its model. No more per-model timelines in the UI.
- **Compare re-run:** "Compare" button re-answers the LAST question with all 3 models ONLY IF the last turn isn't shared (avoid wasted LLM calls); NO duplicate question — replace the single-model turn.
- **Pill routing:** each answer's model pill is clickable → `set_active_model` = "next question voiced by X"; plus an "All 3" route back to compare. Arena becomes a pure compare-viewer.
- **`active_model` semantics:** means "which model answers the NEXT chat question", not "which timeline to show".
- Storage model UNCHANGED: `histories: {model: [turns]}` stays; only the VIEW merges.
