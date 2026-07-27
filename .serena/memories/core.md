Multi-LLM RAG — academic project (IIT Patna AI/ML), branch `multi-llm-rag`. Combines
from-scratch NumPy RAG (preserved on `main`, do not disturb) with this branch's
LangChain/LangGraph orchestration version. Full spec lives in project CLAUDE.md.

**HIGHEST PRIORITY**: this repo is developed in Learning Mode (LEARNING.md). Before
writing or editing any Python, read the mentor-mode rule in `mem:conventions` — an
agent must not write code unless the user types an explicit trigger phrase.

Source map (dependency order):
`models.py` (provider registry, USE_OLLAMA switch) → `ingestion.py` (load+chunk) →
`rag.py` (Chroma index/retriever) → `prompts.py` (grounding system prompt) →
`graph.py` (LangGraph parallel fan-out to models) → `chat_history.py` (per-chat JSON
persistence) → `app.py` (Streamlit UI — currently a near-empty stub, not yet built).
`reindex.py` = standalone CLI for index maintenance. `logger.py` = shared logger, used
project-wide instead of `print()`.

Details:
- Architecture / RAG+graph design decisions: `mem:architecture`
- Language/deps/build config: `mem:tech_stack`
- Commands to run things: `mem:suggested_commands`
- What "done" means for a task: `mem:task_completion`
- Code style + mentor-mode rule + known past mistakes: `mem:conventions`

Repo quirk: both `.venv` (uv-managed, active) and a stray `venv/` exist at repo root —
`venv/` is legacy, do not use or install into it.
