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
- Vector stores: embedding chunks into Chroma and querying them (`rag.py`)

Completed:
- Phase 0: uv setup, Ollama models pulled (llama3.2:3b / qwen2.5:3b / gemma3:4b / nomic-embed-text), USE_OLLAMA bypass design
- Concept: model registry pattern — one dict of interchangeable chat models behind LangChain's common interface (`models.py`, written by Claude pre-learning-mode; study it)
- Concept: Documents, loaders, RecursiveCharacterTextSplitter (`ingestion.py`, written by Claude pre-learning-mode; study it)

Mistakes I made:
- (none logged yet)

Concepts to revise:
- Why chunk overlap exists; why retrieval must happen once and be shared across models for a fair comparison

Questions to ask tomorrow:
-

Resources:
- LangChain concepts: https://python.langchain.com/docs/concepts/
- Chroma integration: https://python.langchain.com/docs/integrations/vectorstores/chroma/
- LangGraph basics: https://langchain-ai.github.io/langgraph/concepts/low_level/

Next milestone:
- Working persisted RAG index: build, query with scores, clear — and `uv run reindex --rebuild` fully functional
