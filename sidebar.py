"""Shared left sidebar (280px panel) rendered on every page.

Rendered once per run from ``app.py`` -- before ``nav.run()`` -- so individual
pages never build their own sidebar.

Layout follows the Stitch mockup: brand block, new-chat action, menu nav,
recent chats, knowledge-source uploader and an index status footer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

import chat_history as chat
from logger import logger
from theme import brand_mark_data_uri, effective_theme, icon

#: (page key, label, material icon) -- page key matches the registry in app.py.
NAV_ITEMS = [
    ("chat", "Current chat", "forum"),
    ("arena", "Arena", "compare_arrows"),
    ("history", "History", "history"),
    ("analytics", "Analytics", "bar_chart"),
    ("settings", "Model settings", "tune"),
]


def _render_brand() -> None:
    st.sidebar.html(
        f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:18px;">
            <img src="{brand_mark_data_uri()}" width="40" height="40"
                 alt="RAG From Scratch logo"
                 style="border-radius:12px; display:block; flex:none;" />
            <div style="line-height:1.2;">
                <div style="font-size:13px; font-weight:800; color:var(--on-surface); letter-spacing:-0.02em;">RAG From Scratch</div>
                <div style="font-size:11px; font-weight:600; color:var(--on-surface);">Chat with Your Documents + Citations</div>
                <div style="font-family:'Geist Mono',monospace; font-size:9px; color:var(--muted); margin-top:1px;">Multi-LLM · Citations</div>
            </div>
        </div>
        """
    )


def _render_nav(pages: dict[str, Any], active_key: str) -> None:
    st.sidebar.html('<div class="section-label">Menu</div>')

    for key, label, material in NAV_ITEMS:
        # The `nav_on_` / `nav_off_` key prefix drives the active-item CSS in
        # assets/styles.css -- Streamlit buttons have no "selected" state, and
        # a key of `x` renders a wrapper with the class `st-key-x`.
        state = "on" if key == active_key else "off"
        clicked = st.sidebar.button(
            label,
            key=f"nav_{state}_{key}",
            icon=f":material/{material}:",
            type="tertiary",
            width="stretch",
        )
        if clicked and key != active_key:
            st.switch_page(pages[key])


def _render_knowledge_source() -> None:
    st.sidebar.html('<div class="section-label">Knowledge source</div>')

    # Ensure uploader_key exists
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = "uploader_0"

    uploads = st.sidebar.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
        key=st.session_state.uploader_key,
        label_visibility="collapsed",
        help="PDF, TXT, MD or DOCX — indexed per chat.",
    )

    def clear_submit():
        current_num = int(st.session_state.uploader_key.split("_")[-1])
        st.session_state.uploader_key = f"uploader_{current_num + 1}"

    build_col, clear_col = st.sidebar.columns(2)
    build_clicked = build_col.button(
        "Build",
        key="build_index",
        icon=":material/database:",
        type="primary",
        width="stretch",
        disabled=not uploads,
        help="Embed the staged files into this chat's.",
    )
    if build_clicked:
        current_files = st.session_state.get(st.session_state.uploader_key)
        if current_files:
            names = ", ".join(f.name for f in current_files)
            with st.spinner(f"Uploading and indexing {len(current_files)} file(s): {names}…"):
                st.session_state["upload_file_messages"] = chat.upload_file(
                    current_files, st.session_state["current_chat_id"])
            st.toast(f"Finished indexing {len(current_files)} file(s).", icon=":material/database:")
    clear_col.button(
        "Clear",
        key="clear_index",
        icon=":material/delete_sweep:",
        type="secondary",
        width="stretch",
        help="Just clear the input files from current uploader",
        on_click=clear_submit,
    )

    _render_footer()


def _render_footer() -> None:

    docs_count = 0
    chunks_count = 0

    st.sidebar.html(
        f"""
        <div style="margin-top:18px; padding-top:14px;
                    border-top:1px solid var(--surface-high);">
            <span class="pill pill-success">
                <span class="status-dot"></span> Index ready
            </span>
            <div style="font-family:'Geist Mono',monospace; font-size:10px;
                        color:var(--muted); margin-top:8px;">
                {icon("bolt", 12)} {docs_count} docs &nbsp;·&nbsp; {chunks_count} chunks
            </div>
        </div>
        """
    )

    with st.sidebar.expander("Guidelines & Terms", icon=":material/gavel:"):
        st.markdown(
            """
            **RAG From Scratch — Certification project (learning purpose only).**

            This is an academic / portfolio build (IIT Patna AI/ML). No SLA, no warranty, no guarantee of accuracy.

            **Be careful what you upload:**
            - Do **not** upload sensitive, confidential, or personally identifiable data (IDs, health records, financial docs, credentials). You are fully responsible for the files you upload.
            - Files are stored locally in `chats/{id}` and vectorized into `chroma_db/` on this machine. They are **not** encrypted at rest and are **not** backed up. Delete the chat to remove its files and vectors.
            - The app answers **only** from retrieved context and cites sources as [1], [2]… Always verify citations before acting on an answer — outputs can be incomplete or mis-cited.

            **Costs & privacy:**
            - With `USE_OLLAMA=true` everything runs locally via Ollama. With `USE_OLLAMA=false` your query + retrieved chunks are sent to OpenAI / Anthropic / Google per their terms.

            **Indexing:**
            - Chunk size is baked into the stored vectors. Change it in **Model settings** only when the chat has no index; otherwise use **Clear** in the sidebar, then rebuild. Flipping `USE_OLLAMA` changes embedding dimensions — run `uv run reindex --clear --rebuild`.

            *Use at your own risk. Authors are not liable for data loss or model output. For learning purposes only.*
            """
        )
        st.caption(
            "Questions? Check Model settings → Retrieval and indexing, or the README.")


def render_sidebar(pages: dict[str, Any], active_key: str) -> None:
    """Draw the full sidebar and return any files staged in the uploader.

    Args:
        pages: ``{key: st.Page}`` from ``app.py``, used for ``st.switch_page``.
        active_key: key of the page currently running, so its nav row highlights.
    """
    _render_brand()

    if st.sidebar.button(
        "New chat",
        key="new_chat",
        icon=":material/add:",
        type="primary",
        width="stretch",
    ):
        logger.info('New chat button clicked')
        chat_id = st.session_state.get("current_chat_id")
        record = chat.load_chat(chat_id)
        record = record if chat.is_chat_empty(
            record) else chat.new_chat()

        st.session_state["current_chat_id"] = record["chat_id"]
        logger.info(record["title"])
        logger.info(record["chat_id"])
        st.switch_page(pages["chat"])

    _render_nav(pages, active_key)

    if active_key in ("chat", "arena"):
        _render_knowledge_source()

    _render_appearance()


def _render_appearance() -> None:
    """Show the live theme + where to switch it.

    Streamlit reserves theme switching to the viewer (⋮ → Settings), app
    code cannot flip native widgets — so this row only *displays* the
    effective theme (``theme.effective_theme()``) and points at the control.
    """
    mode = effective_theme()
    is_dark = mode == "dark"
    st.sidebar.html(
        f"""
        <div style="margin-top:14px; padding-top:12px;
                    border-top:1px solid var(--surface-high);
                    display:flex; align-items:center; gap:8px;">
            <span style="color:var(--muted); display:inline-flex;">
                {icon("dark_mode" if is_dark else "light_mode", 15)}
            </span>
            <span style="font-size:12px; font-weight:600;
                         color:var(--on-surface-variant);">
                {"Dark" if is_dark else "Light"} mode
            </span>
        </div>
        """
    )
    st.sidebar.caption("Switch theme via ⋮ → Settings → Appearance.")
