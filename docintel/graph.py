"""LangGraph StateGraph wiring the full DocIntel pipeline.

Pipeline: ingest -> classify -> extract_entities -> sentiment_topic -> build_index -> qa -> END
"""

from __future__ import annotations

import re
from typing import TypedDict

from langgraph.graph import StateGraph, END

from docintel.analysis import (
    classify_document,
    sentiment_and_topics,
    generate_answer,
    summarize_document,
)
from docintel.ner import extract_entities
from docintel.retriever import chunk_text, TfidfRetriever


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

class DocIntelState(TypedDict, total=False):
    text: str
    question: str
    api_key: str | None
    model: str | None
    classification: dict
    entities: list[dict]
    sentiment_topic: dict
    chunks: list[str]
    retriever: object
    hits: list
    answer: dict
    summary: dict


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def _ingest(state: DocIntelState) -> dict:
    return {"text": state["text"]}


def _classify(state: DocIntelState) -> dict:
    return {"classification": classify_document(state["text"], state.get("api_key"), state.get("model"))}


def _extract_entities(state: DocIntelState) -> dict:
    return {"entities": extract_entities(state["text"])}


def _sentiment_topic(state: DocIntelState) -> dict:
    return {"sentiment_topic": sentiment_and_topics(state["text"], state.get("api_key"), state.get("model"))}


def _build_index(state: DocIntelState) -> dict:
    chunks = chunk_text(state["text"])
    retriever = TfidfRetriever(chunks)
    hits = retriever.retrieve(state.get("question", ""), top_k=5)
    return {"chunks": chunks, "retriever": retriever, "hits": hits}


def _qa(state: DocIntelState) -> dict:
    question = state.get("question", "").strip()
    if not question:
        # No question asked (e.g. initial analysis) — skip the LLM call.
        return {"answer": {"text": "", "sources": []}}
    hits = state.get("hits", [])
    chunk_texts = [h.text if hasattr(h, "text") else h["text"] for h in hits]
    answer = generate_answer(question, chunk_texts, state.get("api_key"), state.get("model"))
    return {"answer": answer}


def _summarize(state: DocIntelState) -> dict:
    return {"summary": summarize_document(state["text"], state.get("api_key"), state.get("model"))}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(DocIntelState)
    g.add_node("ingest", _ingest)
    g.add_node("classify", _classify)
    g.add_node("extract_entities", _extract_entities)
    g.add_node("sentiment_topic", _sentiment_topic)
    g.add_node("build_index", _build_index)
    g.add_node("qa", _qa)
    g.add_node("summarize", _summarize)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "classify")
    g.add_edge("classify", "extract_entities")
    g.add_edge("extract_entities", "sentiment_topic")
    g.add_edge("sentiment_topic", "build_index")
    g.add_edge("build_index", "qa")
    g.add_edge("qa", "summarize")
    g.add_edge("summarize", END)

    return g.compile()


_graph = _build_graph()


def run_docintel(text: str, question: str = "", api_key: str | None = None, model: str | None = None) -> dict:
    """Execute the full pipeline and return the final state."""
    result = _graph.invoke(
        {"text": text, "question": question, "api_key": api_key, "model": model}
    )
    if hasattr(result, "get"):
        return result
    return dict(result)
