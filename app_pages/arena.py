"""Compare mode -- one column per model, all answering the same question.

Retrieval runs ONCE per question and every model receives the identical
context, which is what makes the comparison fair.

Note on "Mark as preferred": it is a plain human click, recorded per turn. The
app never scores, ranks or computes a winner -- automated judging is explicitly
out of scope (CLAUDE.md), so the Stitch mockup's auto "WINNER" badge is
deliberately not reproduced here.

UI only for now: no graph invocation is wired up yet.
"""

from __future__ import annotations

import streamlit as st

import chat_history as chat
from components import empty_state, model_header, page_header, section_label
from theme import MODEL_IDS, icon

#: Fixed columns. The academic deliverable is always OpenAI + Anthropic +
#: Gemini, whether the backend is a cloud provider or an Ollama stand-in.
MODEL_LABELS = list(MODEL_IDS)

chat_id = st.session_state["current_chat_id"]

try:
    record = chat.load_chat(chat_id)
except FileNotFoundError:
    st.error("This chat no longer exists.", icon=":material/error:")
    st.stop()

histories = record.get("histories", {})

# Preference marks live in session state until the persistence hook in
# chat_history.record_compare_turn is added (CLAUDE.md section 10).
st.session_state.setdefault("preferred", {})

# ------------------------------------------------------------------- header --

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

head_left, head_right = st.columns([2.6, 1], vertical_alignment="center")

with head_left:
    page_header(
        "Arena", "Same question, same context, three models side by side.")

with head_right:
    # act_a = st.columns(1)
    if st.button("Reset", icon=":material/refresh:", width="content"):
        st.session_state["preferred"] = {}
        st.rerun()
    # act_b.button("Export", icon=":material/download:", width="stretch")

# --------------------------------------------------------- last asked prompt --

# Every model stores the same user turns, so read the prompt off whichever
# history exists rather than tracking it separately.
last_prompt = None
for turns in histories.values():
    user_turns = [t for t in turns if t["role"] == "user"]
    if user_turns:
        last_prompt = user_turns[-1]["content"]
        break

if last_prompt:
    with st.container(border=True):
        prompt_col, metric_a, metric_b = st.columns(
            [3, 1, 1], vertical_alignment="center")
        prompt_col.html(
            f"""
            <div class="section-label" style="margin:0 0 6px 0;">Current prompt</div>
            <div style="font-size:15px; font-weight:600; color:var(--on-surface);
                        line-height:1.45;">{last_prompt}</div>
            """
        )
        metric_a.metric("Avg latency", "--")
        metric_b.metric("Documents", len(record.get("files", [])))

st.html('<div style="height:18px;"></div>')

# ------------------------------------------------------------ answer columns --

if not histories:
    empty_state(
        "compare_arrows",
        "No comparison yet",
        "Ask a question below to see all three models answer it side by side.",
    )
else:
    columns = st.columns(len(MODEL_LABELS), gap="medium")

    for column, label in zip(columns, MODEL_LABELS):
        turns = histories.get(label, [])
        answers = [t for t in turns if t["role"] == "assistant"]
        answer = answers[-1]["content"] if answers else None
        is_preferred = st.session_state["preferred"].get(label, False)

        with column:
            with st.container(border=True):
                st.html(model_header(label, available=answer is not None))

                if answer:
                    st.markdown(answer)
                else:
                    st.caption("No answer recorded for this model.")

                st.html('<div style="height:8px;"></div>')

                mark_col, cont_col = st.columns(2)

                # Human-only preference marker -- never computed by the app.
                if mark_col.button(
                    "Preferred" if is_preferred else "Mark",
                    key=f"prefer_{label}",
                    icon=":material/star:" if is_preferred else ":material/star_outline:",
                    type="primary" if is_preferred else "secondary",
                    width="stretch",
                    disabled=answer is None,
                    help="Record that you judged this answer best.",
                ):
                    # One preference per turn: marking a column clears the others.
                    st.session_state["preferred"] = {label: not is_preferred}
                    st.rerun()

                if cont_col.button(
                    "Continue",
                    key=f"continue_{label}",
                    icon=":material/arrow_forward:",
                    width="stretch",
                    disabled=answer is None,
                    help=f"Keep chatting with {label} only.",
                ):
                    chat.set_active_model(chat_id, label)
                    st.switch_page("app_pages/current_chat.py")

# -------------------------------------------------------------------- input --

prompt = st.chat_input("Ask all models a question…")

if prompt:
    st.toast("The comparison graph is not wired up yet.",
             icon=":material/build:")
