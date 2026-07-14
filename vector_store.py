"""A minimal vector store built on NumPy + JSON — no vector database.

Embeddings live in one NumPy matrix of shape (n_chunks, dim); the matching
metadata (filename, chunk_id, text) lives in a parallel Python list. Row i
of the matrix belongs to entry i of the metadata list. Persistence is just
two files on disk: embeddings.npy and metadata.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

STORE_DIR: str = "store"
EMBEDDINGS_FILE: str = "embeddings.npy"
METADATA_FILE: str = "metadata.json"

Metadata = Dict[str, Union[str, int]]


class VectorStore:
    """Stores chunk embeddings and metadata, with save/load/search."""

    def __init__(self) -> None:
        """Create an empty store."""
        self.embeddings: Optional[np.ndarray] = None  # shape (n_chunks, dim)
        self.metadata: List[Metadata] = []

    def __len__(self) -> int:
        """Number of chunks currently stored."""
        return len(self.metadata)

    @property
    def num_documents(self) -> int:
        """Number of distinct source files in the store."""
        return len({meta["filename"] for meta in self.metadata})

    def add(self, embeddings: np.ndarray, metadata: List[Metadata]) -> None:
        """Add new embeddings and their metadata to the store.

        Args:
            embeddings: Array of shape (n_new, dim).
            metadata: One metadata dict per embedding row, same order.

        Raises:
            ValueError: If the row count and metadata length do not match.
        """
        if embeddings.shape[0] != len(metadata):
            raise ValueError(
                f"Got {embeddings.shape[0]} embeddings but {len(metadata)} metadata entries."
            )
        if self.embeddings is None:
            self.embeddings = embeddings.astype(np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings.astype(np.float32)])
        self.metadata.extend(metadata)

    def search(self, query_vector: np.ndarray, k: int) -> List[Tuple[float, Metadata]]:
        """Find the k stored chunks most similar to the query vector.

        Uses the hand-written cosine similarity from retriever.py.

        Args:
            query_vector: 1-D array of shape (dim,).
            k: How many results to return.

        Returns:
            A list of (score, metadata) tuples, best match first.
        """
        # Imported here (not at module top) to avoid a circular import:
        # retriever.py imports nothing from this module, but keeping the
        # dependency local makes each module independently importable.
        from retriever import cosine_similarity

        if self.embeddings is None or len(self.metadata) == 0:
            return []

        scores = cosine_similarity(self.embeddings, query_vector)
        k = min(k, len(scores))
        # argsort is ascending, so take the last k indices and reverse them.
        top_indices = np.argsort(scores)[-k:][::-1]
        return [(float(scores[i]), self.metadata[i]) for i in top_indices]

    def save(self, store_dir: str = STORE_DIR) -> None:
        """Persist the store to disk as embeddings.npy + metadata.json.

        Args:
            store_dir: Directory to write into (created if missing).
        """
        directory = Path(store_dir)
        directory.mkdir(parents=True, exist_ok=True)
        if self.embeddings is not None:
            np.save(directory / EMBEDDINGS_FILE, self.embeddings)
        with open(directory / METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, store_dir: str = STORE_DIR) -> Optional["VectorStore"]:
        """Load a store from disk, or return None if no store exists.

        Args:
            store_dir: Directory containing embeddings.npy and metadata.json.

        Returns:
            A populated VectorStore, or None if the files are missing.
        """
        directory = Path(store_dir)
        emb_path = directory / EMBEDDINGS_FILE
        meta_path = directory / METADATA_FILE
        if not emb_path.exists() or not meta_path.exists():
            return None

        store = cls()
        store.embeddings = np.load(emb_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            store.metadata = json.load(f)
        return store

    @staticmethod
    def clear(store_dir: str = STORE_DIR) -> None:
        """Delete the persisted store files from disk.

        Args:
            store_dir: Directory containing the store files.
        """
        directory = Path(store_dir)
        for name in (EMBEDDINGS_FILE, METADATA_FILE):
            path = directory / name
            if path.exists():
                path.unlink()
