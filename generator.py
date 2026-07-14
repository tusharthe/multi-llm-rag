"""Generation: build a grounded prompt from retrieved chunks and get an answer.

The model only ever sees the retrieved chunks, numbered [1], [2], ... The
system prompt forbids outside knowledge and requires inline citations, so
every claim in the answer can be traced back to a chunk shown in the UI.
"""

from typing import List

from embedder import get_client
from retriever import RetrievedChunk

# Configurable constants.
CHAT_MODEL: str = "gpt-4o-mini"

SYSTEM_PROMPT: str = (
    "You are a careful assistant that answers questions using ONLY the "
    "numbered context chunks provided by the user. Rules:\n"
    "1. Use ONLY the provided context. Do not use any outside knowledge.\n"
    "2. If the context does not contain the answer, reply exactly: "
    '"I could not find this in the uploaded documents."\n'
    "3. Cite your sources inline using the chunk numbers, e.g. [1] or [2][3], "
    "immediately after each claim they support.\n"
    "4. Be concise and factual."
)


class GenerationError(Exception):
    """Raised when the chat completion API call fails."""


def build_prompt(question: str, chunks: List[RetrievedChunk]) -> str:
    """Build the user message: numbered context chunks + the question.

    Args:
        question: The user's question.
        chunks: Retrieved chunks, in ranked order (best first). Their
            position in this list determines their citation number.

    Returns:
        The full user prompt string.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[{i}] (from {chunk['filename']}, chunk {chunk['chunk_id']})\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    return (
        f"Context chunks:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above, with inline citations like [1]."
    )


def generate_answer(question: str, chunks: List[RetrievedChunk]) -> str:
    """Generate a grounded, cited answer from the retrieved chunks.

    Args:
        question: The user's question.
        chunks: The retrieved chunks to answer from.

    Returns:
        The model's answer text.

    Raises:
        GenerationError: If the API call fails.
    """
    if not chunks:
        return "I could not find this in the uploaded documents."

    client = get_client()
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(question, chunks)},
            ],
            temperature=0,
        )
    except Exception as exc:
        raise GenerationError(f"Answer generation failed: {exc}") from exc

    answer = response.choices[0].message.content
    return answer.strip() if answer else "I could not find this in the uploaded documents."
