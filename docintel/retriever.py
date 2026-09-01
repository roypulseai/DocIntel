"""TF-IDF retrieval — classical IR, no external services required."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_words: int = 200) -> list[str]:
    """Split *text* into sentence-aware chunks of at most *max_words* words."""
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
# Retrieval
# ---------------------------------------------------------------------------

@dataclass
class RetrievalHit:
    text: str
    score: float
    index: int


class TfidfRetriever:
    """Thin wrapper around scikit-learn TF-IDF + cosine similarity."""

    def __init__(self, chunks: list[str]):
        self._chunks = chunks
        self._empty = False
        try:
            self._vectorizer = TfidfVectorizer(stop_words="english")
            self._matrix = self._vectorizer.fit_transform(chunks)
        except ValueError as exc:
            # Empty vocabulary (every chunk is stop words / punctuation /
            # numbers). Fall back to an unfiltered vectorizer so trivial /
            # degenerate inputs can still be searched instead of crashing.
            if "empty vocabulary" not in str(exc):
                raise
            import numpy as np
            try:
                self._vectorizer = TfidfVectorizer(stop_words=None)
                self._matrix = self._vectorizer.fit_transform(chunks)
            except ValueError:
                # No tokens at all (e.g. blank/whitespace input) — nothing to
                # match. Mark the retriever empty so retrieval returns nothing
                # rather than raising.
                self._empty = True
                self._vectorizer = None
                self._matrix = np.zeros((len(chunks), 1))

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        """Return the *top_k* most similar chunks for *query*."""
        if self._empty or not self._chunks:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            RetrievalHit(text=self._chunks[idx], score=float(score), index=idx)
            for idx, score in ranked[:top_k]
            if score > 0
        ]
