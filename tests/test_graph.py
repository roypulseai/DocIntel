"""
DocIntel test suite.

Design note: the Groq-backed nodes (classify, sentiment_topic, qa) are
exercised here with the API client mocked, so the suite runs deterministically
in CI without a live key. The NER (spaCy), chunking, TF-IDF retrieval, and
LangGraph orchestration/state-passing are all executed for real — nothing
about those is mocked. Running `run_demo.py` with a real GROQ_API_KEY
exercises the full pipeline live end to end.
"""
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from docintel.retriever import chunk_text, TfidfRetriever
from docintel.ner import extract_entities
from docintel.graph import run_docintel

SAMPLE = (
    "CUSTOMER COMPLAINT. Maria Fontaine reported a duplicate charge of "
    "CHF 340.00 on transaction TXN-88213-CH at UBS Card Center in Zurich "
    "on 18 August 2026. She requested a refund within five business days."
)


def _fake_message(json_payload: dict):
    msg = MagicMock()
    msg.content = json.dumps(json_payload)
    return msg


def test_ner_runs_for_real():
    entities = extract_entities(SAMPLE)
    labels = {e["label"] for e in entities}
    texts = {e["text"] for e in entities}
    assert "MONEY" in labels or "ORG" in labels
    assert any("Fontaine" in t or "Zurich" in t for t in texts)
    print(f"[PASS] NER extracted {len(entities)} real entities: {[(e['text'], e['label']) for e in entities]}")


def test_chunking_and_retrieval_run_for_real():
    chunks = chunk_text(SAMPLE, max_words=15)
    assert len(chunks) >= 1
    retriever = TfidfRetriever(chunks)
    hits = retriever.retrieve("What was the transaction reference?", top_k=2)
    assert len(hits) >= 1
    assert hits[0].score > 0
    print(f"[PASS] TF-IDF retrieval returned {len(hits)} chunk(s), top score={hits[0].score:.3f}")


@patch("docintel.analysis.ChatGroq")
def test_full_graph_orchestration(mock_llm_cls):
    classify_resp = _fake_message({"category": "Customer Complaint", "confidence": 0.94, "rationale": "Reports a billing dispute."})
    sentiment_resp = _fake_message({"sentiment": "negative", "sentiment_score": -0.4, "topics": ["billing dispute", "refund delay"]})
    qa_resp = _fake_message({"text": "The reference is TXN-88213-CH for CHF 340.00. [Chunk 0]", "sources": [0]})
    summary_resp = _fake_message({"summary": "A customer reports a duplicate charge on their account and requests a refund.", "key_insights": ["Duplicate charge of CHF 340.00", "Refund not yet processed within 5 business days"]})

    mock_instance = MagicMock()
    mock_instance.invoke.side_effect = [classify_resp, sentiment_resp, qa_resp, summary_resp]
    mock_llm_cls.return_value = mock_instance

    os.environ.setdefault("GROQ_API_KEY", "test-key-for-mocking")

    result = run_docintel(text=SAMPLE, question="What is the transaction reference and amount?")

    assert result["classification"]["category"] == "Customer Complaint"
    assert result["sentiment_topic"]["sentiment"] == "negative"
    assert "chunks" in result and len(result["chunks"]) >= 1
    assert "TXN-88213-CH" in result["answer"]["text"]
    assert result["answer"]["sources"], "QA answer should cite retrieved chunk indices"
    assert result["summary"]["summary"], "Pipeline should produce a summary"
    assert len(result["summary"].get("key_insights", [])) >= 2, "Summary should extract key insights"
    print("[PASS] Full LangGraph pipeline: classify -> extract_entities -> sentiment_topic -> build_index -> qa -> summarize")
    print(f"       Final state keys: {list(result.keys())}")


@patch("docintel.analysis.ChatGroq")
def test_empty_question_skips_qa(mock_llm_cls):
    classify_resp = _fake_message({"category": "News", "confidence": 0.8, "rationale": "ok"})
    sentiment_resp = _fake_message({"sentiment": "neutral", "sentiment_score": 0.0, "topics": []})
    summary_resp = _fake_message({"summary": "A short summary.", "key_insights": ["i1"]})

    mock_instance = MagicMock()
    # Only 3 LLM calls expected (classify, sentiment, summarize) — QA is skipped.
    mock_instance.invoke.side_effect = [classify_resp, sentiment_resp, summary_resp]
    mock_llm_cls.return_value = mock_instance

    os.environ.setdefault("GROQ_API_KEY", "test-key-for-mocking")
    result = run_docintel(text=SAMPLE, question="")

    assert result["answer"] == {"text": "", "sources": []}, "Empty question should short-circuit QA"
    assert mock_instance.invoke.call_count == 3, f"Expected 3 LLM calls, got {mock_instance.invoke.call_count}"
    print("[PASS] Empty question skips the QA LLM call (3 calls total)")


if __name__ == "__main__":
    test_ner_runs_for_real()
    test_chunking_and_retrieval_run_for_real()
    test_full_graph_orchestration()
    test_empty_question_skips_qa()
    print("\nAll DocIntel tests passed.")
