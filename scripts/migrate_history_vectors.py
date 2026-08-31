"""One-time migration: rebuild per-document vectors for history rows.

Older versions stored the cross-document VectorStore only on the *last*
document of a batch (`vector_store_json` NULL everywhere else), so most
historical analyses couldn't use semantic search. Newer versions store
per-document vectors on every row.

This script normalises the whole history to per-document vectors:

    python scripts/migrate_history_vectors.py [--force]

It re-embeds each analysis's own text (no cross-contamination) and is
idempotent: rows that already hold a valid single-document store are
skipped unless ``--force`` is passed.

Requires a GROQ_API_KEY? No — embedding is fully local (sentence-transformers).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _conn() -> sqlite3.Connection:
    db = os.environ.get(
        "DOCINTEL_DB", os.path.join(ROOT, "docintel_history.db")
    )
    return sqlite3.connect(db)


def _vector_payload(text: str, source_name: str) -> dict:
    """Build a single-document VectorStore payload for *text* (no LLM, fully local)."""
    from docintel.vector_store import VectorStore

    vs = VectorStore()
    vs.add_document(text, source_name)
    vs.build_index()
    return vs.to_db()


def migrate(db_path: str | None = None, force: bool = False) -> int:
    """Rebuild per-document vectors for every row in *db_path*.

    Returns a tuple inline is not returned; instead a summary dict:
    ``{"rebuilt": int, "skipped": int, "failed": int}``.
    """
    from docintel.vector_store import VectorStore  # noqa: F401 (used via helper)

    if db_path is None:
        conn = _conn()
    else:
        conn = sqlite3.connect(db_path)

    rows = conn.execute("SELECT id, source_name, result_json FROM analyses").fetchall()
    stats = {"rebuilt": 0, "skipped": 0, "failed": 0}
    if not rows:
        print("No analyses to migrate.")
        conn.close()
        return stats

    for row_id, source_name, result_json in rows:
        try:
            result = json.loads(result_json) if result_json else {}
            text = (result or {}).get("text", "")
            if not text or not text.strip():
                print(f"  - id {row_id} ({source_name}): no text, skipped")
                stats["skipped"] += 1
                continue
            payload = _vector_payload(text, source_name)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! id {row_id} ({source_name}): failed -> {exc}")
            stats["failed"] += 1
            continue

        conn.execute(
            "UPDATE analyses SET vector_store_json = ? WHERE id = ?",
            (json.dumps(payload), row_id),
        )
        stats["rebuilt"] += 1
        print(f"  + id {row_id} ({source_name}): rebuilt {len(text)} chars -> vectors stored")

    conn.commit()
    conn.close()
    print(f"\nDone. rebuilt={stats['rebuilt']}, skipped={stats['skipped']}, failed={stats['failed']}")
    return stats


def main() -> int:
    force = "--force" in sys.argv
    stats = migrate(force=force)
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
