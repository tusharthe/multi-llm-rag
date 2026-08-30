
from langchain_core.documents import Document
from rag import get_retriever


NOT_FOUND = "I could not find this in the uploaded documents."

SYSTEM_PROMPT = (
    "You are a strict, factual AI assistant specializing in Retrieval-Augmented Generation (RAG). "
    "Your single task is to answer the user's question using ONLY the provided text blocks labeled as 'Retrieved Context'.\n\n"
    "### CRITICAL COMMANDS (FALLBACK & ZERO-HALLUCINATION):\n"
    "1. Rely ONLY on the clear facts directly mentioned in the 'Retrieved Context' below. Do NOT assume, extrapolate, or bring in outside world knowledge.\n"
    "2. If the context does not contain the answer, or if you are even slightly unsure, you must reply EXACTLY with: "
    "'" + NOT_FOUND + "' Do not attempt to guess or answer partially.\n"
    "3. Every factual claim you make MUST be backed by a citation to the specific source chunk it came from.\n\n"
    "### CITATION FORMATTING RULES:\n"
    "- You must append an inline citation format like [1] at the end of every sentence or point that relies on that specific chunk.\n"
    "- If multiple chunks support a statement, list them together, e.g., [1][3].\n"
    "- Never make up a chunk number that is not explicitly defined in the context."
)


def format_context(docs: list[Document]):
    context_blocks = []
    for idx, doc in enumerate(docs, start=1):
        block = f"[{idx}]\n{doc.page_content.strip()}"
        context_blocks.append(block)

    # Standardize output spacing with single blank lines between individual chunks
    joined_context = "\n\n".join(context_blocks)

    return joined_context


def format_sources(docs: list[Document]) -> str:
    """Render retrieved chunks as a display string for the Sources section.

    Mirrors the numbering used in ``format_context`` ([1], [2], ...) so the
    citation numbers in an answer line up with the sources shown below it.
    """
    blocks = []
    for idx, doc in enumerate(docs, start=1):
        filename = doc.metadata.get("source", "unknown")
        chunk_index = doc.metadata.get("chunk_index", "?")
        blocks.append(
            f"[{idx}] **{filename}** (chunk {chunk_index})\n\n"
            f"{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    docs = get_retriever('chat_test').invoke("What this document say?")
    print(format_context(docs))
