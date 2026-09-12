from logger import logger
import operator
import time
from typing import Annotated, TypedDict, List, Dict, Literal
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from models import get_models
from prompts import SYSTEM_PROMPT, format_context
from rag import get_retriever
from functools import partial

# Nodes are registered once at import for the static set of available models.
# The actual LLM objects are NOT cached here — run_model re-creates them via
# get_models() so live cfg.* (temperature/top_p/max_tokens) from the sliders
# is respected on every query.
_static_models = get_models()


class RetrievalState(TypedDict, total=False):
    query: str                  # user’s question
    docs: List[Document]        # retrieved context
    # Reducer: merge dicts when multiple nodes update `answers` in parallel
    answers: Annotated[Dict[str, str], operator.or_]
    # Same fan-in for per-model instrumentation: {label: stat-dict} where a
    # stat-dict is {latency_s, input_tokens, output_tokens, total_tokens}.
    # Token fields are None when the provider omits usage_metadata (Ollama).
    stats: Annotated[Dict[str, dict], operator.or_]
    active_model: Literal["All", "OpenAI", "Anthropic", "Gemini", None]
    collection: str


def retrieve(state: RetrievalState) -> RetrievalState:
    query = state["query"]

    logger.debug("retrieve node running | state keys=%s", list(state.keys()))

    docs = get_retriever(collection_name=state["collection"]).invoke(query)

    logger.info("Retrieved %d chunks for query: %s", len(docs), query)

    return {"docs": docs}


def run_model(state: RetrievalState, model_label: str) -> RetrievalState:
    """
    model_label: "OpenAI" | "Anthropic" | "Gemini"
    """
    query = state["query"]
    docs = state["docs"]  # same docs for all models

    # Re-create with live cfg so slider changes (temperature/top_p/max_tokens)
    # are picked up without restarting the app.
    live_models = get_models()
    llm = live_models[model_label]

    human_message = format_context(docs) + "\n\n" + query

    # These nodes run in parallel threads, so multi-line banners interleave and
    # become unattributable. One record per event, model label inside it.
    logger.info("[%s] invoking model", model_label)
    logger.debug("[%s] system prompt: %s", model_label, SYSTEM_PROMPT)
    logger.debug("[%s] human message: %s", model_label, human_message)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_message),
    ]

    t0 = time.perf_counter()

    try:
        resp = llm.invoke(messages)

        logger.debug("[%s] raw response: %s", model_label, resp)

        answer = getattr(resp, "content", str(resp))

        logger.info("[%s] answer received (%d chars)",
                    model_label, len(answer))
        logger.info("[%s] answer received (%s chars)",
                    model_label, answer)

        # LangChain's standard usage_metadata ({input_tokens, output_tokens,
        # total_tokens}); None for providers that don't populate it (Ollama).
        meta = getattr(resp, "usage_metadata", None) or {}
        stat = {
            "latency_s": round(time.perf_counter() - t0, 3),
            "input_tokens": meta.get("input_tokens"),
            "output_tokens": meta.get("output_tokens"),
            "total_tokens": meta.get("total_tokens"),
        }

    except Exception:
        logger.exception("Error while invoking %s model", model_label)
        answer = f"[{model_label} error] Check logs for details."
        stat = {
            "latency_s": round(time.perf_counter() - t0, 3),
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        }

    return {
        "answers": {model_label: answer},
        "stats": {model_label: stat},
    }


def collect(state: RetrievalState) -> RetrievalState:
    return state


def model_router(state: RetrievalState) -> list[str]:
    active_model = state.get("active_model")

    # Use a fresh get_models() so a provider that becomes (un)available is
    # reflected, and so the router sees the same key set as run_model.
    live_models = get_models()
    if not active_model or active_model == "All":
        return [f"{k.lower()}_node" for k in live_models.keys()]

    target_node = f"{active_model.lower()}_node"
    all_valid_nodes = [f"{k.lower()}_node" for k in live_models.keys()]

    if target_node in all_valid_nodes:
        return [target_node]

    return [END]


builder = StateGraph(RetrievalState)

builder.add_node("retrieve", retrieve)
builder.add_node("collect", collect)

builder.add_edge(START, "retrieve")

for model_label in _static_models.keys():
    # e.g. "OpenAI_node", "Anthropic_node", "Gemini_node"
    node_name = f"{model_label.lower()}_node"

    builder.add_node(
        node_name,
        lambda state, lbl=model_label: run_model(state, lbl)
    )  # fan-out

    builder.add_edge(node_name, "collect")   # Fan-in: all nodes end at collect

# Conditional Fan-out directly via function
builder.add_conditional_edges("retrieve", model_router)

builder.add_edge("collect", END)

graph = builder.compile()

if __name__ == "__main__":
    graph = builder.compile()

    initial_state = {
        "query": "List the two project names?",
        "collection": "chat_test"
    }

    final_state = graph.invoke(initial_state)

    logger.info("FINAL STATE answers: %s", final_state.get("answers"))
    logger.info("FINAL STATE full: %s", final_state)
