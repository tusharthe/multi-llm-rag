Python >=3.10. Package manager: **uv** — `pyproject.toml` + `uv.lock` are the source of
truth; `requirements.txt` is only a stale mirror for non-uv users, don't hand-edit it as
if authoritative.

Key deps (see pyproject.toml for full list): streamlit, langchain, langgraph,
langchain-ollama/openai/anthropic/google-genai/chroma/community, pypdf, docx2txt,
pymupdf>=1.28 (PyMuPDFLoader), rapidocr + rapidocr-onnxruntime (image OCR for
scanned/table PDFs via RapidOCRBlobParser), ftfy, python-dotenv.

No linter, formatter, or test framework is configured anywhere in pyproject.toml —
verification is manual smoke-testing only, see `mem:task_completion`.

CLI packaging: `[project.scripts] reindex = "reindex:main"`, built via hatchling with
`only-include = ["reindex.py"]` (flat layout, not a package dir).

Vector store: Chroma persisted at `./chroma_db/`. Embedding dimension is tied to the
active embedder (768 for Ollama `nomic-embed-text` vs 1536 for OpenAI
`text-embedding-3-small`) — flipping `USE_OLLAMA` requires
`uv run reindex --clear --rebuild` or retrieval silently breaks.
