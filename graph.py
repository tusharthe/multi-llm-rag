from logger import logger
import operator
from typing import Annotated, TypedDict, List, Dict
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from models import get_models
from prompts import SYSTEM_PROMPT, format_context
from rag import get_retriever

models = get_models()


class RetrievalState(TypedDict, total=False):
    query: str                  # user’s question
    docs: List[Document]        # retrieved context
    # Reducer: merge dicts when multiple nodes update `answers` in parallel
    answers: Annotated[Dict[str, str], operator.or_]
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

    llm = models[model_label]

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

    try:
        resp = llm.invoke(messages)

        logger.debug("[%s] raw response: %s", model_label, resp)

        answer = getattr(resp, "content", str(resp))

        logger.info("[%s] answer received (%d chars)",
                    model_label, len(answer))
        logger.info("[%s] answer received (%s chars)",
                    model_label, answer)

    except Exception:
        logger.exception("Error while invoking %s model", model_label)
        answer = f"[{model_label} error] Check logs for details."

    return {
        "answers": {model_label: answer},
    }


def collect(state: RetrievalState) -> RetrievalState:
    return state


builder = StateGraph(RetrievalState)

builder.add_node("retrieve", retrieve)
builder.add_node("collect", collect)

builder.add_edge(START, "retrieve")

for model_label in models.keys():
    # e.g. "OpenAI_node", "Anthropic_node", "Gemini_node"
    node_name = f"{model_label}_node"

    def make_node(label: str):
        def node_fn(state: RetrievalState) -> RetrievalState:
            return run_model(state, label)
        return node_fn

    model_node_fn = make_node(model_label)

    builder.add_node(node_name, model_node_fn)
    builder.add_edge("retrieve", node_name)   # fan-out
    builder.add_edge(node_name, "collect")    # fan-in

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
