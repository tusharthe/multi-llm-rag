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
from graph import graph
from logger import logger
from theme import MODEL_IDS, avatar, icon
from config import config as cfg
from rag import get_retriever

chat_id = st.session_state["current_chat_id"]

st.html(
    """
    <style>
        /* 1. Force the main layout wrappers to stay locked at viewport height */
        [data-testid="stAppViewContainer"],
        [data-testid="stMainViewContainer"],
        .main {
            overflow: hidden !important;
            height: 100vh !important;
            max-height: 100vh !important;
        }

        /* 2. Style your target chat box using a custom key assignment */
        .st-key-my_chat_box {
            height: calc(100vh - 170px) !important;
            overflow-y: auto !important;
        }
    </style>
    """
)

st.markdown(
    """
    <style>
        /* 1. Stop global main page from scrolling */
        .stAppDeployContainer, [data-testid="stMain"], [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
            height: 100vh !important;
        }

        /* 2. Target the specific chat container to lock its height to the viewport */
        /* Note: We use the unique key "my_chat_box" which compiles to class .st-key-my_chat_box */
        .st-key-my_chat_box {
            height: calc(100vh - 180px) !important; /* Viewport height minus header/footer padding */
            overflow-y: auto !important; /* Enforce scrolling strictly within this container */
        }
    </style>
    """,
    unsafe_allow_html=True
)

try:
    record = chat.load_chat(chat_id)
except FileNotFoundError:
    st.error("This chat no longer exists.", icon=":material/error:")
    st.stop()

histories = record.get("histories", {})
active_model = record.get("active_model")
files = record.get("files", [])

turn_groups = chat.group_turn_ids(record)

col_chat, col_config = st.columns([2.9, 1.1], gap="large")

upload_status_container = None

with col_chat:

    chat_container = st.container(height=800, border=True,  key="my_chat_box")

    with chat_container:
        head_left, head_right = st.columns(
            [2.4, 1], vertical_alignment="center")

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
                                Next question → {active_model} ·
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
                    "Next question → All 3 models (comparison).</div>"
                )

        with head_right:
            if st.button(
                "Compare",
                icon=":material/compare_arrows:",
                width="content",
                help="Back to Arena. If last answer was single-model, re-runs that question with all 3 (no duplicate).",
            ):
                # Smart Compare: only re-run when last turn is not shared
                if turn_groups:
                    last_group = turn_groups[-1]
                    expected = set(MODEL_IDS.keys()) if isinstance(MODEL_IDS, dict) else set(MODEL_IDS)
                    # Fallback: use MODEL_LABELS size when MODEL_IDS not dict-like
                    try:
                        # MODEL_IDS is dict in theme.py
                        is_shared = expected.issubset(set(last_group["answers"].keys()))
                    except Exception:
                        is_shared = len(last_group["answers"]) >= 3
                    last_query = last_group.get("query")
                    if not is_shared and last_query:
                        try:
                            collection_cmp = chat.collection_name(chat_id)
                            final_state_cmp = graph.invoke(
                                {"query": last_query, "collection": collection_cmp}
                            )
                            # Replace the single-model turn (no duplicate question)
                            chat.delete_turn(chat_id, last_group["turn_id"])
                            chat.record_compare_turn(
                                chat_id,
                                last_query,
                                final_state_cmp["answers"],
                                docs=final_state_cmp.get("docs"),
                            )
                        except Exception:
                            logger.exception("Smart Compare re-run failed")
                            st.error("Compare re-run failed — check logs.", icon=":material/error:")
                            st.stop()
                st.switch_page("app_pages/arena.py")
        upload_status_container = st.empty()
        if st.session_state["upload_file_messages"]:
            results = st.session_state["upload_file_messages"]
            for name, r in results.items():
                if r["ok"]:
                    upload_status_container.success(f"Uploaded {name}")
                else:
                    upload_status_container.error(
                        f"Failed to upload {name}: {r['error']}")
            st.session_state["upload_file_messages"] = {}

        if files:
            st.html(
                '<div style="font-size:10px;height:5px;">Avaiable Documents</div>')
            chips = "".join(
                f'<span class="file-chip">{icon("description", 13)} {name}  {icon("delete", 13)}</span>'
                for name in files
            )
            st.html(
                f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin:16px 0 4px 0;">'
                f"{chips}</div>"
            )

        st.html('<div style="height:12px;"></div>')

        if not turn_groups:
            empty_state(
                "forum",
                "No messages yet",
                "Ask a question below and the answer will appear here.",
            )

        for group in turn_groups:
            if group["query"]:
                spacer, bubble = st.columns([1, 3])
                with bubble.container(border=True):
                    st.markdown(group["query"])

            for model, answer in group["answers"].items():
                with st.container(border=True):
                    st.html(
                        f"""
                        <div style="display:flex; align-items:center; gap:8px;
                                    margin-bottom:2px;">
                            <span class="pill pill-primary">
                                {icon("bolt", 13)} {model}
                            </span>
                        </div>
                        """
                    )
                    st.markdown(answer)
                    is_active = (active_model == model)
                    if st.button(
                        "Active" if is_active else f"Use {model}",
                        key=f"route_{group['turn_id']}_{model}",
                        icon=":material/check:" if is_active else ":material/arrow_forward:",
                        type="primary" if is_active else "secondary",
                        width="content",
                        disabled=is_active,
                        help=f"Next question will be answered by {model}" if not is_active else f"{model} is active",
                    ):
                        chat.set_active_model(chat_id, model)
                        st.rerun()

            if group.get("sources"):
                with st.expander(
                    "Retrieved context", icon=":material/find_in_page:"
                ):
                    st.markdown(group["sources"])

        # --- routing bar: which model answers next ---
        r1, r2 = st.columns([3, 1], vertical_alignment="center")
        with r1:
            st.caption(f"Next → **{active_model if active_model else 'All 3 models'}**")
        with r2:
            if st.button(
                "All 3",
                key="route_all3",
                icon=":material/compare_arrows:",
                width="stretch",
                disabled=active_model is None,
                help="Next question will be answered by all 3 models",
            ):
                chat.set_active_model(chat_id, None)
                st.rerun()

        prompt = st.chat_input(
            "Ask a question about your documents…",
            accept_audio=False,
            accept_file="multiple",
            file_type=["pdf", "txt", "md", "docx"],
        )

with col_config:
    section_label("Model config")

    with st.container(border=True):
        cfg.temperature = st.slider(
            "Temperature", 0.0, 1.0, value=cfg.temperature, step=0.05,
            help="Higher values make answers more varied.",
        )

        cfg.top_p = st.slider(
            "Top-p", 0.0, 1.0, value=cfg.top_p,
            step=0.05, help="Nucleus sampling cutoff.",

        )
        cfg.num_predict = st.slider(
            "Max tokens", 128, 4096,  value=cfg.num_predict, step=128,
            help="Upper bound on answer length.",
        )
        cfg.top_k = st.slider(
            "Retrieved chunks (k)", 1, 10, value=cfg.top_k,
            help="How many context chunks are passed to the model.",
        )

    section_label("Session statistics")
    st.html(
        f"""
        <div class="stat-grid">
            {stat_box("Latency", "--")}
            {stat_box("Tokens", "--")}
            {stat_box("Chunks", str(cfg.top_k))}
            {stat_box("Turns", str(len(turn_groups)))}
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


def process_text(text: str, chat_id: str):
    active_model = chat.get_active_model(chat_id)
    logger.debug("process_text | chat_id=%s active_model=%s",
                 chat_id, active_model)
    collection = chat.collection_name(chat_id)

    if active_model is None:
        final_state = graph.invoke({"query": text, "collection": collection})
        chat.record_compare_turn(
            chat_id, text, final_state["answers"], docs=final_state.get("docs"))
    else:
        final_state = graph.invoke({
            "query": text, "collection": collection, "active_model": active_model,
        })
        ans = None
        for m, a in final_state["answers"].items():
            if m.lower() == active_model.lower():
                ans = a
                break

        if ans is None:
            logger.warning("No answer found for model %s", active_model)

        chat.record_continue_turn(
            chat_id, active_model, text, ans, docs=final_state.get("docs"))

    return final_state["answers"]


if prompt:
    with st.chat_message("user"):
        if prompt.files:
            st.session_state["upload_file_messages"] = chat.upload_file(
                prompt.files, chat_id)
            if prompt.text and prompt.text.strip():
                process_text(prompt.text, chat_id)
        else:
            if prompt.text and prompt.text.strip():
                process_text(prompt.text, chat_id)
        st.rerun()

        # st.toast("Retrieval and generation are not wired up yet.",
        #          icon=":material/build:")
