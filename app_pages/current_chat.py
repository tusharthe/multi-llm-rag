"""Continue mode -- a normal chat with the ONE model the user picked in Arena.

Reads the active chat record from ``chats/{chat_id}.json`` and renders only the
history belonging to ``active_model``. Each model keeps its own transcript, so
switching models shows a different conversation for the same chat.

UI only for now: the chat input stages a question but no retrieval or model
call is wired up yet.
"""

from __future__ import annotations

import streamlit as st

import chat_history as chat
from components import empty_state, section_label, stat_box
from theme import MODEL_IDS, avatar, icon

chat_id = st.session_state["current_chat_id"]

try:
    record = chat.load_chat(chat_id)
except FileNotFoundError:
    st.error("This chat no longer exists.", icon=":material/error:")
    st.stop()

histories = record.get("histories", {})
active_model = record.get("active_model")

# Continue mode needs a chosen model; fall back to the first one with history
# so a chat that only ever ran in Arena still shows something readable.
if not active_model:
    active_model = next(iter(histories), None)

turns = histories.get(active_model, []) if active_model else []
files = record.get("files", [])

col_chat, col_config = st.columns([2.9, 1.1], gap="large")

# --------------------------------------------------------------------- chat --

with col_chat:
    head_left, head_right = st.columns([2.4, 1], vertical_alignment="center")

    with head_left:
        if active_model:
            st.html(
                f"""
                <div style="display:flex; align-items:center; gap:12px;">
                    {avatar(active_model)}
                    <div>
                        <div class="page-title" style="font-size:24px; margin:0;">
                            {record.get("title", "New chat")}
                        </div>
                        <div style="font-family:'Geist Mono',monospace; font-size:11px;
                                    color:var(--muted); margin-top:2px;">
                            Continuing with {active_model} ·
                            {MODEL_IDS.get(active_model, "--")}
                        </div>
                    </div>
                </div>
                """
            )
        else:
            st.html(
                f'<div class="page-title" style="font-size:24px;">'
                f'{record.get("title", "New chat")}</div>'
                '<div class="page-subtitle" style="margin-bottom:0;">'
                "No model chosen yet — run a comparison in Arena first.</div>"
            )

    with head_right:
        act_a, act_b = st.columns(2)
        if act_a.button(
            "Compare",
            icon=":material/compare_arrows:",
            width="stretch",
            help="Back to the side-by-side Arena view.",
        ):
            st.switch_page("app_pages/arena.py")
        act_b.button("Export", icon=":material/download:", width="stretch")

    if files:
        chips = "".join(
            f'<span class="file-chip">{icon("description", 13)} {name}</span>'
            for name in files
        )
        st.html(
            f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin:16px 0 4px 0;">'
            f"{chips}</div>"
        )

    st.html('<div style="height:12px;"></div>')

    if not turns:
        empty_state(
            "forum",
            "No messages yet",
            "Ask a question below and the answer will appear here.",
        )

    for turn in turns:
        if turn["role"] == "user":
            spacer, bubble = st.columns([1, 3])
            with bubble.container(border=True):
                st.markdown(turn["content"])
        else:
            with st.container(border=True):
                st.html(
                    f"""
                    <div style="display:flex; align-items:center; gap:8px;
                                margin-bottom:2px;">
                        <span class="pill pill-primary">
                            {icon("bolt", 13)} {active_model}
                        </span>
                    </div>
                    """
                )
                st.markdown(turn["content"])

                if turn.get("sources"):
                    with st.expander(
                        "Retrieved context", icon=":material/find_in_page:"
                    ):
                        st.markdown(turn["sources"])

# ------------------------------------------------------------ config panel --

with col_config:
    section_label("Model config")

    with st.container(border=True):
        st.slider(
            "Temperature", 0.0, 1.0, key="temperature", step=0.05,
            help="Higher values make answers more varied.",
        )
        st.slider(
            "Top-p", 0.0, 1.0, key="top_p", step=0.05,
            help="Nucleus sampling cutoff.",
        )
        st.slider(
            "Max tokens", 128, 4096, key="max_tokens", step=128,
            help="Upper bound on answer length.",
        )
        st.slider(
            "Retrieved chunks (k)", 1, 10, key="top_k",
            help="How many context chunks are passed to the model.",
        )

    section_label("Session statistics")
    st.html(
        f"""
        <div class="stat-grid">
            {stat_box("Latency", "--")}
            {stat_box("Tokens", "--")}
            {stat_box("Chunks", str(st.session_state["top_k"]))}
            {stat_box("Turns", str(len(turns) // 2))}
        </div>
        """
    )
    st.caption("Populated once model calls are wired up.")

    section_label("Indexed files")
    if files:
        for name in files:
            st.html(
                f'<div class="mono" style="color:var(--on-surface-variant); '
                f'padding:3px 0;">{icon("description", 14)} {name}</div>'
            )
    else:
        st.caption("No documents indexed for this chat.")

# --------------------------------------------------------------------- input --

prompt = st.chat_input(
    "Ask a question about your documents…",
    accept_file="multiple",
    file_type=["pdf", "txt", "md", "docx"],
)

if prompt:
    st.toast("Retrieval and generation are not wired up yet.", icon=":material/build:")
