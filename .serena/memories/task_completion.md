No automated lint/format/test tooling is configured in this project (verified: no
ruff/pytest/mypy section in pyproject.toml). "Done" is manual smoke-testing, per
CLAUDE.md's Testing/Verification section:
- Ingest one PDF + one TXT + one DOCX → chunk count > 0 for each, sidebar stats update.
- Ask a question answered in the docs → every available model responds with `[n]`
  citations pointing at the correct source file.
- Ask a question NOT covered by the docs → models reply with the exact NOT_FOUND
  fallback string (see `prompts.py`), no hallucination.
- Confirm graph parallelism: all model answers arrive together from one
  `graph.invoke()` call, not sequentially.
- "Continue with `<model>`" → follow-up goes only to that model; its history is isolated
  per model (see per-chat design in `mem:architecture`); "Back to compare" restores
  side-by-side mode.
- Restart the app → Chroma loads from `chroma_db/` without re-embedding.
- Remove one API key from `.env` → app still runs with the remaining models and shows a
  notice for the missing one, no crash.

Historically each module also got its own standalone `if __name__ == "__main__":` smoke
test before being wired into the graph/app — check LEARNING.md's "Learning Progress" log
for the specific smoke test used per module (e.g. models.py: invoke returns AIMessage,
embeddings length 768, blanking an env var drops that provider without crashing).
