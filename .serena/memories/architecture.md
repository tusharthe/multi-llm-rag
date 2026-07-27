Pipeline: `ingestion.py` (load+chunk; chunk metadata `source` = bare filename via
`Path(path).name`, overwriting the loader's full-path key) → `rag.py` Chroma index
(`build_index` / `get_retriever` / `clear_index`, `TOP_K=4`) → `graph.py` LangGraph:
`retrieve` node stores RAW `Document` objects in state (not a formatted string, so the
Sources panel keeps chunk metadata) → parallel per-model nodes (fan-out via
`get_models()`, supports any 1-3 available subset) → `collect`. `format_context()` is
called exactly ONCE per model node (inside `run_model`), never in `retrieve`.

Parallel-write reducer: `RetrievalState.answers` is
`Annotated[Dict[str, str], operator.or_]` so concurrent node writes in the same
super-step merge instead of clobbering each other; each model node must return ONLY its
own delta `{"answers": {label: answer}}`, never `**state`. Per-model node functions are
built through a `make_node(label)` closure factory — a bare loop-variable closure would
hit Python's late-binding bug and every node would see the last label.

Per-chat Chroma collection design (decided 2026-07-25): one chat = one collection,
`collection_name=f"chat_{id}"`, sharing one persist directory. Isolation is structural
(chosen over metadata `where=` filtering, since one forgotten filter leaks another
chat's docs, and over per-persist-dir, which is wasteful). `collection_name` threads
through `build_index`/`get_retriever`/`clear_index`; `RetrievalState.collection` carries
it into `retrieve`, but `retrieve` does NOT echo it back into its returned delta
(read-only state keys stay out of node return values).

Chroma collection-name constraint (Chroma-enforced, confirmed live): 3-512 chars,
`[a-zA-Z0-9._-]` only, must start AND end alphanumeric — a leading/trailing `_` is
rejected. Any chat-id generator must respect this.

Two distinct "clear" operations with different blast radii — don't conflate them:
- Per-chat `clear_index` must call the public `vector_store.delete_collection()` (NOT
  `.client`, which doesn't exist — the private attr is `._client`) to drop ONE
  collection.
- Whole-store wipe (`shutil.rmtree` on `chroma_db/`) is `reindex.py --clear` only.

`reindex.py`'s default-collection rebuild walks `docs/` with `glob` (top-level only),
not `rglob`, so per-chat doc subfolders never get merged into the shared default
`COLLECTION_NAME="documents"` collection.

Reopening a persisted Chroma store MUST re-pass the same `embedding_function` used to
build it (the on-disk folder stores vectors, not the embedder) and the same
`collection_name`/`persist_directory` — mismatches fail SILENTLY (empty/wrong results,
no exception).

Retrieval mental model (useful when explaining to the user — don't re-derive from
scratch): the embedding model is the only component that understands meaning (text →
768-D coordinates, same frozen model applied at both index time and query time); Chroma
only measures distance between coordinates, blind to language; the LLMs never participate
in search, they only see the final top-k chunk text. A Chroma "Document" = one chunk, not
one file — retrieval returns the GLOBAL top-k across all ingested files' chunks, not a
per-file read. Semantic similarity can beat naive keyword overlap (e.g. "technologies and
frameworks" outscored a distractor chunk that merely shared the literal word "project")
— this is inherent to embedding-based search, not a bug; metadata filtering / re-ranking
/ query rewriting are explicitly out of scope for this project.
