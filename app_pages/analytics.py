"""Analytics dashboard -- activity aggregated across every saved chat.

Counts here are derived live from the ``chats/*.json`` records, so they reflect
real usage rather than mockup numbers. Latency and token columns stay blank
until per-turn instrumentation is added around the ``llm.invoke`` calls in
``graph.py`` (CLAUDE.md section 11); a provider that omits ``usage_metadata``
must render a placeholder, never crash.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

import pandas as pd
import streamlit as st

import chat_history as chat
from components import empty_state, page_header, section_label

page_header("Analytics", "Usage across every chat in this workspace.")


@st.cache_data(ttl=30, show_spinner=False)
def collect_stats() -> dict:
    """Aggregate per-turn activity out of the saved chat records.

    Cached briefly so switching pages does not re-read every file; the TTL
    keeps it fresh enough that a new answer shows up almost immediately.
    """
    queries_per_day: Counter[str] = Counter()
    answers_per_model: Counter[str] = Counter()
    documents: set[str] = set()
    docs_per_chat: Counter[str] = Counter()
    total_queries = 0

    for summary in chat.list_chats():
        try:
            record = chat.load_chat(summary["chat_id"])
        except (FileNotFoundError, ValueError):
            continue

        title = record.get("title", "New chat")
        for filename in record.get("files", []):
            documents.add(filename)
            docs_per_chat[filename] += 1

        histories = record.get("histories", {})

        # In compare mode the SAME user turn is copied into every model's
        # history, so counting all of them would multiply the query count by
        # the number of models. Count one model's user turns instead.
        per_model_user_counts = []
        for label, turns in histories.items():
            answers_per_model[label] += sum(1 for t in turns if t["role"] == "assistant")
            per_model_user_counts.append(sum(1 for t in turns if t["role"] == "user"))

        total_queries += max(per_model_user_counts, default=0)

        seen_timestamps: set[str] = set()
        for turns in histories.values():
            for turn in turns:
                if turn["role"] != "user":
                    continue
                stamp = turn.get("created_at")
                if not stamp or stamp in seen_timestamps:
                    continue
                seen_timestamps.add(stamp)
                try:
                    day = datetime.fromisoformat(stamp).strftime("%Y-%m-%d")
                except ValueError:
                    continue
                queries_per_day[day] += 1

        if title:
            docs_per_chat.setdefault(title, docs_per_chat.get(title, 0))

    return {
        "chat_count": len(chat.list_chats()),
        "total_queries": total_queries,
        "documents": documents,
        "queries_per_day": dict(queries_per_day),
        "answers_per_model": dict(answers_per_model),
        "docs_per_chat": dict(docs_per_chat),
    }


stats = collect_stats()

if stats["chat_count"] == 0:
    empty_state(
        "bar_chart",
        "Nothing to report yet",
        "Ask a few questions and this dashboard will fill in.",
    )
    st.stop()

# ------------------------------------------------------------------ metrics --

col_a, col_b, col_c, col_d = st.columns(4, gap="medium")

col_a.metric("Documents indexed", len(stats["documents"]), border=True)
col_b.metric("Total queries", stats["total_queries"], border=True)
col_c.metric("Chats", stats["chat_count"], border=True)
col_d.metric(
    "Avg latency",
    "—",
    border=True,
    help="Needs per-turn instrumentation around llm.invoke in graph.py.",
)

st.html('<div style="height:8px;"></div>')

# ------------------------------------------------------------------- charts --

chart_col, split_col = st.columns([2, 1], gap="large")

with chart_col:
    section_label("Daily request volume")
    per_day = stats["queries_per_day"]
    if per_day:
        frame = (
            pd.DataFrame({"date": list(per_day), "queries": list(per_day.values())})
            .assign(date=lambda df: pd.to_datetime(df["date"]))
            .sort_values("date")
            .set_index("date")
        )
        st.bar_chart(frame, height=260)
    else:
        st.caption("No dated activity recorded yet.")

with split_col:
    section_label("Model usage split")
    per_model = stats["answers_per_model"]
    if per_model:
        frame = pd.DataFrame(
            {"answers": list(per_model.values())}, index=list(per_model)
        )
        st.bar_chart(frame, height=260, horizontal=True)
    else:
        st.caption("No answers recorded yet.")

# -------------------------------------------------------------------- table --

section_label("Indexed documents")

documents = stats["docs_per_chat"]
if documents:
    table = pd.DataFrame(
        {
            "Document": list(documents),
            "Chats using it": list(documents.values()),
        }
    ).sort_values("Chats using it", ascending=False)

    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Chats using it": st.column_config.ProgressColumn(
                "Chats using it",
                min_value=0,
                max_value=max(documents.values()),
                format="%d",
            )
        },
    )
else:
    st.caption("No documents indexed yet.")
