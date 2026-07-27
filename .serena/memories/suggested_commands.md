Windows dev machine, uv-managed project.

Setup / run:
```
uv sync                              # create .venv, install deps
uv run streamlit run app.py          # launch app
uv run reindex --clear               # wipe whole persisted index (reindex.py CLI)
uv run reindex --rebuild             # re-embed docs/ into a fresh index
uv run reindex --clear --rebuild     # wipe then rebuild
```

Local-dev bypass prerequisite (USE_OLLAMA=true in .env): Ollama server reachable at
`OLLAMA_BASE_URL` (default localhost:11434), with:
```
ollama pull nomic-embed-text   # embeddings
ollama pull llama3.2:3b        # OpenAI slot stand-in
ollama pull qwen2.5:3b         # Anthropic slot stand-in
ollama pull gemma3:4b          # Gemini slot stand-in
```

Shell: both Bash (git-bash) and PowerShell are available in this environment; no
unix-only lint/test tooling is installed. Prefer forward-slash paths.

Git: working branch is `multi-llm-rag`; `main` holds the from-scratch NumPy RAG
implementation and is treated as a separate, preserved deliverable — don't merge work
across them casually.
