# Session Progress — RAG From Scratch (updated 2026-08-16, evening)

Learning-project repo. Read CLAUDE.md (project spec), LEARNING.md (teaching log — "Current Topic" first), AGENTS.md (agent instructions) before working.

## Where we are
Backend complete. Continue-mode wired end-to-end. Arena chat_input NOW wired to graph (`arena.py:159-165`). Arena preference UI COMPLETE (mark/toggle-off/reset, persists to record). All docs updated to match.

## DONE — record_compare_turn turn_id (step 0)
`record_compare_turn` now stamps ONE `turn_id` (uuid4, generated BEFORE the loop) into both user+assistant dicts of every model; `preferences` initialized via setdefault. Return value still `record` (callers re-read history after rerun).

## Agreed UX redesign (LEARNING.md item 12) — NOT yet implemented
The three-timeline model was REJECTED. Agreed: **one continuous merged conversation, multiple voices**:
1. **Merged transcript** — current_chat renders ALL models' turns grouped by turn_id, sorted by created_at, user question ONCE per group (dedupe: compare turns write the user turn 3×), each answer bubble tagged with its model. Storage stays `histories: {model: [turns]}` — only the VIEW merges.
2. **Compare re-run** — "Compare" button re-answers the LAST question with all 3 models ONLY IF last turn isn't shared; NO duplicate — replace the single-model turn.
3. **Pill routing** — each answer's model pill clickable → `set_active_model` = "next question voiced by X"; plus "All 3" route. Arena becomes pure compare-viewer.
4. `active_model` semantics = "which model answers the NEXT chat question", not "which timeline".

## Next session order
(0) DONE — turn_id stamped in record_compare_turn. (1) DONE — `group_turn_ids(record)` added to chat_history.py (~line 95): merges ALL models' turns into one timeline grouped by turn_id; each group = {turn_id, created_at, query, answers: {model: text}}; legacy fallback via synthetic key `legacy:{role}:{created_at}:{content}`; sorted by created_at. (2) render merged transcript in current_chat.py (replace `turns = histories.get(active_model, [])` at line 77) → (3) pill routing + "All 3" → (4) Compare re-run with no-duplicate replacement. UI-polish leftovers (History buttons, scroll container, Export removal) still pending.

## Key patterns to preserve
- Router returns plain LIST of node names; `add_conditional_edges("retrieve", model_router)` 2-arg form. Do NOT "fix" back to a dict (unhashable type: 'list' crash).
- UI pages call ONLY `graph.invoke`; never models.py/rag.py directly.
- `preferences[turn_id] = label` — turn_id is the key, label the value; one preference per turn.
- Old-chat fallback: use `.get("turn_id")` not `["turn_id"]` (KeyError on old JSON).

## Commands
`uv sync` · `uv run streamlit run app.py` · `uv run reindex --clear --rebuild` (after USE_OLLAMA flip). GPU OOM = VRAM issue, not code bug.