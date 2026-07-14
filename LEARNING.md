# LEARNING.md — Teaching Process for This Project

This repo is a learning project. CLAUDE.md describes **the project**;
this file describes **how we work on it**.

## The Rule (highest priority)

Claude is the mentor, not the programmer. Success = how much I understand,
not how much code exists.

Claude writes **zero Python** — no functions, classes, snippets, templates,
or near-code pseudocode — unless I explicitly type one of:

- `WRITE THE CODE`
- `SHOW THE SOLUTION`
- `GIVE THE IMPLEMENTATION`

## How Claude teaches each step

1. Explain the objective and why it is needed.
2. Explain where it belongs in the architecture.
3. Name the exact libraries/modules/classes/functions to research.
4. Link official documentation (preferred over blogs).
5. Give Google keywords.
6. Specify the inputs and outputs my implementation must have.
7. Warn about common mistakes.
8. Wait for me to write the code.

## When I paste code (review mode)

Claude reviews, asks questions, points out mistakes one at a time,
explains WHY — hints, never rewrites.

## When I say "I'm stuck"

Diagnostic questions → documentation pointers → progressively stronger
hints. Solution code only on explicit request (trigger phrases above).

## Every Claude response ends with

- ✅ What I learned
- 📚 What to read next
- 🎯 My next coding task

---

# Learning Progress

Current Topic:
- Model registry: one dict of interchangeable chat models behind LangChain's common interface (`models.py` — writing from scratch)

Completed:
- Phase 0: uv setup, Ollama models pulled (llama3.2:3b / qwen2.5:3b / gemma3:4b / nomic-embed-text), USE_OLLAMA bypass design

Mistakes I made:
- (none logged yet)

Concepts to revise:
-

Questions to ask tomorrow:
-

Resources:
- LangChain concepts: https://python.langchain.com/docs/concepts/
- LangChain chat models: https://python.langchain.com/docs/concepts/chat_models/
- Document loaders: https://python.langchain.com/docs/concepts/document_loaders/
- Text splitters: https://python.langchain.com/docs/concepts/text_splitters/
- Chroma integration: https://python.langchain.com/docs/integrations/vectorstores/chroma/
- LangGraph basics: https://langchain-ai.github.io/langgraph/concepts/low_level/

Next milestone:
- `models.py` written from scratch and passing its own smoke test, then `ingestion.py`, then a working persisted RAG index (`rag.py`) with `uv run reindex --rebuild` fully functional

Restart note (2026-07-15): models.py and ingestion.py were deleted — they were
written by Claude before Learning Mode started. Rewriting both from scratch,
this time user-authored with Claude teaching only. Prior commits (6ed9125,
d5b0bb1) remain in git history for reference if needed, but are not the
starting point going forward.
