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
- BACKEND WIRING, in progress (2026-08-16). Continue-mode (`app_pages/current_chat.py`)
  is now calling `graph.py` end-to-end instead of sitting UI-only:
  1. DONE — `graph.py` router fixed. `model_router` returns a plain list of
     target node names (`["gemini_node"]` or all three); `add_conditional_edges`
     is called in its 2-arg form (no branch-map dict). Earlier attempt to keep
     a dict like `{"All": [...], "Gemini": "gemini_node"}` crashed with
     `TypeError: unhashable type: 'list'` — a list can be a dict VALUE but
     never a dict KEY, and the router was accidentally being asked to act as
     both the key-picker and the fan-out list-builder at once.
  2. DONE — `process_text()` in `current_chat.py` now branches Arena
     (`active_model is None` -> `graph.invoke` with no `active_model` key ->
     router fans out to all 3) vs Continue (`active_model` set -> passed into
     `graph.invoke` -> router narrows to 1 node) instead of manually calling
     `models.py`/`rag.py` from the UI layer. Decision: orchestration stays
     centralized in `graph.py`; UI only ever calls `graph.invoke`.
  3. DONE — empty/whitespace-only `prompt.text` no longer reaches
     `process_text` (chat_input can return a truthy object with `.text == ""`
     during a file-only submission — same gotcha logged below for
     `ChatInputValue`).
  4. DONE — `process_text` stale-variable bug fixed. The function now reads
     `active_model = chat.get_active_model(chat_id)` ONCE, freshly, at call
     time (line ~244) and branches on that value. The module-level
     `active_model` global (page-render time) is only used for DISPLAY, never
     for branching. Lesson re-confirmed: when two variables are "supposed to
     mean the same thing", they will drift — fetch once, use that.
  5. DONE — casing bug fixed. The answer-match loop now compares
     `m.lower() == active_model.lower()`. Also added a `break` on match and a
     post-loop `if ans is None: logger.warning(...)` guard — the first draft
     put the warning in an `else` on the match (fired for every non-matching
     model = false warnings); moved OUTSIDE the loop so it logs once only when
     no model matched. Lesson: a "not found" check belongs after the search,
     not as an `else` inside it. Debug `print()`s replaced with a single
     `logger.debug("process_text | chat_id=%s active_model=%s", ...)`.
  6. NOTED, not a code bug — `cudaMalloc failed: out of memory` from
     `llama-server` (Ollama) is a VRAM capacity issue, not an app bug. Fix by
     freeing GPU memory, using a smaller local model, or accepting CPU
     fallback — see `AGENTS.md`.
  7. REVIEWED (no changes yet) — `app_pages/arena.py` shell works (columns,
     Mark/Continue buttons, Reset) but the chat_input still shows
     "comparison graph is not wired up yet" — NO `graph.invoke` call. This is
     the biggest remaining gap in the core loop: Arena displays past answers
     but cannot generate new ones.
  8. DESIGN DECISION (mark as preferred, CLAUDE.md §10) — settled on **Option C**:
     stamp a shared `turn_id` (uuid hex) into EVERY dict written by
     `record_compare_turn` (shared user turn + all assistant turns), and keep
     a top-level `preferences: {turn_id: model_label}` dict in the chat record.
     Rationale: "preferred" is a property of the turn, but the turn currently
     has no identity of its own (`created_at` collides within the same second,
     already logged as a mistake). `turn_id` gives stable per-turn identity.
     Open sub-decisions for next session: (a) where `arena.py` gets the
     `turn_id` at click-time (hold latest turn_id in session_state AND record);
     (b) backward compat with old JSON lacking `turn_id`/`preferences` (fall
     back to current `answers[-1]` reading, or accept no stars on old chats);
     (c) unmarking semantics — `preferences.pop(turn_id)` vs strict one-per-turn.
NEXT SESSION: (1) wire Arena chat_input -> graph.invoke -> record_compare_turn
  (needs `record_compare_turn` to RETURN the turn_id), then (2) implement
  `mark_preferred` per Option C. Earlier open UI-polish items (History buttons,
  scroll container, Export removal) remain pending underneath.

Second topic (2026-08-16, after the above): Arena preference feature COMPLETE,
then a MAJOR UX redesign was agreed. Full state of what happened:
  9. DONE — Arena chat_input wired (`arena.py:159-165`): graph.invoke with no
     `active_model` -> all 3 models -> record_compare_turn. The toast is gone.
  10. DONE — preference UI in `arena.py`: `is_preferred = (pref == label)` where
     `pref = preferences.get(turn_id)` (KEY = turn_id, VALUE = label — turn_id
     is the shelf, label is what sits on it); toggle-off via `preferences.pop`;
     "predates preference tracking" warning when `turn_id` is None; Reset wipes
     `preferences = {}` AND saves. Old chats fall back gracefully via
     `answers[-1].get("turn_id")`.
  11. DONE — `record_compare_turn` (`chat_history.py:144`) now stamps ONE
     `turn_id` (uuid4, generated BEFORE the loop) into BOTH the user and
     assistant dicts of every model — same pattern as `record_continue_turn`.
     The one-id-outside-the-loop placement is what makes all 3 models share
     the value (an id generated inside the loop would give each model its own
     id and break turn grouping). `preferences` dict initialized via
     `record.setdefault`. Return value is still `record` — callers re-read
     history after `st.rerun()`, so nothing needs the `turn_id` returned.
  12. DESIGN DECISION — the three-timeline model (each model = own history,
     Arena shows per-model last answer) was REJECTED as UX. Agreed redesign:
     **one continuous merged conversation, multiple voices**.
     a. MERGED TRANSCRIPT — current_chat renders ALL models' turns grouped by
        turn_id, sorted by created_at; user question appears ONCE per group
        (dedupe: compare turns duplicate the user turn 3x); each answer bubble
        shows which model wrote it. Switching models = just "who answered next".
     b. COMPARE RE-RUN — clicking "Compare" re-answers the LAST question with
        all 3 models ONLY IF the last turn isn't shared (no wasted LLM calls).
        Decided: NO duplicate — replace/remove the single-model turn so the
        question appears once, with 3 answers.
     c. PILL-ROUTING — each answer's model pill becomes clickable:
        `set_active_model` = "next question voiced by X"; also an "All 3" route
        to send the next question to compare mode. Arena becomes a pure
        compare-viewer; routing happens from the transcript.
     d. ACTIVE_MODEL stays meaningful as "which model answers the NEXT chat
        question" — not "which timeline to show".
  13. NOTED — Arena columns each read `answers[-1]` of their own history, so a
     Gemini-only continue turn makes Arena show Gemini's newer answer next to
     OpenAI/Anthropic's stale ones. Option B (find latest turn_id present in
     ALL models) fixes the header/column misalignment; superseded by the
     merged-transcript redesign + Compare re-run, which keeps things aligned
     by construction. Revisit if misalignment resurfaces.
  NEXT SESSION ORDER: (0) DONE — stamp turn_id in record_compare_turn,
  (1) DONE — `group_turn_ids(record)` merged-transcript helper added to
  `chat_history.py` (~line 95): one timeline across ALL models, grouped by
  turn_id; each group = {turn_id, created_at, query, answers: {model: text}};
  legacy chats (no turn_id) get a synthetic key
  `legacy:{role}:{created_at}:{content}` so nothing crashes; sorted by
  created_at (stable sort keeps insertion order on same-second ties).
  (2) render merged transcript in current_chat.py (replace
  `turns = histories.get(active_model, [])` at line 77), (3) pill routing +
  "All 3", (4) Compare re-run with no-duplicate replacement. UI-polish
  leftovers (History buttons, scroll, Export) still pending.

  Previous topic (UI POLISH PASS, 2026-07-28) below �?" items 3/4/5 there
  (History page button width, current_chat scroll container, Export button
  removal) are still open and unblocked by this session's work.

Previous Topic:
- UI POLISH PASS, in progress (2026-07-28). The app_pages/ shell renders but is
  not wired to the backend yet; before wiring, six layout/state fixes:
  1. DONE — "Recent chats" removed from the sidebar (History page covers it).
     `_render_chat_list`, `MAX_SIDEBAR_CHATS`, the now-dead `_relative_time` /
     `_truncate` helpers and the `st-key-chat_on_` CSS rule all swept.
  2. DONE — knowledge-source uploader gated on `active_key in ("chat","arena")`;
     `render_sidebar` still returns `uploads` (`[]` on other pages).
     `_render_footer()` moved INSIDE `_render_knowledge_source` so index status
     only shows where indexing is possible.
  3. TODO — History page Open/Delete buttons too wide (`history.py:126-142`).
     They pass `width="stretch"`, but 1.60's button default is ALREADY
     `"content"` — just drop the arg. `st.container(horizontal=True)` can put
     them side by side without nesting more columns.
  4. TODO — current_chat.py: middle column should scroll, sidebar + Model Config
     stay put. Use `st.container(height=..., autoscroll=True)` around the
     transcript loop; once the middle stops growing the page, the side panels
     stay put on their own (no `position: sticky` needed). `height="stretch"`
     needs a BOUNDED parent or it degrades to content height.
  5. TODO — hide the Export button (`arena.py:52`, `current_chat.py:81`). Both
     sit in an `st.columns(2)` split — collapse the split too, don't leave an
     empty half.
  6. DONE-ish — "New chat" no longer creates a blank record on every click.
     Chose EMPTY-CHAT REUSE over true lazy creation: lazy creation would make
     `current_chat_id = None` a real state that all four pages must tolerate,
     for no visible benefit. REMAINING BUG: the emptiness test checks only
     `record["histories"]`, not `record["files"]` — so a chat with documents
     indexed but no question asked yet counts as "empty" and gets reused,
     silently inheriting a populated Chroma collection into what looks like a
     fresh chat. Also still open in sidebar.py: two `print()` calls that should
     be `logger` (the whole reason logger.py exists), an unused
     `from datetime import datetime`, a module docstring still advertising
     "recent chats", and a Build help string clipped to "…into this chat's."
- `st.chat_input(accept_file="multiple")` added to current_chat.py (2026-07-28)
  — NOT yet wired, and it changed the return type from `str` to
  `ChatInputValue`. Three consequences to handle when wiring: (a) pass
  `prompt.text` to `record_continue_turn`, never the object — it is not
  JSON-serialisable and `save_chat` would raise; (b) `if prompt:` now asks
  "does this mapping have keys", not "did the user type something" — a
  file-only submission is truthy with `prompt.text == ""`; (c) `prompt.files`
  are `UploadedFile` objects, same in-memory-vs-path gap as the sidebar
  uploader. OPEN DESIGN QUESTION: this is now a SECOND upload route alongside
  the sidebar panel — do both ingest (then the handler must be one shared
  function), or does one win?
- `logger.py` DONE (2026-07-25): shared `logging` logger (Laravel-style), UTF-8
  daily-rotating file in `logs/` (fixes Windows cp1252 crash structurally),
  `LOG_LEVEL` from `.env`, `propagate=False` + handler guard (Streamlit-safe),
  `daily_namer` → `logger-YYYY-MM-DD.log` (must be deterministic: `backupCount`
  re-runs it to find files to prune). All debug `print()`s across rag/graph/
  ingestion converted to level-appropriate `logger` calls; banner logs collapsed
  to one labelled record per event (parallel threads interleave). `logs/`
  gitignored.
- Backend refactor for per-chat collections DONE (2026-07-25): see
  "Per-chat collection architecture" under Concepts to revise. `rag.py`
  `COLLECTION_NAME="documents"` restored (kept only as the value the reindex
  CLI passes on purpose) and `clear_index` deletes one collection via
  `vector_store.delete_collection()`.
- `chat_history.py` DONE (2026-07-26): per-chat JSON persistence
  (`chats/{chat_id}.json`). `generate_chat_id`/`collection_name`/`chat_paths`/
  `build_empty_record`/`save_chat`/`new_chat`/`load_chat`/`list_chats`/
  `rename_chat`/`set_active_model`/`add_file_to_chat`/`delete_chat` plus the
  two turn-recording functions, all reviewed line-by-line. Turn schema locked:
  `histories: {model_label: [{role, content, created_at(isoformat)}, ...]}` —
  the SAME user-turn dict is duplicated into every model's own list (not
  stored once globally) because "Continue with `<model>`" replays only that
  model's list as self-contained context.
  - `record_compare_turn` / `record_continue_turn` both converged on
    `histories.setdefault(model, []).extend([...])` — the one safe pattern
    for "get-or-create a list value in a dict, then add to it."
  - Bugs caught in review (see Mistakes below): (1) first draft overwrote
    `histories` wholesale each turn — no append; (2) working draft forgot to
    call `save_chat` at all, so `record_compare_turn` mutated only the
    in-memory dict, nothing hit disk; (3) `record_continue_turn` draft mixed
    `dict.get(key, [])` (does NOT insert into the dict) with
    `dict.setdefault(key, []).append(data)`, which for an EXISTING key
    appended the list to itself — a circular reference that crashes
    `json.dumps` inside `save_chat`; (4) turn timestamps briefly used
    `strftime("%Y%m%d_%H%M%S")` while the record's top-level `created_at`/
    `updated_at` used `.isoformat()` — same field name, two formats, and the
    strftime version had no sub-second resolution (collision risk for two
    turns in the same second). Settled on `.isoformat()` everywhere.
  - Left as-is, not urgent: dead commented-out `append_message` block
    (~line 139) superseded by the two real recording functions; open design
    question of whether `record_continue_turn` setting `record["active_model"]
    = model` should instead delegate to the existing `set_active_model`
    helper, or stay self-contained as a safety net.
- Design scope EXPANDED (2026-07-26): a Stitch-generated mockup (exported to
  `Downloads/stitch_rag_hub_ai_interface/`, tokens in its `DESIGN.md`) is now
  the visual target — see "Visual Design Reference" in CLAUDE.md. Two
  decisions made explicit there: (1) Arena's auto "WINNER" badge → REJECTED,
  replaced with a human-clicked "mark preferred" flag (CLAUDE.md §10); (2) the
  mockup's Analytics Dashboard + Model Config panel (Temperature/Top-P/Max
  Tokens/Chunk Size) → ACCEPTED as new scope (CLAUDE.md §9, §11). CLAUDE.md's
  Out-of-Scope list and Testing/Verification section were updated to match —
  read CLAUDE.md directly for the current requirements, don't rely on this
  log entry once the checklist below is done and superseded.
- NEXT: `app.py` — Streamlit UI. Checklist (expanded from the original
  4-stage plan to match the design decisions above):
  1. Chat shell — sidebar from `list_chats()`, "New chat" button, session
     state holds only `current_chat_id` (everything else — active_model,
     histories, files — is re-read from the chat's JSON record via
     `load_chat`, not duplicated into `st.session_state`).
  2. Ingestion — per-chat `st.file_uploader`, save into that chat's
     `docs_dir` (`chat_paths(chat_id)["docs_dir"]`), `ingestion.load_and_split`
     per file wrapped in try/except (one bad file must not kill the batch),
     `rag.build_index(chunks, collection_name=chat_history.collection_name(chat_id))`,
     `add_file_to_chat` per filename, "Clear Index" → `rag.clear_index`. Chunk
     Size override (CLAUDE.md §2) belongs here — a per-chat build-time value,
     passed into `load_and_split`, not a live/retrieval-time setting.
  3. Compare mode / "Arena" (shown when `record["active_model"] is None`) —
     question input, `graph.invoke({"query": q, "collection": collection_name})`,
     `st.columns` (one per model in the returned `answers` dict), a
     "Continue with `<model>`" button per column → `set_active_model` +
     `st.rerun()`, a "Mark as preferred" control per column (CLAUDE.md §10 —
     plain flag on the turn record, no scoring logic), a Sources panel from
     `final_state["docs"]`, then `record_compare_turn`.
  4. Continue mode (shown when `active_model` is set) — replay
     `histories[active_model]` with `st.chat_message`, `st.chat_input` for
     follow-ups, still retrieves per CLAUDE.md #8 but only calls the ONE
     active model (open question: reuse the LangGraph `graph`, which is
     built for parallel fan-out, or call `rag.get_retriever` +
     `prompts.format_context` + one model directly for the single-model
     case?), `record_continue_turn`, "Back to compare" button →
     `set_active_model(chat_id, None)`.
  5. Model Config panel (CLAUDE.md §9) — Temperature/Top-P/Max Tokens
     sliders, session-level (not persisted per chat). Needs `models.py`
     changes first: `make_chat`/`get_models` don't take `top_p` yet, and
     `max_tokens` isn't wired to a per-call override today (it's a module
     constant `DEFAULT_NUM_PREDICT`).
  6. Analytics dashboard (CLAUDE.md §11) — new page, needs instrumentation
     added to `graph.py` (latency around `llm.invoke`, `usage_metadata` off
     the response) and a small stats log to aggregate from. Biggest unknown:
     exact stats-file shape isn't decided yet — deliberately left open in
     CLAUDE.md for whoever implements it.
  Build order still starts at (1)-(4) — (5)/(6) are additive and can come
  after the core loop works end-to-end once.
- `prompts.py` DONE (2026-07-23): SYSTEM_PROMPT (grounding + zero-hallucination + exact NOT_FOUND fallback) + NOT_FOUND constant + `format_context(docs) -> str` returning ONLY numbered `[1]…[k]` blocks (system prompt lives in graph.py as SystemMessage, not flattened here). Citation notation locked to plain `[1]` / `[1][3]` across block label, prompt rules, and future UI. Smoke test prints 4 numbered blocks.
- `graph.py` DONE (2026-07-24): LangGraph retrieve → fan-out to per-model nodes (parallel super-step) → collect, VERIFIED end-to-end. Key wins: `answers: Annotated[Dict[str,str], operator.or_]` reducer merges parallel writes (no clobber); nodes return ONLY their delta `{"answers": {label: answer}}` (never `**state`); dynamic node build by looping `get_models()` (any 1-3 subset, no KeyError); closure bound via `make_node(label)` factory to dodge late-binding bug; each node builds `[SystemMessage(SYSTEM_PROMPT), HumanMessage(format_context(docs)+query)]`; try/except INSIDE node isolates failures. retrieve stores RAW Documents (not formatted string) so Sources panel keeps metadata; format_context called ONCE (in run_model). Verified run: parallel answers merged, Gemini cited [1][2][3], others returned exact NOT_FOUND. GOTCHA: debug print() of PDF text crashes on Windows cp1252 console (● / zero-width space) — strip debug prints before app.py or streamlit node may crash.
- NEXT: `app.py` — Streamlit UI (uploader → build/clear index → ask → 3 side-by-side columns from graph.invoke's answers dict → Sources panel from state docs → Continue-with-model chat).

- `rag.py` DONE (2026-07-18): build_index / get_retriever / clear_index all verified end-to-end. Constants CHROMA_DIR, COLLECTION_NAME="documents", TOP_K=4. Smoke test clear→build→retrieve returns 4 distinct semantically-ranked chunks. Key lessons: reopening Chroma must re-pass embedding_function (folder stores vectors, not the embedder); collection_name/persist_directory are shared lookup keys that fail SILENTLY on mismatch; add_documents appends w/ random UUIDs so reruns duplicate → clear_index (guarded shutil.rmtree) is the reset; delete_collection vs rmtree trade-off (rmtree = dependency-free clean slate, kills orphans, survives USE_OLLAMA dim-flip).
- `ingestion.py` source fix DONE: metadata["source"] = Path(path).name (overwrite loader's full-path key, NOT a parallel file_path key; .name keeps extension vs .stem). Verified: retrieval source collapsed from full path to clean filename.
  - Small finish items STILL left: overlap default 255→200 (line 12), delete dead commented line 54, add docstrings + `-> list[Document]` hints, fix line 66 typo "ingrstion".
  - rag.py tidy item: line 56 __main__ still discards the retriever result — capture + print it.
- NEXT: `prompts.py` — grounded system prompt (answer ONLY from numbered chunks, cite [1][2], exact "I could not find this..." fallback) + context formatting.

Completed:
- Phase 0: uv setup, Ollama models pulled (llama3.2:3b / qwen2.5:3b / gemma3:4b / nomic-embed-text), USE_OLLAMA bypass design
- `models.py` DONE (2026-07-16): dual-mode registry (`get_models` + `get_embeddings` + `make_chat` factory), USE_OLLAMA bool switch, per-slot availability gate (returns any 1-3 subset), all 7 code-review findings closed. Smoke test: invoke returns AIMessage, embeddings len 768, blanking a var drops that provider without crashing.

Mistakes I made:
- `X if c else f()` stores the class instead of an instance in the true branch — surfaced as `invoke() missing 'input'` (my arg became `self`). Fix: decompose into a `make_chat` helper with a plain if/else.
- `return` inside a loop returns the first item, not a dict — need accumulator: init dict before loop, fill inside, return after.
- Availability gate must SKIP an unavailable provider (`if needed:`), not `raise` — raising crashes the whole registry and hides the working models.
- env vars are strings: `USE_OLLAMA is True` / `== 'true'` are fragile — normalize to a real bool once at the top.
- Two mode-specific dict shapes (string vs tuple) can't share one loop; use one uniform tuple table.
- `num_predict` is Ollama-only; cloud chat classes use `max_tokens` (and don't take `base_url`).
- `dict.get(key, [])` returns the default WITHOUT inserting it into the dict — if `key` already exists you get a reference to the real stored list (mutating it mutates the dict), but if `key` is missing you get an orphan list that goes nowhere when you mutate it. `dict.setdefault(key, [])` is the version that inserts-if-missing AND returns the (now real) list either way — that's the one to reach for when the plan is "get-or-create then mutate."
- Mixing the two in one function is worse than using either alone: `x = d.get(k, []); x.extend(...); d.setdefault(k, []).append(x)` — when `k` already existed, `x` and `d.setdefault(k, [])` are the SAME object, so `.append(x)` appends the list to itself, a circular reference. `json.dumps` (and anything else that walks the structure) crashes on that.
- A ternary is easy to wire BACKWARDS precisely because it reads like English but
  evaluates in a fixed order. Wrote `record = chat.new_chat() if not
  record.get("histories") else record` meaning "reuse the empty chat" — it did the
  exact opposite: clicking New chat on an empty chat spawned another blank one (the
  bug being fixed), and clicking it on a chat WITH history kept you in that chat, so
  a second chat could never be started. Defence: state the rule as a sentence first
  ("reuse when empty, create when not"), then read the ternary against it. Runtime
  test that catches it: click the button twice in a row and count the files.
- "Is this record empty?" is a question about the WHOLE record, not the one field you
  happened to look at. `histories` and `files` are two independent ways a chat becomes
  non-empty, and the `files`-only case is the dangerous one — it leaves no trace in
  the chat window, so a wrongly-reused chat looks fresh while sitting on a populated
  Chroma collection.
- A library object can be unsafe to `print`. `st.chat_input(accept_file=...)` returns
  `ChatInputValue`, a `@dataclass` whose `__getattribute__` deliberately raises for
  `audio` when `accept_audio=False` — but the generated `__repr__` touches every
  field, so repr/str/print/st.write/logging all explode. Through `logging` it appears
  as "Unable to print the message and arguments - possible formatting error", which
  points at the format string and NOT at the real cause. Rule of thumb: when logging
  blames formatting, suspect the OBJECT'S `__repr__`. Use `.to_dict()` / `.text`.
- A function silently doing nothing (no exception, no error) is the hardest bug class to catch by reading output — `.get()` swallowing a missing key produced no crash, just data that never reached disk. When a save/persist function "works" in manual testing, check the file on disk, not just the return value in memory.

Concepts to revise:

### How vector retrieval actually searches (2026-07-25) — verified live

Division of labour (only ONE part understands language):
- **Embedding model** (`nomic-embed-text` in dev) — the ONLY component that
  "knows" meaning. It converts text → 768 numbers. Its knowledge is frozen in
  trained weights, applied TWICE with the SAME model: once per chunk at index
  time, once per question at query time. There is NO synonym table or keyword
  map anywhere in the project — "tools ≈ libraries" is baked into the geometry
  (meaning became *position* in 768-D space, learned from billions of training
  sentences where those phrases shared contexts).
- **Chroma** — dumb arithmetic. Given two 768-number vectors it computes cosine
  distance. It never sees words, has no dictionary, understands nothing. Hand it
  random numbers and it measures those just as happily.
- **The LLMs** — NOT in the search loop at all. They only see the final top-k
  chunks as text, after retrieval already picked them.

Mental model: *the embedder is a translator (meaning → coordinates); Chroma is a
ruler (measures distance between coordinates). The ruler doesn't understand
language — it doesn't need to, the translator already folded meaning into the
numbers.*

Vocabulary trap: in Chroma a **"Document" = one CHUNK**, not one file. Upload 4
files → `load_and_split` makes many chunks (~1000 chars each) → ALL chunks live
in ONE collection. Retrieval searches the whole chunk pool across all 4 files at
once and returns the GLOBAL top-k=4 (could be 2 from file A, 1 from C, 1 from
D) — never file-by-file. "Search all four documents" means "pick the 4 best
matching pieces from all of them," NOT "read all four."

Semantic search returns the NEAREST chunks, not the CORRECT ones — live proof:
query "what tools are needed in the project" scored
  0.644  "technologies and frameworks..."  (right meaning, ZERO shared words ✓)
  0.597  "the project deadline is Friday"   (WRONG meaning, beat the answer!)
  0.557  "required libraries: Streamlit..." (the correct answer, only 3rd)
  0.308  "I ate a banana..."                (unrelated, far ✓)
The distractor won because it shared the surface word "project". This is WHY
"Project 2" can NOT act as a filter: the embedder squeezes the WHOLE sentence
into one point, so "Project 2" is just one ingredient blended in — it can't be
pulled back out as a hard rule. Fixing that needs metadata filtering /
re-ranking / query rewriting — all deliberately OUT OF SCOPE (keep it simple).

Parked lever (known, not acted on): `nomic-embed-text` was trained to expect
task prefixes `search_query:` on questions and `search_document:` on chunks.
LangChain's `OllamaEmbeddings` doesn't add them by default, which compresses the
scores and lets distractors creep up. Adding prefixes is a cheap future
retrieval-quality win, but it's an enhancement beyond the simple brief.

### Per-chat collection architecture (decided 2026-07-25)
- One CHAT = one Chroma **collection** (`collection_name="chat_<id>"`, shared
  persist dir). Isolation is structural — other chats' collections are never
  queried. Chosen over metadata filtering (one forgotten `where=` leaks another
  chat's docs) and over per-persist-directory (wasteful).
- `rag.py` now threads `collection_name` through `build_index`/`get_retriever`/
  `clear_index`; `graph.py` carries `collection` in `RetrievalState` and
  `retrieve` passes it to `get_retriever` (but does NOT echo it back in the
  delta — read-only keys stay out of the return).
- `clear_index` must delete ONE collection (`vector_store.delete_collection()`,
  the public method — NOT `.client`, which doesn't exist; the private attr is
  `._client`). It must NEVER `rmtree` the whole store — that's `reindex --clear`
  only. Two jobs, two blast radii.
- Chat-id / collection-name rules (Chroma-enforced, seen live): 3–512 chars,
  only `[a-zA-Z0-9._-]`, must START and END alphanumeric. `chat_20260725_a3f9b1`
  is safe; leading/trailing `_` (e.g. `__attrcheck__`) is REJECTED.
- `reindex.py` uses `glob` (top-level of docs/ only, NOT `rglob`) so it never
  merges per-chat subfolders into the default collection; it re-adds the
  `build_index(chunks, collection_name=COLLECTION_NAME)` call.

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
