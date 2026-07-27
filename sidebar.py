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
from theme import icon

#: (page key, label, material icon) -- page key matches the registry in app.py.
NAV_ITEMS = [
    ("chat", "Current chat", "forum"),
    ("arena", "Arena", "compare_arrows"),
    ("history", "History", "history"),
    ("analytics", "Analytics", "bar_chart"),
    ("settings", "Model settings", "tune"),
]

MAX_SIDEBAR_CHATS = 8


def _relative_time(iso_timestamp: str | None) -> str:
    """Render an ISO timestamp as a short relative label ("2h ago")."""
    if not iso_timestamp:
        return "--"
    try:
        moment = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return "--"

    seconds = int((datetime.now() - moment).total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    if seconds < 604800:
        return f"{seconds // 86400}d ago"
    return moment.strftime("%d %b")


def _truncate(text: str | None, limit: int = 22) -> str:
    text = (text or "New chat").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _render_brand() -> None:
    st.sidebar.html(
        f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:18px;">
            <div style="background:var(--primary); color:#fff; width:40px; height:40px;
                        border-radius:12px; display:flex; align-items:center;
                        justify-content:center;">
                {icon("hub", 22)}
            </div>
            <div>
                <div style="font-size:16px; font-weight:700; color:var(--on-surface);
                            line-height:1.2;">RAG Hub Pro</div>
                <div style="font-family:'Geist Mono',monospace; font-size:11px;
                            color:var(--muted);">Multi-LLM documents</div>
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


def _render_chat_list(pages: dict[str, Any]) -> None:
    st.sidebar.html('<div class="section-label">Recent chats</div>')

    try:
        chats = chat.list_chats()
    except Exception:
        chats = []

    if not chats:
        st.sidebar.caption("No chats yet — start one above.")
        return

    current_id = st.session_state.get("current_chat_id")

    for item in chats[:MAX_SIDEBAR_CHATS]:
        chat_id = item["chat_id"]
        state = "on" if chat_id == current_id else "off"
        label = f"{_truncate(item.get('title'))}  ·  {_relative_time(item.get('updated_at'))}"

        if st.sidebar.button(
            label,
            key=f"chat_{state}_{chat_id}",
            type="tertiary",
            width="stretch",
        ):
            st.session_state["current_chat_id"] = chat_id
            st.switch_page(pages["chat"])

    if len(chats) > MAX_SIDEBAR_CHATS:
        if st.sidebar.button(
            f"View all {len(chats)} chats",
            key="chat_view_all",
            icon=":material/more_horiz:",
            type="tertiary",
            width="stretch",
        ):
            st.switch_page(pages["history"])


def _render_knowledge_source() -> list[Any]:
    st.sidebar.html('<div class="section-label">Knowledge source</div>')

    uploads = st.sidebar.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
        key="sidebar_uploader",
        label_visibility="collapsed",
        help="PDF, TXT, MD or DOCX — indexed per chat.",
    )

    build_col, clear_col = st.sidebar.columns(2)
    build_col.button(
        "Build",
        key="build_index",
        icon=":material/database:",
        type="primary",
        width="stretch",
        disabled=not uploads,
        help="Embed the staged files into this chat's Chroma collection.",
    )
    clear_col.button(
        "Clear",
        key="clear_index",
        icon=":material/delete_sweep:",
        type="secondary",
        width="stretch",
        help="Drop this chat's collection. Required before changing chunk size.",
    )

    return uploads or []


def _render_footer() -> None:
    # Placeholder counts -- wired to the real Chroma collection once indexing
    # is connected to the UI.
    st.sidebar.html(
        f"""
        <div style="margin-top:18px; padding-top:14px;
                    border-top:1px solid var(--surface-high);">
            <span class="pill pill-success">
                <span class="status-dot"></span> Index ready
            </span>
            <div style="font-family:'Geist Mono',monospace; font-size:10px;
                        color:var(--muted); margin-top:8px;">
                {icon("bolt", 12)} 0 docs &nbsp;·&nbsp; 0 chunks
            </div>
        </div>
        """
    )


def render_sidebar(pages: dict[str, Any], active_key: str) -> list[Any]:
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
        record = chat.new_chat()
        st.session_state["current_chat_id"] = record["chat_id"]
        st.switch_page(pages["chat"])

    _render_nav(pages, active_key)
    _render_chat_list(pages)
    uploads = _render_knowledge_source()
    _render_footer()

    return uploads
