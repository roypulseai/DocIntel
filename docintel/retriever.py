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
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        """Return the *top_k* most similar chunks for *query*."""
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            RetrievalHit(text=self._chunks[idx], score=float(score), index=idx)
            for idx, score in ranked[:top_k]
            if score > 0
        ]
