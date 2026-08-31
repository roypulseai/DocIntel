"""LLM-backed analysis nodes — classification, sentiment, QA.

Uses LangChain-Groq (Llama 3 via Groq free tier) instead of Anthropic Claude.
"""

from __future__ import annotations

import json
import os

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


def _get_llm(temperature: float = 0.0) -> ChatGroq:
    """Return a Groq-backed ChatGroq instance."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    return ChatGroq(model=model, api_key=api_key, temperature=temperature)


def _parse_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return json.loads(text[start:end])
    return json.loads(text)


import re


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_document(text: str) -> dict:
    """Zero-shot document classification via Groq (Llama 3)."""
    llm = _get_llm()
    prompt = (
        "You are a document classifier. Classify the following document "
        "into a category and provide a confidence score.\n\n"
        "Respond with ONLY a JSON object (no markdown fences):\n"
        '{"category": "<string>", "confidence": <float 0-1>, "rationale": "<string>"}\n\n'
        f"Document:\n{text[:3000]}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return _parse_json(resp.content)


# ---------------------------------------------------------------------------
# Sentiment & Topics
# ---------------------------------------------------------------------------

def sentiment_and_topics(text: str) -> dict:
    """Sentiment polarity + topic extraction via Groq (Llama 3)."""
    llm = _get_llm()
    prompt = (
        "Analyze the sentiment and extract key topics from the following document.\n\n"
        "Respond with ONLY a JSON object (no markdown fences):\n"
        '{"sentiment": "<positive|negative|neutral|mixed>", '
        '"sentiment_score": <float -1.0 to 1.0>, '
        '"topics": ["<topic1>", "<topic2>", ...]}\n\n'
        f"Document:\n{text[:3000]}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return _parse_json(resp.content)


# ---------------------------------------------------------------------------
# RAG QA
# ---------------------------------------------------------------------------

def generate_answer(text: str, question: str, chunks: list[str]) -> dict:
    """Answer *question* grounded in retrieved *chunks* with cited sources."""
    llm = _get_llm()
    context = "\n\n".join(f"[Chunk {i}] {c}" for i, c in enumerate(chunks))
    prompt = (
        "You are a helpful document analyst. Answer the user's question using ONLY "
        "the provided context chunks. Cite chunk indices in your answer.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Respond with ONLY a JSON object (no markdown fences):\n"
        '{"text": "<your answer with [chunk N] citations>", '
        '"sources": [<list of chunk indices used>]}\n'
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return _parse_json(resp.content)
