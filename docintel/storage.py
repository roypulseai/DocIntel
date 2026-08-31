"""Lightweight SQLite persistence for DocIntel analysis history.

Stores each completed analysis so users can review past results after a
restart. Only the standard library ``sqlite3`` is used - no extra deps.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Any, Optional

from docintel.retriever import RetrievalHit
from docintel.vector_store import SearchHit

_DB_PATH = os.environ.get(
    "DOCINTEL_DB", os.path.join(os.path.dirname(__file__), "..", "docintel_history.db")
)

_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name   TEXT NOT NULL,
        source_kind   TEXT NOT NULL,
        created_at    REAL NOT NULL,
        summary       TEXT,
        category      TEXT,
        confidence    REAL,
        sentiment     TEXT,
        entity_count  INTEGER,
        result_json   TEXT NOT NULL,
        vector_store_json TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at DESC)",
]


class HistoryDB:
    """Thread-safe wrapper around a SQLite analyses table."""

    def __init__(self, path: str = _DB_PATH) -> None:
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True) if os.path.dirname(self.path) else None
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        for _stmt in _SCHEMA_STATEMENTS:
            self._conn.execute(_stmt)
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass

    def _json_safe(self, obj: Any) -> Any:
        """Recursively convert graph-state objects into JSON-safe primitives."""
        if isinstance(obj, dict):
            return {k: self._json_safe(v) for k, v in obj.items() if k != "retriever"}
        if isinstance(obj, (list, tuple)):
            return [self._json_safe(v) for v in obj]
        if isinstance(obj, RetrievalHit):
            return {"text": obj.text, "score": obj.score, "index": obj.index}
        if isinstance(obj, SearchHit):
            return {
                "text": obj.text,
                "score": obj.score,
                "index": obj.index,
                "source": obj.source,
            }
        if isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        return str(obj)

    def save_analysis(
        self,
        source_name: str,
        source_kind: str,
        result: dict[str, Any],
        vector_store_data: dict[str, Any] | None = None,
    ) -> int:
        result = self._json_safe(result)
        summary = result.get("summary", {}).get("summary", "")
        classification = result.get("classification", {})
        category = classification.get("category", "")
        confidence = classification.get("confidence", 0)
        sentiment = result.get("sentiment_topic", {}).get("sentiment", "")
        entities = result.get("entities", [])
        created_at = time.time()
        vs_json = json.dumps(vector_store_data) if vector_store_data else None
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO analyses"
                "(source_name, source_kind, created_at, summary, category,"
                " confidence, sentiment, entity_count, result_json, vector_store_json)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    source_name,
                    source_kind,
                    created_at,
                    summary,
                    category,
                    confidence,
                    sentiment,
                    len(entities),
                    json.dumps(result),
                    vs_json,
                ),
            )
            self._conn.commit()
            return cur.lastrowid

    def list_analyses(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, source_name, source_kind, created_at, summary,"
                " category, confidence, sentiment, entity_count"
                " FROM analyses ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        cols = [
            "id", "source_name", "source_kind", "created_at", "summary",
            "category", "confidence", "sentiment", "entity_count",
        ]
        return [dict(zip(cols, r)) for r in rows]

    def get_analysis(self, analysis_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, source_name, source_kind, created_at, result_json, vector_store_json"
                " FROM analyses WHERE id = ?",
                (analysis_id,),
            ).fetchone()
        if not row:
            return None
        vs_data = json.loads(row[5]) if row[5] else None
        return {
            "id": row[0],
            "source_name": row[1],
            "source_kind": row[2],
            "created_at": row[3],
            "result": json.loads(row[4]),
            "vector_store_data": vs_data,
        }

    def list_analyses_with_vectors(self) -> list[dict[str, Any]]:
        """Return all analyses that have vector store data for cross-doc search."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, source_name, vector_store_json"
                " FROM analyses WHERE vector_store_json IS NOT NULL"
                " ORDER BY created_at DESC"
            ).fetchall()
        results = []
        for row in rows:
            vs_data = json.loads(row[2]) if row[2] else None
            if vs_data:
                results.append({"id": row[0], "source_name": row[1], "vector_store_data": vs_data})
        return results

    def delete_analysis(self, analysis_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            self._conn.commit()

    def delete_all(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM analyses")
            self._conn.commit()
