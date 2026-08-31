"""FAISS + sentence-transformers vector store for semantic search.

Uses ``all-MiniLM-L6-v2`` (80 MB, 384-dim, runs on CPU) to embed document
chunks and ``faiss`` to index them for fast nearest-neighbor retrieval.

The store is built incrementally: call ``add_document(text, name)``
once per uploaded file, then ``build_index()`` to finalize.  Queries go
through ``search()`` which returns ranked ``SearchHit`` results tagged
with their source document name and chunk index.

For persistence the vectors and chunks can be serialized to bytes/JSON
via ``to_db()`` / ``from_db()`` — those bytes are stored in SQLite by
the app layer.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

# Lazy globals — loaded once across all stores
_model = None
_model_lock = threading.Lock()
_MODEL_NAME = "all-MiniLM-L6-v2"
_DIMENSION = 384


def _get_model():
    """Return the sentence-transformers model, loading it on first use."""
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
        return _model


def _chunk_text(text: str, max_words: int = 200) -> list[str]:
    """Split text into sentence-aware chunks (duplicated from retriever to
    avoid circular imports — kept intentionally small)."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current_words: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(current_words) + len(words) > max_words and current_words:
            chunks.append(" ".join(current_words))
            current_words = []
        current_words.extend(words)
    if current_words:
        chunks.append(" ".join(current_words))
    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SearchHit:
    text: str
    score: float
    index: int
    source: str


@dataclass
class VectorStore:
    """FAISS-backed vector index over all added documents."""

    _chunks: list[str] = field(default_factory=list)
    _sources: list[str] = field(default_factory=list)
    _chunk_ids: list[int] = field(default_factory=list)
    _vectors: Optional[np.ndarray] = field(default=None)
    _index: Any = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_document(self, text: str, source_name: str) -> None:
        """Chunk *text* and store chunks tagged with *source_name*."""
        new_chunks = _chunk_text(text)
        offset = len(self._chunks)
        self._chunks.extend(new_chunks)
        self._sources.extend([source_name] * len(new_chunks))
        self._chunk_ids.extend(range(offset, offset + len(new_chunks)))
        self._index = None  # invalidate cached index

    def build_index(self) -> None:
        """Compute embeddings and build the FAISS inner-product index."""
        if not self._chunks:
            return
        model = _get_model()
        self._vectors = model.encode(
            self._chunks,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        import faiss
        self._index = faiss.IndexFlatIP(_DIMENSION)
        self._index.add(self._vectors)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> list[SearchHit]:
        """Return the *top_k* most relevant chunks for *query*."""
        if self._index is None or not self._chunks:
            return []
        model = _get_model()
        q_vec = model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(q_vec, k)
        hits: list[SearchHit] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or score < min_score:
                continue
            hits.append(
                SearchHit(
                    text=self._chunks[idx],
                    score=float(score),
                    index=int(self._chunk_ids[idx]),
                    source=self._sources[idx],
                )
            )
        return hits

    # ------------------------------------------------------------------
    # Merging (for cross-store queries)
    # ------------------------------------------------------------------

    @staticmethod
    def merge(stores: list[VectorStore]) -> VectorStore:
        """Merge several built stores into one queryable store."""
        merged = VectorStore()
        offset = 0
        all_chunks, all_sources, all_ids = [], [], []
        vecs: list[np.ndarray] = []
        for s in stores:
            if s._vectors is None:
                continue
            all_chunks.extend(s._chunks)
            all_sources.extend(s._sources)
            all_ids.extend([cid + offset for cid in s._chunk_ids])
            vecs.append(s._vectors)
            offset += len(s._chunks)
        if not all_chunks:
            return merged
        merged._chunks = all_chunks
        merged._sources = all_sources
        merged._chunk_ids = all_ids
        merged._vectors = np.vstack(vecs)
        import faiss
        merged._index = faiss.IndexFlatIP(_DIMENSION)
        merged._index.add(merged._vectors)
        return merged

    # ------------------------------------------------------------------
    # Persistence  (to/from SQLite-compatible bytes/JSON)
    # ------------------------------------------------------------------

    def to_db(self) -> dict[str, Any]:
        """Serialize index data for storage in SQLite (JSON-safe)."""
        import base64
        vec_bytes = (
            self._vectors.tobytes() if self._vectors is not None else None
        )
        return {
            "chunks": self._chunks,
            "sources": self._sources,
            "chunk_ids": self._chunk_ids,
            "dimension": self._vectors.shape[1] if self._vectors is not None else None,
            "vectors_b64": base64.b64encode(vec_bytes).decode("ascii") if vec_bytes is not None else None,
        }

    @classmethod
    def from_db(cls, data: dict[str, Any]) -> VectorStore:
        """Reconstruct a VectorStore from data produced by ``to_db``."""
        import base64
        store = cls()
        store._chunks = data.get("chunks", [])
        store._sources = data.get("sources", [])
        store._chunk_ids = data.get("chunk_ids", [])
        vec_b64 = data.get("vectors_b64")
        dim = data.get("dimension")
        if vec_b64 and dim:
            vec_bytes = base64.b64decode(vec_b64)
            store._vectors = np.frombuffer(vec_bytes, dtype=np.float32).reshape(-1, dim)
            import faiss
            store._index = faiss.IndexFlatIP(dim)
            store._index.add(store._vectors)
        return store

    def __len__(self) -> int:
        return len(self._chunks)
