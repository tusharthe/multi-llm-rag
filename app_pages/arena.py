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
from graph import graph
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
preferences = record.get('preferences', {})

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
        record['preferences'] = {}
        chat.save_chat(record)
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

# Pure compare-viewer: show the latest turn that all models answered.
turn_groups = chat.group_turn_ids(record)
expected = set(MODEL_LABELS)
last_shared = None
for g in reversed(turn_groups):
    if expected.issubset(set(g["answers"].keys())):
        last_shared = g
        break

if not turn_groups or last_shared is None:
    empty_state(
        "compare_arrows",
        "No comparison yet",
        "Ask a question below to see all three models answer it side by side.",
    )
else:
    turn_id = last_shared["turn_id"]
    pref = preferences.get(turn_id)
    columns = st.columns(len(MODEL_LABELS), gap="medium")

    for column, label in zip(columns, MODEL_LABELS):
        answer = last_shared["answers"].get(label)
        is_preferred = (pref == label)

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
                    if turn_id is None:
                        st.warning("This chat predates preference tracking.")
                    elif is_preferred:
                        preferences.pop(turn_id)
                    else:
                        preferences[turn_id] = label
                    record['preferences'] = preferences
                    chat.save_chat(record)
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

thinking_placeholder = st.empty()
prompt = st.chat_input("Ask all models a question…")

if prompt:
    if prompt.text and prompt.text.strip():
        with thinking_placeholder:
            with st.status("Thinking with all 3 models…  retrieving + generating in parallel", expanded=True) as status:
                st.write("Retrieving relevant chunks from your documents…")
                collection = chat.collection_name(chat_id)
                final_state = graph.invoke(
                    {"query": prompt.text, "collection": collection})
                st.write(f"Generating answers ({len(final_state.get('answers', {}))} models)…")
                chat.record_compare_turn(
                    chat_id, prompt.text, final_state["answers"],
                    docs=final_state.get("docs"),
                    stats=final_state.get("stats"))
                status.update(label="Answer ready", state="complete", expanded=False)
        # Auto-rename on first message (one time)
        try:
            fresh = chat.load_chat(chat_id)
            if fresh.get("title", "New chat") == "New chat":
                clean = prompt.text.strip().replace("\n", " ")[:50].strip()
                if clean:
                    chat.rename_chat(chat_id, clean)
        except Exception:
            pass
    st.rerun()
