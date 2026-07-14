"""Embeddings: turn text chunks into vectors using the OpenAI API.

Texts are sent in batches (the API accepts a list per call) to keep the
number of HTTP requests small. The result is one NumPy array with one row
per input text.
"""

import os
from typing import List

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Configurable constants.
EMBED_MODEL: str = "text-embedding-3-small"
EMBED_BATCH_SIZE: int = 100

load_dotenv()


class EmbeddingError(Exception):
    """Raised when the embedding API call fails."""


def get_client() -> OpenAI:
    """Create an OpenAI client from the OPENAI_API_KEY in the environment.

    Returns:
        A configured OpenAI client.

    Raises:
        EmbeddingError: If the API key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return OpenAI(api_key=api_key)


def embed_texts(texts: List[str], batch_size: int = EMBED_BATCH_SIZE) -> np.ndarray:
    """Embed a list of texts into a single NumPy array.

    Args:
        texts: The chunk texts to embed.
        batch_size: How many texts to send per API call.

    Returns:
        An array of shape (len(texts), dim), dtype float32.

    Raises:
        EmbeddingError: If any API call fails or texts is empty.
    """
    if not texts:
        raise EmbeddingError("No texts to embed.")

    client = get_client()
    all_vectors: List[List[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        try:
            response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        except Exception as exc:
            raise EmbeddingError(f"Embedding API call failed: {exc}") from exc
        # The API returns embeddings in the same order as the input batch.
        all_vectors.extend(item.embedding for item in response.data)

    return np.array(all_vectors, dtype=np.float32)


def embed_query(question: str) -> np.ndarray:
    """Embed a single question into one vector.

    Args:
        question: The user's question.

    Returns:
        A 1-D array of shape (dim,), dtype float32.

    Raises:
        EmbeddingError: If the API call fails.
    """
    return embed_texts([question])[0]
