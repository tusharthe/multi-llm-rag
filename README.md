# RAG From Scratch (Chat with Your Documents + Citations)

Ask questions over your own documents (PDF / TXT / DOCX / MD). Every question
is answered side-by-side by three models (OpenAI, Anthropic, Gemini) using
only the retrieved document chunks, with [1], [2] style citations pointing at
the source file and chunk. You can then keep chatting with whichever model you
prefer, or re-run a question as a three-way comparison. A history page keeps
past chats and an analytics page summarises usage and latency.

## Requirements

- Python 3.10+
- `uv` (recommended, install from https://docs.astral.sh/uv/) or plain `pip`
- Either local or cloud models (pick one in `.env`):
  - Local (free): Ollama running at http://localhost:11434 with the models
    listed in `.env.example` pulled (`nomic-embed-text` plus one chat model
    per provider slot).
  - Cloud: `USE_OLLAMA=false` plus funded `OPENAI_API_KEY`,
    `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY`.

## Setup and run

1. Copy `.env.example` to `.env` and edit it (choose Ollama or cloud keys).
2. Install dependencies: `uv sync` (or `pip install -r requirements.txt`).
3. Start the app: `uv run streamlit run app.py` (or `streamlit run app.py`).
4. Open http://localhost:8501 in a browser.

## How to use

1. A first chat is created automatically; rename it from the sidebar.
2. Upload one or more documents in the sidebar and click Build Index.
3. Type a question. Every available model answers from the same retrieved
   context; the cited sources are listed under the answers.
4. Click "Continue with ..." under an answer to keep chatting with that
   model, or Compare to re-answer the last question with all three.
5. After flipping `USE_OLLAMA`, the old index no longer matches (embeddings
   differ per backend), so clear and rebuild it first:
   `uv run reindex --clear --rebuild`.

## Notes

- `chats/`, `docs/`, `chroma_db/` and `logs/` are created automatically on
  first run and hold local state only; they are not part of the submission.
- Retrieval uses top-4 chunks shared by all models, so comparisons stay fair.
- If a model is unavailable (missing key, Ollama down) the app keeps working
  with the rest and says so in the UI instead of crashing.
