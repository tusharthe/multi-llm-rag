# Session Progress — RAG From Scratch (updated 2026-08-30, end of day)

Learning-project repo. Read CLAUDE.md, LEARNING.md (Current Topic), AGENTS.md before working.

## Where we are
Backend complete. Step 2 (merged transcript + sources) DONE and committed `e768fb4`. Step 3 (pill routing + All 3) and Step 4 (smart Compare + Arena pure viewer) DONE and tested, pending final commit. All redesign docs updated.

## DONE today (2026-08-30)
- `prompts.format_sources(docs)` added; `record_compare_turn`/`record_continue_turn` now accept `docs` and store `sources` on user turn; `group_turn_ids` carries `sources` per group.
- `current_chat.py`: merged transcript (`turn_groups = group_turn_ids(record)`), header "Next → {model} / All 3", Turns stat `len(turn_groups)`, user bubble `group["query"]` + per-model answer bubbles with correct `model` pill, pill-routing buttons `route_{turn_id}_{model}` → `set_active_model`, All 3 bar `route_all3` → `None`, smart Compare (check `expected=MODEL_LABELS ⊆ answers.keys()`, if not shared re-run graph all-3, `delete_turn` to avoid duplicate).
- `chat_history.py`: `group_turn_ids` full; `record_compare_turn` turn_id on both dicts + sources + preferences init; `record_continue_turn` docs + sources; `delete_turn(chat_id, turn_id)` removes turn from all models + preferences; legacy fallback via synthetic key.
- `app_pages/arena.py`: input now accepts files + passes `docs`; pure viewer via `group_turn_ids` → `last_shared` (latest turn where all 3 answered), aligned columns, preference stars keyed to `last_shared` turn_id.
- Tests: `e768fb4` step 2; post-commit tests for merged, arena viewer, smart Compare no-duplicate, pill routing, legacy fallback — all PASSED.
- Docs: LEARNING.md items 14-17, AGENTS.md Known Bugs + Redesign COMPLETE, CLAUDE.md §8.

## Remaining
- UI polish: History buttons width, scroll container, Export removal (LEARNING.md previous topic items 3/4/5).
- Analytics Dashboard (§11) not started; Model Config → backend plumbing (§9) pending.
- One open bug: Continue-mode `ans is None` when `active_model` unknown → `None` saved (AGENTS.md).

## Next session
- UI polish leftovers, then Analytics (§11) or Model Config wiring (§9) — pick one.
- No storage change: `histories: {model: [turns]}`; view merges via `group_turn_ids`.

## Commands
`uv sync` · `uv run streamlit run app.py` · `uv run reindex --clear --rebuild` after USE_OLLAMA flip. GPU OOM = VRAM issue, not code bug.
