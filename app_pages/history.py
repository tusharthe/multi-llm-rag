"""Chat history -- every saved conversation, newest first.

Reads the real records written by ``chat_history.py``; ``list_chats`` already
sorts by ``updated_at`` descending, so no extra sorting happens here.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

import chat_history as chat
from components import empty_state, page_header
from theme import MODEL_IDS, icon

EXCERPT_LIMIT = 180

page_header("Chat history", "Revisit, resume or delete a previous session.")


def _format_date(iso_timestamp: str | None) -> str:
    if not iso_timestamp:
        return "--"
    try:
        return datetime.fromisoformat(iso_timestamp).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return "--"


def _excerpt(chat_id: str) -> str:
    """Return the most recent assistant reply from any model, truncated."""
    try:
        record = chat.load_chat(chat_id)
    except (FileNotFoundError, ValueError):
        return "Could not read this chat."

    latest = None
    for turns in record.get("histories", {}).values():
        for turn in turns:
            if turn["role"] != "assistant":
                continue
            if latest is None or turn.get("created_at", "") > latest.get("created_at", ""):
                latest = turn

    if latest is None:
        return "No messages yet."

    text = " ".join(latest["content"].split())
    return text if len(text) <= EXCERPT_LIMIT else text[:EXCERPT_LIMIT] + "…"


try:
    chats = chat.list_chats()
except Exception:
    chats = []

if not chats:
    empty_state(
        "history",
        "No chats yet",
        "Use “New chat” in the sidebar to start your first session.",
    )
    st.stop()

# ------------------------------------------------------------------ toolbar --

search_col, count_col = st.columns([4, 1], vertical_alignment="center")
query = search_col.text_input(
    "Search chats",
    placeholder="Search by title…",
    label_visibility="collapsed",
    icon=":material/search:",
)
count_col.html(
    f'<div class="mono" style="color:var(--muted); text-align:right;">'
    f"{len(chats)} total</div>"
)

if query:
    needle = query.lower()
    chats = [c for c in chats if needle in (c.get("title") or "").lower()]
    if not chats:
        st.caption(f"No chats match “{query}”.")

st.html('<div style="height:10px;"></div>')

# -------------------------------------------------------------------- cards --

current_id = st.session_state.get("current_chat_id")

for item in chats:
    chat_id = item["chat_id"]
    is_current = chat_id == current_id

    with st.container(border=True):
        title_col, action_col = st.columns([3.4, 1], vertical_alignment="center")

        with title_col:
            model = item.get("active_model")
            tag = (
                f'<span class="pill pill-primary">{model} · {MODEL_IDS.get(model, "--")}</span>'
                if model
                else '<span class="pill pill-muted">Compare mode</span>'
            )
            current_tag = (
                '<span class="pill pill-success"><span class="status-dot"></span>Open</span>'
                if is_current
                else ""
            )
            st.html(
                f"""
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                    <span class="history-title">{item.get("title", "New chat")}</span>
                    {tag}{current_tag}
                </div>
                <div class="history-meta">
                    <span>{icon("schedule", 13)} {_format_date(item.get("updated_at"))}</span>
                    <span>{icon("description", 13)} {item.get("file_count", 0)} files</span>
                </div>
                <p class="history-excerpt">{_excerpt(chat_id)}</p>
                """
            )

        with action_col:
            if st.button(
                "Open",
                key=f"open_{chat_id}",
                icon=":material/arrow_forward:",
                type="primary",
                width="stretch",
                disabled=is_current,
            ):
                st.session_state["current_chat_id"] = chat_id
                st.switch_page("app_pages/current_chat.py")

            if st.button(
                "Delete",
                key=f"delete_{chat_id}",
                icon=":material/delete:",
                width="stretch",
            ):
                # Deleting the open chat leaves current_chat_id dangling on
                # purpose -- ensure_active_chat() in app.py re-resolves it to
                # the next most recent chat on the following run.
                chat.delete_chat(chat_id)
                if is_current:
                    st.session_state.pop("current_chat_id", None)
                st.rerun()
