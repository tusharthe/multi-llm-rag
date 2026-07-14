"""Retrieval: hand-written cosine similarity + top-k chunk lookup.

Cosine similarity measures the angle between two vectors, ignoring their
length: 1.0 means "same direction" (very similar meaning), 0.0 means
unrelated. It is written directly in NumPy here — no sklearn, no FAISS —
because implementing it is part of the assignment.
"""

from typing import Dict, List, Union

import numpy as np

from embedder import embed_query
from vector_store import VectorStore

# Default number of chunks to retrieve per question.
TOP_K: int = 4

# A retrieval result: metadata plus the similarity score.
RetrievedChunk = Dict[str, Union[str, int, float]]


def cosine_similarity(matrix: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between each row of a matrix and one vector.

    Formula: sim_i = (A_i · q) / (||A_i|| * ||q||)

    Args:
        matrix: Array of shape (n, dim) — one embedding per row.
        query: Array of shape (dim,) — the question embedding.

    Returns:
        Array of shape (n,) with the similarity of each row to the query.
    """
    # Dot product of every row with the query: shape (n,).
    dots = matrix @ query
    # Norms (vector lengths). A tiny epsilon avoids division by zero for
    # an all-zeros vector (which should not occur with real embeddings).
    row_norms = np.linalg.norm(matrix, axis=1)
    query_norm = np.linalg.norm(query)
    epsilon = 1e-10
    return dots / (row_norms * query_norm + epsilon)


def retrieve_top_k(question: str, store: VectorStore, k: int = TOP_K) -> List[RetrievedChunk]:
    """Embed the question and return the k most similar stored chunks.

    Args:
        question: The user's question in plain text.
        store: The vector store holding all chunk embeddings + metadata.
        k: How many chunks to return.

    Returns:
        A list of dicts, best match first, each containing:
        filename, chunk_id, text, and score (cosine similarity).
    """
    query_vector = embed_query(question)
    results = store.search(query_vector, k)
    return [
        {
            "filename": meta["filename"],
            "chunk_id": meta["chunk_id"],
            "text": meta["text"],
            "score": score,
        }
        for score, meta in results
    ]
