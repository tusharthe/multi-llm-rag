"""Model settings -- provider availability and the shared generation params.

Generation parameters are session-level: one set applies to whichever models
get called, threaded through ``models.get_models()`` at call time. Chunk size
is different -- it is a per-chat BUILD-TIME value, since chunks are baked into
the stored vectors and cannot be changed retroactively.
"""

from __future__ import annotations

import streamlit as st

import chat_history as chat
from components import page_header, section_label
from theme import MODEL_IDS, avatar
from config import config as cfg

page_header("Model settings", "Providers, generation parameters and indexing.")

# models.py pulls in the LangChain provider packages; if one is missing the
# page should still render rather than blanking out with a traceback.
try:
    import models

    config_error = None
except Exception as exc:  # noqa: BLE001 - surfaced in the UI below
    models = None
    config_error = str(exc)

# ----------------------------------------------------------------- providers --

section_label("Providers")

if config_error:
    st.error(
        f"Could not load `models.py`: {config_error}",
        icon=":material/error:",
    )
else:
    use_ollama = cfg.use_ollama
    st.caption(
        "Running against local Ollama models (`USE_OLLAMA=true`)."
        if use_ollama
        else "Running against the cloud providers (`USE_OLLAMA=false`)."
    )

    columns = st.columns(3, gap="medium")

    for column, (label, (ollama_name, _cls, prod_model, api_key)) in zip(
        columns, models.model_list.items()
    ):
        backend = ollama_name if use_ollama else prod_model
        available = bool(ollama_name if use_ollama else api_key)

        with column:
            with st.container(border=True):
                st.html(
                    f"""
                    <div style="display:flex; align-items:center; gap:10px;">
                        {avatar(label)}
                        <div>
                            <p class="model-name">{label}</p>
                            <p class="model-id">{MODEL_IDS.get(label, "--")}</p>
                        </div>
                    </div>
                    """
                )

                if available:
                    st.badge("Configured", icon=":material/check:",
                             color="green")
                else:
                    st.badge("Not configured",
                             icon=":material/block:", color="gray")

                st.caption(f"Backend: `{backend or 'unset'}`")

    if not use_ollama:
        st.caption(
            "A provider without an API key is skipped — the app runs with "
            "whichever models remain."
        )

# ------------------------------------------------------ generation params ----

section_label("Generation parameters")
st.caption("Shared by every model call. Session-level, not saved per chat.")

with st.container(border=True):
    left, mid, right = st.columns(3, gap="medium")

    cfg.temperature = left.slider(
        "Temperature", 0.0, 1.0, value=cfg.temperature, key="temperature", step=0.05,
        help="Higher values make answers more varied.",
    )
    cfg.top_p = mid.slider(
        "Top-p", 0.0, 1.0, value=cfg.top_p, key="top_p", step=0.05,
        help="Nucleus sampling cutoff.",
    )
    cfg.num_predict = right.slider(
        "Max tokens", 128, 4096, value=cfg.num_predict, key="max_tokens", step=128,
        help="Upper bound on answer length.",
    )

# ------------------------------------------------------ retrieval settings ---

section_label("Retrieval and indexing")

chat_id = st.session_state.get("current_chat_id")
try:
    record = chat.load_chat(chat_id) if chat_id else {}
except (FileNotFoundError, ValueError):
    record = {}

has_index = bool(record.get("files"))

with st.container(border=True):
    left, right = st.columns(2, gap="medium")

    cfg.top_k = left.slider(
        "Retrieved chunks (k)", 1, 10, value=cfg.top_k, key="top_k",
        help="How many context chunks each model receives.",
    )
    cfg.chunk_size = right.slider(
        "Chunk size", 200, 2000, value=cfg.chunk_size, key="chunk_size", step=100,
        disabled=has_index,
        help=(
            "Applied when the index is built. Locked while this chat already "
            "has one — clear the index first."
        ),
    )

    if has_index:
        st.caption(
            f"This chat has {len(record['files'])} indexed file(s). "
            "Chunk size is baked into the stored vectors — use “Clear” in the "
            "sidebar, then rebuild, to change it."
        )

# ---------------------------------------------------------------- reindex ----

section_label("Index maintenance")

st.caption(
    "Switching `USE_OLLAMA` changes the embedding dimension "
    "(nomic-embed-text 768 vs text-embedding-3-small 1536), and a Chroma "
    "collection is tied to one dimension. After flipping the flag, rebuild:"
)
st.code("uv run reindex --clear --rebuild", language="bash")
