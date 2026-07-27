**Learning Mode — highest-priority rule (LEARNING.md)**: the assistant is a mentor, not
the programmer. Write **zero Python** — no functions, classes, snippets, or near-code
pseudocode — unless the user explicitly types one of: `WRITE THE CODE`,
`SHOW THE SOLUTION`, `GIVE THE IMPLEMENTATION`. Default teaching flow for a coding task:
explain the objective and why → where it fits in the architecture → exact
libraries/classes/functions to research → doc links + Google keywords → required
inputs/outputs → common mistakes to watch for → then wait for the user to write it. When
the user pastes code: review + ask questions + hint at mistakes one at a time (explain
WHY), never rewrite it for them. Every response ends with a ✅/📚/🎯 recap block (learned
/ read next / next task).

Code style: small functions, docstrings, type hints (beginner-readable, academic
submission target). Streamlit imports confined to `app.py`; every other module must be
importable standalone. All external calls (API, file I/O) wrapped in try/except and
surfaced per-model/per-file in the UI — one failure must never crash the whole
operation. Constants (CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, model names, COLLECTION_NAME)
live at the top of their owning module and are env-overridable.

Citation notation is locked to plain `[1]` / `[1][3]` (not `[1, 3]`, not footnotes) —
kept consistent across `format_context`, `SYSTEM_PROMPT`, and the UI.

GOTCHA: raw `print()` of document/PDF text can crash on Windows due to cp1252 console
encoding (e.g. bullet char, zero-width space). Always route debug/info output through
`logger.py` (UTF-8 file handler), never bare `print()` for anything that might contain
document text.

Past mistakes worth re-checking for in similar new code (from models.py review):
- `X if cond else f()` in an assignment can store a *class* instead of an *instance* in
  the true branch — surfaces as `invoke() missing 'input'`. Decompose into a real
  if/else (e.g. a `make_chat`-style helper) instead of a ternary for object construction.
- `return` inside a loop exits after the first iteration — build an accumulator dict
  before the loop, fill it inside, `return` only after the loop ends.
- Availability/feature gates must *skip* an unavailable item (`if needed: ...`), never
  `raise` — raising crashes the whole registry/graph and hides everything that *was*
  working.
- Env vars are always strings: normalize booleans like `USE_OLLAMA` to a real bool once,
  at the top of the module — don't compare `is True` / `== 'true'` ad hoc elsewhere.
- Ollama-specific kwargs (`num_predict`, `base_url`) have no equivalent on cloud chat
  classes (which use `max_tokens` and no `base_url`) — branch construction per mode
  rather than passing a shared kwargs dict.
