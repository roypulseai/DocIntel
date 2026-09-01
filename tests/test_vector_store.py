"""Tests for the FAISS vector store (semantic search + persistence)."""
import json
import os

import pytest

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from docintel.vector_store import VectorStore  # noqa: E402


@pytest.fixture
def vs():
    store = VectorStore()
    store.add_document(
        "I was charged CHF 340.00 twice. Please refund the duplicate amount.", "complaint.txt"
    )
    store.add_document(
        "The Senate voted 67-33 to advance the AI Accountability Act.", "news.txt"
    )
    store.add_document(
        "CloudVault agrees to 99.95% uptime SLA for health records.", "contract.txt"
    )
    store.build_index()
    return store


def test_indexes_all_documents(vs):
    assert len(vs) == 3


def test_semantic_search_ranks_correct_document(vs):
    hits = vs.search("refund money", top_k=3)
    assert hits, "semantic search should return hits"
    assert hits[0].source == "complaint.txt", f"Expected complaint first, got {hits[0].source}"


def test_persistence_round_trip(vs):
    db_data = vs.to_db()
    json.dumps(db_data)  # must be JSON-serializable (saved to SQLite)
    restored = VectorStore.from_db(db_data)
    h2 = restored.search("uptime SLA", top_k=1)
    assert h2 and h2[0].source == "contract.txt", f"Expected contract, got {h2}"


def test_merge(vs):
    vs2 = VectorStore()
    vs2.add_document("The provider guarantees AES-256 encryption.", "policy.txt")
    vs2.build_index()
    merged = VectorStore.merge([vs, vs2])
    h3 = merged.search("encryption", top_k=1)
    assert h3 and h3[0].source == "policy.txt"


def test_substore_per_document_vectors(vs):
    sub = vs.substore("complaint.txt")
    assert sub._sources == ["complaint.txt"]
    assert sub.search("refund")[0].source == "complaint.txt"
    roundtrip = VectorStore.from_db(sub.to_db())
    assert roundtrip.search("refund") and roundtrip.search("refund")[0].source == "complaint.txt"


def test_search_returns_empty_on_unbuilt_or_blank_store():
    empty = VectorStore()
    assert empty.search("anything") == []
