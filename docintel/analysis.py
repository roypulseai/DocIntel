"""LLM-backed analysis nodes — classification, sentiment, summary, QA.

Uses LangChain-Groq (openai/gpt-oss or qwen via Groq free tier).

API key / model are passed explicitly per call (from the Streamlit session,
or falling back to environment variables / .env). They are never read from or
written to a process-global that would leak one user's key to every concurrent
session in a shared deployment.
"""

from __future__ import annotations

import json
import os
import re
import time

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Character budget for a single LLM call; documents longer than this are
# processed with a chunk-and-map-reduce strategy instead of being truncated.
# A document that must be read in more than one pass is reduced by combining
# per-pass results.
_CLASSIFY_CHUNK_CHARS = 3000
_SENTIMENT_CHUNK_CHARS = 3000
_SUMMARY_CHUNK_CHARS = 6000


def _get_llm(temperature: float = 0.0, api_key: str | None = None, model: str | None = None) -> ChatGroq:
    """Return a Groq-backed ChatGroq instance.

    Prefers the explicit *api_key* / *model* (per-session), falling back to
    environment variables / .env.
    """
    return ChatGroq(
        model=model or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=api_key or os.environ.get("GROQ_API_KEY", ""),
        temperature=temperature,
    )


def _llm_invoke(llm, prompt: str, attempts: int = 4) -> object:
    """Invoke *llm* with retries on rate limits / transient errors.

    Uses exponential backoff for 429 and 5xx-style errors, re-raising other
    errors immediately. Returns the model response (with ``.content``).
    """
    import groq

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return llm.invoke([HumanMessage(content=prompt)])
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            is_rate = isinstance(exc, groq.RateLimitError) or "rate" in str(exc).lower()
            is_transient = isinstance(
                exc, (groq.APITimeoutError, groq.APIConnectionError, groq.InternalServerError)
            )
            if not (is_rate or is_transient) or attempt == attempts:
                raise exc
            time.sleep(min(2 ** attempt, 30))
    raise last_exc  # pragma: no cover


def _parse_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from LLM output.

    Returns an empty dict if the output can't be parsed as JSON, so
    downstream code never crashes on a malformed model response.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    try:
        if start != -1 and end > start:
            parsed = json.loads(text[start:end])
        else:
            parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """Split *text* into chunks of at most *max_chars* chars.

    Splits on sentence boundaries where possible so each chunk stays readable.
    A single over-long sentence (no break) is hard-split into its own chunks.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        # Hard-split any single over-long sentence into its own chunks.
        while len(sent) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sent[:max_chars])
            sent = sent[max_chars:]
        if not sent:
            continue
        if len(current) + len(sent) + 1 > max_chars:
            if current:
                chunks.append(current)
            current = sent
        else:
            current = (current + " " + sent).strip()
    if current:
        chunks.append(current)
    return chunks


def _llm(api_key: str | None, model: str | None) -> ChatGroq:
    return _get_llm(api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

_CLASSIFY_PROMPT = (
    "You are a document classifier. Classify the following document "
    "into a category and provide a confidence score.\n\n"
    "Respond with ONLY a JSON object (no markdown fences):\n"
    '{{"category": "<string>", "confidence": <float 0-1>, "rationale": "<string>"}}\n\n'
    "Document:\n{text}"
)


def _classify_chunk(llm, text: str) -> dict:
    return _parse_json(_llm_invoke(llm, _CLASSIFY_PROMPT.format(text=text)).content)


def classify_document(text: str, api_key: str | None = None, model: str | None = None) -> dict:
    """Zero-shot document classification via Groq (GPT-OSS).

    Long documents are classified chunk-wise and the highest-confidence
    category is selected, so no part of the document is silently dropped.
    """
    llm = _llm(api_key, model)
    chunks = _chunk_text(text, _CLASSIFY_CHUNK_CHARS)

    results = [_classify_chunk(llm, c) for c in chunks]
    results = [r for r in results if r.get("category")]

    if not results:
        return {}

    # Pick the category with the highest confidence (majority in ties).
    best = max(
        results,
        key=lambda r: (r.get("confidence", 0), sum(1 for x in results if x.get("category") == r.get("category"))),
    )
    best["category"] = best.get("category", "Unclassified")
    if len(results) > 1:
        best["rationale"] = (
            f"{best.get('rationale', '')} (classified from {len(chunks)} document sections)"
        ).strip()
    return best


# ---------------------------------------------------------------------------
# Sentiment & Topics
# ---------------------------------------------------------------------------

_SENTIMENT_PROMPT = (
    "Analyze the sentiment and extract key topics from the following document.\n\n"
    "Respond with ONLY a JSON object (no markdown fences):\n"
    '{{"sentiment": "<positive|negative|neutral|mixed>", '
    '"sentiment_score": <float -1.0 to 1.0>, '
    '"topics": ["<topic1>", "<topic2>", ...]}}\n\n'
    "Document:\n{text}"
)


def _sentiment_chunk(llm, text: str) -> dict:
    return _parse_json(_llm_invoke(llm, _SENTIMENT_PROMPT.format(text=text)).content)


def sentiment_and_topics(text: str, api_key: str | None = None, model: str | None = None) -> dict:
    """Sentiment polarity + topic extraction via Groq (GPT-OSS).

    Long documents are analysed chunk-wise; per-chunk scores are averaged and
    topics merged, so the result reflects the whole document.
    """
    llm = _llm(api_key, model)
    chunks = _chunk_text(text, _SENTIMENT_CHUNK_CHARS)

    results = [_sentiment_chunk(llm, c) for c in chunks]
    results = [r for r in results if r.get("sentiment") or "sentiment_score" in r]

    if not results:
        return {}

    scores = [
        r.get("sentiment_score", 0.0) for r in results if isinstance(r.get("sentiment_score"), (int, float))
    ]
    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0

    # Dominant sentiment across chunks (majority), falling back to continuous.
    sentiments = [r.get("sentiment", "neutral") for r in results if r.get("sentiment")]
    if sentiments:
        dominant = max(set(sentiments), key=sentiments.count)
    else:
        dominant = "positive" if avg_score > 0.15 else ("negative" if avg_score < -0.15 else "neutral")

    topics: list[str] = []
    seen = set()
    for r in results:
        for t in r.get("topics", []):
            if isinstance(t, str) and t.strip() and t.strip().lower() not in seen:
                seen.add(t.strip().lower())
                topics.append(t.strip())
    if len(chunks) > 1 and not topics:
        topics = ["(document analysed in multiple sections)"]

    return {"sentiment": dominant, "sentiment_score": avg_score, "topics": topics}


# ---------------------------------------------------------------------------
# RAG QA
# ---------------------------------------------------------------------------

def generate_answer(question: str, chunks: list[str], api_key: str | None = None, model: str | None = None) -> dict:
    """Answer *question* grounded in retrieved *chunks* with cited sources."""
    llm = _llm(api_key, model)
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
    resp = _llm_invoke(llm, prompt)
    return _parse_json(resp.content)


# ---------------------------------------------------------------------------
# Summary & key insights
# ---------------------------------------------------------------------------

_SUMMARY_PROMPT = (
    "You are an expert document analyst. Read the following document section "
    "and produce a concise summary plus the most important key insights.\n\n"
    "Respond with ONLY a JSON object (no markdown fences):\n"
    '{{"summary": "<2-4 sentence overview of this section>", '
    '"key_insights": ["<insight 1>", "<insight 2>", ...]}}\n\n'
    "Document:\n{text}"
)

_COMBINE_PROMPT = (
    "You are an expert document analyst. Below are summaries of the sections "
    "of a longer document. Combine them into ONE cohesive executive summary "
    "of the WHOLE document, and list the most important key insights across "
    "all sections.\n\n"
    "Section summaries:\n{parts}\n\n"
    "Respond with ONLY a JSON object (no markdown fences):\n"
    '{{"summary": "<3-6 sentence overview of the whole document>", '
    '"key_insights": ["<insight 1>", "<insight 2>", ...]}}\n'
)


def _summary_chunk(llm, text: str) -> dict:
    return _parse_json(_llm_invoke(llm, _SUMMARY_PROMPT.format(text=text)).content)


def _combine_summaries(llm, items: list[dict], char_budget: int) -> dict:
    """Reduce a list of per-chunk ``{summary, key_insights}`` into one result."""
    # Build a compact combined prompt from the per-chunk summaries.
    parts = []
    for i, it in enumerate(items, 1):
        summary = (it.get("summary") or "").strip()
        insights = it.get("key_insights") or []
        parts.append(f"[Section {i}] {summary}")
        for k in insights:
            if isinstance(k, str):
                parts.append(f"  - {k}")
    combined = "\n".join(parts)[:char_budget]
    return _parse_json(_llm_invoke(llm, _COMBINE_PROMPT.format(parts=combined)).content)


def summarize_document(text: str, api_key: str | None = None, model: str | None = None) -> dict:
    """Extract an executive summary and key insights from the document.

    Short documents are summarised in one pass. Long documents use a
    map-reduce strategy: each section is summarised, then the per-section
    summaries are combined into a final whole-document summary.
    """
    llm = _llm(api_key, model)
    chunks = _chunk_text(text, _SUMMARY_CHUNK_CHARS)

    if len(chunks) == 1:
        return _parse_json(_llm_invoke(llm, _SUMMARY_PROMPT.format(text=chunks[0])).content)

    per_section = [_summary_chunk(llm, c) for c in chunks]
    # Combine with a budget generous enough to hold all section summaries.
    return _combine_summaries(llm, per_section, char_budget=5000 * max(1, len(chunks)))
